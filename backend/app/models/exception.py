"""异常履历 ORM 模型。"""
from .base import Base, Column, Integer, String, DateTime, Text

from app.core.timeutil import beijing_now


class ExceptionRecord(Base):
    """异常履历记录表"""
    __tablename__ = "exception_records"

    id = Column(String(50), primary_key=True)                            # UUID 字符串主键
    exception_no = Column(String(50), unique=True, nullable=False)        # EXC-20260908-001
    occurred_time = Column(DateTime, nullable=False)                      # 发生时间
    discoverer = Column(String(50), nullable=False)                       # 发现人
    exception_type = Column(String(30), nullable=False)                   # 设备异常/质量异常/物料异常/工艺异常/系统异常/人员操作/其他
    exception_level = Column(String(20), default='major')                 # critical/major/minor
    phenomenon_desc = Column(Text, nullable=False)                        # 现象描述
    cause_category = Column(String(30))                                    # 原因分类
    temporary_measure = Column(Text)                                       # 临时措施
    responsible_person = Column(String(50))                                # 责任人
    resolved_time = Column(DateTime)                                       # 解决时间
    is_stopped = Column(Integer, default=0)                               # 是否停线 0/1
    stop_duration = Column(Integer, default=0)                            # 停线时长（分钟）
    root_cause_analysis = Column(Text)                                     # 根本原因分析
    long_term_solution = Column(Text)                                      # 长期对策
    verification_result = Column(String(200))                              # 验证结果
    status = Column(String(20), default='pending')                        # pending/processing/resolved/closed
    attachment = Column(String(500))                                       # 附件
    created_by = Column(String(50))                                        # 创建人
    created_at = Column(DateTime, default=beijing_now)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now)


__all__ = ["ExceptionRecord"]
