"""
schemas 包统一入口。

保持对原单文件 schemas.py 的调用兼容：
- `from app.schemas import ApiResponse, WeeklyProductionOut, StatusUpdateRequest, MonthlyGenerateRequest, ...` 继续工作
"""
from .common import ApiResponse, PaginatedData

from .auth import (
    UserOut, UserCreate, UserUpdate, UserPermissionOut,
    UserWithPermissions, UserPermissionUpdate, LoginRequest, LoginResponse,
)
from .device import (
    AoiAiDeviceBase, AoiAiDeviceCreate, AoiAiDeviceUpdate, AoiAiDeviceOut,
)
from .production import (
    WeeklyProductionBase, WeeklyProductionCreate, WeeklyProductionUpdate, WeeklyProductionOut,
    MonthlyProductionBase, MonthlyProductionCreate, MonthlyProductionUpdate, MonthlyProductionOut,
    MonthlyGenerateRequest,  # 原 routers/production.py 内联类迁入
)
from .network import (
    ServerBase, ServerCreate, ServerUpdate, ServerOut,
    AgingRackBase, AgingRackCreate, AgingRackUpdate, AgingRackOut,
    WifiApBase, WifiApCreate, WifiApUpdate, WifiApOut,
)
from .mes import (
    WorkOrderBase, WorkOrderCreate, WorkOrderUpdate, WorkOrderOut,
    BugBase, BugCreate, BugUpdate, BugOut,
    DevRequestBase, DevRequestCreate, DevRequestUpdate, DevRequestOut,
    StatusUpdateRequest,  # 原 routers/mes.py 内联类迁入
)
from .antivirus import (
    ProjectCreate, ProjectUpdate, ProjectItem,
    AntiVirusRecordCreate, AntiVirusRecordUpdate, AntiVirusRecordOut,
)

__all__ = [
    # common
    "ApiResponse", "PaginatedData",
    # auth
    "UserOut", "UserCreate", "UserUpdate", "UserPermissionOut",
    "UserWithPermissions", "UserPermissionUpdate", "LoginRequest", "LoginResponse",
    # device
    "AoiAiDeviceBase", "AoiAiDeviceCreate", "AoiAiDeviceUpdate", "AoiAiDeviceOut",
    # production
    "WeeklyProductionBase", "WeeklyProductionCreate", "WeeklyProductionUpdate", "WeeklyProductionOut",
    "MonthlyProductionBase", "MonthlyProductionCreate", "MonthlyProductionUpdate", "MonthlyProductionOut",
    "MonthlyGenerateRequest",
    # network
    "ServerBase", "ServerCreate", "ServerUpdate", "ServerOut",
    "AgingRackBase", "AgingRackCreate", "AgingRackUpdate", "AgingRackOut",
    "WifiApBase", "WifiApCreate", "WifiApUpdate", "WifiApOut",
    # mes
    "WorkOrderBase", "WorkOrderCreate", "WorkOrderUpdate", "WorkOrderOut", "StatusUpdateRequest",
    "BugBase", "BugCreate", "BugUpdate", "BugOut",
    "DevRequestBase", "DevRequestCreate", "DevRequestUpdate", "DevRequestOut",
    # antivirus + project
    "ProjectCreate", "ProjectUpdate", "ProjectItem",
    "AntiVirusRecordCreate", "AntiVirusRecordUpdate", "AntiVirusRecordOut",
]
