"""
ESOP 料号管理路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_user, require_role, write_operation_log
from core.crud import (
    get_esop_parts_paginated, create_esop_part,
    update_esop_part, delete_esop_part,
)
from schemas import ApiResponse, PaginatedData

router = APIRouter(prefix="/esop-parts", tags=["ESOP料号"])


def _to_dict(p) -> dict:
    return {
        "id": p.id,
        "station_name": p.station_name,
        "process_name": p.process_name,
        "part_number": p.part_number,
        "file_name": p.file_name,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


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
    """ESOP 料号分页列表"""
    items, total = get_esop_parts_paginated(db, page, page_size, keyword, station_name, process_name, file_name)
    return ApiResponse(data=PaginatedData(
        total=total, page=page, page_size=page_size,
        items=[_to_dict(d) for d in items],
    ))


@router.post("")
def create_esop(
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    """新增 ESOP 料号"""
    part = create_esop_part(db, data)
    write_operation_log(db, current_user["username"], "CREATE", "esop_parts", str(part.id), f"新增料号: {data.get('part_number', '')}", request)
    return ApiResponse(data=_to_dict(part))


@router.put("/{part_id}")
def update_esop(
    part_id: int,
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    """编辑 ESOP 料号"""
    part = update_esop_part(db, part_id, data)
    if not part:
        raise HTTPException(status_code=404, detail="料号记录不存在")
    write_operation_log(db, current_user["username"], "UPDATE", "esop_parts", str(part_id), "更新料号", request)
    return ApiResponse(data=_to_dict(part))


@router.delete("/{part_id}")
def delete_esop(
    part_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """删除 ESOP 料号"""
    ok = delete_esop_part(db, part_id)
    if not ok:
        raise HTTPException(status_code=404, detail="料号记录不存在")
    write_operation_log(db, current_user["username"], "DELETE", "esop_parts", str(part_id), "删除料号", request)
    return ApiResponse(message="删除成功")
