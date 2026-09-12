"""库房管理服务：治具借还 + 耗材领用/补货，含统计与操作流水。

核心改动：
- 借出创建 BorrowRecord，归还按记录归还（解决多人借出只能还最后一人的 bug）
- 维修状态用 repair_qty（计入库存但不可借出），替代旧 in_repar 布尔
- 出入库记录备注可编辑
"""
from typing import Optional, Tuple, List, Dict, Any

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.timeutil import beijing_now
from app.core.crud import write_operation_log
from app.models import WarehousePart, BorrowRecord, PartTransaction

JIG = "治具"
CONSUMABLE = "耗材"


# ---------------- 序列化 ----------------
def _part_to_dict(p: WarehousePart) -> Dict[str, Any]:
    if p.part_type == JIG:
        if p.repair_qty and p.repair_qty > 0:
            status = "维修中"
        elif p.available_qty >= p.total_qty:
            status = "在库"
        elif p.available_qty <= 0:
            status = "已借出"
        else:
            # 部分借出：仍有可用余量，应允许继续借出
            status = "部分借出"
        qty_text = f"{p.available_qty}/{p.total_qty}"
        stock_qty = p.total_qty
    else:
        stock_qty = p.total_qty
        if stock_qty <= 0:
            status = "缺货"
        elif p.warn_qty and stock_qty <= p.warn_qty:
            status = "低于预警"
        else:
            status = "正常"
        qty_text = f"{stock_qty} {p.unit or ''}".strip()
    return {
        "id": p.id,
        "name": p.name,
        "model": p.model or "",
        "code": p.code or "",
        "part_type": p.part_type,
        "total_qty": p.total_qty,
        "available_qty": p.available_qty,
        "stock_qty": stock_qty,
        "unit": p.unit or "",
        "location": p.location or "",
        "warn_qty": p.warn_qty or 0,
        "repair_qty": p.repair_qty or 0,
        "status": status,
        "qty_text": qty_text,
        "current_borrower": p.current_borrower,
        "borrow_time": p.borrow_time.strftime("%Y-%m-%d %H:%M:%S") if p.borrow_time else None,
        "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else None,
        "updated_at": p.updated_at.strftime("%Y-%m-%d %H:%M:%S") if p.updated_at else None,
    }


def _tx_to_dict(t: PartTransaction) -> Dict[str, Any]:
    return {
        "id": t.id,
        "part_id": t.part_id,
        "part_name": t.part_name,
        "tx_type": t.tx_type,
        "qty": t.qty,
        "operator": t.operator or "",
        "department_manager": t.department_manager or "",
        "line": t.line or "",
        "borrow_time": t.borrow_time.strftime("%Y-%m-%d %H:%M:%S") if t.borrow_time else None,
        "return_time": t.return_time.strftime("%Y-%m-%d %H:%M:%S") if t.return_time else None,
        "remark": t.remark or "",
        "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else None,
    }


def _borrow_to_dict(r: BorrowRecord) -> Dict[str, Any]:
    return {
        "id": r.id,
        "part_id": r.part_id,
        "borrower": r.borrower or "",
        "department_manager": r.department_manager or "",
        "line": r.line or "",
        "qty": r.qty,
        "borrow_time": r.borrow_time.strftime("%Y-%m-%d %H:%M:%S") if r.borrow_time else None,
        "status": r.status,
        "remark": r.remark or "",
    }


def _get_part(db: Session, part_id: int) -> WarehousePart:
    p = db.get(WarehousePart, part_id)
    if not p:
        raise HTTPException(status_code=404, detail="物品不存在")
    return p


