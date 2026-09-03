"""MES（工单 / BUG / 需求）Schema。

包含原散落在 routers/mes.py:79 的 StatusUpdateRequest。
"""
from .common import BaseModel, Optional, date, datetime


# ============================================================
# 工单
# ============================================================
class WorkOrderBase(BaseModel):
    order_number: str
    order_type: str
    product_name: str
    priority: str = "中"
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    status: str = "待开始"
    responsible_person: Optional[str] = None
    description: Optional[str] = None


class WorkOrderCreate(WorkOrderBase):
    pass


class WorkOrderUpdate(BaseModel):
    order_number: Optional[str] = None
    order_type: Optional[str] = None
    product_name: Optional[str] = None
    priority: Optional[str] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    status: Optional[str] = None
    responsible_person: Optional[str] = None
    description: Optional[str] = None


class WorkOrderOut(WorkOrderBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 原散落在 routers/mes.py 的工单状态更新 Schema
class StatusUpdateRequest(BaseModel):
    status: str


# ============================================================
# BUG
# ============================================================
class BugBase(BaseModel):
    bug_id: Optional[str] = None   # 新增时可省略，后端自动生成自增编号；编辑时若不填则保持原值
    title: str
    severity: str
    module: Optional[str] = None
    status: str = "新建"
    discoverer: Optional[str] = None
    assignee: Optional[str] = None
    created_date: Optional[date] = None
    deadline: Optional[date] = None
    solution: Optional[str] = None


class BugCreate(BugBase):
    pass


class BugUpdate(BaseModel):
    bug_id: Optional[str] = None
    title: Optional[str] = None
    severity: Optional[str] = None
    module: Optional[str] = None
    status: Optional[str] = None
    discoverer: Optional[str] = None
    assignee: Optional[str] = None
    deadline: Optional[date] = None
    solution: Optional[str] = None


class BugOut(BugBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# 二次开发需求
# ============================================================
class DevRequestBase(BaseModel):
    request_id: Optional[str] = None   # 新增时可省略，后端自动生成随机5位编号；编辑时若不填则保持原值
    title: str
    source: Optional[str] = None
    priority: str = "中"
    status: str = "收集"
    submitter: Optional[str] = None
    assignee: Optional[str] = None
    expected_date: Optional[date] = None
    responsible_person: Optional[str] = None
    progress: float = 0
    description: Optional[str] = None


class DevRequestCreate(DevRequestBase):
    pass


class DevRequestUpdate(BaseModel):
    request_id: Optional[str] = None
    title: Optional[str] = None
    source: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    submitter: Optional[str] = None
    assignee: Optional[str] = None
    expected_date: Optional[date] = None
    responsible_person: Optional[str] = None
    progress: Optional[float] = None
    description: Optional[str] = None


class DevRequestOut(DevRequestBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


__all__ = [
    "WorkOrderBase", "WorkOrderCreate", "WorkOrderUpdate", "WorkOrderOut", "StatusUpdateRequest",
    "BugBase", "BugCreate", "BugUpdate", "BugOut",
    "DevRequestBase", "DevRequestCreate", "DevRequestUpdate", "DevRequestOut",
]
