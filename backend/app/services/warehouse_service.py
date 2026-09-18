"""库房管理服务：治具借还 + 耗材领用/补货，含统计与操作流水。

核心改动：
- 借出创建 BorrowRecord，归还按记录归还（解决多人借出只能还最后一人的 bug）
- 维修状态用 repair_qty（计入库存但不可借出），替代旧 in_repar 布尔
- 出入库记录备注可编辑
"""
from typing import Optional, Tuple, List, Dict, Any

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, text, asc, desc

from app.core.timeutil import beijing_now
from app.core.crud import write_operation_log
from app.models import WarehousePart, BorrowRecord, PartTransaction
from app.models.users import User, UserPermission

JIG = "治具"
CONSUMABLE = "耗材"


# ---------------- 序列化 ----------------
def _get_troubled_status_map(db: Session, part_ids: List[int]) -> Dict[int, Optional[str]]:
    """批量查询物品的异常状态（报失 > 报损 > 维修）。"""
    if not part_ids:
        return {}
    result: Dict[int, str] = {}
    # 治具：BorrowRecord 状态
    brs = db.query(BorrowRecord).filter(
        BorrowRecord.part_id.in_(part_ids),
        BorrowRecord.status.in_(["丢失", "损坏"])
    ).all()
    for r in brs:
        if r.part_id not in result:
            result[r.part_id] = "报失" if r.status == "丢失" else "报损"
        elif r.status == "丢失":
            result[r.part_id] = "报失"
    # 耗材：PartTransaction 中未归还的异常记录
    txs = db.query(PartTransaction).filter(
        PartTransaction.part_id.in_(part_ids),
        PartTransaction.tx_type.in_(["丢失", "损坏", "维修"]),
        PartTransaction.return_time.is_(None)
    ).all()
    for t in txs:
        m = {"丢失": "报失", "损坏": "报损", "维修": "维修"}
        st = m[t.tx_type]
        if t.part_id not in result:
            result[t.part_id] = st
        elif st == "报失" or (st == "报损" and result[t.part_id] != "报失"):
            result[t.part_id] = st
    return result


def _part_to_dict(p: WarehousePart, troubled_status: Optional[str] = None) -> Dict[str, Any]:
    if p.part_type == JIG:
        if troubled_status:
            status = troubled_status
        elif p.repair_qty and p.repair_qty > 0:
            status = "维修"
        elif p.available_qty < p.total_qty:
            status = "借出"
        else:
            status = "在库"
        qty_text = f"{p.available_qty}/{p.total_qty}"
        stock_qty = p.total_qty
    else:
        stock_qty = p.total_qty
        if troubled_status:
            status = troubled_status
        elif stock_qty <= 0:
            status = "缺货"
        elif p.warn_qty and stock_qty <= p.warn_qty:
            status = "预警"
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


def _tx_to_dict(t: PartTransaction, part_info: dict = None) -> Dict[str, Any]:
    """part_info: {part_id: {model, part_type}} — 由调用方传入以补充型号/类型。"""
    d = {
        "id": t.id,
        "part_id": t.part_id,
        "part_name": t.part_name,
        "tx_type": t.tx_type,
        # 有 return_time 即视为已归还，无论 tx_type 是借出/损坏/丢失/维修
        "display_status": "已归还" if t.return_time else None,
        "qty": t.qty,
        "operator": t.operator or "",
        "department_manager": t.department_manager or "",
        "line": t.line or "",
        "borrow_time": t.borrow_time.strftime("%Y-%m-%d %H:%M:%S") if t.borrow_time else None,
        "return_time": t.return_time.strftime("%Y-%m-%d %H:%M:%S") if t.return_time else None,
        "remark": t.remark or "",
        "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else None,
    }
    # 补充物品型号与类型（用于前端展示）
    if part_info and t.part_id in part_info:
        d["model"] = part_info[t.part_id].get("model") or ""
        d["part_type"] = part_info[t.part_id].get("part_type") or ""
    return d


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
               stock_status: Optional[str] = None,
               sort_by: Optional[str] = None,
               sort_order: Optional[str] = None,
               status: Optional[str] = None) -> Tuple[List[dict], int]:
    q = db.query(WarehousePart)
    if part_type in (JIG, CONSUMABLE):
        q = q.filter(WarehousePart.part_type == part_type)
    if low_stock:
        q = q.filter(
            WarehousePart.part_type == CONSUMABLE,
            WarehousePart.warn_qty > 0,
            WarehousePart.total_qty <= WarehousePart.warn_qty,
        )
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

    # 从原始匹配数开始
    total_raw = q.count()

    # 状态筛选：状态为计算字段，需在 Python 层处理
    if status:
        # 获取所有匹配 ID，计算状态后再按状态过滤、分页
        all_ids = [r[0] for r in q.with_entities(WarehousePart.id).all()]
        troubled_map = _get_troubled_status_map(db, all_ids) if all_ids else {}
        # 查出全部记录
        all_parts = q.order_by(WarehousePart.part_type.asc(), WarehousePart.id.desc()).all()
        filtered_parts = []
        for p in all_parts:
            ts = troubled_map.get(p.id)
            computed = _part_to_dict(p, ts)["status"]
            if computed == status:
                filtered_parts.append(p)
        total = len(filtered_parts)
        # 内存分页
        start = (page - 1) * page_size
        items = filtered_parts[start:start + page_size]
        troubled_map = _get_troubled_status_map(db, [p.id for p in items]) if items else {}
        return [_part_to_dict(p, troubled_map.get(p.id)) for p in items], total

    # 排序（无状态筛选时走原逻辑）
    sort_map = {
        'total_qty': WarehousePart.total_qty,
        'available_qty': WarehousePart.available_qty,
        'stock_qty': WarehousePart.total_qty,
        'warn_qty': WarehousePart.warn_qty,
    }
    col = sort_map.get(sort_by)
    if col and sort_order in ('asc', 'desc'):
        order = asc(col) if sort_order == 'asc' else desc(col)
        items = (q.order_by(order, WarehousePart.id.desc())
                  .offset((page - 1) * page_size).limit(page_size).all())
    else:
        items = (q.order_by(WarehousePart.part_type.asc(), WarehousePart.id.desc())
                  .offset((page - 1) * page_size).limit(page_size).all())
    troubled_map = _get_troubled_status_map(db, [p.id for p in items]) if items else {}
    return [_part_to_dict(p, troubled_map.get(p.id)) for p in items], total_raw


