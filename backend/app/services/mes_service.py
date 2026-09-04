from typing import Optional, List, Dict, Any
from io import BytesIO
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.repositories import mes_repository as repo
from app.core.crud import write_operation_log


def mes_dashboard(db: Session) -> Dict[str, Any]:
    return repo.get_dashboard(db)


# Work orders

def list_work_orders(db: Session, page: int = 1, page_size: int = 20, keyword: Optional[str] = None, status: Optional[str] = None, priority: Optional[str] = None, order_type: Optional[str] = None):
    items, total = repo.work_orders_paginated(db, page, page_size, keyword, status, priority, order_type)
    def _order_to_dict(d):
        return {
            "id": d.id, "order_number": d.order_number, "order_type": d.order_type,
            "product_name": d.product_name, "priority": d.priority,
            "planned_start": d.planned_start.isoformat() if d.planned_start else None,
            "planned_end": d.planned_end.isoformat() if d.planned_end else None,
            "actual_start": d.actual_start.isoformat() if d.actual_start else None,
            "actual_end": d.actual_end.isoformat() if d.actual_end else None,
            "status": d.status, "responsible_person": d.responsible_person,
            "description": d.description,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        }
    return [ _order_to_dict(d) for d in items ], total


def get_work_order(db: Session, order_number: str):
    from app.models import WorkOrder as WO
    item = db.query(WO).filter(WO.order_number == order_number).first()
    if not item: return None
    return {
        "id": item.id, "order_number": item.order_number, "order_type": item.order_type,
        "product_name": item.product_name, "priority": item.priority,
        "planned_start": item.planned_start.isoformat() if item.planned_start else None,
        "planned_end": item.planned_end.isoformat() if item.planned_end else None,
        "actual_start": item.actual_start.isoformat() if item.actual_start else None,
        "actual_end": item.actual_end.isoformat() if item.actual_end else None,
        "status": item.status, "responsible_person": item.responsible_person,
        "description": item.description,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def add_work_order(db: Session, data: Dict[str, Any], request, username: str):
    order = repo.create_work_order_repo(db, data)
    write_operation_log(db, username, "CREATE", "work_order", data.get("order_number"), f"新增工单: {data.get('product_name')}", request)
    return get_work_order(db, order.order_number)


def edit_work_order(db: Session, order_number: str, data: Dict[str, Any], request, username: str):
    order = repo.update_work_order_repo(db, order_number, data)
    if not order:
        return None
    write_operation_log(db, username, "UPDATE", "work_order", order_number, "更新工单", request)
    return get_work_order(db, order.order_number)


def remove_work_order(db: Session, order_number: str, request, username: str):
    ok = repo.delete_work_order_repo(db, order_number)
    if not ok:
        return False
    write_operation_log(db, username, "DELETE", "work_order", order_number, "删除工单", request)
    return True


def update_order_status(db: Session, order_number: str, new_status: str, request, username: str):
    from datetime import datetime
    update_data = {"status": new_status}
    if new_status == "进行中":
        update_data["actual_start"] = datetime.utcnow()
    elif new_status == "已完成":
        update_data["actual_end"] = datetime.utcnow()
    order = repo.update_work_order_repo(db, order_number, update_data)
    if not order:
        return None
    write_operation_log(db, username, "UPDATE", "work_order", order_number, f"状态流转 -> {new_status}", request)
    return get_work_order(db, order.order_number)


# Bugs

def list_bugs(db: Session, page: int = 1, page_size: int = 20, keyword: Optional[str] = None, status: Optional[str] = None, severity: Optional[str] = None):
    items, total = repo.bugs_paginated(db, page, page_size, keyword, status, severity)
    def _bug_to_dict(d):
        return {
            "id": d.id, "bug_id": d.bug_id, "title": d.title,
            "severity": (d.severity or "").strip().lstrip("|").rstrip("|").strip(),
            "module": d.module,
            "status": (d.status or "").strip().lstrip("|").rstrip("|").strip(),
            "discoverer": d.discoverer, "assignee": d.assignee,
            "created_date": d.created_date.isoformat() if d.created_date else None,
            "deadline": d.deadline.isoformat() if d.deadline else None,
            "solution": d.solution,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        }
    return [ _bug_to_dict(d) for d in items ], total


def get_bug(db: Session, bug_id: str):
    from app.models import Bug as B
    item = db.query(B).filter(B.bug_id == bug_id).first()
    if not item: return None
    return {
        "id": item.id, "bug_id": item.bug_id, "title": item.title,
        "severity": (item.severity or "").strip().lstrip("|").rstrip("|").strip(),
        "module": item.module,
        "status": (item.status or "").strip().lstrip("|").rstrip("|").strip(),
        "discoverer": item.discoverer, "assignee": item.assignee,
        "created_date": item.created_date.isoformat() if item.created_date else None,
        "deadline": item.deadline.isoformat() if item.deadline else None,
        "solution": item.solution,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def add_bug(db: Session, data: Dict[str, Any], request, username: str):
    bug = repo.create_bug_repo(db, data)
    write_operation_log(db, username, "CREATE", "bug", data.get("bug_id"), f"新增BUG: {data.get('title')}", request)
    return get_bug(db, bug.bug_id)


def edit_bug(db: Session, bug_id: str, data: Dict[str, Any], request, username: str):
    bug = repo.update_bug_repo(db, bug_id, data)
    if not bug:
        return None
    write_operation_log(db, username, "UPDATE", "bug", bug_id, "更新BUG", request)
    return get_bug(db, bug.bug_id)


def remove_bug(db: Session, bug_id: str, request, username: str):
    ok = repo.delete_bug_repo(db, bug_id)
    if not ok:
        return False
    write_operation_log(db, username, "DELETE", "bug", bug_id, "删除BUG", request)
    return True


# Dev requests

def list_dev_requests(db: Session, page: int = 1, page_size: int = 20, keyword: Optional[str] = None, status: Optional[str] = None, priority: Optional[str] = None):
    items, total = repo.dev_requests_paginated(db, page, page_size, keyword, status, priority)
    def _req_to_dict(d):
        return {
            "id": d.id, "request_id": d.request_id, "title": d.title, "source": d.source,
            "priority": (d.priority or "").strip().lstrip("|").rstrip("|").strip(),
            "status": (d.status or "").strip().lstrip("|").rstrip("|").strip(),
            "submitter": d.submitter, "assignee": d.assignee,
            "expected_date": d.expected_date.isoformat() if d.expected_date else None,
            "responsible_person": d.responsible_person, "progress": d.progress,
            "description": d.description,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        }
    return [ _req_to_dict(d) for d in items ], total


def get_dev_request(db: Session, request_id: str):
    from app.models import DevRequest as DR
    item = db.query(DR).filter(DR.request_id == request_id).first()
    if not item: return None
    return {
        "id": item.id, "request_id": item.request_id, "title": item.title, "source": item.source,
        "priority": (item.priority or "").strip().lstrip("|").rstrip("|").strip(),
        "status": (item.status or "").strip().lstrip("|").rstrip("|").strip(),
        "submitter": item.submitter, "assignee": item.assignee,
        "expected_date": item.expected_date.isoformat() if item.expected_date else None,
        "responsible_person": item.responsible_person, "progress": item.progress,
        "description": item.description,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def add_dev_request(db: Session, data: Dict[str, Any], request, username: str):
    req = repo.create_dev_request_repo(db, data)
    write_operation_log(db, username, "CREATE", "dev_request", data.get("request_id"), f"新增需求: {data.get('title')}", request)
    return get_dev_request(db, req.request_id)


def edit_dev_request(db: Session, request_id: str, data: Dict[str, Any], req_ctx, username: str):
    req = repo.update_dev_request_repo(db, request_id, data)
    if not req:
        return None
    write_operation_log(db, username, "UPDATE", "dev_request", request_id, "更新需求", req_ctx)
    return get_dev_request(db, req.request_id)


def remove_dev_request(db: Session, request_id: str, req_ctx, username: str):
    ok = repo.delete_dev_request_repo(db, request_id)
    if not ok:
        return False
    write_operation_log(db, username, "DELETE", "dev_request", request_id, "删除需求", req_ctx)
    return True


def export_work_orders_excel(db: Session, items):
    from openpyxl import Workbook
    wb = Workbook(); ws = wb.active; ws.title = "工单"
    ws.append(["工单号","类型","产品名","优先级","计划开始","计划结束","实际开始","实际结束","状态","负责人","描述"])
    for d in items:
        ws.append([d.get("order_number"), d.get("order_type"), d.get("product_name"), d.get("priority"),
                    str(d.get("planned_start") or ""), str(d.get("planned_end") or ""),
                    str(d.get("actual_start") or ""), str(d.get("actual_end") or ""), d.get("status"),
                    d.get("responsible_person") or "", d.get("description") or ""])
    output = BytesIO(); wb.save(output); output.seek(0)
    return output


def export_bugs_excel(db: Session, items):
    from openpyxl import Workbook
    wb = Workbook(); ws = wb.active; ws.title = "BUG"
    ws.append(["BUG_ID","标题","严重等级","模块","状态","发现人","责任人","创建日期","期限","解决方案"])
    for d in items:
        ws.append([d.get("bug_id"), d.get("title"), d.get("severity"), d.get("module"), d.get("status"),
                    d.get("discoverer") or "", d.get("assignee") or "", str(d.get("created_date") or ""), str(d.get("deadline") or ""), d.get("solution") or ""]) 
    output = BytesIO(); wb.save(output); output.seek(0)
    return output
