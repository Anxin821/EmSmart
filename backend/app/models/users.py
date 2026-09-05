"""用户与权限相关 ORM 模型。"""
from .base import Base, Column, Integer, String, Boolean, DateTime

from app.core.timeutil import beijing_now


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), nullable=False, default="viewer")  # admin / engineer / viewer
    email = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=beijing_now)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now)


class UserPermission(Base):
    """用户模块权限表"""
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    module_key = Column(String(50), nullable=False)  # devices / weekly / monthly / ...
    can_read = Column(Boolean, default=True)
    can_write = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    created_at = Column(DateTime, default=beijing_now)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now)


__all__ = ["User", "UserPermission"]
