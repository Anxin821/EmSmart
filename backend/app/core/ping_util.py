"""Ping 探测 + 日志记录

日志按天切割，存放于 backend/logs/ping/YYYY-MM-DD.log
"""

import os
import platform
import subprocess
from datetime import datetime
from typing import Optional

# backend/logs/ping/
_PING_LOG_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "logs", "ping"
))


def _write_ping_log(ip: str, line: str) -> None:
    try:
        os.makedirs(_PING_LOG_DIR, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        path = os.path.join(_PING_LOG_DIR, f"{date_str}.log")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {line}\n")
    except Exception:
        pass


def ping_device(ip: Optional[str], timeout: int = 2000) -> bool:
    """对指定 IP 执行一次 Ping，记录详细回复到日志，返回是否可达。"""
    if not ip or not isinstance(ip, str):
        return False
    ip = ip.strip()
    try:
        import socket
        socket.inet_aton(ip)
    except (OSError, ValueError):
        return False
    try:
        if platform.system().lower() == "windows":
            result = subprocess.run(
                ["ping", "-n", "1", "-w", str(timeout), ip],
                capture_output=True, timeout=5, shell=False,
            )
        else:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "2", ip],
                capture_output=True, timeout=5, shell=False,
            )

        encoding = "gbk" if platform.system().lower() == "windows" else "utf-8"
        raw = (result.stdout or b"").decode(encoding, errors="replace")
        for ln in raw.splitlines():
            ln = ln.strip()
            if not ln:
                continue
            if any(kw in ln for kw in ("来自", "回复", "请求超时", "无法访问",
                                       "time=", "TTL=", "ttl=",
                                       "timeout", "unreachable", "timed out")):
                _write_ping_log(ip, ln)

        return result.returncode == 0
    except Exception:
        return False