# ---------------- 列表 / 统计 / 详情 ----------------
def list_parts(db: Session, page: int = 1, page_size: int = 20,
               keyword: Optional[str] = None, part_type: Optional[str] = None,
               low_stock: bool = False,
               stock_status: Optional[str] = None) -> Tuple[List[dict], int]:
    q = db.query(WarehousePart)
    if part_type in (JIG, CONSUMABLE):
        q = q.filter(WarehousePart.part_type == part_type)
    if low_stock:
        q = q.filter(
            WarehousePart.part_type == CONSUMABLE,
            WarehousePart.warn_qty > 0,
            WarehousePart.total_qty <= WarehousePart.warn_qty,
        )
    # 统计卡联动筛选：口径与 get_stats 完全一致
    # borrowed：治具维修中/已借出/部分借出，或耗材缺货；in_stock：其余
    if stock_status == "borrowed":
        q = q.filter(or_(
            and_(WarehousePart.part_type == JIG,
                 or_(WarehousePart.repair_qty > 0,
                     WarehousePart.available_qty < WarehousePart.total_qty)),
            and_(WarehousePart.part_type == CONSUMABLE,
                 WarehousePart.total_qty <= 0),
        ))
    elif stock_status == "in_stock":
        q = q.filter(or_(
            and_(WarehousePart.part_type == JIG,
                 WarehousePart.repair_qty == 0,
                 WarehousePart.available_qty >= WarehousePart.total_qty),
            and_(WarehousePart.part_type == CONSUMABLE,
                 WarehousePart.total_qty > 0),
        ))
    if keyword:
        kw = f"%{keyword.strip()}%"
        q = q.filter(or_(
            WarehousePart.name.like(kw),
            WarehousePart.model.like(kw),
            WarehousePart.current_borrower.like(kw),
            WarehousePart.location.like(kw),
            WarehousePart.id.in_(
                db.query(PartTransaction.part_id).filter(PartTransaction.operator.like(kw))
            ),
        ))
    total = q.count()
    items = (q.order_by(WarehousePart.part_type.asc(), WarehousePart.id.desc())
              .offset((page - 1) * page_size).limit(page_size).all())
    return [_part_to_dict(p) for p in items], total


def get_stats(db: Session, part_type: Optional[str] = None) -> Dict[str, Any]:
    """统计物品状态。支持按类型过滤（治具/耗材），避免总治具/总耗材数字混在一起。"""
    q = db.query(WarehousePart)
    if part_type:
        q = q.filter(WarehousePart.part_type == part_type)
    parts = q.all()
    in_stock = 0
    borrowed_out = 0
    low_items: List[dict] = []
    for p in parts:
        d = _part_to_dict(p)
        if p.part_type == JIG:
            if (p.repair_qty and p.repair_qty > 0) or d["status"] in ("已借出", "部分借出"):
                borrowed_out += 1
            else:
                in_stock += 1
        else:
            if p.total_qty <= 0:
                borrowed_out += 1      # 耗材缺货 ≈ 已领用完
            else:
                in_stock += 1
            if p.warn_qty and p.total_qty <= p.warn_qty:
                low_items.append(d)
    return {
        "total": len(parts),
        "in_stock": in_stock,
        "borrowed_out": borrowed_out,
        "low_stock": len(low_items),
        "low_stock_items": low_items,
    }


def get_detail(db: Session, part_id: int) -> Optional[dict]:
    p = db.get(WarehousePart, part_id)
    if not p:
        return None
    txs = (db.query(PartTransaction)
             .filter(PartTransaction.part_id == part_id)
             .order_by(PartTransaction.id.desc()).limit(5).all())
    # 治具：附带当前未归还的借出记录
    borrows = []
    if p.part_type == JIG:
        active = (db.query(BorrowRecord)
                    .filter(BorrowRecord.part_id == part_id,
                            BorrowRecord.status == "借出")
                    .order_by(BorrowRecord.id.desc()).all())
        borrows = [_borrow_to_dict(r) for r in active]
    return {
        "part": _part_to_dict(p),
        "transactions": [_tx_to_dict(t) for t in txs],
        "borrow_records": borrows,
    }


def list_transactions(db: Session, page: int = 1, page_size: int = 50,
                      tx_type: Optional[str] = None,
                      keyword: Optional[str] = None) -> Tuple[List[dict], int]:
    """查询所有物品的借出/领用/归还/补货流水（按时间倒序）。"""
    q = db.query(PartTransaction)
    if tx_type in ("借出", "归还", "领用", "补货", "维修"):
        q = q.filter(PartTransaction.tx_type == tx_type)
    if keyword:
        kw = f"%{keyword.strip()}%"
        q = q.filter(or_(
            PartTransaction.part_name.like(kw),
            PartTransaction.operator.like(kw),
            PartTransaction.remark.like(kw),
            PartTransaction.department_manager.like(kw),
        ))
    total = q.count()
    items = (q.order_by(PartTransaction.id.desc())
              .offset((page - 1) * page_size).limit(page_size).all())
    return [_tx_to_dict(t) for t in items], total


