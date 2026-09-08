from sqlalchemy.orm import Session
import uuid

from app.models.exception import ExceptionRecord
from app.repositories.exception_repository import ExceptionRepository
from app.schemas.exception import ExceptionRecordCreate, ExceptionRecordUpdate
from app.core.timeutil import beijing_now


def _to_dict(r: ExceptionRecord) -> dict:
    """ORM → dict，datetime 字段序列化为 'YYYY-MM-DD HH:MM:SS' 字符串。"""
    def _fmt(v):
        return v.strftime("%Y-%m-%d %H:%M:%S") if v else None
    return {
        "id": r.id,
        "exception_no": r.exception_no,
        "occurred_time": _fmt(r.occurred_time),
        "discoverer": r.discoverer,
        "exception_type": r.exception_type,
        "exception_level": r.exception_level,
        "phenomenon_desc": r.phenomenon_desc,
        "cause_category": r.cause_category,
        "temporary_measure": r.temporary_measure,
        "responsible_person": r.responsible_person,
        "resolved_time": _fmt(r.resolved_time),
        "is_stopped": r.is_stopped,
        "stop_duration": r.stop_duration,
        "root_cause_analysis": r.root_cause_analysis,
        "long_term_solution": r.long_term_solution,
        "verification_result": r.verification_result,
        "status": r.status,
        "attachment": r.attachment,
        "created_by": r.created_by,
        "created_at": _fmt(r.created_at),
        "updated_at": _fmt(r.updated_at),
    }


class ExceptionService:

    @staticmethod
    def get_list(db: Session, page: int, page_size: int, keyword: str = None, type: str = None,
                 status: str = None, level: str = None, stopped: str = None):
        items, total = ExceptionRepository.get_list(
            db, page, page_size, keyword, type, status, level, stopped
        )
        return ([_to_dict(r) for r in items], total)

    @staticmethod
    def get_by_id(db: Session, record_id: str):
        record = ExceptionRepository.get_by_id(db, record_id)
        if not record:
            raise ValueError("异常记录不存在")
        return _to_dict(record)

    @staticmethod
    def create(db: Session, data: ExceptionRecordCreate, username: str):
        # 生成主键（UUID，与已有记录的字符串主键风格一致）
        dict_data = data.model_dump()
        dict_data["id"] = uuid.uuid4().hex.upper()

        # 生成编号：EXC-20260908-001
        today = beijing_now().strftime("%Y%m%d")
        count = db.query(ExceptionRecord).filter(
            ExceptionRecord.exception_no.like(f"EXC-{today}%")
        ).count()
        no = f"EXC-{today}-{str(count + 1).zfill(3)}"

        dict_data["exception_no"] = no
        dict_data["created_by"] = username
        record = ExceptionRepository.create(db, dict_data)
        return _to_dict(record)

    @staticmethod
    def update(db: Session, record_id: str, data: ExceptionRecordUpdate):
        record = ExceptionRepository.get_by_id(db, record_id)
        if not record:
            raise ValueError("异常记录不存在")
        updated = ExceptionRepository.update(db, record, data.model_dump(exclude_unset=True))
        return _to_dict(updated)

    @staticmethod
    def delete(db: Session, record_id: str):
        record = ExceptionRepository.get_by_id(db, record_id)
        if not record:
            raise ValueError("异常记录不存在")
        ExceptionRepository.delete(db, record)

    @staticmethod
    def get_dashboard(db: Session):
        return ExceptionRepository.get_dashboard(db)
