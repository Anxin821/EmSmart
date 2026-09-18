"""库房管理路由：治具借还 + 耗材领用/补货。"""
from io import BytesIO
from typing import Optional
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.schemas import ApiResponse, PaginatedData
from app.services import warehouse_service as service

router = APIRouter(prefix="/warehouse", tags=["库房管理"])


@router.get("/stats")
def warehouse_stats(
    part_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(data=service.get_stats(db, part_type=part_type))


@router.get("/parts")
def list_parts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    part_type: Optional[str] = None,
    low_stock: bool = False,
    stock_status: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    items, total = service.list_parts(db, page=page, page_size=page_size,
                                      keyword=keyword, part_type=part_type,
                                      low_stock=low_stock, stock_status=stock_status,
                                      sort_by=sort_by, sort_order=sort_order,
                                      status=status)
    return ApiResponse(data=PaginatedData(total=total, page=page, page_size=page_size, items=items))


@router.get("/parts/template")
def download_template():
    """下载导入模板（.xlsx），表头带蓝色背景。"""
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill, Font, Alignment, Side, Border
    wb = Workbook()
    ws = wb.active
    ws.title = "物品模板"
    headers = ["物品名称", "型号", "编号", "类型", "数量", "货位", "单位", "预警值"]
    # 表头样式：蓝色背景 + 白色粗体 + 居中 + 框线
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=11)
    header_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_align
        cell.border = thin_border
    # 示例行
    ws.cell(row=2, column=1, value="点胶治具")
    ws.cell(row=2, column=2, value="PD10/TK1080")
    ws.cell(row=2, column=3, value="JIG-001")
    ws.cell(row=2, column=4, value="治具")
    ws.cell(row=2, column=5, value=10)
    ws.cell(row=2, column=6, value="A01-1-2")
    ws.cell(row=2, column=7, value="个")
    ws.cell(row=2, column=8, value=2)
    # 列宽
    for col_idx in range(1, len(headers) + 1):
        ws.column_dimensions[chr(64 + col_idx)].width = 20
    # 表头行高
    ws.row_dimensions[1].height = 28
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return Response(
        content=buf.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=template.xlsx; filename*=UTF-8''{quote('物品导入模板.xlsx')}"},
    )


@router.post("/parts/import")
def import_parts(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    """批量导入物品（支持 .xlsx / .xls）。表头：物品名称、型号、类型、数量、货位、单位、预警值"""
    filename = (file.filename or "").lower()
    if not filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="仅支持 .xlsx / .xls 文件")
    try:
        from openpyxl import load_workbook
        wb = load_workbook(filename=BytesIO(file.file.read()), read_only=True, data_only=True)
        ws = wb.active
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
    return ApiResponse(data=service.update_part(db, part_id, data, request, current_user["username"], current_user["role"]))


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


@router.get("/parts/{part_id}/borrow-records")
def list_borrow_records(
    part_id: int,
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """查询治具的借出记录（默认只看未归还的）。"""
    records = service.list_borrow_records(db, part_id, active_only=active_only)
    return ApiResponse(data=records)


@router.get("/parts/{part_id}/consume-records")
def list_consume_records(
    part_id: int,
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """查询耗材的领用记录（默认只看未归还的）。"""
    records = service.list_consume_records(db, part_id, active_only=active_only)
    return ApiResponse(data=records)


@router.get("/parts/{part_id}/transactions")
def list_part_transactions(
    part_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """查询指定物品的操作流水。"""
    items, total = service.list_transactions(db, page=page, page_size=page_size)
    part_txs = [t for t in items if t["part_id"] == part_id]
    return ApiResponse(data=PaginatedData(total=len(part_txs), page=page, page_size=page_size, items=part_txs))


@router.get("/operators")
def list_operators(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """返回历史借/领用人列表（前端 el-select allow-create 使用）。"""
    return ApiResponse(data=service.get_operators(db))


@router.get("/department-managers")
def list_department_managers(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """返回历史部门负责人列表（前端 el-select allow-create 使用）。"""
    return ApiResponse(data=service.get_department_managers(db))


@router.get("/unreturned/{borrower}")
def check_unreturned(
    borrower: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """查询某个借用人当前未归还的所有治具（借出时不还又来借时的提醒）。"""
    return ApiResponse(data=service.check_unreturned_by_borrower(db, borrower))


@router.get("/transactions")
def list_all_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    tx_type: Optional[str] = None,
    is_returned: bool = Query(False),
    keyword: Optional[str] = None,
    borrow_date: Optional[str] = None,
    return_date: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """查询所有物品的借出/领用/归还/补货流水。"""
    items, total = service.list_transactions(db, page=page, page_size=page_size,
                                             tx_type=tx_type, is_returned=is_returned,
                                             keyword=keyword,
                                             borrow_date=borrow_date, return_date=return_date,
                                             date_from=date_from, date_to=date_to,
                                             sort_by=sort_by, sort_order=sort_order)
    return ApiResponse(data=PaginatedData(total=total, page=page, page_size=page_size, items=items))


@router.put("/transactions/{tx_id}/remark")
def update_tx_remark(
    tx_id: int,
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    """编辑出入库记录的备注。"""
    remark = (data.get("remark") or "").strip()
    result = service.update_tx_remark(db, tx_id, remark, request, current_user["username"])
    if not result:
        raise HTTPException(status_code=404, detail="记录不存在")
    return ApiResponse(data=result)


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


@router.post("/parts/{part_id}/to-repair")
def to_repair(
    part_id: int,
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    """治具转维修：将借出记录转为维修状态（数量计入库存但不可借出）。"""
    return ApiResponse(data=service.to_repair(db, part_id, data, request, current_user["username"]))


@router.post("/parts/{part_id}/finish-repair")
def finish_repair(
    part_id: int,
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    """治具维修完成：恢复正常可借出。"""
    return ApiResponse(data=service.finish_repair(db, part_id, data, request, current_user["username"]))


@router.post("/parts/{part_id}/consume")
def consume_part(
    part_id: int,
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    return ApiResponse(data=service.consume(db, part_id, data, request, current_user["username"]))


@router.post("/parts/{part_id}/loss")
def report_loss(
    part_id: int,
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    """治具报失：借出后丢失，总数-可用-。"""
    return ApiResponse(data=service.report_loss(db, part_id, data, request, current_user["username"]))


@router.post("/parts/{part_id}/found-back")
def found_back(
    part_id: int,
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    """治具已找回：报失的物品找回了，总数+可用+。"""
    return ApiResponse(data=service.found_back(db, part_id, data, request, current_user["username"]))


@router.post("/parts/{part_id}/damaged")
def report_damaged(
    part_id: int,
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    """治具报损：借出后损坏，总数-可用-。"""
    return ApiResponse(data=service.report_damaged(db, part_id, data, request, current_user["username"]))


@router.post("/parts/{part_id}/repair-damaged")
def repair_damaged(
    part_id: int,
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    """治具已修复：报损的物品修好了，总数+可用+。"""
    return ApiResponse(data=service.repair_damaged(db, part_id, data, request, current_user["username"]))


@router.post("/parts/{part_id}/restock")
def restock_part(
    part_id: int,
    data: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    return ApiResponse(data=service.restock(db, part_id, data, request, current_user["username"]))