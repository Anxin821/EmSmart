"""
智能工厂工作任务管理平台 —— FastAPI 主入口（重构统一版）

说明：
- 合并了之前 main.py（开发态 + 健康检查 + login/me）与 main_clean.py（前端生产静态 + SPA fallback），
  生产/开发都用 uvicorn main:app 启动。
- 已移除对已删除文件 templates/index.html、index-cdn.html 的引用。
"""
from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# ---------- 本地模块 ----------
from core.config import settings
from core.database import engine, Base, SessionLocal, get_db
from core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_role,
    build_permissions,     # 步骤 ⑧-5：统一权限构造
    write_operation_log,
)
from models import User, UserPermission, Project
from schemas import (
    LoginRequest,
    LoginResponse,
    ApiResponse,
    UserWithPermissions,
)

# ---------- 路由模块 ----------
from routers.devices import router as devices_router
from routers.production import router as production_router
from routers.network import router as network_router
from routers.mes import router as mes_router
from routers.dashboard import router as dashboard_router
from routers.projects import router as projects_router
from routers.antivirus import router as antivirus_router
from routers.users import router as users_router
from routers.responsibilities import router as responsibilities_router

# ---------- 定时任务 ----------
from tasks import check_server_health


# ============================================================
# 前端静态资源 & SPA catch-all
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
# 生产环境优先取 frontend/dist；开发态若无 dist，回退到 Vite dev (3000) 入口壳 frontend/index.html
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"
FRONTEND_DEV_INDEX = BASE_DIR / "frontend" / "index.html"


def _serve_spa_index():
    """根据 dist 是否存在智能选择 SPA index 文件（不存在直接返回 JSON 提示）。"""
    if FRONTEND_INDEX.exists():
        return FileResponse(FRONTEND_INDEX)
    if FRONTEND_DEV_INDEX.exists():
        return FileResponse(FRONTEND_DEV_INDEX)
    return JSONResponse(
        {"message": "SPA 入口不存在。请先构建前端 (cd frontend && npm run build) 或启动 Vite dev 服务器。"},
        status_code=503,
    )


# ============================================================
# 启动生命周期：建表 + 启动健康检查 + seed 默认 admin
# ============================================================
def _ensure_tables_and_seed():
    # 1. 建表（models/__init__.py 已把 15 个子类全部注册到 Base.metadata）
    Base.metadata.create_all(bind=engine)

    # 2. 默认 admin / engineer / viewer
    db: Session = SessionLocal()
    try:
        defaults = [
            ("admin", "admin123", "系统管理员", "admin"),
            ("engineer", "admin123", "工艺工程师", "engineer"),
            ("viewer", "admin123", "只读账户", "viewer"),
        ]
        any_created = False
        for username, password, full_name, role in defaults:
            exists = db.query(User).filter(User.username == username).first()
            if not exists:
                db.add(User(
                    username=username,
                    password_hash=hash_password(password),
                    full_name=full_name,
                    role=role,
                ))
                any_created = True
        if any_created:
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    _ensure_tables_and_seed()

    # 启动健康检查协程（事件循环内以 daemon task 形式跑，不阻塞 uvicorn）
    loop = asyncio.get_event_loop()
    health_task = loop.create_task(
        check_server_health(get_session=lambda: SessionLocal()),
        name="server_health_daemon",
    )

    try:
        yield
    finally:
        # shutdown
        health_task.cancel()
        try:
            await health_task
        except (asyncio.CancelledError, Exception):
            pass


# ============================================================
# FastAPI App
# ============================================================
app = FastAPI(
    title="智能工厂工作任务管理平台",
    description="AOI/AI 设备 + 生产周报月报 + 网络设施 + MES + 杀毒 + 权限 的统一后台",
    version="2.0.0 (重构分层版)",
    lifespan=lifespan,
)

# CORS：兼容 Vite 3000 / 5173 以及局域网 8000 直访
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        f"http://{settings.APP_HOST}:{settings.APP_PORT}",
        f"http://172.16.112.245:{settings.APP_PORT}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 挂载前端静态（生产 frontend/dist/assets），没有就不挂，避免 404 噪音 ---
if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")