def get_stats(db: Session, part_type: Optional[str] = None) -> Dict[str, Any]:
    """统计物品状态 + 看板指标（资产完好率、外借回收率、库存达标率、待办总数）。"""
    q = db.query(WarehousePart)
    if part_type:
        q = q.filter(WarehousePart.part_type == part_type)
    parts = q.all()

    total = len(parts)
    in_stock = 0
    borrowed_out = 0
    low_items: List[dict] = []
    repair_items: List[dict] = []

    # 批量预加载异常状态
    troubled_map = _get_troubled_status_map(db, [p.id for p in parts]) if parts else {}

    for p in parts:
        d = _part_to_dict(p, troubled_map.get(p.id))
        status = d["status"]
        if p.part_type == JIG:
            if status in ("借出", "维修", "报损", "报失"):
                borrowed_out += 1
            else:
                in_stock += 1
            if p.repair_qty and p.repair_qty > 0:
                repair_items.append(d)
        else:
            if status in ("缺货", "报损", "报失", "维修"):
                borrowed_out += 1
            else:
                in_stock += 1
            if p.warn_qty and p.total_qty <= p.warn_qty:
                low_items.append(d)

    # 丢失/损坏：从BorrowRecord获取
    lost_rows = db.query(BorrowRecord).filter(
        BorrowRecord.status == "丢失"
    ).all()
    damaged_rows = db.query(BorrowRecord).filter(
        BorrowRecord.status == "损坏"
    ).all()

    # 组装丢失/损坏的物品信息（使用带异常状态的 dict）
    lost_items = []
    damaged_items = []
    part_map = {p.id: _part_to_dict(p, troubled_map.get(p.id)) for p in parts}
    for br in lost_rows:
        info = part_map.get(br.part_id)
        if info:
            lost_items.append({**info,
                "borrower": br.borrower,
                "borrow_time": str(br.borrow_time)[:10] if br.borrow_time else "",
                "borrow_record_id": br.id,
            })
    for br in damaged_rows:
        info = part_map.get(br.part_id)
        if info:
            damaged_items.append({**info,
                "borrower": br.borrower,
                "borrow_time": str(br.borrow_time)[:10] if br.borrow_time else "",
                "borrow_record_id": br.id,
            })

    # 外借回收率 = 已归还记录数 / 总借出记录数（仅统计治具）
    jig_ids = [p.id for p in parts if p.part_type == JIG]
    if jig_ids:
        total_borrowed = db.query(BorrowRecord).filter(BorrowRecord.part_id.in_(jig_ids)).count()
        total_returned = db.query(BorrowRecord).filter(
            BorrowRecord.part_id.in_(jig_ids),
            BorrowRecord.status == "已归还"
        ).count()
        return_rate = round(total_returned / total_borrowed * 100, 1) if total_borrowed > 0 else 100.0
    else:
        return_rate = 100.0

    repair_count = len(repair_items)
    lost_count = len(lost_items)
    damaged_count = len(damaged_items)

    # 资产完好率 = (total - 丢损物品数) / total
    lost_part_ids = set(br.part_id for br in lost_rows)
    damaged_part_ids = set(br.part_id for br in damaged_rows)
    bad_parts = lost_part_ids | damaged_part_ids
    good_rate = round((total - len(bad_parts)) / total * 100, 1) if total > 0 else 100.0
    stock_rate = round((total - len(low_items)) / total * 100, 1) if total > 0 else 100.0
    pending_total = len(low_items) + repair_count + lost_count + damaged_count

    return {
        "total": total,
        "in_stock": in_stock,
        "borrowed_out": borrowed_out,
        "repair_count": repair_count,
        "lost_count": lost_count,
        "damaged_count": damaged_count,
        "low_stock": len(low_items),
        "pending_total": pending_total,
        "good_rate": good_rate,
        "return_rate": return_rate,
        "stock_rate": stock_rate,
        "low_stock_items": low_items,
        "repair_items": repair_items,
        "lost_items": lost_items,
        "damaged_items": damaged_items,
    }


