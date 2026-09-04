from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.user_repository import get_user_by_username, get_user_by_id, list_users, get_user_permissions
from app.core.auth import PERMISSION_MODULES, hash_password
from app.models import User, UserPermission
from app.schemas import UserCreate, UserPermissionOut, UserPermissionUpdate, UserUpdate, UserWithPermissions

# 权限模块清单唯一来源：app.core.auth.PERMISSION_MODULES（与前端 Users.vue 的 11 个业务模块一致）
ALL_MODULES = PERMISSION_MODULES
_ALLOWED_KEYS = {m["key"] for m in PERMISSION_MODULES}


def get_user_permission_list(db: Session, user_id: int):
    perms = get_user_permissions(db, user_id)
    perm_map = {p.module_key: p for p in perms}
    result = []
    for mod in ALL_MODULES:
        key = mod["key"]
        if key in perm_map:
            result.append(UserPermissionOut(
                module_key=key,
                can_read=perm_map[key].can_read,
                can_write=perm_map[key].can_write,
            ))
        else:
            result.append(UserPermissionOut(module_key=key, can_read=True, can_write=False))
    return result


def fetch_users(db: Session):
    result = []
    for u in list_users(db):
        result.append(UserWithPermissions(
            id=u.id, username=u.username, full_name=u.full_name,
            role=u.role, email=u.email, is_active=u.is_active,
            created_at=u.created_at, permissions=get_user_permission_list(db, u.id),
        ))
    return result


def create_user(db: Session, payload: UserCreate):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(400, "用户名已存在")
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        email=payload.email,
    )
    db.add(user)
    db.flush()
    for mod in ALL_MODULES:
        db.add(UserPermission(user_id=user.id, module_key=mod["key"], can_read=True, can_write=False))
    db.commit()
    return user


def update_user_profile(db: Session, current_user: dict, payload: UserUpdate):
    user = get_user_by_username(db, current_user["username"])
    if not user:
        raise HTTPException(404, "用户不存在")
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.email is not None:
        user.email = payload.email
    if payload.password:
        user.password_hash = hash_password(payload.password)
    db.commit()
    return user


def update_user_by_id(db: Session, user_id: int, payload: UserUpdate):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    if payload.username is not None and payload.username != user.username:
        if db.query(User).filter(User.username == payload.username, User.id != user_id).first():
            raise HTTPException(400, "用户名已存在")
        user.username = payload.username
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        user.role = payload.role
    if payload.email is not None:
        user.email = payload.email
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password:
        user.password_hash = hash_password(payload.password)
    db.commit()
    return user


def delete_user_by_id(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    if user.username == "admin":
        raise HTTPException(400, "不能删除 admin 账户")
    db.query(UserPermission).filter(UserPermission.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return True


def update_user_permissions(db: Session, user_id: int, payload: UserPermissionUpdate):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    invalid = sorted({p.module_key for p in payload.permissions} - _ALLOWED_KEYS)
    if invalid:
        raise HTTPException(400, f"存在未注册的模块 key: {invalid}")
    db.query(UserPermission).filter(UserPermission.user_id == user_id).delete()
    db.flush()
    for p in payload.permissions:
        db.add(UserPermission(
            user_id=user_id,
            module_key=p.module_key,
            can_read=p.can_read,
            can_write=p.can_write,
        ))
    db.commit()
    return True
