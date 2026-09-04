from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.core.crud import write_operation_log
from app.repositories import esop_repository as repo


def to_dict(p) -> dict:
    return {
        "id": p.id,
        "station_name": p.station_name,
        "process_name": p.process_name,
        "part_number": p.part_number,
        "file_name": p.file_name,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


def list_esop_parts(db: Session, page: int =1, page_size: int =20, keyword: Optional[str]=None, station_name: Optional[str]=None, process_name: Optional[str]=None, file_name: Optional[str]=None):
    items, total = repo.list_esop_parts(db, page, page_size, keyword, station_name, process_name, file_name)
    return ([to_dict(d) for d in items], total)


def create_esop(db: Session, data: dict, request, username: str):
    part = repo.create_esop_part_repo(db, data)
    write_operation_log(db, username, "CREATE", "esop_parts", str(part.id), f"新增料号: {data.get('part_number','')}", request)
    return to_dict(part)


def update_esop(db: Session, part_id: int, data: dict, request, username: str):
    part = repo.update_esop_part_repo(db, part_id, data)
    if not part:
        return None
    write_operation_log(db, username, "UPDATE", "esop_parts", str(part_id), "更新料号", request)
    return to_dict(part)


def delete_esop(db: Session, part_id: int, request, username: str):
    ok = repo.delete_esop_part_repo(db, part_id)
    if not ok:
        return False
    write_operation_log(db, username, "DELETE", "esop_parts", str(part_id), "删除料号", request)
    return True
