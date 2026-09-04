from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.services.auth_service import authenticate_user, build_auth_payload
from app.core.auth import build_permissions, get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas import ApiResponse, LoginRequest, LoginResponse, UserWithPermissions

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=ApiResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    payload = authenticate_user(db, body.username, body.password, request=request)
    return ApiResponse(data=LoginResponse(
        access_token=payload["access_token"],
        username=payload["username"],
        role=payload["role"],
        full_name=payload["full_name"],
    ).model_dump() | {"permissions": payload["permissions"], "id": payload["id"]})


@router.get("/me", response_model=ApiResponse)
def me(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_in_db = db.query(User).filter(User.username == current_user["username"]).first()
    if not user_in_db:
        raise HTTPException(status_code=404, detail="用户不存在")
    permissions = build_permissions(db, user_in_db)
    resp = UserWithPermissions.model_validate(user_in_db, from_attributes=True)
    resp.permissions = [{
        "module_key": p["module_key"],
        "can_read": p["can_read"],
        "can_write": p["can_write"],
    } for p in permissions]
    return ApiResponse(data=resp.model_dump())
