from typing import Optional, Tuple, List
from sqlalchemy.orm import Session

from app.core.crud import get_esop_parts_paginated, create_esop_part, update_esop_part, delete_esop_part

__all__ = [
    "get_esop_parts_paginated",
    "create_esop_part",
    "update_esop_part",
    "delete_esop_part",
]


def list_esop_parts(db: Session, page: int = 1, page_size: int = 20, keyword: Optional[str] = None, station_name: Optional[str] = None, process_name: Optional[str] = None, file_name: Optional[str] = None):
    return get_esop_parts_paginated(db, page, page_size, keyword, station_name, process_name, file_name)


def create_esop_part_repo(db: Session, data: dict):
    return create_esop_part(db, data)


def update_esop_part_repo(db: Session, part_id: int, data: dict):
    return update_esop_part(db, part_id, data)


def delete_esop_part_repo(db: Session, part_id: int):
    return delete_esop_part(db, part_id)
