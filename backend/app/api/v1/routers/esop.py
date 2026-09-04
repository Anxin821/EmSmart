from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.schemas import ApiResponse, PaginatedData
from app.services import esop_service as service

router = APIRouter(prefix="/esop-parts", tags=["ESOP料号"])


def _to_dict(p) -> dict:
    return p  # service already returns dicts


@router.get("")
def list_esop_parts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    station_name: Optional[str] = None,
    process_name: Optional[str] = None,
    file_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    items, total = service.list_esop_parts(db, page=page, page_size=page_size, keyword=keyword, station_name=station_name, process_name=process_name, file_name=file_name)
    return ApiResponse(data=PaginatedData(total=total, page=page, page_size=page_size, items=items))


@router.post("")
def create_esop(
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    part = service.create_esop(db, data, request, current_user["username"])
    return ApiResponse(data=part)


@router.put("/{part_id}")
def update_esop(
    part_id: int,
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    part = service.update_esop(db, part_id, data, request, current_user["username"])
    if not part:
        raise HTTPException(status_code=404, detail="料号记录不存在")
    return ApiResponse(data=part)


@router.delete("/{part_id}")
def delete_esop(
    part_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    ok = service.delete_esop(db, part_id, request, current_user["username"])
    if not ok:
        raise HTTPException(status_code=404, detail="料号记录不存在")
    return ApiResponse(message="删除成功")
