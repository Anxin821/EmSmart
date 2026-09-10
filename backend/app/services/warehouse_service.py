"""库房管理服务：治具借还 + 耗材领用/补货，含统计与操作流水。"""
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.timeutil import beijing_now
from app.core.crud import write_operation_log
from app.models import WarehousePart, PartTransaction

JIG = "治具"
CONSUMABLE = "耗材"


# ---------------- 序列化 ----------------
def _part_to_dict(p: WarehousePart) -> Dict[str, Any]:
    if p.part_type == JIG:
        if p.in_repair:
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
        "part_type": p.part_type,
        "total_qty": p.total_qty,
        "available_qty": p.available_qty,
        "stock_qty": stock_qty,
        "unit": p.unit or "",
        "location": p.location or "",
        "warn_qty": p.warn_qty or 0,
        "in_repair": bool(p.in_repair),
        "status": status,
        "qty_text": qty_text,
        "current_borrower": p.current_borrower,
        "borrow_time": p.borrow_time.strftime("%Y-%m-%d %H:%M:%S") if p.borrow_time else None,
        "expected_return": p.expected_return.strftime("%Y-%m-%d") if p.expected_return else None,
        "supplier": p.supplier or "",
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
        "line": t.line or "",
        "supplier": t.supplier or "",
        "remark": t.remark or "",
        "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else None,
    }


def _get_part(db: Session, part_id: int) -> WarehousePart:
    p = db.get(WarehousePart, part_id)
    if not p:
        raise HTTPException(status_code=404, detail="物品不存在")
    return p


