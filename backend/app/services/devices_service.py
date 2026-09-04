from typing import Optional, List, Tuple, Dict, Any
from io import BytesIO
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import devices_repository as repo
from app.core.crud import write_operation_log


def _clean_device_status(status) -> str:
    if status is None:
        return "正常"
    s = str(status).strip().lstrip("|").rstrip("|").strip()
    return s or "正常"


def _device_to_dict(d) -> dict:
    return {
        "id": d.id, "device_id": d.device_id, "name": d.name,
        "device_type": d.device_type, "production_line": d.production_line,
        "location": d.location, "ip_address": d.ip_address,
        "status": _clean_device_status(d.status),
        "responsible_person": d.responsible_person,
        "install_date": d.install_date.isoformat() if d.install_date else None,
        "remark": d.remark,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }


def list_devices(db: Session, page: int = 1, page_size: int = 20, keyword: Optional[str] = None, production_line: Optional[str] = None, status: Optional[str] = None, device_type: Optional[str] = None):
    items, total = repo.list_devices(db, page=page, page_size=page_size, keyword=keyword, production_line=production_line, status=status, device_type=device_type)
    return ([_device_to_dict(d) for d in items], total)


def create_device(db: Session, payload: dict, request, username: str):
    existing = repo.get_device_by_id(db, payload.get("device_id"))
    if existing:
        raise HTTPException(status_code=400, detail="设备ID已存在")
    device = repo.create_device(db, payload)
    write_operation_log(db, username, "CREATE", "aoi_device", payload.get("device_id"), f"新增设备: {payload.get('name')}", request)
    return _device_to_dict(device)


def edit_device(db: Session, item_id: int, payload: dict, request, username: str):
    device = repo.update_device(db, item_id, payload)
    if not device:
        return None
    write_operation_log(db, username, "UPDATE", "aoi_device", str(item_id), "更新设备", request)
    return _device_to_dict(device)


def remove_device(db: Session, item_id: int, request, username: str):
    ok = repo.delete_device(db, item_id)
    if not ok:
        return False
    write_operation_log(db, username, "DELETE", "aoi_device", str(item_id), "删除设备", request)
    return True


def get_device(db: Session, item_id: int):
    device = repo.get_device_by_pk(db, item_id)
    if not device:
        return None
    return _device_to_dict(device)


def import_devices(db: Session, rows_data: List[dict], request, username: str):
    count = repo.import_devices(db, rows_data)
    write_operation_log(db, username, "CREATE", "aoi_device", None, f"批量导入 {count} 台设备", request)
    return count


def export_devices_rows(db: Session, items):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "AOI&AI设备"
    headers = ["设备ID", "名称", "类型", "产线", "位置", "IP地址", "状态", "负责人", "安装日期", "备注"]
    ws.append(headers)
    for d in items:
        ws.append([
            d.device_id, d.name, d.device_type, d.production_line, d.location or "",
            d.ip_address or "", d.status or "", d.responsible_person or "",
            str(d.install_date) if d.install_date else "", d.remark or "",
        ])
    output = BytesIO(); wb.save(output); output.seek(0)
    return output
