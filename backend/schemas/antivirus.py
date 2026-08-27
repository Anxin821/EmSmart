"""项目 + 杀毒记录 Schema。"""
from .common import BaseModel, Optional, datetime


class ProjectCreate(BaseModel):
    project_code: str
    project_name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectItem(BaseModel):
    project_code: str
    project_name: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AntiVirusRecordCreate(BaseModel):
    device_id: str
    antivirus_time: datetime
    production_line: str
    operator: str
    cycle: str = "每天"
    remark: Optional[str] = None


class AntiVirusRecordUpdate(BaseModel):
    device_id: Optional[str] = None
    antivirus_time: Optional[datetime] = None
    production_line: Optional[str] = None
    operator: Optional[str] = None
    cycle: Optional[str] = None
    remark: Optional[str] = None


class AntiVirusRecordOut(BaseModel):
    id: int
    device_id: str
    antivirus_time: Optional[datetime] = None
    production_line: str
    operator: str
    cycle: str
    next_antivirus_time: Optional[datetime] = None
    remark: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


__all__ = [
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectItem",
    "AntiVirusRecordCreate",
    "AntiVirusRecordUpdate",
    "AntiVirusRecordOut",
]
