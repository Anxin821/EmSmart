"""后台定时任务：服务器健康检查（异步轮询，更新数据库状态字段）。

从 main.py 拆出以保持入口文件简洁。
"""
from __future__ import annotations

import asyncio
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Dict, Optional, Tuple

from app.core.ping_util import ping_device
from app.core.timeutil import beijing_now

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.core.database import SessionLocal  # noqa: F401  (只做类型提示避免循环 import)

# 模块级线程池：SSH 健康检查专用，避免每轮创建/销毁的开销
_SERVER_POOL = ThreadPoolExecutor(max_workers=20, thread_name_prefix="srv_probe")


def _tcp_open(host: str, port: int = 22, timeout: float = 0.8) -> bool:
    """TCP 端口连通检测。不通直接 False。"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


def _tcp_open_multi(host: str, ports=(22, 3389, 80, 443), timeout: float = 1.0) -> bool:
    """多端口 TCP 探测，兼容 Windows / 嵌入式设备。"""
    for port in ports:
        if _tcp_open(host, port, timeout):
            return True
    return False


def _probe_one(ip: str) -> Tuple[bool, Optional[int]]:
    """Worker：只做网络探测，不碰 DB。返回 (online, rtt)。"""
    rtt = ping_device(ip, 1500)
    if rtt is not None:
        return True, rtt
    return _tcp_open_multi(ip), None


async def check_server_health(get_session) -> None:
    """
    循环：按「Ping 间隔」设置扫描网络设备，更新状态、最后检查时间，
    并对账离线告警（落库 network_alerts + 钉钉推送）。

    并发探测：模块级 ThreadPoolExecutor(max_workers=20) 并发 ping 所有服务器，
    将单轮耗时从「80 × 1.5s = 120s」降至「max(ping 耗时) ≈ 1.5~8s」。

    防抖设计：
    - 连续 2 轮（~30s @ interval=15s）失败才判定离线，减少瞬时抖动误报；
    - 恢复在线立即标记，无须防抖（停机后恢复应尽快通知）；
    - 移除随机 CPU/内存采样，避免运维看到假数据怀疑监控可信度。

    设计：
    - 主循环在 event loop 中用 asyncio.sleep 实现等待，间隔读取 settings 表（默认 15s）；
    - DB 操作与同步网络调用 (socket/subprocess) 放到 loop.run_in_executor 中避免阻塞事件循环；
    - 并发只并发"探测"动作，DB 更新在主线程串行执行（无竞态）；
    - 任何单条 server 报错不影响整体循环（try/except 包裹每条记录）；
    - 服务器由本任务检测（含资源采样）；老化架/WiFi AP 的 Ping 与全量告警对账
      复用 network_service.monitor_tick（迁移自 wifi-monitor 的 ping_task）。
    """
    from app.models import Server as ServerModel

    def _tick():
        db: Session = get_session()
        try:
            servers = db.query(ServerModel).all()
            # 收集需要探测的目标（跳过维护 / 无 IP）
            targets = [
                (s.id, s.ip_address.strip())
                for s in servers
                if s.ip_address and s.ip_address.strip() and s.status != "维护"
            ]
            # ── 并发探测（只做网络 IO，不碰 DB） ──
            results: Dict[int, Tuple[bool, Optional[int]]] = {}
            if targets:
                futures = {_SERVER_POOL.submit(_probe_one, ip): sid for sid, ip in targets}
                for future in as_completed(futures):
                    sid = futures[future]
                    try:
                        online, rtt = future.result()
                        results[sid] = (online, rtt)
                    except Exception:
                        results[sid] = (False, None)

            # ── 主线程串行更新 DB（无竞态） ──
            now = beijing_now()
            changed = False
            for s in servers:
                if s.id not in results:
                    continue
                online, rtt = results[s.id]
                try:
                    if online:
                        # ── 在线 ──
                        if s.status != "在线":
                            s.status = "在线"
                        s.fail_count = 0
                        s.last_latency_ms = rtt
                        s.last_check_time = now
                        s.last_online_time = now
                        changed = True
                    else:
                        # ── 离线（防抖：连续 fail_count >= 3 才判离线，15s×3=45s） ──
                        s.fail_count = (s.fail_count or 0) + 1
                        if s.fail_count >= 3 and s.status != "离线":
                            s.status = "离线"
                            changed = True
                        s.last_check_time = now
                except Exception:
                    continue
            if changed:
                try:
                    db.commit()
                except Exception:
                    db.rollback()
        finally:
            db.close()

    def _monitor_tick() -> int:
        """老化架/AP Ping + 全设备告警对账；返回下一轮间隔秒数（异常回退 60s）。"""
        db: Session = get_session()
        try:
            from app.services import network_service
            return int(network_service.monitor_tick(db) or 60)
        except Exception:
            return 60
        finally:
            db.close()

    loop = asyncio.get_event_loop()
    while True:
        interval = 60
        try:
            await loop.run_in_executor(None, _tick)
            interval = await loop.run_in_executor(None, _monitor_tick)
        except Exception:
            # 本轮任何异常都吞掉，继续下一轮
            pass
        await asyncio.sleep(interval)


__all__ = ["check_server_health"]