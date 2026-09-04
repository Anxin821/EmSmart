import json
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.core.crud import write_operation_log
from app.repositories import responsibilities_repository as repo


def _serialize(r) -> dict:
    try:
        items = json.loads(r.items or "[]")
    except json.JSONDecodeError:
        items = []
    return {
        "id": r.id,
        "name": r.name,
        "title": r.title,
        "items": items,
        "sort_order": r.sort_order,
    }


def list_job_duties(db: Session) -> List[Dict[str, Any]]:
    rows = repo.list_job_duties_repo(db)
    return [_serialize(r) for r in rows]


def create_job_duty(db: Session, body: dict, request, username: str):
    payload = dict()
    payload["name"] = body.get("name").strip()
    payload["title"] = body.get("title").strip()
    items = body.get("items")
    payload["items"] = json.dumps(items, ensure_ascii=False) if items is not None else "[]"
    payload["sort_order"] = body.get("sort_order") if body.get("sort_order") is not None else None

    # decide default sort_order
    if payload.get("sort_order") is None:
        max_order = db.query(repo.list_job_duties_repo.__globals__["JobResponsibility"].sort_order).order_by(repo.list_job_duties_repo.__globals__["JobResponsibility"].sort_order.desc()).first()
        payload["sort_order"] = (max_order[0] or 0) + 1 if max_order else 1

    row = repo.create_job_duty_repo(db, payload)
    write_operation_log(db, username, "CREATE", "job_duties", str(row.id), f"新增岗位: {payload.get('name')}", request)
    return _serialize(row)


def patch_job_duty(db: Session, duty_id: int, body: dict, request, username: str):
    row = repo.get_job_duty_repo(db, duty_id)
    if not row:
        return None
    updates = {}
    if body.get("name") is not None:
        updates["name"] = body.get("name").strip()
    if body.get("title") is not None:
        updates["title"] = body.get("title").strip()
    if body.get("sort_order") is not None:
        updates["sort_order"] = body.get("sort_order")
    if body.get("items") is not None:
        updates["items"] = json.dumps(body.get("items"), ensure_ascii=False)
    updated = repo.update_job_duty_repo(db, duty_id, updates)
    write_operation_log(db, username, "UPDATE", "job_duties", str(duty_id), "更新岗位", request)
    return _serialize(updated)


def put_job_duty_items(db: Session, duty_id: int, body: dict, request, username: str):
    row = repo.get_job_duty_repo(db, duty_id)
    if not row:
        return None
    updates = {}
    if "items" in body and body["items"] is not None:
        updates["items"] = json.dumps(body["items"], ensure_ascii=False)
    if "title" in body and body["title"] is not None:
        updates["title"] = body["title"]
    if "name" in body and body["name"] is not None:
        updates["name"] = body["name"]
    updated = repo.update_job_duty_repo(db, duty_id, updates)
    write_operation_log(db, username, "UPDATE", "job_duties", str(duty_id), "更新岗位职责条目", request)
    return _serialize(updated)


def delete_job_duty(db: Session, duty_id: int, request, username: str):
    ok = repo.delete_job_duty_repo(db, duty_id)
    if not ok:
        return False
    write_operation_log(db, username, "DELETE", "job_duties", str(duty_id), "删除岗位", request)
    return True
