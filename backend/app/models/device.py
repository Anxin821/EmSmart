"""AOI&AI 设备 ORM 模型。"""
from .base import Base, Column, Integer, String, Date, DateTime, Text

from app.core.timeutil import beijing_now


class AoiAiDevice(Base):
    """AOI&AI 设备部署表"""
    __tablename__ = "aoi_ai_devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    device_type = Column(String(10), nullable=False)       # AOI / AI
    production_line = Column(String(10), nullable=False)    # 1线-8线
    location = Column(String(100))
    ip_address = Column(String(50))
    status = Column(String(20), nullable=False, default="正常")  # 正常 / 故障 / 保养中
    responsible_person = Column(String(50))
    install_date = Column(Date)
    remark = Column(Text)
    created_at = Column(DateTime, default=beijing_now)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now)


__all__ = ["AoiAiDevice"]
