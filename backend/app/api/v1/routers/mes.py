from io import BytesIO
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.schemas import (
    WorkOrderCreate, WorkOrderUpdate,
    BugCreate, BugUpdate,
    DevRequestCreate, DevRequestUpdate,
    StatusUpdateRequest, ApiResponse, PaginatedData,
)
from app.services import mes_service as service

router = APIRouter(prefix="/mes", tags=["MES系统"])


@router.get("/dashboard")
def mes_dashboard(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return ApiResponse(data=service.mes_dashboard(db))


@router.get("/work-orders")
def list_work_orders(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None, status: Optional[str] = None,
    priority: Optional[str] = None, order_type: Optional[str] = None,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
):
    items, total = service.list_work_orders(db, page=page, page_size=page_size, keyword=keyword, status=status, priority=priority, order_type=order_type)
    return ApiResponse(data=PaginatedData(total=total, page=page, page_size=page_size, items=items))


@router.get("/work-orders/{order_number}")
def get_work_order(order_number: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    item = service.get_work_order(db, order_number)
    if not item: raise HTTPException(404, "工单不存在")
    return ApiResponse(data=item)


@router.post("/work-orders")
def add_work_order(data: WorkOrderCreate, request: Request, db: Session = Depends(get_db),
                   current_user: dict = Depends(require_role("admin", "engineer"))):
    order = service.add_work_order(db, data.model_dump(), request, current_user["username"])
    return ApiResponse(data=order)


@router.put("/work-orders/{order_number}")
def edit_work_order(order_number: str, data: WorkOrderUpdate, request: Request,
                    db: Session = Depends(get_db), current_user: dict = Depends(require_role("admin", "engineer"))):
    order = service.edit_work_order(db, order_number, data.model_dump(exclude_unset=True), request, current_user["username"])
    if not order:
        raise HTTPException(404, "工单不存在")
    return ApiResponse(data=order)


@router.delete("/work-orders/{order_number}")
def remove_work_order(order_number: str, request: Request, db: Session = Depends(get_db),
                      current_user: dict = Depends(require_role("admin"))):
    ok = service.remove_work_order(db, order_number, request, current_user["username"])
    if not ok:
        raise HTTPException(404, "工单不存在")
    return ApiResponse(message="删除成功")


@router.put("/work-orders/{order_number}/status")
def update_order_status(
    order_number: str,
    body: StatusUpdateRequest,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    res = service.update_order_status(db, order_number, body.status, request, current_user["username"])
    if not res:
        raise HTTPException(404, "工单不存在")
    return ApiResponse(data=res)


@router.get("/work-orders/export")
def export_work_orders(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    order_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    items, _ = service.list_work_orders(db, 1, 10000, keyword, status, priority, order_type)
    output = service.export_work_orders_excel(db, items)
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=work_orders.xlsx"})


# BUGs
@router.get("/bugs")
def list_bugs(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None, status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
):
    items, total = service.list_bugs(db, page=page, page_size=page_size, keyword=keyword, status=status, severity=severity)
    return ApiResponse(data=PaginatedData(total=total, page=page, page_size=page_size, items=items))


@router.get("/bugs/{bug_id}")
def get_bug(bug_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    item = service.get_bug(db, bug_id)
    if not item: raise HTTPException(404, "BUG不存在")
    return ApiResponse(data=item)


@router.post("/bugs")
def add_bug(data: BugCreate, request: Request, db: Session = Depends(get_db),
            current_user: dict = Depends(require_role("admin", "engineer"))):
    bug = service.add_bug(db, data.model_dump(exclude_unset=False), request, current_user["username"])
    return ApiResponse(data=bug)


@router.put("/bugs/{bug_id}")
def edit_bug(bug_id: str, data: BugUpdate, request: Request, db: Session = Depends(get_db),
             current_user: dict = Depends(require_role("admin", "engineer"))):
    bug = service.edit_bug(db, bug_id, data.model_dump(exclude_unset=True), request, current_user["username"])
    if not bug: raise HTTPException(404, "BUG不存在")
    return ApiResponse(data=bug)


@router.delete("/bugs/{bug_id}")
def remove_bug(bug_id: str, request: Request, db: Session = Depends(get_db),
               current_user: dict = Depends(require_role("admin"))):
    ok = service.remove_bug(db, bug_id, request, current_user["username"])
    if not ok: raise HTTPException(404, "BUG不存在")
    return ApiResponse(message="删除成功")


@router.put("/bugs/{bug_id}/status")
def update_bug_status(
    bug_id: str,
    body: StatusUpdateRequest,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    valid = ["确认新增", "修复中", "解决关闭"]
    new_status = body.status
    if new_status not in valid:
        raise HTTPException(400, f"无效状态，可选值: {', '.join(valid)}")
    bug = service.edit_bug(db, bug_id, {"status": new_status}, request, current_user["username"])
    if not bug: raise HTTPException(404, "BUG不存在")
    return ApiResponse(data=bug)


@router.get("/bugs/export")
def export_bugs(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    items, _ = service.list_bugs(db, 1, 10000, keyword, status, severity)
    output = service.export_bugs_excel(db, items)
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=bugs.xlsx"})


# Dev requests
@router.get("/dev-requests")
def list_dev_requests(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None, status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
):
    items, total = service.list_dev_requests(db, page=page, page_size=page_size, keyword=keyword, status=status, priority=priority)
    return ApiResponse(data=PaginatedData(total=total, page=page, page_size=page_size, items=items))


@router.get("/dev-requests/{request_id}")
def get_dev_request(request_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    item = service.get_dev_request(db, request_id)
    if not item: raise HTTPException(404, "需求不存在")
    return ApiResponse(data=item)


@router.post("/dev-requests")
def add_dev_request(data: DevRequestCreate, request: Request, db: Session = Depends(get_db),
                    current_user: dict = Depends(require_role("admin", "engineer"))):
    req = service.add_dev_request(db, data.model_dump(), request, current_user["username"])
    return ApiResponse(data=req)


@router.put("/dev-requests/{request_id}")
def edit_dev_request(request_id: str, data: DevRequestUpdate, req_ctx: Request,
                     db: Session = Depends(get_db), current_user: dict = Depends(require_role("admin", "engineer"))):
    req = service.edit_dev_request(db, request_id, data.model_dump(exclude_unset=True), req_ctx, current_user["username"])
    if not req: raise HTTPException(404, "需求不存在")
    return ApiResponse(data=req)


@router.delete("/dev-requests/{request_id}")
def remove_dev_request(request_id: str, req_ctx: Request, db: Session = Depends(get_db),
                       current_user: dict = Depends(require_role("admin"))):
    ok = service.remove_dev_request(db, request_id, req_ctx, current_user["username"])
    if not ok: raise HTTPException(404, "需求不存在")
    return ApiResponse(message="删除成功")


@router.get("/dev-requests/export")
def export_dev_requests(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    items, _ = service.list_dev_requests(db, 1, 10000, keyword, status, priority)
    output = service.export_dev_requests_excel(db, items)
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=dev_requests.xlsx"})