def get_detail(db: Session, part_id: int) -> Optional[dict]:
    p = db.get(WarehousePart, part_id)
    if not p:
        return None
    txs = (db.query(PartTransaction)
             .filter(PartTransaction.part_id == part_id)
             .order_by(PartTransaction.id.desc()).limit(5).all())
    # 治具：附带当前未归还的借出记录
    troubled_map = _get_troubled_status_map(db, [p.id])
    borrows = []
    if p.part_type == JIG:
        active = (db.query(BorrowRecord)
                    .filter(BorrowRecord.part_id == part_id,
                            BorrowRecord.status == "借出")
                    .order_by(BorrowRecord.id.desc()).all())
        borrows = [_borrow_to_dict(r) for r in active]
    return {
        "part": _part_to_dict(p, troubled_map.get(p.id)),
        "transactions": [_tx_to_dict(t) for t in txs],
        "borrow_records": borrows,
    }


def get_operators(db: Session, limit: int = 50) -> List[str]:
    """返回历史借/领用人列表（用于前端 el-select 记忆）。"""
    rows = db.query(PartTransaction.operator).filter(
        PartTransaction.operator.isnot(None),
        PartTransaction.operator != ""
    ).distinct().order_by(PartTransaction.operator).limit(limit).all()
    return [r[0] for r in rows]


def get_department_managers(db: Session, limit: int = 50) -> List[str]:
    """返回历史部门负责人列表（用于前端 el-select 记忆）。"""
    rows = db.query(PartTransaction.department_manager).filter(
        PartTransaction.department_manager.isnot(None),
        PartTransaction.department_manager != ""
    ).distinct().order_by(PartTransaction.department_manager).limit(limit).all()
    return [r[0] for r in rows]


def list_transactions(db: Session, page: int = 1, page_size: int = 50,
                      tx_type: Optional[str] = None,
                      is_returned: bool = False,
                      keyword: Optional[str] = None,
                      borrow_date: Optional[str] = None,
                      return_date: Optional[str] = None,
                      date_from: Optional[str] = None,
                      date_to: Optional[str] = None,
                      sort_by: Optional[str] = None,
                      sort_order: Optional[str] = None) -> Tuple[List[dict], int]:
    """查询所有物品的借出/领用/归还/补货流水（按时间倒序）。"""
    from datetime import datetime
    q = db.query(PartTransaction)
    if is_returned:
        q = q.filter(or_(
            PartTransaction.tx_type == '归还',
            and_(PartTransaction.tx_type.in_(['借出', '领用']), PartTransaction.return_time.isnot(None))
        ))
    elif tx_type in ("借出", "领用"):
        # 只显示尚未归还的（return_time IS NULL），已归还的记录不混入
        q = q.filter(PartTransaction.tx_type == tx_type, PartTransaction.return_time.is_(None))
    elif tx_type in ("归还", "补货", "减少", "维修", "丢失", "损坏"):
        q = q.filter(PartTransaction.tx_type == tx_type)
    if keyword:
        kw = f"%{keyword.strip()}%"
        q = q.filter(or_(
            PartTransaction.part_name.like(kw),
            PartTransaction.operator.like(kw),
            PartTransaction.remark.like(kw),
            PartTransaction.department_manager.like(kw),
            PartTransaction.line.like(kw),
        ))
    if borrow_date:
        try:
            d = datetime.strptime(borrow_date.strip(), "%Y-%m-%d")
            d_end = d.replace(hour=23, minute=59, second=59)
            q = q.filter(PartTransaction.borrow_time >= d,
                         PartTransaction.borrow_time <= d_end)
        except ValueError:
            pass
    if return_date:
        try:
            d = datetime.strptime(return_date.strip(), "%Y-%m-%d")
            d_end = d.replace(hour=23, minute=59, second=59)
            q = q.filter(PartTransaction.return_time >= d,
                         PartTransaction.return_time <= d_end)
        except ValueError:
            pass
    if date_from:
        try:
            d = datetime.strptime(date_from.strip(), "%Y-%m-%d")
            q = q.filter(PartTransaction.created_at >= d)
        except ValueError:
            pass
    if date_to:
        try:
            d = datetime.strptime(date_to.strip(), "%Y-%m-%d")
            d = d.replace(hour=23, minute=59, second=59)
            q = q.filter(PartTransaction.created_at <= d)
        except ValueError:
            pass
    total = q.count()
    # 排序
    if sort_by == 'qty' and sort_order in ('asc', 'desc'):
        col = PartTransaction.qty
        order = asc(col) if sort_order == 'asc' else desc(col)
        items = (q.order_by(order, PartTransaction.id.desc())
                  .offset((page - 1) * page_size).limit(page_size).all())
    else:
        items = (q.order_by(PartTransaction.id.desc())
                  .offset((page - 1) * page_size).limit(page_size).all())
    # 批量查询 part_type / model 以补充给前端
    part_ids = {t.part_id for t in items}
    part_info = {}
    if part_ids:
        parts = db.query(WarehousePart).filter(WarehousePart.id.in_(part_ids)).all()
        part_info = {p.id: {"model": p.model or "", "part_type": p.part_type or ""} for p in parts}
    return [_tx_to_dict(t, part_info) for t in items], total


