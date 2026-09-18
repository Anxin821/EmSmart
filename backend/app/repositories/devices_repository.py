from typing import Optional, List, Tuple, Dict
from io import BytesIO
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.crud import (
    get_aoi_devices_paginated, create_aoi_device, update_aoi_device,
    delete_aoi_device, get_aoi_device_by_id, get_aoi_device_by_pk, batch_import_devices,
)
from app.models.device import AoiAiDevice

__all__ = [
    "get_aoi_devices_paginated",
    "create_aoi_device",
    "update_aoi_device",
    "delete_aoi_device",
    "get_aoi_device_by_id",
    "get_aoi_device_by_pk",
    "batch_import_devices",
    "count_devices_by_status",
]


def count_devices_by_status(db: Session) -> Dict[str, int]:
    """统计各状态设备数量，返回 { normal: N, fault: N, maintenance: N, total: N }。"""
    rows = (
        db.query(AoiAiDevice.status, func.count(AoiAiDevice.id))
        .group_by(AoiAiDevice.status)
        .all()
    )
    status_map = {"正常": "normal", "故障": "fault", "保养中": "maintenance"}
    result = {"normal": 0, "fault": 0, "maintenance": 0}
    total = 0
    for status, cnt in rows:
        key = str(status).strip() if status else "正常"
        eng_key = status_map.get(key)
        if eng_key:
            result[eng_key] = cnt
        total += cnt
    result["total"] = total
    return result

# Thin wrapper exposing existing core.crud functions for service layer

def list_devices(db: Session, page: int = 1, page_size: int = 20, keyword: Optional[str] = None, production_line: Optional[str] = None, status: Optional[str] = None, device_type: Optional[str] = None):
    return get_aoi_devices_paginated(db, page, page_size, keyword, production_line, status, device_type)


def create_device(db: Session, data: dict):
    return create_aoi_device(db, data)


def update_device(db: Session, item_id: int, data: dict):
    return update_aoi_device(db, item_id, data)


def delete_device(db: Session, item_id: int):
    return delete_aoi_device(db, item_id)


def get_device_by_pk(db: Session, item_id: int):
    return get_aoi_device_by_pk(db, item_id)


def get_device_by_id(db: Session, device_id: str):
    return get_aoi_device_by_id(db, device_id)


def import_devices(db: Session, rows_data: List[dict]):
    return batch_import_devices(db, rows_data)