def list_borrow_records(db: Session, part_id: int, active_only: bool = True) -> List[dict]:
    """查询治具的借出记录（默认只看未归还的）。"""
    p = _get_part(db, part_id)
    if p.part_type != JIG:
        raise HTTPException(status_code=400, detail="仅治具有借出记录")
    q = db.query(BorrowRecord).filter(BorrowRecord.part_id == part_id)
    if active_only:
        q = q.filter(BorrowRecord.status == "借出")
    records = q.order_by(BorrowRecord.id.desc()).all()
    return [_borrow_to_dict(r) for r in records]


# ---------------- CRUD ----------------
def create_part(db: Session, data: dict, request, username: str) -> dict:
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="物品名称不能为空")
    part_type = data.get("part_type") or JIG
    if part_type not in (JIG, CONSUMABLE):
        raise HTTPException(status_code=400, detail="类型只能是 治具 / 耗材")
    total = max(0, int(data.get("total_qty") or 0))
    p = WarehousePart(
        name=name,
        model=(data.get("model") or "").strip(),
        code=(data.get("code") or "").strip(),
        part_type=part_type,
        total_qty=total,
        available_qty=total if part_type == JIG else 0,
        unit=(data.get("unit") or "").strip(),
        location=(data.get("location") or "").strip(),
        warn_qty=max(0, int(data.get("warn_qty") or 0)) if part_type == CONSUMABLE else 0,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    # 新增物品时记录入库流水
    if total > 0:
        _add_tx(db, p, "入库" if part_type == JIG else "补货", total,
                operator=username, remark=f"新增{part_type}初始入库")
        db.commit()
        db.refresh(p)
    write_operation_log(db, username, "CREATE", "warehouse", str(p.id),
                        f"新增{part_type}: {name}", request)
    return _part_to_dict(p)


def update_part(db: Session, part_id: int, data: dict, request, username: str) -> Optional[dict]:
    p = _get_part(db, part_id)
    if "name" in data and data["name"]:
        p.name = str(data["name"]).strip()
    if "model" in data:
        p.model = (data.get("model") or "").strip()
    if "code" in data:
        p.code = (data.get("code") or "").strip()
    if "location" in data:
        p.location = (data.get("location") or "").strip()
    if "unit" in data and p.part_type == CONSUMABLE:
        p.unit = (data.get("unit") or "").strip()
    if "warn_qty" in data and p.part_type == CONSUMABLE:
        p.warn_qty = max(0, int(data.get("warn_qty") or 0))
    if "total_qty" in data:
        new_total = max(0, int(data.get("total_qty") or 0))
        if p.part_type == JIG:
            # 治具总数调整：可用数量按差值同向调整（新增治具=可用增加）
            delta = new_total - p.total_qty
            old_total = p.total_qty
            p.available_qty = max(0, min(new_total, p.available_qty + delta))
            p.total_qty = new_total
            # 总数变化时记录流水
            if delta != 0:
                db.flush()
                _add_tx(db, p, "补货" if delta > 0 else "减少", abs(delta),
                        operator=username,
                        remark=f"编辑总数: {old_total} → {new_total}")
        else:
            old_total = p.total_qty
            p.total_qty = new_total
            if new_total != old_total:
                delta = new_total - old_total
                db.flush()
                _add_tx(db, p, "补货" if delta > 0 else "减少", abs(delta),
                        operator=username,
                        remark=f"编辑库存: {old_total} → {new_total}")
    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "UPDATE", "warehouse", str(p.id),
                        f"编辑物品: {p.name}", request)
    return _part_to_dict(p)


