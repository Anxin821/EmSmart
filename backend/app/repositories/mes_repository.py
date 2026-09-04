from typing import Optional, List, Tuple
from io import BytesIO
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.crud import (
    get_mes_dashboard,
    get_work_orders_paginated, create_work_order, update_work_order, delete_work_order,
    get_bugs_paginated, create_bug, update_bug, delete_bug,
    get_dev_requests_paginated, create_dev_request, update_dev_request, delete_dev_request,
)


__all__ = [
    "get_mes_dashboard",
    "get_work_orders_paginated",
    "create_work_order",
    "update_work_order",
    "delete_work_order",
    "get_bugs_paginated",
    "create_bug",
    "update_bug",
    "delete_bug",
    "get_dev_requests_paginated",
    "create_dev_request",
    "update_dev_request",
    "delete_dev_request",
]


def get_dashboard(db: Session):
    return get_mes_dashboard(db)


def work_orders_paginated(db: Session, page: int, page_size: int, keyword: Optional[str], status: Optional[str], priority: Optional[str], order_type: Optional[str]):
    return get_work_orders_paginated(db, page, page_size, keyword, status, priority, order_type)


def create_work_order_repo(db: Session, data: dict):
    return create_work_order(db, data)


def update_work_order_repo(db: Session, order_number: str, data: dict):
    return update_work_order(db, order_number, data)


def delete_work_order_repo(db: Session, order_number: str):
    return delete_work_order(db, order_number)


def bugs_paginated(db: Session, page: int, page_size: int, keyword: Optional[str], status: Optional[str], severity: Optional[str]):
    return get_bugs_paginated(db, page, page_size, keyword, status, severity)


def create_bug_repo(db: Session, data: dict):
    return create_bug(db, data)


def update_bug_repo(db: Session, bug_id: str, data: dict):
    return update_bug(db, bug_id, data)


def delete_bug_repo(db: Session, bug_id: str):
    return delete_bug(db, bug_id)


def dev_requests_paginated(db: Session, page: int, page_size: int, keyword: Optional[str], status: Optional[str], priority: Optional[str]):
    return get_dev_requests_paginated(db, page, page_size, keyword, status, priority)


def create_dev_request_repo(db: Session, data: dict):
    return create_dev_request(db, data)


def update_dev_request_repo(db: Session, request_id: str, data: dict):
    return update_dev_request(db, request_id, data)


def delete_dev_request_repo(db: Session, request_id: str):
    return delete_dev_request(db, request_id)
