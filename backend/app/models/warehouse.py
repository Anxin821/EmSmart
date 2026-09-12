"""库房管理 ORM 模型：治具（借还）+ 耗材（领用/补货）一体化。
核心改动：
- 新增 BorrowRecord 表追踪每笔借出（支持多人借出、按记录归还、转维修）
- WarehousePart 新增 repair_qty 字段（维修中数量，计入库存但不可借出）
- 去掉 in_repair 布尔字段（改用 repair_qty > 0 判断）
- 去掉 expected_return / supplier 字段
"""
from .base import Base, Column, Integer, String, DateTime, Text, Boolean

from app.core.timeutil import beijing_now


class WarehousePart(Base):
    """库房物品表（治具 / 耗材）"""
    __tablename__ = "warehouse_parts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)          # 物品名称
    model = Column(String(100))                         # 型号
    code = Column(String(100))                          # 编号
    part_type = Column(String(10), nullable=False)      # 治具 / 耗材
    total_qty = Column(Integer, default=0)              # 治具=总数；耗材=当前库存
    available_qty = Column(Integer, default=0)          # 治具=在库数量（含维修，不含借出）
    repair_qty = Column(Integer, default=0)              # 治具维修中数量（计入库存但不可借出）
    unit = Column(String(20))                           # 耗材单位（个/卷/包…）
    location = Column(String(50))                       # 货位编码（如 A01-1-2）
    warn_qty = Column(Integer, default=0)               # 耗材低库存预警值
    current_borrower = Column(String(50))               # 治具最近借用人（仅展示用）
    borrow_time = Column(DateTime)                      # 最近借出时间
    created_at = Column(DateTime, default=beijing_now)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now)


class BorrowRecord(Base):
    """治具借出记录：追踪每笔借出，支持按记录归还和转维修。"""
    __tablename__ = "warehouse_borrow_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    part_id = Column(Integer, nullable=False, index=True)
    borrower = Column(String(50))                       # 借用人
    department_manager = Column(String(50))             # 部门负责人
    line = Column(String(20))                           # 线体
    qty = Column(Integer, default=1)                    # 借出数量
    borrow_time = Column(DateTime, default=beijing_now)
    status = Column(String(10), default="借出")          # 借出 / 已归还 / 维修
    remark = Column(String(255))
    created_at = Column(DateTime, default=beijing_now)


class PartTransaction(Base):
    """库房操作流水：借出 / 归还 / 领用 / 补货 / 维修"""
    __tablename__ = "part_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    part_id = Column(Integer, nullable=False, index=True)
    part_name = Column(String(100))                     # 物品名称快照
    tx_type = Column(String(10), nullable=False)        # 借出 / 归还 / 领用 / 补货 / 维修
    qty = Column(Integer, default=0)                    # 数量
    operator = Column(String(50))                       # 借用人 / 领用人
    department_manager = Column(String(50))             # 部门负责人
    line = Column(String(20))                           # 线体
    borrow_time = Column(DateTime)                      # 借出时间
    return_time = Column(DateTime)                      # 归还时间
    remark = Column(String(255))                        # 备注（可编辑）
    created_at = Column(DateTime, default=beijing_now)


__all__ = ["WarehousePart", "BorrowRecord", "PartTransaction"]
