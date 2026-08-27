"""
智能工厂工作任务管理平台 —— FastAPI 主入口

职责：应用初始化、中间件配置、路由注册、SPA 静态资源服务。
认证 / 枚举选项等业务路由已拆分至 routers/ 子模块。
"""
from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# ---------- 本地模块 ----------
from core.config import settings
from core.database import engine, Base, SessionLocal, get_db
from core.auth import hash_password
from models import User

# ---------- 路由模块 ----------
from routers.auth import router as auth_router
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
# 路由注册
# ============================================================
API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
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
