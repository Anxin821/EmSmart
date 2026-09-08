"""异常履历 Schema。"""
from .common import BaseModel, Optional, datetime


class ExceptionRecordBase(BaseModel):
    occurred_time: datetime
    discoverer: str
    exception_type: str
    exception_level: str = 'major'
    phenomenon_desc: str
    cause_category: Optional[str] = None
    temporary_measure: Optional[str] = None
    responsible_person: Optional[str] = None
    resolved_time: Optional[datetime] = None
    is_stopped: int = 0
    stop_duration: int = 0
    root_cause_analysis: Optional[str] = None
    long_term_solution: Optional[str] = None
    verification_result: Optional[str] = None
    status: str = 'pending'
    attachment: Optional[str] = None


class ExceptionRecordCreate(ExceptionRecordBase):
    pass


class ExceptionRecordUpdate(BaseModel):
    occurred_time: Optional[datetime] = None
    discoverer: Optional[str] = None
    exception_type: Optional[str] = None
    exception_level: Optional[str] = None
    phenomenon_desc: Optional[str] = None
    cause_category: Optional[str] = None
    temporary_measure: Optional[str] = None
    responsible_person: Optional[str] = None
    resolved_time: Optional[datetime] = None
    is_stopped: Optional[int] = None
    stop_duration: Optional[int] = None
    root_cause_analysis: Optional[str] = None
    long_term_solution: Optional[str] = None
    verification_result: Optional[str] = None
    status: Optional[str] = None
    attachment: Optional[str] = None


class ExceptionRecordResponse(ExceptionRecordBase):
    id: str
    exception_no: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


__all__ = [
    "ExceptionRecordBase",
    "ExceptionRecordCreate",
    "ExceptionRecordUpdate",
    "ExceptionRecordResponse",
]
