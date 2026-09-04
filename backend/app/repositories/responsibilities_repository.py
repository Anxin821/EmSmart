from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import JobResponsibility

__all__ = ["list_job_duties_repo", "get_job_duty_repo", "create_job_duty_repo", "update_job_duty_repo", "delete_job_duty_repo"]


def list_job_duties_repo(db: Session):
    return db.query(JobResponsibility).order_by(JobResponsibility.sort_order, JobResponsibility.id).all()


def get_job_duty_repo(db: Session, duty_id: int):
    return db.query(JobResponsibility).filter(JobResponsibility.id == duty_id).first()


def create_job_duty_repo(db: Session, payload: dict):
    row = JobResponsibility(**payload)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_job_duty_repo(db: Session, duty_id: int, updates: dict):
    row = get_job_duty_repo(db, duty_id)
    if not row:
        return None
    for k, v in updates.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


def delete_job_duty_repo(db: Session, duty_id: int):
    row = get_job_duty_repo(db, duty_id)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True
