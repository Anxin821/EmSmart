from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import require_role, get_current_user
from app.schemas import ApiResponse, PaginatedData
from app.services import antivirus_service as service

router = APIRouter(prefix="/antivirus", tags=["设备杀毒"])


@router.get("/records")
def list_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    production_line: Optional[str] = None,
    device_id: Optional[str] = None,
    cycle: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    items, total = service.list_records(db, page=page, page_size=page_size, production_line=production_line, device_id=device_id, cycle=cycle)
    return ApiResponse(data=PaginatedData(total=total, page=page, page_size=page_size, items=items))


@router.get("/records/{record_id}")
def get_record(record_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    r = service.get_record(db, record_id)
    if not r:
        from fastapi import HTTPException
        raise HTTPException(404, "记录不存在")
    return ApiResponse(data=r)


@router.post("/records")
def create_record(
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    r = service.create_record(db, body)
    return ApiResponse(data=r, message="创建成功")


@router.put("/records/{record_id}")
def update_record(
    record_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    r = service.update_record(db, record_id, body)
    if not r:
        from fastapi import HTTPException
        raise HTTPException(404, "记录不存在")
    return ApiResponse(data=r, message="更新成功")


@router.delete("/records/{record_id}")
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    ok = service.delete_record(db, record_id)
    if not ok:
        from fastapi import HTTPException
        raise HTTPException(404, "记录不存在")
    return ApiResponse(message="删除成功")


@router.post("/records/import")
def import_records(
    records: list,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    count = service.import_records(db, records)
    return ApiResponse(data={"imported": count}, message="导入成功")


@router.get("/overdue-records")
def list_overdue_records(
    status: Optional[str] = Query(None, pattern="^(overdue|pending)$"),
    production_line: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    items, total = service.list_overdue_records(db, status=status, production_line=production_line, page=page, page_size=page_size)
    return ApiResponse(data=PaginatedData(total=total, page=page, page_size=page_size, items=items))


@router.get("/dashboard")
def antivirus_dashboard(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return ApiResponse(data=service.antivirus_dashboard(db))
