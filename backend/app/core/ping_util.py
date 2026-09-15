"""Ping 探测 + 日志记录

日志按天切割，保留 30 天，存放于 backend/logs/ping/ping.log
历史文件自动归入 archive/ 子目录，不干扰日常查看。
"""

import logging
import os
import platform
import re
import subprocess
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

# ── 日志配置（TimedRotatingFileHandler：线程安全、自动跨天、保留 30 天） ──────
_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs" / "ping"
_LOG_ARCHIVE = _LOG_DIR / "archive"
_LOG_DIR.mkdir(parents=True, exist_ok=True)


def _rotator_namer(default_name: str) -> str:
    """轮转时把旧文件放入 archive/ 子目录，避免污染 ping.log 同层目录。"""
    p = Path(default_name)
    _LOG_ARCHIVE.mkdir(parents=True, exist_ok=True)
    return str(_LOG_ARCHIVE / p.name)


_logger = logging.getLogger("ping")
_logger.setLevel(logging.INFO)
if not _logger.handlers:
    _handler = TimedRotatingFileHandler(
        _LOG_DIR / "ping.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    _handler.namer = _rotator_namer
    _handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
    # 不传播到 root logger，避免与 uvicorn 日志混在一起
    _logger.propagate = False
    _logger.addHandler(_handler)


def _write_ping_log(ip: str, line: str) -> None:
    """线程安全地写入 ping 日志。"""
    try:
        _logger.info(f"{ip} - {line}")
    except Exception:
        pass


def ping_device(ip: Optional[str], timeout: int = 2000) -> Optional[int]:
    """对指定 IP 执行一次 Ping，记录详细回复到日志。

    Returns:
        int — RTT 毫秒值（回包可达）；
        None — 不可达、超时或异常。
    """
    if not ip or not isinstance(ip, str):
        return None
    ip = ip.strip()
    try:
        import socket
        socket.inet_aton(ip)
    except (OSError, ValueError):
        return None
    try:
        if platform.system().lower() == "windows":
            result = subprocess.run(
                ["ping", "-n", "1", "-w", str(timeout), ip],
                capture_output=True, timeout=5, shell=False,
            )
        else:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", str(int(timeout / 1000) + 1), ip],
                capture_output=True, timeout=5, shell=False,
            )

        encoding = "gbk" if platform.system().lower() == "windows" else "utf-8"
        raw = (result.stdout or b"").decode(encoding, errors="replace")
        rtt = None
        for ln in raw.splitlines():
            ln = ln.strip()
            if not ln:
                continue
            if any(kw in ln for kw in ("来自", "回复", "请求超时", "无法访问",
                                       "time=", "TTL=", "ttl=",
                                       "timeout", "unreachable", "timed out")):
                _write_ping_log(ip, ln)
            # 提取 RTT：中文 "时间=3ms"/"时间<1ms" 或英文 "time=5ms"/"time<1ms"
            if rtt is None:
                m = re.search(r"(?:时间|time)([=:<])\s*(\d+)", ln, re.IGNORECASE)
                if m:
                    sep, digits = m.group(1), m.group(2)
                    # "时间<1ms" 表示 <1ms，返回 0；其他情况取实际毫秒值
                    rtt = 0 if sep == "<" and digits == "1" else int(digits)
        if result.returncode == 0 and rtt is not None:
            _write_ping_log(ip, f"OK rtt={rtt}ms")   # ★ 强制记录：每次 ping 必留一行
            return rtt
        _write_ping_log(ip, f"FAIL (rc={result.returncode})")  # ★ 不通也记录
        return None
    except Exception:
        return None