def list_borrow_records(db: Session, part_id: int, active_only: bool = True) -> List[dict]:
    """查询治具的借出记录（默认只看未归还的）。"""
    p = _get_part(db, part_id)
    if p.part_type != JIG:
        raise HTTPException(status_code=400, detail="仅治具有借出记录")
    q = db.query(BorrowRecord).filter(BorrowRecord.part_id == part_id)
    if active_only:
        q = q.filter(BorrowRecord.status.in_(["借出", "维修", "丢失", "损坏"]))
    records = q.order_by(BorrowRecord.id.desc()).all()
    return [_borrow_to_dict(r) for r in records]


def list_consume_records(db: Session, part_id: int, active_only: bool = True) -> List[dict]:
    """查询耗材的领用/维修/丢失/损坏记录（默认只看未归还的：return_time IS NULL）。"""
    p = _get_part(db, part_id)
    if p.part_type != CONSUMABLE:
        raise HTTPException(status_code=400, detail="仅耗材有领用记录")
    q = db.query(PartTransaction).filter(
        PartTransaction.part_id == part_id,
        PartTransaction.tx_type.in_(["领用", "维修", "丢失", "损坏"]),
    )
    if active_only:
        q = q.filter(PartTransaction.return_time.is_(None))
    records = q.order_by(PartTransaction.id.desc()).all()
    return [_tx_to_dict(r) for r in records]


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


