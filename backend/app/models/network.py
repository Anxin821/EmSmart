"""网络设施（服务器/老化架/WiFi AP）ORM 模型。"""
from .base import Base, Column, Integer, String, Float, DateTime

from app.core.timeutil import beijing_now


class Server(Base):
    """服务器部署表"""
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    production_line = Column(String(10), nullable=False)
    rack_location = Column(String(50))
    ip_address = Column(String(50))
    model = Column(String(100))
    os = Column(String(50))
    status = Column(String(20), nullable=False, default="在线")  # 在线 / 离线 / 维护
    cpu_usage = Column(Float, default=0)
    memory_usage = Column(Float, default=0)
    disk_usage = Column(Float, default=0)
    responsible_person = Column(String(50))
    last_check_time = Column(DateTime)
    created_at = Column(DateTime, default=beijing_now)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now)


class AgingRack(Base):
    """老化架部署表"""
    __tablename__ = "aging_racks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rack_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    production_line = Column(String(10), nullable=False)
    location = Column(String(100))
    ip_address = Column(String(50))
    total_slots = Column(Integer, nullable=False, default=0)
    used_slots = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="在线")
    responsible_person = Column(String(50))
    created_at = Column(DateTime, default=beijing_now)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now)


class WifiAp(Base):
    """WiFi AP 部署表"""
    __tablename__ = "wifi_aps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ap_id = Column(String(50), unique=True, nullable=False)
    ssid = Column(String(100), nullable=False)
    production_line = Column(String(10), nullable=False)
    ip_address = Column(String(50))
    mac_address = Column(String(20))   # AP 的 MAC 地址（wifi-monitor 迁移字段）
    location = Column(String(100))
    channel = Column(Integer, default=0)
    connected_devices = Column(Integer, default=0)
    status = Column(String(20), nullable=False, default="在线")
    responsible_person = Column(String(50))
    created_at = Column(DateTime, default=beijing_now)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now)


class NetworkAlert(Base):
    """网络告警记录表（离线检测 / Syslog 告警统一落表，供看板 KPI 与告警追溯）"""
    __tablename__ = "network_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_type = Column(String(20), nullable=False)     # 服务器 / 老化架 / WiFi AP
    device_name = Column(String(100), nullable=False)
    device_key = Column(String(80))                      # 类型+业务ID，用于未处理告警去重
    production_line = Column(String(10))
    ip_address = Column(String(50))
    alert_type = Column(String(30), default="离线告警")   # 离线告警 / 日志告警
    level = Column(String(20), default="warning")        # warning / critical
    message = Column(String(500))
    status = Column(String(20), nullable=False, default="未处理")  # 未处理 / 已处理
    created_at = Column(DateTime, default=beijing_now)
    resolved_at = Column(DateTime)


__all__ = ["Server", "AgingRack", "WifiAp", "NetworkAlert"]