def delete_part(db: Session, part_id: int, request, username: str) -> bool:
    p = db.get(WarehousePart, part_id)
    if not p:
        return False
    name = p.name
    db.query(PartTransaction).filter(PartTransaction.part_id == part_id).delete()
    db.query(BorrowRecord).filter(BorrowRecord.part_id == part_id).delete()
    db.delete(p)
    db.commit()
    write_operation_log(db, username, "DELETE", "warehouse", str(part_id),
                        f"删除物品: {name}", request)
    return True


# ---------------- 借还 / 领用 / 补货 / 维修 ----------------
def _add_tx(db, p: WarehousePart, tx_type: str, qty: int,
            operator: str = "", department_manager: str = "", line: str = "",
            remark: str = "", borrow_time=None, return_time=None):
    db.add(PartTransaction(
        part_id=p.id, part_name=p.name, tx_type=tx_type, qty=qty,
        operator=operator, department_manager=department_manager,
        line=line, remark=remark or "",
        borrow_time=borrow_time, return_time=return_time,
    ))


def _borrow_to_repair_qty(p: WarehousePart) -> int:
    """治具维修中数量 = repair_qty。"""
    return p.repair_qty or 0


def borrow(db: Session, part_id: int, data: dict, request, username: str) -> dict:
    """治具借出：每次借出创建一条 BorrowRecord，支持多人分别归还。"""
    p = _get_part(db, part_id)
    if p.part_type != JIG:
        raise HTTPException(status_code=400, detail="仅治具支持借出操作")
    # 维修中数量不可借出
    borrowable = p.available_qty - _borrow_to_repair_qty(p)
    if borrowable <= 0:
        raise HTTPException(status_code=400, detail="该治具维修中或已全部借出，暂不可借出")
    qty = int(data.get("qty") or 1)
    if qty <= 0:
        raise HTTPException(status_code=400, detail="借出数量必须大于 0")
    if qty > borrowable:
        raise HTTPException(status_code=400, detail=f"可借数量不足（当前可借 {borrowable}）")
    borrower = (data.get("operator") or data.get("borrower") or "").strip()
    line = (data.get("line") or "").strip()
    dept_mgr = (data.get("department_manager") or "").strip()
    if not borrower or not line:
        raise HTTPException(status_code=400, detail="借用人和线体为必填项")
    p.available_qty -= qty
    p.current_borrower = borrower
    p.borrow_time = beijing_now()
    # 创建借出记录
    db.add(BorrowRecord(
        part_id=p.id, borrower=borrower, department_manager=dept_mgr,
        line=line, qty=qty, remark=data.get("remark") or "",
    ))
    _add_tx(db, p, "借出", qty, operator=borrower, department_manager=dept_mgr,
            line=line, remark=data.get("remark") or "",
            borrow_time=p.borrow_time)
    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "BORROW", "warehouse", str(p.id),
                        f"治具借出: {p.name} x{qty} 借用人:{borrower}", request)
    return _part_to_dict(p)


def return_part(db: Session, part_id: int, data: dict, request, username: str) -> dict:
    """治具归还：按 borrow_record_id 归还指定借出记录（支持多人分别归还）。"""
    p = _get_part(db, part_id)
    if p.part_type != JIG:
        raise HTTPException(status_code=400, detail="仅治具支持归还操作")
    record_id = data.get("borrow_record_id")
    if not record_id:
        raise HTTPException(status_code=400, detail="请选择要归还的借出记录")
    r = db.get(BorrowRecord, int(record_id))
    if not r or r.part_id != p.id:
        raise HTTPException(status_code=404, detail="借出记录不存在")
    if r.status != "借出":
        raise HTTPException(status_code=400, detail="该记录已归还或已转维修")
    # 归还：可用+qty，记录标记已归还
    p.available_qty += r.qty
    r.status = "已归还"
    return_now = beijing_now()
    # 更新最近借用人（取下一条未归还记录）
    next_active = (db.query(BorrowRecord)
                     .filter(BorrowRecord.part_id == p.id,
                             BorrowRecord.status == "借出")
                     .order_by(BorrowRecord.id.desc()).first())
    if next_active:
        p.current_borrower = next_active.borrower
        p.borrow_time = next_active.borrow_time
    else:
        p.current_borrower = None
        p.borrow_time = None
    _add_tx(db, p, "归还", r.qty, operator=r.borrower or "",
            department_manager=r.department_manager or "", line=r.line or "",
            remark=data.get("remark") or "",
            borrow_time=r.borrow_time, return_time=return_now)
    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "RETURN", "warehouse", str(p.id),
                        f"治具归还: {p.name} x{r.qty} 归还人:{r.borrower}", request)
    return _part_to_dict(p)