# ============================================================
# 路由前缀
# ============================================================
API_PREFIX = "/api/v1"

app.include_router(devices_router, prefix=API_PREFIX)
app.include_router(production_router, prefix=API_PREFIX)
app.include_router(network_router, prefix=API_PREFIX)
app.include_router(mes_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(projects_router, prefix=API_PREFIX)
app.include_router(antivirus_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(responsibilities_router, prefix=API_PREFIX)


# ============================================================
# 根级 API（鉴权 + 枚举选项） —— 保持和原 main.py 完全相同的路径 & 语义
# ============================================================
@app.post(f"{API_PREFIX}/login", response_model=ApiResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user_in_db = db.query(User).filter(User.username == body.username).first()
    if not user_in_db or not verify_password(body.password, user_in_db.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user_in_db.is_active:
        raise HTTPException(status_code=403, detail="账户已停用")

    token = create_access_token({
        "sub": user_in_db.username,
        "role": user_in_db.role,
        "full_name": user_in_db.full_name or "",
    })
    # 步骤 ⑧-5：统一权限构造函数（之前 login/me 两段完全相同的13行代码）
    permissions = build_permissions(db, user_in_db)

    write_operation_log(db, user_in_db.username, "LOGIN", "auth", None, f"登录成功，角色 {user_in_db.role}", request)
    return ApiResponse(data=LoginResponse(
        access_token=token,
        username=user_in_db.username,
        role=user_in_db.role,
        full_name=user_in_db.full_name or "",
    ).model_dump() | {"permissions": permissions, "id": user_in_db.id})


@app.get(f"{API_PREFIX}/me", response_model=ApiResponse)
def me(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_in_db = db.query(User).filter(User.username == current_user["username"]).first()
    if not user_in_db:
        raise HTTPException(status_code=404, detail="用户不存在")
    permissions = build_permissions(db, user_in_db)
    resp = UserWithPermissions.model_validate(user_in_db, from_attributes=True)
    resp.permissions = [{"module_key": p["module_key"], "can_read": p["can_read"], "can_write": p["can_write"]}
                        for p in permissions]
    return ApiResponse(data=resp.model_dump())


# ---------- 枚举选项 ----------
@app.get(f"{API_PREFIX}/options/lines")
def option_lines():
    return ApiResponse(data=[f"{i}线" for i in range(1, 9)])


@app.get(f"{API_PREFIX}/options/projects")
def option_projects(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    rows = db.query(Project).filter(Project.is_active == True).all()
    return ApiResponse(data=[{"project_code": p.project_code, "project_name": p.project_name} for p in rows])


@app.get(f"{API_PREFIX}/options/device-statuses")
def option_device_statuses():
    return ApiResponse(data=["正常", "故障", "保养中"])


@app.get(f"{API_PREFIX}/options/device-types")
def option_device_types():
    return ApiResponse(data=["AOI", "AI"])


@app.get(f"{API_PREFIX}/options/roles")
def option_roles():
    return ApiResponse(data=[
        {"role": "admin", "title": "系统管理员"},
        {"role": "engineer", "title": "工程师"},
        {"role": "viewer", "title": "只读用户"},
    ])


@app.get(f"{API_PREFIX}/options/order-statuses")
def option_order_statuses():
    return ApiResponse(data=["待开始", "进行中", "已完成", "挂起"])


@app.get(f"{API_PREFIX}/options/mes-statuses")
def option_mes_statuses():
    return ApiResponse(data={
        "bug": ["新建", "确认", "修复中", "已解决", "关闭"],
        "req": ["收集", "评估", "开发中", "测试", "上线"],
        "order_priority": ["紧急", "高", "中", "低"],
        "bug_severity": ["致命", "严重", "一般", "建议"],
    })


# ============================================================
# SPA 入口（保证浏览器直接刷新 /index/devices 这类 history 路由不 404）
# ============================================================
@app.get("/")
@app.get("/index")
@app.get("/index/{full_path:path}")
def spa_index(full_path: str | None = None):
    return _serve_spa_index()


# ============================================================
# 直接启动（python main.py）
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",   # 必须使用字符串模式（reload 模式要求）
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
