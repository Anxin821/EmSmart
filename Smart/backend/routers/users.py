"""
智能工厂工作任务管理平台 - 用户管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth import get_current_user, require_role, hash_password, check_module_access
from models import User, UserPermission
from schemas import UserOut, UserCreate, UserUpdate, UserWithPermissions, UserPermissionOut, UserPermissionUpdate

router = APIRouter(tags=["用户管理"])

# 所有模块定义
ALL_MODULES = [
    {"key": "devices", "label": "AOI&AI 设备管理"},
    {"key": "weekly", "label": "生产周报管理"},
    {"key": "monthly", "label": "生产月报管理"},
    {"key": "servers", "label": "服务器管理"},
    {"key": "agingracks", "label": "老化架管理"},
    {"key": "wifi", "label": "WiFi AP 管理"},
    {"key": "orders", "label": "MES 工单管理"},
    {"key": "bugs", "label": "MES BUG 管理"},
    {"key": "devreqs", "label": "MES 需求管理"},
    {"key": "antivirus", "label": "设备杀毒记录"},
    {"key": "projects", "label": "项目管理"},
    {"key": "users", "label": "用户管理"},
]


def _get_user_perms(db: Session, user_id: int) -> list[UserPermissionOut]:
    """获取用户权限列表，不足模块补齐默认值"""
    perms = db.query(UserPermission).filter(UserPermission.user_id == user_id).all()
    perm_map = {p.module_key: p for p in perms}
    result = []
    for mod in ALL_MODULES:
        pk = mod["key"]
        if pk in perm_map:
            result.append(UserPermissionOut(
                module_key=pk,
                can_read=perm_map[pk].can_read,
                can_write=perm_map[pk].can_write,
            ))
        else:
            result.append(UserPermissionOut(module_key=pk, can_read=True, can_write=False))
    return result


@router.get("/users")
def list_users(db: Session = Depends(get_db), current_user: dict = Depends(check_module_access("users"))):
    users = db.query(User).order_by(User.id).all()
    result = []
    for u in users:
        perms = _get_user_perms(db, u.id)
        result.append(UserWithPermissions(
            id=u.id, username=u.username, full_name=u.full_name,
            role=u.role, email=u.email, is_active=u.is_active,
            created_at=u.created_at, permissions=perms,
        ))
    return {"code": 200, "data": [r.model_dump() for r in result], "total": len(result)}


@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(check_module_access("users"))):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "用户不存在")
    perms = _get_user_perms(db, u.id)
    return {"code": 200, "data": UserWithPermissions(
        id=u.id, username=u.username, full_name=u.full_name,
        role=u.role, email=u.email, is_active=u.is_active,
        created_at=u.created_at, permissions=perms,
    ).model_dump()}


@router.post("/users")
def create_user(data: UserCreate, db: Session = Depends(get_db), current_user: dict = Depends(check_module_access("users", write=True))):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, "用户名已存在")
    u = User(
        username=data.username,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        email=data.email,
    )
    db.add(u)
    db.flush()
    # 为新用户创建默认权限（仅读）
    for mod in ALL_MODULES:
        db.add(UserPermission(user_id=u.id, module_key=mod["key"], can_read=True, can_write=False))
    db.commit()
    return {"code": 200, "message": "创建成功", "data": {"id": u.id}}


@router.put("/users/{user_id}")
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), current_user: dict = Depends(check_module_access("users", write=True))):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "用户不存在")
    if data.full_name is not None:
        u.full_name = data.full_name
    if data.role is not None:
        u.role = data.role
    if data.email is not None:
        u.email = data.email
    if data.is_active is not None:
        u.is_active = data.is_active
    if data.password:
        u.password_hash = hash_password(data.password)
    db.commit()
    return {"code": 200, "message": "更新成功"}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(check_module_access("users", write=True))):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "用户不存在")
    if u.username == "admin":
        raise HTTPException(400, "不能删除 admin 账户")
    # 级联删除权限
    db.query(UserPermission).filter(UserPermission.user_id == user_id).delete()
    db.delete(u)
    db.commit()
    return {"code": 200, "message": "删除成功"}


@router.put("/users/{user_id}/permissions")
def update_user_perms(user_id: int, data: UserPermissionUpdate, db: Session = Depends(get_db), current_user: dict = Depends(check_module_access("users", write=True))):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "用户不存在")
    # 清除旧权限
    db.query(UserPermission).filter(UserPermission.user_id == user_id).delete()
    db.flush()
    # 写入新权限
    for p in data.permissions:
        db.add(UserPermission(
            user_id=user_id,
            module_key=p.module_key,
            can_read=p.can_read,
            can_write=p.can_write,
        ))
    db.commit()
    return {"code": 200, "message": "权限更新成功"}
