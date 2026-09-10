"""库房管理 ORM 模型：治具（借还）+ 耗材（领用/补货）一体化。"""
from .base import Base, Column, Integer, String, Date, DateTime, Text, Boolean

from app.core.timeutil import beijing_now


class WarehousePart(Base):
    """库房物品表（治具 / 耗材）"""
    __tablename__ = "warehouse_parts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)          # 物品名称
    model = Column(String(100))                         # 型号 / 内部编号
    part_type = Column(String(10), nullable=False)      # 治具 / 耗材
    total_qty = Column(Integer, default=0)              # 治具=总数；耗材=当前库存
    available_qty = Column(Integer, default=0)          # 治具=可用数量（耗材不使用）
    unit = Column(String(20))                           # 耗材单位（个/卷/包…）
    location = Column(String(50))                       # 货位编码（如 A01-1-2）
    warn_qty = Column(Integer, default=0)               # 耗材低库存预警值
    in_repair = Column(Boolean, default=False)          # 治具维修中标记
    current_borrower = Column(String(50))               # 治具当前借用人（最近一次借出）
    borrow_time = Column(DateTime)                      # 借出时间
    expected_return = Column(Date)                      # 预计归还日期
    supplier = Column(String(100))                      # 最近供应商
    created_at = Column(DateTime, default=beijing_now)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now)


class PartTransaction(Base):
    """库房操作流水：借出 / 归还 / 领用 / 补货"""
    __tablename__ = "part_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    part_id = Column(Integer, nullable=False, index=True)
    part_name = Column(String(100))                     # 物品名称快照
    tx_type = Column(String(10), nullable=False)        # 借出 / 归还 / 领用 / 补货
    qty = Column(Integer, default=0)                    # 数量
    operator = Column(String(50))                       # 借用人 / 领用人
    line = Column(String(20))                           # 线体
    supplier = Column(String(100))                      # 供应商（补货）
    remark = Column(String(255))                        # 备注
    created_at = Column(DateTime, default=beijing_now)


__all__ = ["WarehousePart", "PartTransaction"]
