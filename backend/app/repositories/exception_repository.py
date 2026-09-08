from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.exception import ExceptionRecord
from typing import Optional, Tuple, List


class ExceptionRepository:

    @staticmethod
    def get_list(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        exception_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Tuple[List[ExceptionRecord], int]:
        query = db.query(ExceptionRecord)
        if keyword:
            query = query.filter(
                or_(
                    ExceptionRecord.exception_no.like(f"%{keyword}%"),
                    ExceptionRecord.phenomenon_desc.like(f"%{keyword}%"),
                    ExceptionRecord.discoverer.like(f"%{keyword}%")
                )
            )
        if exception_type:
            query = query.filter(ExceptionRecord.exception_type == exception_type)
        if status:
            query = query.filter(ExceptionRecord.status == status)

        total = query.count()
        items = query.order_by(ExceptionRecord.created_at.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, record_id: str):
        return db.query(ExceptionRecord).filter(ExceptionRecord.id == record_id).first()

    @staticmethod
    def create(db: Session, data: dict):
        record = ExceptionRecord(**data)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def update(db: Session, record: ExceptionRecord, data: dict):
        for key, value in data.items():
            if value is not None and hasattr(record, key):
                setattr(record, key, value)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def delete(db: Session, record: ExceptionRecord):
        db.delete(record)
        db.commit()

    @staticmethod
    def get_dashboard(db: Session) -> dict:
        all_count = db.query(ExceptionRecord).count()
        pending = db.query(ExceptionRecord).filter(ExceptionRecord.status == 'pending').count()
        processing = db.query(ExceptionRecord).filter(ExceptionRecord.status == 'processing').count()
        resolved = db.query(ExceptionRecord).filter(ExceptionRecord.status == 'resolved').count()
        closed = db.query(ExceptionRecord).filter(ExceptionRecord.status == 'closed').count()

        # 按类型统计
        types = []
        from sqlalchemy import func
        type_stats = db.query(
            ExceptionRecord.exception_type,
            func.count(ExceptionRecord.id).label('count')
        ).group_by(ExceptionRecord.exception_type).all()
        for row in type_stats:
            types.append({"type": row[0], "count": row[1]})

        return {
            "total": all_count,
            "pending": pending,
            "processing": processing,
            "resolved": resolved,
            "closed": closed,
            "by_type": types
        }