def to_repair(db: Session, part_id: int, data: dict, request, username: str) -> dict:
    """治具转维修：将指定借出记录转为维修状态。
    数量算在库里面（available_qty 加回），但 repair_qty 同步增加，不可再借出。
    """
    p = _get_part(db, part_id)
    if p.part_type != JIG:
        raise HTTPException(status_code=400, detail="仅治具支持转维修操作")
    record_id = data.get("borrow_record_id")
    if not record_id:
        raise HTTPException(status_code=400, detail="请选择要转维修的借出记录")
    r = db.get(BorrowRecord, int(record_id))
    if not r or r.part_id != p.id:
        raise HTTPException(status_code=404, detail="借出记录不存在")
    if r.status != "借出":
        raise HTTPException(status_code=400, detail="该记录已归还或已转维修")
    # 转维修：repair_qty 增加（不可借出）
    # 注意：借出时 available_qty 已减去 qty，转维修后可用仍保持已减状态（维修中不可借出）
    p.repair_qty = (p.repair_qty or 0) + r.qty
    r.status = "维修"
    # 更新最近借用人
    next_active = (db.query(BorrowRecord)
                     .filter(BorrowRecord.part_id == p.id,
                             BorrowRecord.status == "借出")
                     .order_by(BorrowRecord.id.desc()).first())
    if next_active:
        p.current_borrower = next_active.borrower
        p.borrow_time = next_active.borrow_time
    else:
        p.current_borrower = None
        p.borrow_time = None
    _add_tx(db, p, "维修", r.qty, operator=r.borrower or "",
            department_manager=r.department_manager or "", line=r.line or "",
            remark=data.get("remark") or "借出转维修")
    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "REPAIR", "warehouse", str(p.id),
                        f"治具转维修: {p.name} x{r.qty} 借用人:{r.borrower}", request)
    return _part_to_dict(p)


def finish_repair(db: Session, part_id: int, data: dict, request, username: str) -> dict:
    """治具维修完成：将 repair_qty 减回，恢复正常可借出。"""
    p = _get_part(db, part_id)
    if p.part_type != JIG:
        raise HTTPException(status_code=400, detail="仅治具支持维修完成操作")
    qty = int(data.get("qty") or 0)
    if qty <= 0:
        qty = p.repair_qty or 0
    if qty <= 0:
        raise HTTPException(status_code=400, detail="该治具当前无维修中数量")
    qty = min(qty, p.repair_qty or 0)
    p.repair_qty = (p.repair_qty or 0) - qty
    # 维修完成：可用加回，但不超过总数（防止双重计算）
    p.available_qty = min(p.total_qty, p.available_qty + qty)
    # 维修完成：把对应的 BorrowRecord 标记为已归还
    repair_records = (db.query(BorrowRecord)
                        .filter(BorrowRecord.part_id == p.id,
                                BorrowRecord.status == "维修")
                        .order_by(BorrowRecord.id.asc()).all())
    remain = qty
    for r in repair_records:
        if remain <= 0:
            break
        if r.qty <= remain:
            remain -= r.qty
            r.status = "已归还"
        else:
            # 部分维修完成：拆分记录（简单处理：标记已归还，减少数量）
            r.qty -= remain
            remain = 0
    _add_tx(db, p, "维修", qty, operator="",
            remark=data.get("remark") or "维修完成")
    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "REPAIR_DONE", "warehouse", str(p.id),
                        f"治具维修完成: {p.name} x{qty}", request)
    return _part_to_dict(p)


