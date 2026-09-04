from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import build_permissions, create_access_token, verify_password, write_operation_log
from app.repositories.user_repository import get_user_by_username


def authenticate_user(db: Session, username: str, password: str, request: Request | None = None):
    """Validate username/password, build JWT and permission payload.

    This is the business logic layer; router should be thin and delegate here.
    """
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已停用")

    token = create_access_token({
        "sub": user.username,
        "role": user.role,
        "full_name": user.full_name or "",
    })
    permissions = build_permissions(db, user)

    if request is not None:
        write_operation_log(db, user.username, "LOGIN", "auth", None, f"登录成功，角色 {user.role}", request)

    payload = {
        "access_token": token,
        "username": user.username,
        "role": user.role,
        "full_name": user.full_name or "",
        "permissions": permissions,
        "id": user.id,
    }
    return payload


def build_auth_payload(user, permissions: list[dict] | None = None):
    """Serialize user info with permissions into API payload."""
    permissions = permissions or []
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "full_name": user.full_name or "",
        "email": user.email,
        "is_active": user.is_active,
        "permissions": [{
            "module_key": p["module_key"],
            "can_read": p["can_read"],
            "can_write": p["can_write"],
        } for p in permissions],
    }
