"""
core 包 —— 平台核心基础设施模块。

包含认证、配置、数据库连接、CRUD 操作等基础能力，
供 routers / tasks / main 等各层调用。
"""
from .config import settings
from .database import engine, Base, SessionLocal, get_db
from .auth import (
    hash_password, verify_password,
    create_access_token, decode_access_token,
    get_current_user, require_role,
    check_module_access, write_operation_log,
    build_permissions,
)
from .crud import *  # noqa: F401,F403
