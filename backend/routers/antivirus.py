"""
设备杀毒记录管理 - API 路由
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database import get_db
from models import AntivirusRecord
from schemas import AntiVirusRecordCreate, AntiVirusRecordUpdate, AntiVirusRecordOut, PaginatedData
from core.auth import require_role, get_current_user

router = APIRouter(prefix="/antivirus", tags=["设备杀毒"])


def _record_to_dict(r: AntivirusRecord) -> dict:
    return {
        "id": r.id,
        "device_id": r.device_id,
        "antivirus_time": r.antivirus_time.isoformat() if r.antivirus_time else None,
        "production_line": r.production_line,
        "operator": r.operator,
        "cycle": r.cycle,
        "next_antivirus_time": r.next_antivirus_time.isoformat() if r.next_antivirus_time else None,
        "remark": r.remark,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


def _calc_next_time(antivirus_time: datetime, cycle: str) -> datetime:
    if cycle == "每天":
        return antivirus_time + timedelta(days=1)
    else:
        return antivirus_time + timedelta(days=7)


# ==================== CRUD ====================

@router.get("/records")
def list_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    production_line: Optional[str] = None,
    device_id: Optional[str] = None,
    cycle: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(AntivirusRecord)
    if production_line:
        q = q.filter(AntivirusRecord.production_line == production_line)
    if device_id:
        q = q.filter(AntivirusRecord.device_id.like(f"%{device_id}%"))
    if cycle:
        q = q.filter(AntivirusRecord.cycle == cycle)
    total = q.count()
    records = q.order_by(AntivirusRecord.antivirus_time.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"code": 200, "data": PaginatedData(total=total, page=page, page_size=page_size, items=[_record_to_dict(r) for r in records])}


@router.get("/records/{record_id}")
def get_record(record_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    r = db.query(AntivirusRecord).filter(AntivirusRecord.id == record_id).first()
    if not r:
        raise HTTPException(404, "记录不存在")
    return {"code": 200, "data": _record_to_dict(r)}


@router.post("/records")
def create_record(
    body: AntiVirusRecordCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    next_time = _calc_next_time(body.antivirus_time, body.cycle)
    r = AntivirusRecord(
        device_id=body.device_id,
        antivirus_time=body.antivirus_time,
        production_line=body.production_line,
        operator=body.operator,
        cycle=body.cycle,
        next_antivirus_time=next_time,
        remark=body.remark,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return {"code": 200, "data": _record_to_dict(r), "message": "创建成功"}


@router.put("/records/{record_id}")
def update_record(
    record_id: int,
    body: AntiVirusRecordUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    r = db.query(AntivirusRecord).filter(AntivirusRecord.id == record_id).first()
    if not r:
        raise HTTPException(404, "记录不存在")
    update_data = body.model_dump(exclude_unset=True)
    if "antivirus_time" in update_data or "cycle" in update_data:
        av_time = update_data.get("antivirus_time", r.antivirus_time)
        cycle = update_data.get("cycle", r.cycle)
        r.next_antivirus_time = _calc_next_time(av_time, cycle)
    for k, v in update_data.items():
        if k != "next_antivirus_time":
            setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return {"code": 200, "data": _record_to_dict(r), "message": "更新成功"}


@router.delete("/records/{record_id}")
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    r = db.query(AntivirusRecord).filter(AntivirusRecord.id == record_id).first()
    if not r:
        raise HTTPException(404, "记录不存在")
    db.delete(r)
    db.flush()
    db.commit()
    return {"code": 200, "ok": True, "message": "删除成功"}


@router.post("/records/import")
def import_records(
    records: list[AntiVirusRecordCreate],
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("admin", "engineer")),
):
    """批量导入杀毒记录"""
    created = []
    for body in records:
        next_time = _calc_next_time(body.antivirus_time, body.cycle)
        r = AntivirusRecord(
            device_id=body.device_id,
            antivirus_time=body.antivirus_time,
            production_line=body.production_line,
            operator=body.operator,
            cycle=body.cycle,
            next_antivirus_time=next_time,
            remark=body.remark,
        )
        db.add(r)
        created.append(r)
    db.commit()
    return {"code": 200, "ok": True, "imported": len(created)}


# ==================== 看板 ====================

@router.get("/dashboard")
def antivirus_dashboard(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """设备杀毒看板：全局统计 + 按线体分布（含进度百分比）"""
    from sqlalchemy import func

    now = datetime.utcnow()

    # 取所有杀毒记录中每个设备最新的一条
    latest = (
        db.query(
            AntivirusRecord.device_id,
            func.max(AntivirusRecord.antivirus_time).label("last_time"),
        )
        .group_by(AntivirusRecord.device_id)
        .subquery()
    )
    records = (
        db.query(AntivirusRecord)
        .join(latest, (AntivirusRecord.device_id == latest.c.device_id)
                         & (AntivirusRecord.antivirus_time == latest.c.last_time))
        .all()
    )

    total_devices = len(records)
    done_count = 0
    pending_count = 0
    overdue_count = 0

    # 统计顺序固定：1-8线 + 品质线 + 维修线
    line_order = [f"{i}线" for i in range(1, 9)] + ["品质线", "维修线"]
    line_map = {ln: {"line": ln, "total": 0, "done": 0, "pending": 0, "overdue": 0} for ln in line_order}

    def _classify(r):
        if r.next_antivirus_time and r.next_antivirus_time > now:
            return "done"
        elif r.next_antivirus_time and r.next_antivirus_time <= now:
            return "overdue"
        else:
            return "pending"

    for r in records:
        tag = _classify(r)
        if   tag == "done":    done_count    += 1
        elif tag == "overdue": overdue_count += 1
        else:                  pending_count += 1

        line_name = r.production_line or "未分组"
        if line_name not in line_map:
            line_map[line_name] = {"line": line_name, "total": 0, "done": 0, "pending": 0, "overdue": 0}
            line_order.append(line_name)
        line_map[line_name]["total"] += 1
        line_map[line_name][tag]     += 1

    # 补全未出现的固定顺序线体（保持表格行一致），并计算进度
    distribution = []
    for ln in line_order:
        row = line_map.get(ln, {"line": ln, "total": 0, "done": 0, "pending": 0, "overdue": 0})
        total = row["total"]
        if total > 0:
            ratio = round(row["done"] / total * 100)
        else:
            ratio = 0
        row["progress"] = ratio
        # 状态色：全绿=done 100%；有overdue=红色；其他(pending多/总数为0)=灰色
        if total == 0:
            row["level"] = "muted"
        elif row["overdue"] > 0:
            row["level"] = "danger"
        elif ratio >= 100:
            row["level"] = "success"
        else:
            row["level"] = "danger"
        distribution.append(row)

    return {
        "code": 200,
        "data": {
            "total_devices": total_devices,
            "done_count":    done_count,
            "pending_count": pending_count,
            "overdue_count": overdue_count,
            "distribution":  distribution,
        },
    }
