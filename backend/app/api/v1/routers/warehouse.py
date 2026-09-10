"""库房管理路由：治具借还 + 耗材领用/补货。"""
from io import BytesIO
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.schemas import ApiResponse, PaginatedData
from app.services import warehouse_service as service

router = APIRouter(prefix="/warehouse", tags=["库房管理"])


@router.get("/stats")
def warehouse_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(data=service.get_stats(db))


@router.get("/parts")
def list_parts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    part_type: Optional[str] = None,
    low_stock: bool = False,
    stock_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    items, total = service.list_parts(db, page=page, page_size=page_size,
                                      keyword=keyword, part_type=part_type, low_stock=low_stock,
                                      stock_status=stock_status)
    return ApiResponse(data=PaginatedData(total=total, page=page, page_size=page_size, items=items))


@router.post("/parts/import")
def import_parts(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    """批量导入物品（支持 .xlsx / .xls）。表头：物品名称、型号、类型、数量、货位、单位、预警值、供应商"""
    filename = (file.filename or "").lower()
    if not filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="仅支持 .xlsx / .xls 文件")
    try:
        from openpyxl import load_workbook
        wb = load_workbook(filename=BytesIO(file.file.read()), read_only=True, data_only=True)
        ws = wb.active
        # 全部行（第 1 行为表头）一并传给 service，由 service 做列名映射
        rows = [list(r) for r in ws.iter_rows(values_only=True)]
        wb.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Excel 解析失败：{e}")
    return ApiResponse(data=service.batch_import(db, rows, request, current_user["username"]))


@router.post("/parts")
def create_part(
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    return ApiResponse(data=service.create_part(db, data, request, current_user["username"]))


@router.put("/parts/{part_id}")
def update_part(
    part_id: int,
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    return ApiResponse(data=service.update_part(db, part_id, data, request, current_user["username"]))


@router.delete("/parts/{part_id}")
def delete_part(
    part_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    ok = service.delete_part(db, part_id, request, current_user["username"])
    if not ok:
        raise HTTPException(status_code=404, detail="物品不存在")
    return ApiResponse(message="删除成功")


@router.get("/parts/{part_id}")
def part_detail(
    part_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    detail = service.get_detail(db, part_id)
    if not detail:
        raise HTTPException(status_code=404, detail="物品不存在")
    return ApiResponse(data=detail)


@router.post("/parts/{part_id}/borrow")
def borrow_part(
    part_id: int,
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    return ApiResponse(data=service.borrow(db, part_id, data, request, current_user["username"]))


@router.post("/parts/{part_id}/return")
def return_part(
    part_id: int,
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    return ApiResponse(data=service.return_part(db, part_id, data, request, current_user["username"]))


@router.post("/parts/{part_id}/consume")
def consume_part(
    part_id: int,
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    return ApiResponse(data=service.consume(db, part_id, data, request, current_user["username"]))


@router.post("/parts/{part_id}/restock")
def restock_part(
    part_id: int,
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    return ApiResponse(data=service.restock(db, part_id, data, request, current_user["username"]))
