from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas import ApiResponse, PaginatedData
from app.schemas.exception import ExceptionRecordCreate, ExceptionRecordUpdate
from app.services.exception_service import ExceptionService

router = APIRouter(prefix="/exception", tags=["异常管理"])


@router.get("/dashboard/stats")
def get_dashboard(db: Session = Depends(get_db)):
    return ApiResponse(data=ExceptionService.get_dashboard(db))


@router.get("/list")
def list_exceptions(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
):
    items, total = ExceptionService.get_list(db, page, page_size, keyword, type, status)
    return ApiResponse(data=PaginatedData(total=total, page=page, page_size=page_size, items=items))


@router.post("")
def create_exception(
    data: ExceptionRecordCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        return ApiResponse(data=ExceptionService.create(db, data, current_user["username"]))
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/{record_id}")
def get_exception(record_id: str, db: Session = Depends(get_db)):
    try:
        return ApiResponse(data=ExceptionService.get_by_id(db, record_id))
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.put("/{record_id}")
def update_exception(
    record_id: str,
    data: ExceptionRecordUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        return ApiResponse(data=ExceptionService.update(db, record_id, data))
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/{record_id}")
def delete_exception(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        ExceptionService.delete(db, record_id)
        return ApiResponse(message="删除成功")
    except ValueError as e:
        raise HTTPException(404, str(e))
