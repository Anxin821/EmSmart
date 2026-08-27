"""
models 包统一入口。

保持对原单文件 models.py 的调用兼容：
- `from models import User, AoiAiDevice, ...` 继续工作
- `Base.metadata.create_all(bind=engine)` 也继续工作（所有子类都被注册到 Base.metadata）
"""
from .base import Base

# 所有 ORM 模型必须显式导入，确保 SQLAlchemy Base.metadata 收集到全部 15 张表
from .users import User, UserPermission
from .device import AoiAiDevice
from .production import WeeklyProduction, MonthlyProduction
from .network import Server, AgingRack, WifiAp
from .mes import WorkOrder, Bug, DevRequest
from .system import Project, OperationLog, AntivirusRecord, JobResponsibility

__all__ = [
    "Base",
    "User",
    "UserPermission",
    "AoiAiDevice",
    "WeeklyProduction",
    "MonthlyProduction",
    "Server",
    "AgingRack",
    "WifiAp",
    "WorkOrder",
    "Bug",
    "DevRequest",
    "Project",
    "OperationLog",
    "AntivirusRecord",
    "JobResponsibility",
]
