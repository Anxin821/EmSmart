from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models import Project
from app.schemas import ApiResponse

# 枚举选项路由：各模块共用的下拉选项。
# 注意：不要把它挂在 /auth 下——前端统一以 /options/* 调用（见 frontend/src/api/devices.js optionsApi）。
router = APIRouter(prefix="/options", tags=["options"])


@router.get("/lines")
def option_lines():
    return ApiResponse(data=[f"{i}线" for i in range(1, 9)])


@router.get("/projects")
def option_projects(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    rows = db.query(Project).filter(Project.is_active == True).order_by(Project.project_code.asc()).all()
    seen = set()
    data = []
    for p in rows:
        code = (p.project_code or "").strip()
        name = (p.project_name or "").strip()
        if not code and not name:
            continue
        key = (name or code).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        data.append({"project_code": code, "project_name": name})
    return ApiResponse(data=data)
