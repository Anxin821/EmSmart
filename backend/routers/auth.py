"""
认证与枚举选项路由模块

提供：
- POST /login   用户登录
- GET  /me      当前用户信息 + 权限
- GET  /options/*  各模块下拉枚举
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import (
    verify_password,
    create_access_token,
    get_current_user,
    build_permissions,
    write_operation_log,
)
from models import User, Project
from schemas import (
    LoginRequest,
    LoginResponse,
    ApiResponse,
    UserWithPermissions,
)

router = APIRouter()


# ============================================================
# 登录 / 当前用户
# ============================================================
@router.post("/login", response_model=ApiResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user_in_db = db.query(User).filter(User.username == body.username).first()
    if not user_in_db:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not verify_password(body.password, user_in_db.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user_in_db.is_active:
        raise HTTPException(status_code=403, detail="账户已停用")

    token = create_access_token({
        "sub": user_in_db.username,
        "role": user_in_db.role,
        "full_name": user_in_db.full_name or "",
    })
    permissions = build_permissions(db, user_in_db)

    write_operation_log(db, user_in_db.username, "LOGIN", "auth", None, f"登录成功，角色 {user_in_db.role}", request)
    return ApiResponse(data=LoginResponse(
        access_token=token,
        username=user_in_db.username,
        role=user_in_db.role,
        full_name=user_in_db.full_name or "",
    ).model_dump() | {"permissions": permissions, "id": user_in_db.id})


@router.get("/me", response_model=ApiResponse)
def me(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_in_db = db.query(User).filter(User.username == current_user["username"]).first()
    if not user_in_db:
        raise HTTPException(status_code=404, detail="用户不存在")
    permissions = build_permissions(db, user_in_db)
    resp = UserWithPermissions.model_validate(user_in_db, from_attributes=True)
    resp.permissions = [{"module_key": p["module_key"], "can_read": p["can_read"], "can_write": p["can_write"]}
                        for p in permissions]
    return ApiResponse(data=resp.model_dump())


# ============================================================
# 枚举选项
# ============================================================
@router.get("/options/lines")
def option_lines():
    return ApiResponse(data=[f"{i}线" for i in range(1, 9)])


@router.get("/options/projects")
def option_projects(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    rows = db.query(Project).filter(Project.is_active == True).order_by(Project.project_code.asc()).all()
    seen = set()
    data = []
    for p in rows:
        code = (p.project_code or '').strip()
        name = (p.project_name or '').strip()
        if not code and not name:
            continue
        key = (name or code).strip().lower()
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        data.append({"project_code": code, "project_name": name})
    return ApiResponse(data=data)


@router.get("/options/device-statuses")
def option_device_statuses():
    return ApiResponse(data=["正常", "故障", "保养中"])


@router.get("/options/device-types")
def option_device_types():
    return ApiResponse(data=["AOI", "AI"])


@router.get("/options/roles")
def option_roles():
    return ApiResponse(data=[
        {"role": "admin", "title": "系统管理员"},
        {"role": "engineer", "title": "工程师"},
        {"role": "viewer", "title": "只读用户"},
    ])


@router.get("/options/order-statuses")
def option_order_statuses():
    return ApiResponse(data=["待开始", "进行中", "已完成", "挂起"])


@router.get("/options/mes-statuses")
def option_mes_statuses():
    return ApiResponse(data={
        "bug": ["确认新增", "修复中", "解决关闭"],
        "req": ["收集评估", "开发测试中", "上线"],
        "order_priority": ["紧急", "高", "中", "低"],
        "bug_severity": ["致命", "严重", "一般", "建议"],
    })
