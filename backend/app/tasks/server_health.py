"""后台定时任务：服务器健康检查（异步轮询，更新数据库状态字段）。

从 main.py 拆出以保持入口文件简洁。
"""
from __future__ import annotations

import asyncio
import socket
import subprocess
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.core.database import SessionLocal  # noqa: F401  (只做类型提示避免循环 import)


def _ping(host: str, timeout_ms: int = 300) -> bool:
    """Windows PowerShell 下可用的 ICMP ping。不可达返回 False 不抛错。"""
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", str(timeout_ms), host],
            capture_output=True, text=True, timeout=2
        )
        return result.returncode == 0
    except Exception:
        return False


def _tcp_open(host: str, port: int = 22, timeout: float = 0.8) -> bool:
    """更轻量的 TCP 连通检测（默认 22 端口，服务器 ssh）。不通直接 False。"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


async def check_server_health(get_session) -> None:
    """
    循环：每 60 秒扫描 servers 表全部在线设备，更新状态、资源使用率、最后检查时间。

    设计：
    - 主循环在 event loop 中用 asyncio.sleep 实现等待；
    - DB 操作与同步网络调用 (socket/subprocess) 放到 loop.run_in_executor 中避免阻塞事件循环；
    - 任何单条 server 报错不影响整体循环（try/except 包裹每条记录）。
    """
    from app.models import Server as ServerModel

    def _tick():
        db: Session = get_session()
        try:
            servers = db.query(ServerModel).all()
            changed_any = False
            for s in servers:
                try:
                    ip = (s.ip_address or "").strip()
                    if ip:
                        online = _tcp_open(ip, 22, 0.6) or _ping(ip, 400)
                        new_status = "在线" if online else "离线"
                    else:
                        online = False
                        new_status = "维护"  # 没填 IP 时标记维护状态
                    import random
                    # 若在线，模拟轻量资源采样（后续可接入真实 agent；离线归零）
                    if online:
                        cpu = round(random.uniform(5, 55), 1)
                        mem = round(random.uniform(10, 80), 1)
                        disk = round(random.uniform(20, 70), 1)
                    else:
                        cpu = mem = disk = 0
                    if (s.status != new_status or
                            abs((s.cpu_usage or 0) - cpu) > 0.01 or
                            abs((s.memory_usage or 0) - mem) > 0.01 or
                            abs((s.disk_usage or 0) - disk) > 0.01):
                        s.status = new_status
                        s.cpu_usage = cpu
                        s.memory_usage = mem
                        s.disk_usage = disk
                        s.last_check_time = datetime.utcnow()
                        changed_any = True
                except Exception:
                    # 单条失败：跳过，不抛错
                    continue
            if changed_any:
                try:
                    db.commit()
                except Exception:
                    db.rollback()
        finally:
            db.close()

    loop = asyncio.get_event_loop()
    while True:
        try:
            await loop.run_in_executor(None, _tick)
        except Exception:
            # 本轮任何异常都吞掉，继续下一轮
            pass
        await asyncio.sleep(60)


__all__ = ["check_server_health"]
