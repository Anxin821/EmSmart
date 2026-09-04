from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.services.production_service import (
    create_monthly,
    create_weekly,
    delete_monthly,
    delete_weekly,
    generate_monthly,
    get_monthly_by_id,
    get_weekly_by_id,
    import_weekly_excel,
    import_weekly_raw_excel,
    list_monthly,
    list_weekly,
    monthly_stats,
    monthly_trend,
    update_monthly,
    update_weekly,
)
from app.core.auth import get_current_user, require_role
from app.core.database import get_db
from app.schemas import MonthlyGenerateRequest, MonthlyProductionCreate, MonthlyProductionUpdate, WeeklyProductionCreate, WeeklyProductionUpdate
from app.schemas import ApiResponse, PaginatedData

router = APIRouter(prefix="/production", tags=["production"])


@router.get("/weekly")
def list_weekly_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    year: Optional[int] = None,
    week: Optional[int] = None,
    production_line: Optional[str] = None,
    project: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    items, total = list_weekly(db, page, page_size, year, week, production_line, project)
    return ApiResponse(data=PaginatedData(total=total, page=page, page_size=page_size, items=items))


@router.get("/weekly/{record_id}")
def get_weekly_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(data=get_weekly_by_id(db, record_id))


@router.post("/weekly")
def create_weekly_record(
    data: WeeklyProductionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    record = create_weekly(db, data)
    from app.core.crud import write_operation_log
    write_operation_log(db, current_user["username"], "CREATE", "weekly_production", str(record["id"]), f"录入周报: {data.year}W{data.week_number}", request)
    return ApiResponse(data=record)


@router.put("/weekly/{record_id}")
def edit_weekly_record(
    record_id: int,
    data: WeeklyProductionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    record = update_weekly(db, record_id, data)
    from app.core.crud import write_operation_log
    write_operation_log(db, current_user["username"], "UPDATE", "weekly_production", str(record_id), "更新周报", request)
    return ApiResponse(data=record)


@router.delete("/weekly/{record_id}")
def remove_weekly_record(
    record_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    delete_weekly(db, record_id)
    from app.core.crud import write_operation_log
    write_operation_log(db, current_user["username"], "DELETE", "weekly_production", str(record_id), "删除周报", request)
    return ApiResponse(message="删除成功")


@router.post("/weekly/import")
def import_weekly_records(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    result = import_weekly_excel(db, file)
    return ApiResponse(data={"imported": result}, message="导入成功")


@router.post("/weekly/import-raw")
def import_weekly_raw_records(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    result = import_weekly_raw_excel(db, file)
    return ApiResponse(data={"imported": result}, message="导入成功")


@router.get("/weekly/export")
def export_weekly_records(
    year: Optional[int] = None,
    week: Optional[int] = None,
    production_line: Optional[str] = None,
    project: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    items, _ = list_weekly(db, 1, 10000, year, week, production_line, project)
    wb = Workbook()
    ws = wb.active
    ws.title = "周报"
    headers = ["年", "周数", "产线", "项目", "总产量", "合格数", "不良数", "直通率(%)", "录入人", "更新时间"]
    ws.append(headers)
    for d in items[0]:
        ws.append([d["year"], d["week_number"], d["production_line"], d["project"], d["total_output"], d["qualified_count"], d["defect_count"] or 0, d["yield_rate"] or 0, d["recorder"] or "", d["updated_at"]])
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=weekly_production.xlsx"})


@router.get("/monthly")
def list_monthly_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    year: Optional[int] = None,
    month: Optional[int] = None,
    project: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    items, total, stats = list_monthly(db, page, page_size, year, month, project)
    return ApiResponse(data=PaginatedData(total=total, page=page, page_size=page_size, items=items, extra=stats))


@router.get("/monthly/stats")
def monthly_stats_route(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(data=monthly_stats(db, year, month))


@router.get("/monthly/trend")
def monthly_trend_route(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(data={"items": monthly_trend(db, year)})


@router.post("/monthly")
def create_monthly_record(
    data: MonthlyProductionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    record = create_monthly(db, data)
    from app.core.crud import write_operation_log
    write_operation_log(db, current_user["username"], "CREATE", "monthly_production", str(record["id"]), f"录入月报: {data.year}M{data.month}", request)
    return ApiResponse(data=record)


@router.get("/monthly/{record_id}")
def get_monthly_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(data=get_monthly_by_id(db, record_id))


@router.put("/monthly/{record_id}")
def edit_monthly_record(
    record_id: int,
    data: MonthlyProductionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    record = update_monthly(db, record_id, data)
    from app.core.crud import write_operation_log
    write_operation_log(db, current_user["username"], "UPDATE", "monthly_production", str(record_id), "更新月报", request)
    return ApiResponse(data=record)


@router.delete("/monthly/{record_id}")
def remove_monthly_record(
    record_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    delete_monthly(db, record_id)
    from app.core.crud import write_operation_log
    write_operation_log(db, current_user["username"], "DELETE", "monthly_production", str(record_id), "删除月报", request)
    return ApiResponse(message="删除成功")


@router.post("/monthly/generate")
def generate_monthly_record(
    body: MonthlyGenerateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    count = generate_monthly(db, body, current_user["username"])
    from app.core.crud import write_operation_log
    write_operation_log(db, current_user["username"], "CREATE", "monthly_production", None, f"汇总生成 {body.year}M{body.month} 月报，共 {count} 条", request)
    return ApiResponse(data={"generated": count}, message=f"成功生成 {count} 条月报记录")


@router.get("/monthly/export")
def export_monthly_records(
    year: Optional[int] = None,
    month: Optional[int] = None,
    production_line: Optional[str] = None,
    project: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    items, _ = list_monthly(db, 1, 10000, year, month, project)
    wb = Workbook()
    ws = wb.active
    ws.title = "月报"
    headers = ["年", "月", "产线", "项目", "月总产量", "月合格数", "月不良数", "月直通率(%)", "录入人", "更新时间"]
    ws.append(headers)
    for d in items[0]:
        ws.append([d["year"], d["month"], d["production_line"], d["project"], d["monthly_total_output"], d["monthly_qualified_count"], d["monthly_defect_count"] or 0, d["monthly_yield_rate"] or 0, d["recorder"] or "", d["updated_at"]])
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=monthly_production.xlsx"})