def report_loss(db: Session, part_id: int, data: dict, request, username: str) -> dict:
    """治具报失：借出后丢失，负责人确认。
    库存总数不变，可用减少（丢失数量）。
    """
    p = _get_part(db, part_id)
    if p.part_type != JIG:
        raise HTTPException(status_code=400, detail="仅治具支持报失操作")
    record_id = data.get("borrow_record_id")
    if not record_id:
        raise HTTPException(status_code=400, detail="请选择要报失的借出记录")
    r = db.get(BorrowRecord, int(record_id))
    if not r or r.part_id != p.id:
        raise HTTPException(status_code=404, detail="借出记录不存在")
    if r.status != "借出":
        raise HTTPException(status_code=400, detail="该记录已归还或已转维修")
    # 报失：总数不变，可用减少（因借出时已减，这里不再调整 available_qty）
    # 但总数也不变，故 total_qty 保持不变
    r.status = "丢失"
    # 更新最近借用人
    next_active = (db.query(BorrowRecord)
                     .filter(BorrowRecord.part_id == p.id,
                             BorrowRecord.status == "借出")
                     .order_by(BorrowRecord.id.desc()).first())
    if next_active:
        p.current_borrower = next_active.borrower
        p.borrow_time = next_active.borrow_time
    else:
        p.current_borrower = None
        p.borrow_time = None
    _add_tx(db, p, "报失", r.qty, operator=r.borrower or "",
            department_manager=r.department_manager or "", line=r.line or "",
            remark=data.get("remark") or "借出后丢失")
    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "LOSS", "warehouse", str(p.id),
                        f"治具报失: {p.name} x{r.qty} 借用人:{r.borrower}", request)
    return _part_to_dict(p)


def report_damaged(db: Session, part_id: int, data: dict, request, username: str) -> dict:
    """治具损坏：借出后损坏。
    库存总数不变，可用减少（损坏数量）。
    """
    p = _get_part(db, part_id)
    if p.part_type != JIG:
        raise HTTPException(status_code=400, detail="仅治具支持报损操作")
    record_id = data.get("borrow_record_id")
    if not record_id:
        raise HTTPException(status_code=400, detail="请选择要报损的借出记录")
    r = db.get(BorrowRecord, int(record_id))
    if not r or r.part_id != p.id:
        raise HTTPException(status_code=404, detail="借出记录不存在")
    if r.status != "借出":
        raise HTTPException(status_code=400, detail="该记录已归还或已转维修")
    # 损坏：总数不变，可用减少（因借出时已减，这里不再调整 available_qty）
    r.status = "损坏"
    # 更新最近借用人
    next_active = (db.query(BorrowRecord)
                     .filter(BorrowRecord.part_id == p.id,
                             BorrowRecord.status == "借出")
                     .order_by(BorrowRecord.id.desc()).first())
    if next_active:
        p.current_borrower = next_active.borrower
        p.borrow_time = next_active.borrow_time
    else:
        p.current_borrower = None
        p.borrow_time = None
    _add_tx(db, p, "报损", r.qty, operator=r.borrower or "",
            department_manager=r.department_manager or "", line=r.line or "",
            remark=data.get("remark") or "借出后损坏")
    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "DAMAGED", "warehouse", str(p.id),
                        f"治具报损: {p.name} x{r.qty} 借用人:{r.borrower}", request)
    return _part_to_dict(p)


def update_tx_remark(db: Session, tx_id: int, remark: str, request, username: str) -> Optional[dict]:
    """编辑出入库记录的备注。"""
    t = db.get(PartTransaction, tx_id)
    if not t:
        return None
    t.remark = (remark or "")[:255]
    db.commit()
    db.refresh(t)
    write_operation_log(db, username, "UPDATE", "warehouse_tx", str(t.id),
                        f"编辑备注: {t.part_name} {t.tx_type}", request)
    return _tx_to_dict(t)


