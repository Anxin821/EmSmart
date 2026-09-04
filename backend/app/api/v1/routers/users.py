from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.services.user_service import (
    create_user,
    delete_user_by_id,
    fetch_users,
    update_user_by_id,
    update_user_permissions,
    update_user_profile,
)
from app.core.auth import check_module_access, get_current_user, hash_password
from app.core.database import get_db
from app.schemas import UserCreate, UserPermissionUpdate, UserUpdate

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("")
def list_users(db: Session = Depends(get_db), current_user: dict = Depends(check_module_access("users"))):
    items = fetch_users(db)
    return {"code": 200, "data": [r.model_dump() for r in items], "total": len(items)}


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(check_module_access("users"))):
    user = next((u for u in fetch_users(db) if u.id == user_id), None)
    if not user:
        raise HTTPException(404, "用户不存在")
    return {"code": 200, "data": user.model_dump()}


@router.post("")
def create_user_route(data: UserCreate, db: Session = Depends(get_db), current_user: dict = Depends(check_module_access("users", write=True))):
    user = create_user(db, data)
    return {"code": 200, "message": "创建成功", "data": {"id": user.id}}


@router.put("/me")
def update_current_user_profile(data: UserUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user = update_user_profile(db, current_user, data)
    return {"code": 200, "message": "个人信息已更新", "data": {"full_name": user.full_name, "email": user.email, "username": user.username}}


@router.put("/{user_id}")
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), current_user: dict = Depends(check_module_access("users", write=True))):
    update_user_by_id(db, user_id, data)
    return {"code": 200, "message": "更新成功"}


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(check_module_access("users", write=True))):
    delete_user_by_id(db, user_id)
    return {"code": 200, "message": "删除成功"}


@router.put("/{user_id}/permissions")
def update_user_perms(user_id: int, data: UserPermissionUpdate, db: Session = Depends(get_db), current_user: dict = Depends(check_module_access("users", write=True))):
    update_user_permissions(db, user_id, data)
    return {"code": 200, "message": "权限更新成功"}
