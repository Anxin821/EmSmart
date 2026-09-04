from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.repositories import antivirus_repository as repo


def list_records(db: Session, page: int = 1, page_size: int = 20, production_line: Optional[str] = None, device_id: Optional[str] = None, cycle: Optional[str] = None):
    records, total = repo.list_records(db, page=page, page_size=page_size, production_line=production_line, device_id=device_id, cycle=cycle)
    return [repo._record_to_dict(r) for r in records], total


def get_record(db: Session, record_id: int):
    r = repo.get_record(db, record_id)
    return repo._record_to_dict(r) if r else None


def create_record(db: Session, body_data: dict):
    r = repo.create_record(db, body_data)
    return repo._record_to_dict(r)


def update_record(db: Session, record_id: int, update_data: dict):
    r = repo.update_record(db, record_id, update_data)
    return repo._record_to_dict(r) if r else None


def delete_record(db: Session, record_id: int):
    return repo.delete_record(db, record_id)


def import_records(db: Session, records: List[dict]):
    return repo.import_records(db, records)


def list_overdue_records(db: Session, status: Optional[str] = None, production_line: Optional[str] = None, page: int = 1, page_size: int = 50):
    records, total = repo.list_overdue_records(db, status=status, production_line=production_line, page=page, page_size=page_size)
    return [repo._record_to_dict(r) for r in records], total


def antivirus_dashboard(db: Session) -> Dict[str, Any]:
    return repo.antivirus_dashboard(db)
