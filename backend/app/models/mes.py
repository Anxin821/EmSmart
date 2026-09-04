"""MES（工单/BUG/需求）ORM 模型。"""
from .base import Base, Column, Integer, String, Date, DateTime, Text, Float, datetime


class WorkOrder(Base):
    """日常工单表"""
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String(50), unique=True, nullable=False)
    order_type = Column(String(20), nullable=False)          # 组装 / 包装
    product_name = Column(String(100), nullable=False)
    priority = Column(String(10), nullable=False, default="中")  # 紧急 / 高 / 中 / 低
    planned_start = Column(DateTime)
    planned_end = Column(DateTime)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    status = Column(String(20), nullable=False, default="待开始")  # 待开始 / 进行中 / 已完成 / 挂起
    responsible_person = Column(String(50))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Bug(Base):
    """异常BUG表"""
    __tablename__ = "bugs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bug_id = Column(String(50), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    severity = Column(String(10), nullable=False)            # 致命 / 严重 / 一般 / 建议
    module = Column(String(100))
    status = Column(String(20), nullable=False, default="确认新增")  # 确认新增 / 修复中 / 解决关闭
    discoverer = Column(String(50))
    assignee = Column(String(50))
    created_date = Column(Date, default=datetime.utcnow)
    deadline = Column(Date)
    solution = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DevRequest(Base):
    """二次开发需求表"""
    __tablename__ = "dev_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(50), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    source = Column(String(100))
    priority = Column(String(10), nullable=False, default="中")
    status = Column(String(20), nullable=False, default="收集评估")  # 收集评估 / 开发测试中 / 上线
    submitter = Column(String(50))         # 提出人
    assignee = Column(String(50))          # 责任人
    expected_date = Column(Date)
    responsible_person = Column(String(50))  # 保留兼容旧字段
    progress = Column(Float, default=0)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


__all__ = ["WorkOrder", "Bug", "DevRequest"]
