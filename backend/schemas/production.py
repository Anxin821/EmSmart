"""周报/月报 Schema。

包含原本散落在 routers/production.py 的 MonthlyGenerateRequest。
"""
from .common import BaseModel, Optional, datetime


class WeeklyProductionBase(BaseModel):
    year: int
    week_number: int
    production_line: str
    project: str
    total_output: int = 0
    qualified_count: int = 0
    recorder: Optional[str] = None


class WeeklyProductionCreate(WeeklyProductionBase):
    pass


class WeeklyProductionUpdate(BaseModel):
    total_output: Optional[int] = None
    qualified_count: Optional[int] = None
    recorder: Optional[str] = None


class WeeklyProductionOut(WeeklyProductionBase):
    id: int
    defect_count: Optional[int] = None
    yield_rate: Optional[float] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MonthlyProductionBase(BaseModel):
    year: int
    month: int
    production_line: str
    project: str
    monthly_total_output: int = 0
    monthly_qualified_count: int = 0
    recorder: Optional[str] = None


class MonthlyProductionCreate(MonthlyProductionBase):
    pass


class MonthlyProductionUpdate(BaseModel):
    monthly_total_output: Optional[int] = None
    monthly_qualified_count: Optional[int] = None
    recorder: Optional[str] = None


class MonthlyProductionOut(MonthlyProductionBase):
    id: int
    monthly_defect_count: Optional[int] = None
    monthly_yield_rate: Optional[float] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 原散落在 routers/production.py:264 的 Schema 迁移至此
class MonthlyGenerateRequest(BaseModel):
    year: int
    month: int


__all__ = [
    "WeeklyProductionBase",
    "WeeklyProductionCreate",
    "WeeklyProductionUpdate",
    "WeeklyProductionOut",
    "MonthlyProductionBase",
    "MonthlyProductionCreate",
    "MonthlyProductionUpdate",
    "MonthlyProductionOut",
    "MonthlyGenerateRequest",
]
