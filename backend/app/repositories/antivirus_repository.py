from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import AntivirusRecord


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


def _dedupe_latest_by_device_line(records: List[AntivirusRecord]) -> List[AntivirusRecord]:
    latest = {}
    for r in records:
        key = (r.device_id, r.production_line)
        cur = latest.get(key)
        if cur is None or (r.antivirus_time, r.id) > (cur.antivirus_time, cur.id):
            latest[key] = r
    return list(latest.values())


def _classify_antivirus_status(next_antivirus_time: Optional[datetime], now: datetime, pending_window_hours: int = 24) -> str:
    if not next_antivirus_time:
        return "pending"
    if next_antivirus_time <= now:
        return "overdue"
    if next_antivirus_time <= now + timedelta(hours=pending_window_hours):
        return "pending"
    return "done"


# CRUD

def list_records(db: Session, page: int = 1, page_size: int = 20, production_line: Optional[str] = None, device_id: Optional[str] = None, cycle: Optional[str] = None):
    q = db.query(AntivirusRecord)
    if production_line:
        q = q.filter(AntivirusRecord.production_line == production_line)
    if device_id:
        q = q.filter(AntivirusRecord.device_id.like(f"%{device_id}%"))
    if cycle:
        q = q.filter(AntivirusRecord.cycle == cycle)
    total = q.count()
    records = q.order_by(AntivirusRecord.antivirus_time.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return records, total


def get_record(db: Session, record_id: int):
    return db.query(AntivirusRecord).filter(AntivirusRecord.id == record_id).first()


def create_record(db: Session, body_data: dict):
    next_time = _calc_next_time(body_data["antivirus_time"], body_data["cycle"])
    r = AntivirusRecord(
        device_id=body_data["device_id"],
        antivirus_time=body_data["antivirus_time"],
        production_line=body_data.get("production_line"),
        operator=body_data.get("operator"),
        cycle=body_data.get("cycle"),
        next_antivirus_time=next_time,
        remark=body_data.get("remark"),
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def update_record(db: Session, record_id: int, update_data: dict):
    r = db.query(AntivirusRecord).filter(AntivirusRecord.id == record_id).first()
    if not r:
        return None
    if "antivirus_time" in update_data or "cycle" in update_data:
        av_time = update_data.get("antivirus_time", r.antivirus_time)
        cycle = update_data.get("cycle", r.cycle)
        r.next_antivirus_time = _calc_next_time(av_time, cycle)
    for k, v in update_data.items():
        if k != "next_antivirus_time":
            setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return r


def delete_record(db: Session, record_id: int) -> bool:
    r = db.query(AntivirusRecord).filter(AntivirusRecord.id == record_id).first()
    if not r:
        return False
    db.delete(r)
    db.commit()
    return True


def import_records(db: Session, records: List[dict]) -> int:
    created = []
    for body in records:
        next_time = _calc_next_time(body["antivirus_time"], body["cycle"])
        r = AntivirusRecord(
            device_id=body["device_id"],
            antivirus_time=body["antivirus_time"],
            production_line=body.get("production_line"),
            operator=body.get("operator"),
            cycle=body.get("cycle"),
            next_antivirus_time=next_time,
            remark=body.get("remark"),
        )
        db.add(r)
        created.append(r)
    db.commit()
    return len(created)


# Dashboard / aggregation

def list_overdue_records(db: Session, status: Optional[str] = None, production_line: Optional[str] = None, page: int = 1, page_size: int = 50):
    now = datetime.utcnow()
    latest = _dedupe_latest_by_device_line(db.query(AntivirusRecord).all())

    def _matches(r: AntivirusRecord) -> bool:
        tag = _classify_antivirus_status(r.next_antivirus_time, now)
        if status == "pending":
            return tag == "pending" and (not production_line or r.production_line == production_line)
        if status == "overdue":
            return tag == "overdue" and (not production_line or r.production_line == production_line)
        return tag == "overdue" and (not production_line or r.production_line == production_line)

    records = [r for r in latest if _matches(r)]
    records.sort(key=lambda r: (r.next_antivirus_time or datetime.min, r.id))
    total = len(records)
    start = (page - 1) * page_size
    page_records = records[start:start + page_size]
    return page_records, total


def antivirus_dashboard(db: Session) -> Dict[str, Any]:
    now = datetime.utcnow()
    records = _dedupe_latest_by_device_line(db.query(AntivirusRecord).all())

    total_devices = len(records)
    done_count = 0
    pending_count = 0
    overdue_count = 0

    line_order = [f"{i}线" for i in range(1, 9)] + ["品质线", "维修线"]
    line_map = {ln: {"line": ln, "total": 0, "done": 0, "pending": 0, "overdue": 0} for ln in line_order}

    for r in records:
        tag = _classify_antivirus_status(r.next_antivirus_time, now)
        if tag == "done":
            done_count += 1
        elif tag == "overdue":
            overdue_count += 1
        else:
            pending_count += 1

        line_name = r.production_line or "未分组"
        if line_name not in line_map:
            line_map[line_name] = {"line": line_name, "total": 0, "done": 0, "pending": 0, "overdue": 0}
            line_order.append(line_name)
        line_map[line_name]["total"] += 1
        line_map[line_name][tag] += 1

    distribution = []
    for ln in line_order:
        row = line_map.get(ln, {"line": ln, "total": 0, "done": 0, "pending": 0, "overdue": 0})
        total = row["total"]
        if total > 0:
            ratio = round(row["done"] / total * 100)
        else:
            ratio = 0
        row["progress"] = ratio
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
        "total_devices": total_devices,
        "done_count": done_count,
        "pending_count": pending_count,
        "overdue_count": overdue_count,
        "distribution": distribution,
    }
