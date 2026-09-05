"""周报/月报生产数据 ORM 模型。"""
from .base import Base, Column, Integer, String, Float, DateTime, Computed, datetime


class WeeklyProduction(Base):
    """每周生产数据表"""
    __tablename__ = "weekly_production"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False)
    week_number = Column(Integer, nullable=False)
    production_line = Column(String(10), nullable=False)
    project = Column(String(50), nullable=False)            # A / B / C
    total_output = Column(Integer, nullable=False, default=0)
    qualified_count = Column(Integer, nullable=False, default=0)
    defect_count = Column(Integer, Computed("total_output - qualified_count"))
    yield_rate = Column(Float, Computed("CASE WHEN total_output > 0 THEN ROUND(CAST(qualified_count AS FLOAT) / total_output * 100, 2) ELSE 0 END"))
    recorder = Column(String(50))
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class MonthlyProduction(Base):
    """每月生产数据表"""
    __tablename__ = "monthly_production"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    production_line = Column(String(10), nullable=False)
    project = Column(String(50), nullable=False)
    monthly_total_output = Column(Integer, nullable=False, default=0)
    monthly_qualified_count = Column(Integer, nullable=False, default=0)
    monthly_defect_count = Column(Integer, Computed("monthly_total_output - monthly_qualified_count"))
    monthly_yield_rate = Column(Float, Computed("CASE WHEN monthly_total_output > 0 THEN ROUND(CAST(monthly_qualified_count AS FLOAT) / monthly_total_output * 100, 2) ELSE 0 END"))
    recorder = Column(String(50))
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


__all__ = ["WeeklyProduction", "MonthlyProduction"]
