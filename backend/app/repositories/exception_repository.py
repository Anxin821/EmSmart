from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.exception import ExceptionRecord
from typing import Optional, Tuple, List


class ExceptionRepository:

    @staticmethod
    def get_list(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        exception_type: Optional[str] = None,
        status: Optional[str] = None,
        level: Optional[str] = None,
        stopped: Optional[str] = None,
    ) -> Tuple[List[ExceptionRecord], int]:
        query = db.query(ExceptionRecord)
        if keyword:
            query = query.filter(
                or_(
                    ExceptionRecord.exception_no.like(f"%{keyword}%"),
                    ExceptionRecord.phenomenon_desc.like(f"%{keyword}%"),
                    ExceptionRecord.discoverer.like(f"%{keyword}%")
                )
            )
        if exception_type:
            query = query.filter(ExceptionRecord.exception_type == exception_type)
        if status:
            # 两态归并：待处理含历史“处理中”，已解决含历史“已关闭”
            status_map = {
                'pending': ['pending', 'processing'],
                'resolved': ['resolved', 'closed'],
            }
            statuses = status_map.get(status, [status])
            query = query.filter(ExceptionRecord.status.in_(statuses))
        if level:
            query = query.filter(ExceptionRecord.exception_level == level)
        if stopped is not None and stopped != '':
            query = query.filter(ExceptionRecord.is_stopped == int(stopped))

        total = query.count()
        items = query.order_by(ExceptionRecord.created_at.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()
        return items, total

    @staticmethod
    def get_by_id(db: Session, record_id: str):
        return db.query(ExceptionRecord).filter(ExceptionRecord.id == record_id).first()

    @staticmethod
    def create(db: Session, data: dict):
        record = ExceptionRecord(**data)
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def update(db: Session, record: ExceptionRecord, data: dict):
        for key, value in data.items():
            if value is not None and hasattr(record, key):
                setattr(record, key, value)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def delete(db: Session, record: ExceptionRecord):
        db.delete(record)
        db.commit()

    @staticmethod
    def get_dashboard(db: Session) -> dict:
        from sqlalchemy import func
        from datetime import timedelta
        from app.core.timeutil import beijing_now

        all_count = db.query(ExceptionRecord).count()
        # 状态简化为「待处理 / 已解决」两态：未解决（含历史的处理中）归入待处理，已关闭归入已解决
        pending = db.query(ExceptionRecord).filter(
            ExceptionRecord.status.in_(['pending', 'processing'])
        ).count()
        resolved = db.query(ExceptionRecord).filter(
            ExceptionRecord.status.in_(['resolved', 'closed'])
        ).count()

        # 解决率
        resolution_rate = round(resolved / all_count * 100, 1) if all_count else 0.0

        # 按异常等级统计
        level_rows = db.query(
            ExceptionRecord.exception_level,
            func.count(ExceptionRecord.id)
        ).group_by(ExceptionRecord.exception_level).all()
        level_map = {lv: cnt for lv, cnt in level_rows}

        # 停线异常数
        stopped = db.query(ExceptionRecord).filter(ExceptionRecord.is_stopped == 1).count()

        # 按类型统计（含待处理/已解决拆分）
        type_rows = db.query(
            ExceptionRecord.exception_type,
            ExceptionRecord.status,
            func.count(ExceptionRecord.id)
        ).group_by(ExceptionRecord.exception_type, ExceptionRecord.status).all()
        type_agg = {}
        for t, s, c in type_rows:
            row = type_agg.setdefault(t, {"type": t, "total": 0, "pending": 0, "resolved": 0})
            row["total"] += c
            if s in ('resolved', 'closed'):
                row["resolved"] += c
            else:
                row["pending"] += c
        by_type = sorted(type_agg.values(), key=lambda x: x["total"], reverse=True)

        # 近 14 天趋势：按发生时间统计每日新增与每日解决
        today = beijing_now().replace(hour=0, minute=0, second=0, microsecond=0)
        start = today - timedelta(days=13)
        recent = db.query(ExceptionRecord).filter(
            ExceptionRecord.occurred_time >= start
        ).all()
        trend_map = {}
        for i in range(14):
            d = start + timedelta(days=i)
            trend_map[d.strftime("%m-%d")] = {"date": d.strftime("%m-%d"), "new": 0, "resolved": 0}
        for r in recent:
            if not r.occurred_time:
                continue
            key = r.occurred_time.strftime("%m-%d")
            if key in trend_map:
                trend_map[key]["new"] += 1
                if r.status in ('resolved', 'closed'):
                    trend_map[key]["resolved"] += 1
        trend = list(trend_map.values())

        return {
            "total": all_count,
            "pending": pending,
            "resolved": resolved,
            "resolution_rate": resolution_rate,
            "by_level": {
                "critical": level_map.get("critical", 0),
                "major": level_map.get("major", 0),
                "minor": level_map.get("minor", 0),
            },
            "stopped": stopped,
            "by_type": by_type,
            "trend": trend,
        }