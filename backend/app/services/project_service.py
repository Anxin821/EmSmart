from fastapi import HTTPException, Request

from app.repositories.project_repository import create_project, delete_project, get_project_by_id, get_projects, update_project
from app.core.auth import write_operation_log
from app.schemas import ProjectCreate, ProjectUpdate


def list_projects(db, include_inactive: bool = False):
    return get_projects(db, include_inactive=include_inactive)


def add_project(db, payload: ProjectCreate, request: Request, current_user: dict):
    record = create_project(db, payload.model_dump())
    write_operation_log(db, current_user["username"], "CREATE", "projects", record.project_code,
                       f"新增项目: {record.project_code} {record.project_name}", request)
    return record


def edit_project(db, project_id: int, payload: ProjectUpdate, request: Request, current_user: dict):
    record = update_project(db, project_id, payload.model_dump(exclude_unset=True))
    if not record:
        raise HTTPException(status_code=404, detail="项目不存在")
    write_operation_log(db, current_user["username"], "UPDATE", "projects", str(project_id), "更新项目", request)
    return record


def remove_project(db, project_id: int, request: Request, current_user: dict):
    success = delete_project(db, project_id)
    if not success:
        raise HTTPException(status_code=404, detail="项目不存在")
    write_operation_log(db, current_user["username"], "DELETE", "projects", str(project_id), "删除项目", request)
    return True
