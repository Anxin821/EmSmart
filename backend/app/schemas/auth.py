"""登录 / 用户相关 Pydantic Schema。"""
from .common import BaseModel, Optional, datetime


class UserOut(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    role: str
    email: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    role: str = "viewer"
    email: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserPermissionOut(BaseModel):
    module_key: str
    can_read: bool
    can_write: bool

    class Config:
        from_attributes = True


class UserWithPermissions(UserOut):
    permissions: list[UserPermissionOut] = []


class UserPermissionUpdate(BaseModel):
    permissions: list[UserPermissionOut]


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
    full_name: str


__all__ = [
    "UserOut",
    "UserCreate",
    "UserUpdate",
    "UserPermissionOut",
    "UserWithPermissions",
    "UserPermissionUpdate",
    "LoginRequest",
    "LoginResponse",
]
