"""系统/杂项表：项目、操作日志、杀毒记录、岗位职责。"""
from .base import Base, Column, Integer, String, Boolean, Date, DateTime, Text, datetime


class Project(Base):
    """项目表"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_code = Column(String(20), unique=True, nullable=False)  # 项目编码 A/B/C...
    project_name = Column(String(100), nullable=False)              # 项目名称
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OperationLog(Base):
    """操作日志表"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    target_type = Column(String(50))
    target_id = Column(String(50))
    detail = Column(Text)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class AntivirusRecord(Base):
    """设备杀毒记录表"""
    __tablename__ = "antivirus_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(50), nullable=False)
    antivirus_time = Column(DateTime, nullable=False)
    production_line = Column(String(10), nullable=False)
    operator = Column(String(50), nullable=False)
    cycle = Column(String(10), nullable=False, default="每天")  # 每天 / 每周
    next_antivirus_time = Column(DateTime, nullable=False)
    remark = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobResponsibility(Base):
    """岗位职责表"""
    __tablename__ = "job_responsibilities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)          # 人员姓名
    title = Column(String(50), nullable=False)          # 岗位名称（工程师/技术员）
    items = Column(Text, default="[]")                  # JSON: [{"content":"职责","is_primary":true}]
    sort_order = Column(Integer, default=0)             # 排序
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


__all__ = ["Project", "OperationLog", "AntivirusRecord", "JobResponsibility"]
