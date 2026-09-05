"""ESOP 料号 ORM 模型。"""
from .base import Base, Column, Integer, String, DateTime

from app.core.timeutil import beijing_now


class EsopPart(Base):
    """ESOP 料号表"""
    __tablename__ = "esop_parts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_name = Column(String(100), nullable=False)    # 工位名称
    process_name = Column(String(100), nullable=False)    # 工序名称
    part_number = Column(String(100), nullable=False)     # 料号
    file_name = Column(String(255))                        # ESOP 文件名称
    created_at = Column(DateTime, default=beijing_now)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now)


__all__ = ["EsopPart"]
