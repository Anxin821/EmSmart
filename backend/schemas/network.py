"""服务器 / 老化架 / WiFi AP Schema。"""
from .common import BaseModel, Optional, datetime


# ============================================================
# 服务器
# ============================================================
class ServerBase(BaseModel):
    server_id: str
    name: str
    production_line: str
    rack_location: Optional[str] = None
    ip_address: Optional[str] = None
    model: Optional[str] = None
    os: Optional[str] = None
    status: str = "在线"
    cpu_usage: Optional[float] = 0
    memory_usage: Optional[float] = 0
    disk_usage: Optional[float] = 0
    responsible_person: Optional[str] = None


class ServerCreate(ServerBase):
    pass


class ServerUpdate(BaseModel):
    name: Optional[str] = None
    production_line: Optional[str] = None
    rack_location: Optional[str] = None
    ip_address: Optional[str] = None
    model: Optional[str] = None
    os: Optional[str] = None
    status: Optional[str] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    responsible_person: Optional[str] = None


class ServerOut(ServerBase):
    id: int
    last_check_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# 老化架
# ============================================================
class AgingRackBase(BaseModel):
    rack_id: str
    name: str
    production_line: str
    location: Optional[str] = None
    ip_address: Optional[str] = None
    total_slots: int = 0
    used_slots: int = 0
    status: str = "正常"
    responsible_person: Optional[str] = None


class AgingRackCreate(AgingRackBase):
    pass


class AgingRackUpdate(BaseModel):
    rack_id: Optional[str] = None
    name: Optional[str] = None
    production_line: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    total_slots: Optional[int] = None
    used_slots: Optional[int] = None
    status: Optional[str] = None
    responsible_person: Optional[str] = None


class AgingRackOut(AgingRackBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# WiFi AP
# ============================================================
class WifiApBase(BaseModel):
    ap_id: str
    ssid: str
    production_line: str
    ip_address: Optional[str] = None
    location: Optional[str] = None
    channel: Optional[int] = 0
    connected_devices: Optional[int] = 0
    status: str = "在线"
    responsible_person: Optional[str] = None


class WifiApCreate(WifiApBase):
    pass


class WifiApUpdate(BaseModel):
    ap_id: Optional[str] = None
    ssid: Optional[str] = None
    production_line: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[str] = None
    channel: Optional[int] = None
    connected_devices: Optional[int] = None
    status: Optional[str] = None
    responsible_person: Optional[str] = None


class WifiApOut(WifiApBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


__all__ = [
    "ServerBase", "ServerCreate", "ServerUpdate", "ServerOut",
    "AgingRackBase", "AgingRackCreate", "AgingRackUpdate", "AgingRackOut",
    "WifiApBase", "WifiApCreate", "WifiApUpdate", "WifiApOut",
]
