"""Syslog UDP 监听守护线程（迁移自 wifi-monitor/syslog_listener.py）。

工作流程：UDP recvfrom → UTF-8/GBK 解码 → 解析时间/等级/消息 →
关键词或严重等级命中 → network_service.record_syslog_alert（落库 + 钉钉）。

设计要点：
- 以 daemon 线程在 FastAPI lifespan 中启动，随进程退出自动结束；
- 监听开关 / 端口 / 关键词全部读 settings 表，界面保存后下一轮自动生效，无需重启；
- socket 阻塞超时 2 秒，使线程能周期性重读配置（开关切换、端口变更）；
- 绑定失败（如 Windows 非管理员占用 514）只打印警告并重试，绝不阻断后端启动；
- 每条日志使用独立 DB Session，处理异常不影响监听循环。
"""
from __future__ import annotations

import re
import socket
import threading
from typing import TYPE_CHECKING

# 「日期时间 + Tab + 剩余内容」格式（旧 wifi-monitor 设备上报格式）
_TS_TAB_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\t+(.*)")
# H3C/标准 Syslog：<PRI>时间戳 主机名 正文（空格分隔），如
# <182>2026-09-04 14:37:46 H3C 系统/6/用户admin从172.16.112.159登录。
_PRI_RE = re.compile(r"^<(\d{1,3})>")
_TS_SPACE_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(.*)$"
)
# RFC3164 英文月份时间（Sep  4 14:37:46 host ...）兜底
_TS_RFC3164_RE = re.compile(
    r"^([A-Z][a-z]{2})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2})\s+(\S+)\s+(.*)$"
)
# PRI 低 3 位为 RFC5424 severity
_SEVERITY = {
    0: "emergency", 1: "alert", 2: "critical", 3: "error",
    4: "warning", 5: "notice", 6: "info", 7: "debug",
}

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def parse_syslog(data: bytes):
    """解析 UDP 报文：兼容 UTF-8 / GBK；返回 dict 或 None。

    支持：
    1. Tab 分隔：``2026-09-04 14:37:46\\t\\twarning\\thost\\t正文``；
    2. H3C/标准 Syslog：``<182>2026-09-04 14:37:46 H3C 正文``（PRI 头可选）；
    3. 无法识别的报文整条作为 raw/message，仍可参与关键词匹配。
    所有分支都保留完整原文 ``raw``，告警时原样转发到钉钉。
    """
    message = None
    for enc in ("utf-8", "gbk"):
        try:
            message = data.decode(enc).strip()
            break
        except (UnicodeDecodeError, LookupError):
            continue
    if not message:
        return None

    raw = message
    level = ""

    # 剥离 <PRI> 头并换算等级（如 <182> → 182&7=6 → info）
    pri = _PRI_RE.match(message)
    if pri:
        severity = int(pri.group(1)) & 7
        level = _SEVERITY.get(severity, "")
        message = message[pri.end():].lstrip()

    # 格式 1：Tab 分隔
    m = _TS_TAB_RE.match(message)
    if m:
        timestamp, rest = m.groups()
        parts = rest.split("\t")
        return {
            "raw": raw,
            "timestamp": timestamp,
            "level": parts[0] if len(parts) > 0 else level,
            "source": parts[1] if len(parts) > 1 else "",
            "message": parts[2] if len(parts) > 2 else rest,
            "full_message": rest,
        }

    # 格式 2：标准 Syslog 空格分隔（时间 + 主机名 + 正文）
    m = _TS_SPACE_RE.match(message)
    if m:
        timestamp, source, rest = m.groups()
        rest = rest.strip()
        return {
            "raw": raw,
            "timestamp": timestamp,
            "level": level,
            "source": source,
            "message": rest,
            "full_message": rest,
        }

    # 格式 3：RFC3164 英文时间（无年份，用当前年补齐）
    m = _TS_RFC3164_RE.match(message)
    if m:
        mon, day, hhmmss, source, rest = m.groups()
        from app.core.timeutil import beijing_now
        year = beijing_now().year
        return {
            "raw": raw,
            "timestamp": f"{year} {mon} {int(day):02d} {hhmmss}",
            "level": level,
            "source": source,
            "message": rest.strip(),
            "full_message": rest.strip(),
        }

    return {"raw": raw, "message": message, "level": level}


def should_alert(parsed: dict, keywords: list[str]) -> bool:
    """消息命中任一关键词，或日志等级属于告警级别 → True。"""
    from app.services.network_service import SYSLOG_ALERT_LEVELS

    msg = parsed.get("message") or parsed.get("raw") or ""
    if any(kw and kw.lower() in msg.lower() for kw in keywords):
        return True
    level = (parsed.get("level") or "").strip().lower()
    return level in SYSLOG_ALERT_LEVELS


def syslog_listener_loop(get_session) -> None:
    """线程主循环：按 settings 动态管理 UDP socket。"""
    sock: socket.socket | None = None
    bound_port: int | None = None
    bind_fail_until = 0.0

    import time
    print("[Syslog] 监听守护线程已启动（默认未开启，可在网络看板「告警设置」中启用）")

    while True:
        db: Session | None = None
        try:
            db = get_session()
            from app.services import network_service
            cfg = network_service.get_settings(db)

            enabled = bool(cfg.get("syslog_enabled"))
            port = int(cfg.get("syslog_port") or 514)

            # 配置变化：关闭旧 socket
            if sock is not None and (not enabled or port != bound_port):
                try:
                    sock.close()
                except OSError:
                    pass
                sock = None
                bound_port = None
                print(f"[Syslog] 已停止监听（enabled={enabled}, port={port}）")

            # 需要开启但未绑定（含失败重试，间隔 5 秒）
            if enabled and sock is None and time.time() >= bind_fail_until:
                try:
                    new_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    new_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    new_sock.bind(("0.0.0.0", port))
                    new_sock.settimeout(2.0)
                    sock = new_sock
                    bound_port = port
                    print(f"[Syslog] 开始监听 UDP 0.0.0.0:{port} ...")
                except OSError as e:
                    print(f"[Syslog] 绑定 UDP {port} 失败（5 秒后重试）：{e}。"
                          f"Windows 下监听 514 需以管理员身份运行，或改用 >1024 端口。")
                    bind_fail_until = time.time() + 5
                    try:
                        new_sock.close()
                    except Exception:
                        pass

            db.close()
            db = None

            if sock is None:
                time.sleep(2)
                continue

            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                continue

            src_ip = addr[0]
            parsed = parse_syslog(data)
            if not parsed:
                continue

            # 每包重新取会话读取最新关键词并写告警
            db = get_session()
            try:
                cfg2 = network_service.get_settings(db)
                kws = [k.strip() for k in (cfg2.get("syslog_keywords") or "").replace("，", ",").split(",")]
                if should_alert(parsed, kws):
                    network_service.record_syslog_alert(db, src_ip, parsed)
            except Exception as e:
                print(f"[Syslog] 处理来自 {src_ip} 的日志失败：{e}")
            finally:
                db.close()
                db = None

        except Exception as e:
            print(f"[Syslog] 监听循环异常：{e}")
            time.sleep(2)
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass


def start_syslog_listener(get_session) -> threading.Thread:
    """启动 daemon 线程并返回线程对象。"""
    t = threading.Thread(
        target=syslog_listener_loop,
        args=(get_session,),
        name="syslog_listener",
        daemon=True,
    )
    t.start()
    return t


__all__ = ["parse_syslog", "should_alert", "start_syslog_listener"]
