from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.services.project_service import add_project, edit_project, list_projects, remove_project
from app.core.auth import get_current_user, require_role
from app.core.database import get_db
from app.schemas import ApiResponse, ProjectCreate, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["项目管理"])


@router.get("")
def get_projects_route(include_inactive: bool = False, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    items = list_projects(db, include_inactive=include_inactive)
    return ApiResponse(data=[{
        "id": p.id,
        "project_code": p.project_code,
        "project_name": p.project_name,
        "description": p.description,
        "is_active": p.is_active,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    } for p in items])


@router.post("")
def add_project_route(data: ProjectCreate, request: Request, db: Session = Depends(get_db), current_user: dict = Depends(require_role("admin", "engineer"))):
    record = add_project(db, data, request, current_user)
    return ApiResponse(data={
        "id": record.id,
        "project_code": record.project_code,
        "project_name": record.project_name,
        "is_active": record.is_active,
    })


@router.put("/{project_id}")
def edit_project_route(project_id: int, data: ProjectUpdate, request: Request, db: Session = Depends(get_db), current_user: dict = Depends(require_role("admin", "engineer"))):
    record = edit_project(db, project_id, data, request, current_user)
    return ApiResponse(data={
        "id": record.id,
        "project_code": record.project_code,
        "project_name": record.project_name,
        "is_active": record.is_active,
    })


@router.delete("/{project_id}")
def remove_project_route(project_id: int, request: Request, db: Session = Depends(get_db), current_user: dict = Depends(require_role("admin"))):
    remove_project(db, project_id, request, current_user)
    return ApiResponse(message=f"项目 {project_id} 已删除")
