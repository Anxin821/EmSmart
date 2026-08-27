"""AOI&AI 设备 Schema。"""
from .common import BaseModel, Optional, date, datetime


class AoiAiDeviceBase(BaseModel):
    device_id: str
    name: str
    device_type: str
    production_line: str
    location: Optional[str] = None
    ip_address: Optional[str] = None
    status: str = "正常"
    responsible_person: Optional[str] = None
    install_date: Optional[date] = None
    remark: Optional[str] = None


class AoiAiDeviceCreate(AoiAiDeviceBase):
    pass


class AoiAiDeviceUpdate(BaseModel):
    name: Optional[str] = None
    device_type: Optional[str] = None
    production_line: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[str] = None
    responsible_person: Optional[str] = None
    install_date: Optional[date] = None
    remark: Optional[str] = None


class AoiAiDeviceOut(AoiAiDeviceBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


__all__ = [
    "AoiAiDeviceBase",
    "AoiAiDeviceCreate",
    "AoiAiDeviceUpdate",
    "AoiAiDeviceOut",
]