def consume(db: Session, part_id: int, data: dict, request, username: str) -> dict:
    p = _get_part(db, part_id)
    if p.part_type != CONSUMABLE:
        raise HTTPException(status_code=400, detail="仅耗材支持领用操作")
    qty = int(data.get("qty") or 1)
    if qty <= 0:
        raise HTTPException(status_code=400, detail="领用数量必须大于 0")
    if qty > p.total_qty:
        raise HTTPException(status_code=400, detail=f"库存不足（当前库存 {p.total_qty}）")
    operator = (data.get("operator") or data.get("consumer") or "").strip()
    line = (data.get("line") or "").strip()
    dept_mgr = (data.get("department_manager") or "").strip()
    if not operator or not line:
        raise HTTPException(status_code=400, detail="领用人和线体为必填项")
    p.total_qty -= qty
    _add_tx(db, p, "领用", qty, operator=operator, department_manager=dept_mgr,
            line=line, remark=data.get("remark") or "")
    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "CONSUME", "warehouse", str(p.id),
                        f"耗材领用: {p.name} x{qty} 领用人:{operator}", request)
    return _part_to_dict(p)


def _normalize_type(val) -> str:
    """Excel 类型列归一化：含「治」→治具；含「耗/材」→耗材；其余默认耗材。"""
    s = str(val or "").strip()
    if "治" in s:
        return JIG
    if "耗" in s or "材" in s:
        return CONSUMABLE
    return CONSUMABLE


def batch_import(db: Session, rows: list, request, username: str) -> dict:
    """批量导入物品。rows 为 openpyxl 全部行（第 1 行为表头）。

    行级隔离：每行复用 create_part（内部独立提交 + 操作日志），
    单行失败回滚该行并收集错误，不影响其他行。
    """
    if not rows:
        raise HTTPException(status_code=400, detail="文件为空，未读取到任何数据")

    header = [str(c).strip() if c is not None else "" for c in rows[0]]
    col_map: Dict[str, int] = {}
    header_aliases = {
        "name":      ("物品名称", "名称", "name"),
        "model":     ("型号", "型号/编号", "编号", "model"),
        "part_type": ("类型", "part_type"),
        "total_qty": ("数量", "库存", "总数", "初始库存", "total_qty"),
        "location":  ("货位", "货位编码", "location"),
        "unit":      ("单位", "unit"),
        "warn_qty":  ("预警值", "预警", "warn_qty"),
    }
    for key, aliases in header_aliases.items():
        for idx, col in enumerate(header):
            if col in aliases:
                col_map[key] = idx
                break
    if "name" not in col_map:
        raise HTTPException(status_code=400, detail="未找到「物品名称」列，请检查表头（需包含：物品名称、型号、类型、数量、货位、单位、预警值）")

    success, failed = 0, 0
    errors: List[str] = []

    for row_idx, row in enumerate(rows[1:], start=2):
        # 跳过完全空行
        if not row or all(c is None or str(c).strip() == "" for c in row):
            continue
        try:
            data: Dict[str, Any] = {}
            for key, ci in col_map.items():
                if ci < len(row):
                    val = row[ci]
                    if val is not None and str(val).strip():
                        data[key] = val
            if not str(data.get("name") or "").strip():
                errors.append(f"第 {row_idx} 行：物品名称不能为空")
                failed += 1
                continue
            data["part_type"] = _normalize_type(data.get("part_type"))
            create_part(db, data, request, username)   # 内部独立提交
            success += 1
        except HTTPException as e:
            db.rollback()
            errors.append(f"第 {row_idx} 行：{e.detail}")
            failed += 1
        except Exception as e:
            db.rollback()
            errors.append(f"第 {row_idx} 行：{e}")
            failed += 1

    write_operation_log(db, username, "IMPORT", "warehouse", None,
                        f"批量导入物品: 成功{success} 失败{failed}", request)
    return {"success": success, "failed": failed, "errors": errors[:50]}


def restock(db: Session, part_id: int, data: dict, request, username: str) -> dict:
    p = _get_part(db, part_id)
    if p.part_type != CONSUMABLE:
        raise HTTPException(status_code=400, detail="仅耗材支持补货操作")
    qty = int(data.get("qty") or 0)
    if qty <= 0:
        raise HTTPException(status_code=400, detail="补货数量必须大于 0")
    p.total_qty += qty
    _add_tx(db, p, "补货", qty, remark=data.get("remark") or "")
    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "RESTOCK", "warehouse", str(p.id),
                        f"耗材补货: {p.name} x{qty}", request)
    return _part_to_dict(p)