def _user_can_edit_qty(db: Session, username: str) -> bool:
    """检查用户是否有权编辑治具/耗材的库存数量（admin 或拥有 warehouse 写权限）。"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if user.role == "admin":
        return True
    perm = db.query(UserPermission).filter(
        UserPermission.user_id == user.id,
        UserPermission.module_key == "warehouse",
    ).first()
    return perm is not None and perm.can_write


def update_part(db: Session, part_id: int, data: dict, request, username: str, role: str = "viewer") -> Optional[dict]:
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
    # 有权限的用户（admin 或仓库写权限）可修改治具/耗材数量，否则忽略 total_qty 字段
    if "total_qty" in data and _user_can_edit_qty(db, username):
        new_total = max(0, int(data.get("total_qty") or 0))
        if p.part_type == JIG:
            delta = new_total - p.total_qty
            old_total = p.total_qty
            p.available_qty = max(0, min(new_total, p.available_qty + delta))
            p.total_qty = new_total
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
    display_name = f"{p.model} - {p.name}" if p.model else p.name
    db.add(PartTransaction(
        part_id=p.id, part_name=display_name, tx_type=tx_type, qty=qty,
        operator=operator, department_manager=department_manager,
        line=line, remark=remark or "",
        borrow_time=borrow_time, return_time=return_time,
    ))


def _borrow_to_repair_qty(p: WarehousePart) -> int:
    """治具维修中数量 = repair_qty。"""
    return p.repair_qty or 0


def check_unreturned_by_borrower(db: Session, borrower: str) -> List[dict]:
    """查询某个借用人当前未归还的所有治具借出记录（跨物品）。"""
    records = db.query(BorrowRecord).filter(
        BorrowRecord.borrower == borrower,
        BorrowRecord.status == "借出"
    ).all()
    if not records:
        return []
    part_ids = list(set(r.part_id for r in records))
    parts = {p.id: p for p in db.query(WarehousePart).filter(WarehousePart.id.in_(part_ids)).all()}
    result = []
    for r in records:
        p = parts.get(r.part_id)
        result.append({
            "part_id": r.part_id,
            "part_name": p.name if p else "未知",
            "part_model": p.model if p else "",
            "borrow_time": r.borrow_time.strftime("%Y-%m-%d %H:%M:%S") if r.borrow_time else None,
            "qty": r.qty,
            "borrow_record_id": r.id,
        })
    return result


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
    # 创建借出记录（borrow_time 与 PartTransaction 保持一致，便于归还时匹配）
    db.add(BorrowRecord(
        part_id=p.id, borrower=borrower, department_manager=dept_mgr,
        line=line, qty=qty, borrow_time=p.borrow_time,
        remark=data.get("remark") or "",
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
    """归还：治具按 borrow_record_id 归还；耗材按 consume_tx_id 归还（补 return_time）。"""
    p = _get_part(db, part_id)
    return_now = beijing_now()

    if p.part_type == JIG:
        # ---- 治具归还 ----
        record_id = data.get("borrow_record_id")
        if not record_id:
            raise HTTPException(status_code=400, detail="请选择要归还的借出记录")
        r = db.get(BorrowRecord, int(record_id))
        if not r or r.part_id != p.id:
            raise HTTPException(status_code=404, detail="借出记录不存在")
        if r.status != "借出":
            raise HTTPException(status_code=400, detail="该记录已归还或已转维修")
        p.available_qty = min(p.total_qty, p.available_qty + r.qty)
        r.status = "已归还"
        # 找到对应的借出流水，补上归还时间
        borrow_tx = db.query(PartTransaction).filter(
            PartTransaction.part_id == p.id,
            PartTransaction.tx_type == "借出",
            PartTransaction.operator == r.borrower,
            func.DATEDIFF(text("SECOND"), PartTransaction.borrow_time, r.borrow_time) == 0,
            PartTransaction.return_time.is_(None)
        ).order_by(PartTransaction.id.desc()).first()
        if borrow_tx:
            borrow_tx.return_time = return_now
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
        db.commit()
        db.refresh(p)
        write_operation_log(db, username, "RETURN", "warehouse", str(p.id),
                            f"治具归还: {p.name} x{r.qty} 归还人:{r.borrower}", request)
        return _part_to_dict(p)

    elif p.part_type == CONSUMABLE:
        # ---- 耗材归还 ----
        consume_tx_id = data.get("consume_tx_id")
        if not consume_tx_id:
            raise HTTPException(status_code=400, detail="请选择要归还的领用记录")
        tx = db.get(PartTransaction, int(consume_tx_id))
        if not tx or tx.part_id != p.id:
            raise HTTPException(status_code=404, detail="领用记录不存在")
        if tx.tx_type != "领用":
            raise HTTPException(status_code=400, detail="该记录不是领用记录")
        if tx.return_time:
            raise HTTPException(status_code=400, detail="该记录已归还")
        tx.return_time = return_now
        p.total_qty += tx.qty
        db.commit()
        db.refresh(p)
        write_operation_log(db, username, "RETURN", "warehouse", str(p.id),
                            f"耗材归还: {p.name} x{tx.qty} 归还人:{tx.operator}", request)
        return _part_to_dict(p)

    else:
        raise HTTPException(status_code=400, detail="不支持的操作")


def _change_tx_type(db: Session, p, from_type: str, operator, borrow_time, new_type: str, remark: str = ""):
    """根据借出人+borrow_time 匹配 PartTransaction 并修改类型（治具用）。"""
    tx = db.query(PartTransaction).filter(
        PartTransaction.part_id == p.id,
        PartTransaction.tx_type == from_type,
        PartTransaction.operator == operator,
        func.DATEDIFF(text("SECOND"), PartTransaction.borrow_time, borrow_time) == 0,
        PartTransaction.return_time.is_(None)
    ).order_by(PartTransaction.id.desc()).first()
    if tx:
        tx.tx_type = new_type
        tx.remark = remark or tx.remark
        tx.part_name = f"{p.model} - {p.name}" if p.model else p.name


def to_repair(db: Session, part_id: int, data: dict, request, username: str) -> dict:
    """治具/耗材转维修。
    
    原借出/领用流水直接改为"维修"类型，不新增单独记录。
    """
    p = _get_part(db, part_id)
    record_id = data.get("borrow_record_id")
    if not record_id:
        raise HTTPException(status_code=400, detail="请选择要转维修的记录")
    
    is_jig = p.part_type == JIG
    
    if is_jig:
        r = db.get(BorrowRecord, int(record_id))
        if not r or r.part_id != p.id:
            raise HTTPException(status_code=404, detail="借出记录不存在")
        if r.status != "借出":
            raise HTTPException(status_code=400, detail="该记录已归还或已转维修")
        r.status = "维修"
        remark = data.get("remark") or "设备维修中"
        _change_tx_type(db, p, "借出", r.borrower, r.borrow_time, "维修", remark)
        p.repair_qty = (p.repair_qty or 0) + r.qty
        next_active = (db.query(BorrowRecord)
                         .filter(BorrowRecord.part_id == p.id, BorrowRecord.status == "借出")
                         .order_by(BorrowRecord.id.desc()).first())
        if next_active:
            p.current_borrower = next_active.borrower
            p.borrow_time = next_active.borrow_time
        else:
            p.current_borrower = r.borrower
            p.borrow_time = beijing_now()
    else:
        # 耗材：PartTransaction tx_type="领用" → "维修"
        tx = db.get(PartTransaction, int(record_id))
        if not tx or tx.part_id != p.id:
            raise HTTPException(status_code=404, detail="领用记录不存在")
        if tx.tx_type != "领用":
            raise HTTPException(status_code=400, detail="该记录不是领用状态，无法转维修")
        tx.tx_type = "维修"
        tx.remark = data.get("remark") or "耗材转维修中"
    
    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "REPAIR", "warehouse", str(p.id),
                        f"{p.part_type}转维修: {p.name} 记录ID:{record_id}", request)
    return _part_to_dict(p)


def finish_repair(db: Session, part_id: int, data: dict, request, username: str) -> dict:
    """治具/耗材维修完成。"""
    p = _get_part(db, part_id)
    is_jig = p.part_type == JIG
    now = beijing_now()

    if is_jig:
        qty = int(data.get("qty") or 0)
        if qty <= 0:
            qty = p.repair_qty or 0
        if qty <= 0:
            raise HTTPException(status_code=400, detail="该治具当前无维修中数量")
        qty = min(qty, p.repair_qty or 0)

        # ① 找到当前"维修"记录，类型改为"归还"，补归还时间，备注更新
        repair_tx = db.query(PartTransaction).filter(
            PartTransaction.part_id == p.id,
            PartTransaction.tx_type == "维修",
            PartTransaction.return_time.is_(None)
        ).order_by(PartTransaction.id.desc()).first()
        if repair_tx:
            repair_tx.tx_type = "归还"
            repair_tx.return_time = now
            repair_tx.remark = "设备维修完成"
            repair_tx.part_name = f"{p.model} - {p.name}" if p.model else p.name

        # ② repair_qty 减回，available_qty 加回
        p.repair_qty = (p.repair_qty or 0) - qty
        p.available_qty = min(p.total_qty, p.available_qty + qty)

        # ③ 对应的 BorrowRecord 标记为已归还
        repair_records = (db.query(BorrowRecord)
                            .filter(BorrowRecord.part_id == p.id, BorrowRecord.status == "维修")
                            .order_by(BorrowRecord.id.asc()).all())
        remain = qty
        for r in repair_records:
            if remain <= 0:
                break
            if r.qty <= remain:
                remain -= r.qty
                r.status = "已归还"
            else:
                r.qty -= remain
                remain = 0

        # ④ 更新最近借用人
        next_active = (db.query(BorrowRecord)
                         .filter(BorrowRecord.part_id == p.id, BorrowRecord.status == "借出")
                         .order_by(BorrowRecord.id.desc()).first())
        if next_active:
            p.current_borrower = next_active.borrower
            p.borrow_time = next_active.borrow_time
        else:
            p.current_borrower = None
            p.borrow_time = None
    else:
        # 耗材：PartTransaction tx_type="维修" → 改为"归还"，补 return_time
        record_id = data.get("borrow_record_id")
        if not record_id:
            raise HTTPException(status_code=400, detail="请选择要维修完成的记录")
        tx = db.get(PartTransaction, int(record_id))
        if not tx or tx.part_id != p.id:
            raise HTTPException(status_code=404, detail="领用记录不存在")
        if tx.tx_type != "维修":
            raise HTTPException(status_code=400, detail="该记录不是维修状态")
        if tx.return_time:
            raise HTTPException(status_code=400, detail="该记录已处理")
        tx.tx_type = "归还"
        tx.return_time = now
        tx.remark = "耗材维修完成"

    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "REPAIR_DONE", "warehouse", str(p.id),
                        f"{p.part_type}维修完成: {p.name}", request)
    return _part_to_dict(p)


def report_loss(db: Session, part_id: int, data: dict, request, username: str) -> dict:
    """治具/耗材报失。
    
    原借出/领用流水直接改为"丢失"类型，不新增单独记录。
    """
    p = _get_part(db, part_id)
    record_id = data.get("borrow_record_id")
    if not record_id:
        raise HTTPException(status_code=400, detail="请选择要报失的记录")
    
    is_jig = p.part_type == JIG
    
    if is_jig:
        r = db.get(BorrowRecord, int(record_id))
        if not r or r.part_id != p.id:
            raise HTTPException(status_code=404, detail="借出记录不存在")
        if r.status != "借出":
            raise HTTPException(status_code=400, detail="该记录已归还或已转维修")
        p.total_qty = max(0, (p.total_qty or 0) - r.qty)
        p.available_qty = max(0, min(p.available_qty, p.total_qty))
        r.status = "丢失"
        remark = data.get("remark") or "借出后丢失"
        _change_tx_type(db, p, "借出", r.borrower, r.borrow_time, "丢失", remark)
        next_active = (db.query(BorrowRecord)
                         .filter(BorrowRecord.part_id == p.id, BorrowRecord.status == "借出")
                         .order_by(BorrowRecord.id.desc()).first())
        if next_active:
            p.current_borrower = next_active.borrower
            p.borrow_time = next_active.borrow_time
        else:
            p.current_borrower = None
            p.borrow_time = None
    else:
        # 耗材：PartTransaction tx_type="领用" → "丢失"
        tx = db.get(PartTransaction, int(record_id))
        if not tx or tx.part_id != p.id:
            raise HTTPException(status_code=404, detail="领用记录不存在")
        if tx.tx_type != "领用":
            raise HTTPException(status_code=400, detail="该记录不是领用状态，无法报失")
        tx.tx_type = "丢失"
        tx.remark = data.get("remark") or "耗材报失"

    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "LOSS", "warehouse", str(p.id),
                        f"{p.part_type}报失: {p.name} 记录ID:{record_id}", request)
    return _part_to_dict(p)


def found_back(db: Session, part_id: int, data: dict, request, username: str) -> dict:
    """治具/耗材已找回。"""
    p = _get_part(db, part_id)
    record_id = data.get("borrow_record_id")
    now = beijing_now()
    is_jig = p.part_type == JIG

    if is_jig:
        if not record_id:
            raise HTTPException(status_code=400, detail="请选择要已找回的丢失记录")
        r = db.get(BorrowRecord, int(record_id))
        if not r or r.part_id != p.id:
            raise HTTPException(status_code=404, detail="借出记录不存在")
        if r.status != "丢失":
            raise HTTPException(status_code=400, detail="该记录不是丢失状态，无法执行已找回")
        p.total_qty = (p.total_qty or 0) + r.qty
        p.available_qty = min(p.total_qty, (p.available_qty or 0) + r.qty)
        r.status = "已归还"
        loss_tx = db.query(PartTransaction).filter(
            PartTransaction.part_id == p.id,
            PartTransaction.tx_type == "丢失",
            PartTransaction.return_time.is_(None)
        ).order_by(PartTransaction.id.desc()).first()
        if loss_tx:
            loss_tx.tx_type = "归还"
            loss_tx.return_time = now
            loss_tx.remark = "设备已找回"
            loss_tx.part_name = f"{p.model} - {p.name}" if p.model else p.name
        next_active = (db.query(BorrowRecord)
                         .filter(BorrowRecord.part_id == p.id, BorrowRecord.status == "借出")
                         .order_by(BorrowRecord.id.desc()).first())
        if next_active:
            p.current_borrower = next_active.borrower
            p.borrow_time = next_active.borrow_time
        else:
            p.current_borrower = None
            p.borrow_time = None
    else:
        # 耗材：PartTransaction tx_type="丢失" → 改为"归还"，补 return_time
        if not record_id:
            raise HTTPException(status_code=400, detail="请选择要已找回的记录")
        tx = db.get(PartTransaction, int(record_id))
        if not tx or tx.part_id != p.id:
            raise HTTPException(status_code=404, detail="领用记录不存在")
        if tx.tx_type != "丢失":
            raise HTTPException(status_code=400, detail="该记录不是丢失状态")
        if tx.return_time:
            raise HTTPException(status_code=400, detail="该记录已处理")
        tx.tx_type = "归还"
        tx.return_time = now
        tx.remark = "耗材已找回"

    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "FOUND_BACK", "warehouse", str(p.id),
                        f"{p.part_type}已找回: {p.name}", request)
    return _part_to_dict(p)


def report_damaged(db: Session, part_id: int, data: dict, request, username: str) -> dict:
    """治具/耗材报损。
    
    原借出/领用流水直接改为"损坏"类型，不新增单独记录。
    """
    p = _get_part(db, part_id)
    record_id = data.get("borrow_record_id")
    if not record_id:
        raise HTTPException(status_code=400, detail="请选择要报损的记录")
    
    is_jig = p.part_type == JIG
    
    if is_jig:
        r = db.get(BorrowRecord, int(record_id))
        if not r or r.part_id != p.id:
            raise HTTPException(status_code=404, detail="借出记录不存在")
        if r.status != "借出":
            raise HTTPException(status_code=400, detail="该记录已归还或已转维修")
        r.status = "损坏"
        remark = data.get("remark") or "借出后损坏"
        _change_tx_type(db, p, "借出", r.borrower, r.borrow_time, "损坏", remark)
        next_active = (db.query(BorrowRecord)
                         .filter(BorrowRecord.part_id == p.id, BorrowRecord.status == "借出")
                         .order_by(BorrowRecord.id.desc()).first())
        if next_active:
            p.current_borrower = next_active.borrower
            p.borrow_time = next_active.borrow_time
        else:
            p.current_borrower = None
            p.borrow_time = None
    else:
        # 耗材：PartTransaction tx_type="领用" → "损坏"
        tx = db.get(PartTransaction, int(record_id))
        if not tx or tx.part_id != p.id:
            raise HTTPException(status_code=404, detail="领用记录不存在")
        if tx.tx_type != "领用":
            raise HTTPException(status_code=400, detail="该记录不是领用状态，无法报损")
        tx.tx_type = "损坏"
        tx.remark = data.get("remark") or "耗材报损"

    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "DAMAGED", "warehouse", str(p.id),
                        f"{p.part_type}报损: {p.name} 记录ID:{record_id}", request)
    return _part_to_dict(p)


def repair_damaged(db: Session, part_id: int, data: dict, request, username: str) -> dict:
    """治具/耗材已修复。"""
    p = _get_part(db, part_id)
    record_id = data.get("borrow_record_id")
    now = beijing_now()
    is_jig = p.part_type == JIG

    if is_jig:
        if not record_id:
            raise HTTPException(status_code=400, detail="请选择要已修复的损坏记录")
        r = db.get(BorrowRecord, int(record_id))
        if not r or r.part_id != p.id:
            raise HTTPException(status_code=404, detail="借出记录不存在")
        if r.status != "损坏":
            raise HTTPException(status_code=400, detail="该记录不是损坏状态，无法执行已修复")
        p.available_qty = min(p.total_qty, (p.available_qty or 0) + r.qty)
        r.status = "已归还"
        damaged_tx = db.query(PartTransaction).filter(
            PartTransaction.part_id == p.id,
            PartTransaction.tx_type == "损坏",
            PartTransaction.return_time.is_(None)
        ).order_by(PartTransaction.id.desc()).first()
        if damaged_tx:
            damaged_tx.tx_type = "归还"
            damaged_tx.return_time = now
            damaged_tx.remark = "设备已修复"
            damaged_tx.part_name = f"{p.model} - {p.name}" if p.model else p.name
        next_active = (db.query(BorrowRecord)
                         .filter(BorrowRecord.part_id == p.id, BorrowRecord.status == "借出")
                         .order_by(BorrowRecord.id.desc()).first())
        if next_active:
            p.current_borrower = next_active.borrower
            p.borrow_time = next_active.borrow_time
        else:
            p.current_borrower = None
            p.borrow_time = None
    else:
        # 耗材：PartTransaction tx_type="损坏" → 改为"归还"，补 return_time
        if not record_id:
            raise HTTPException(status_code=400, detail="请选择要已修复的记录")
        tx = db.get(PartTransaction, int(record_id))
        if not tx or tx.part_id != p.id:
            raise HTTPException(status_code=404, detail="领用记录不存在")
        if tx.tx_type != "损坏":
            raise HTTPException(status_code=400, detail="该记录不是损坏状态")
        if tx.return_time:
            raise HTTPException(status_code=400, detail="该记录已处理")
        tx.tx_type = "归还"
        tx.return_time = now
        tx.remark = "耗材已修复"

    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "REPAIR_DAMAGED", "warehouse", str(p.id),
                        f"{p.part_type}已修复: {p.name}", request)
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
            line=line, remark=data.get("remark") or "",
            borrow_time=beijing_now())
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
        "model":     ("型号", "型号/编号", "model"),
        "code":      ("编号", "编号/编码", "编码", "code"),
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
    _add_tx(db, p, "补货", qty, operator=username, remark=data.get("remark") or "")
    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "RESTOCK", "warehouse", str(p.id),
                        f"耗材补货: {p.name} x{qty}", request)
    return _part_to_dict(p)