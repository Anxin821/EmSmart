"""
智能工厂工作任务管理平台 - 项目路由
提供项目编码的增删改查
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_user, require_role, write_operation_log
from schemas import ProjectCreate, ProjectUpdate, ProjectItem, ApiResponse
from core.crud import get_projects, create_project, update_project, delete_project, get_project_by_id

router = APIRouter(prefix="/projects", tags=["项目管理"])


@router.get("")
def list_projects(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """获取所有项目（用于下拉选项和管理列表）"""
    items = get_projects(db, include_inactive=include_inactive)
    return ApiResponse(data=[
        {
            "id": p.id,
            "project_code": p.project_code,
            "project_name": p.project_name,
            "description": p.description,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in items
    ])


@router.post("")
def add_project(
    data: ProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    """新增项目"""
    record = create_project(db, data.model_dump())
    write_operation_log(db, current_user["username"], "CREATE", "projects", data.project_code,
                       f"新增项目: {data.project_code} {data.project_name}", request)
    return ApiResponse(data={
        "id": record.id,
        "project_code": record.project_code,
        "project_name": record.project_name,
        "is_active": record.is_active,
    })


@router.put("/{project_id}")
def edit_project(
    project_id: int,
    data: ProjectUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    """编辑项目"""
    record = update_project(db, project_id, data.model_dump(exclude_unset=True))
    if not record:
        raise HTTPException(status_code=404, detail="项目不存在")
    write_operation_log(db, current_user["username"], "UPDATE", "projects", str(project_id), "更新项目", request)
    return ApiResponse(data={
        "id": record.id,
        "project_code": record.project_code,
        "project_name": record.project_name,
        "is_active": record.is_active,
    })


@router.delete("/{project_id}")
def remove_project(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """删除项目（硬删除，如需软删除改为 update_project 设置 is_active=False）"""
    success = delete_project(db, project_id)
    if not success:
        raise HTTPException(status_code=404, detail="项目不存在")
    write_operation_log(db, current_user["username"], "DELETE", "projects", str(project_id), "删除项目", request)
    return ApiResponse(message=f"项目 {project_id} 已删除")