def _parse_date(s: Optional[str]):
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="日期格式应为 YYYY-MM-DD")


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
    # 注意：SQL Server 仅支持 "col IS NULL"，不支持 "col IS 0/1"，
    # 故布尔列用 == 比较（生成 = 0 / = 1），NULL 单独用 is_(None) 兜底
    if stock_status == "borrowed":
        q = q.filter(or_(
            and_(WarehousePart.part_type == JIG,
                 or_(WarehousePart.in_repair == True,  # noqa: E712
                     WarehousePart.available_qty < WarehousePart.total_qty)),
            and_(WarehousePart.part_type == CONSUMABLE,
                 WarehousePart.total_qty <= 0),
        ))
    elif stock_status == "in_stock":
        q = q.filter(or_(
            and_(WarehousePart.part_type == JIG,
                 or_(WarehousePart.in_repair == False,  # noqa: E712
                     WarehousePart.in_repair.is_(None)),
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


def get_stats(db: Session) -> Dict[str, Any]:
    parts = db.query(WarehousePart).all()
    in_stock = 0
    borrowed_out = 0
    low_items: List[dict] = []
    for p in parts:
        d = _part_to_dict(p)
        if p.part_type == JIG:
            if p.in_repair or d["status"] in ("已借出", "部分借出"):
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
    return {"part": _part_to_dict(p), "transactions": [_tx_to_dict(t) for t in txs]}


def list_transactions(db: Session, page: int = 1, page_size: int = 50,
                      tx_type: Optional[str] = None) -> Tuple[List[dict], int]:
    """查询所有物品的借出/领用/归还/补货流水（按时间倒序）。"""
    q = db.query(PartTransaction)
    if tx_type in ("借出", "归还", "领用", "补货"):
        q = q.filter(PartTransaction.tx_type == tx_type)
    total = q.count()
    items = (q.order_by(PartTransaction.id.desc())
              .offset((page - 1) * page_size).limit(page_size).all())
    return [_tx_to_dict(t) for t in items], total


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
        part_type=part_type,
        total_qty=total,
        available_qty=total if part_type == JIG else 0,
        unit=(data.get("unit") or "").strip(),
        location=(data.get("location") or "").strip(),
        warn_qty=max(0, int(data.get("warn_qty") or 0)) if part_type == CONSUMABLE else 0,
        supplier=(data.get("supplier") or "").strip(),
        in_repair=bool(data.get("in_repair")) if part_type == JIG else False,
    )
    db.add(p)
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
    if "location" in data:
        p.location = (data.get("location") or "").strip()
    if "unit" in data and p.part_type == CONSUMABLE:
        p.unit = (data.get("unit") or "").strip()
    if "supplier" in data:
        p.supplier = (data.get("supplier") or "").strip()
    if "warn_qty" in data and p.part_type == CONSUMABLE:
        p.warn_qty = max(0, int(data.get("warn_qty") or 0))
    if "total_qty" in data:
        new_total = max(0, int(data.get("total_qty") or 0))
        if p.part_type == JIG:
            # 治具总数调整：可用数量按差值同向调整（新增治具=可用增加）
            delta = new_total - p.total_qty
            p.available_qty = max(0, min(new_total, p.available_qty + delta))
        p.total_qty = new_total
    if "in_repair" in data and p.part_type == JIG:
        p.in_repair = bool(data.get("in_repair"))
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
    db.delete(p)
    db.commit()
    write_operation_log(db, username, "DELETE", "warehouse", str(part_id),
                        f"删除物品: {name}", request)
    return True


# ---------------- 借还 / 领用 / 补货 ----------------
def _add_tx(db, p: WarehousePart, tx_type: str, qty: int,
            operator: str = "", line: str = "", supplier: str = "", remark: str = ""):
    db.add(PartTransaction(
        part_id=p.id, part_name=p.name, tx_type=tx_type, qty=qty,
        operator=operator, line=line, supplier=supplier, remark=remark or "",
    ))


def borrow(db: Session, part_id: int, data: dict, request, username: str) -> dict:
    p = _get_part(db, part_id)
    if p.part_type != JIG:
        raise HTTPException(status_code=400, detail="仅治具支持借出操作")
    if p.in_repair:
        raise HTTPException(status_code=400, detail="该治具维修中，暂不可借出")
    qty = int(data.get("qty") or 1)
    if qty <= 0:
        raise HTTPException(status_code=400, detail="借出数量必须大于 0")
    if qty > p.available_qty:
        raise HTTPException(status_code=400, detail=f"可用数量不足（当前可用 {p.available_qty}）")
    borrower = (data.get("operator") or data.get("borrower") or "").strip()
    line = (data.get("line") or "").strip()
    if not borrower or not line:
        raise HTTPException(status_code=400, detail="借用人和线体为必填项")
    p.available_qty -= qty
    p.current_borrower = borrower
    p.borrow_time = beijing_now()
    p.expected_return = _parse_date(data.get("expected_return"))
    _add_tx(db, p, "借出", qty, operator=borrower, line=line, remark=data.get("remark") or "")
    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "BORROW", "warehouse", str(p.id),
                        f"治具借出: {p.name} x{qty} 借用人:{borrower}", request)
    return _part_to_dict(p)


def return_part(db: Session, part_id: int, data: dict, request, username: str) -> dict:
    p = _get_part(db, part_id)
    if p.part_type != JIG:
        raise HTTPException(status_code=400, detail="仅治具支持归还操作")
    qty = p.total_qty - p.available_qty
    if qty <= 0:
        raise HTTPException(status_code=400, detail="该治具当前没有借出记录")
    borrower = p.current_borrower or ""
    p.available_qty = p.total_qty
    p.current_borrower = None
    p.borrow_time = None
    p.expected_return = None
    _add_tx(db, p, "归还", qty, operator=borrower, remark=data.get("remark") or "")
    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "RETURN", "warehouse", str(p.id),
                        f"治具归还: {p.name} x{qty}", request)
    return _part_to_dict(p)


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
    if not operator or not line:
        raise HTTPException(status_code=400, detail="领用人和线体为必填项")
    p.total_qty -= qty
    _add_tx(db, p, "领用", qty, operator=operator, line=line, remark=data.get("remark") or "")
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
        "supplier":  ("供应商", "supplier"),
    }
    for key, aliases in header_aliases.items():
        for idx, col in enumerate(header):
            if col in aliases:
                col_map[key] = idx
                break
    if "name" not in col_map:
        raise HTTPException(status_code=400, detail="未找到「物品名称」列，请检查表头（需包含：物品名称、型号、类型、数量、货位、单位、预警值、供应商）")

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
    supplier = (data.get("supplier") or "").strip()
    p.total_qty += qty
    if supplier:
        p.supplier = supplier
    _add_tx(db, p, "补货", qty, supplier=supplier, remark=data.get("remark") or "")
    db.commit()
    db.refresh(p)
    write_operation_log(db, username, "RESTOCK", "warehouse", str(p.id),
                        f"耗材补货: {p.name} x{qty}", request)
    return _part_to_dict(p)
