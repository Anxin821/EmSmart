"""
智能工厂工作任务管理平台 - CRUD 数据库操作封装
提供各业务模块的标准增删改查函数
"""
from typing import Optional, List, Tuple
from datetime import date, datetime, timedelta
from sqlalchemy import func, and_, or_, text, desc, case, Date as DateType
from sqlalchemy.orm import Session, joinedload
from models import (
    User, AoiAiDevice, WeeklyProduction, MonthlyProduction,
    Server, AgingRack, WifiAp, WorkOrder, Bug, DevRequest, OperationLog, Project, EsopPart
)
from core.auth import hash_password


# ============================================================
# 用户相关
# ============================================================
def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username, User.is_active == True).first()


# ============================================================
# AOI&AI 设备 CRUD
# ============================================================
def get_aoi_devices_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    production_line: Optional[str] = None,
    status: Optional[str] = None,
    device_type: Optional[str] = None,
) -> Tuple[List[AoiAiDevice], int]:
    """分页查询 AOI&AI 设备，支持筛选"""
    query = db.query(AoiAiDevice)

    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(
            or_(AoiAiDevice.name.like(kw), AoiAiDevice.device_id.like(kw), AoiAiDevice.ip_address.like(kw))
        )
    if production_line:
        query = query.filter(AoiAiDevice.production_line == production_line)
    if status:
        query = query.filter(AoiAiDevice.status == status)
    if device_type:
        query = query.filter(AoiAiDevice.device_type == device_type)

    total = query.count()
    items = query.order_by(AoiAiDevice.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def _clean_device_status(status) -> str:
    """统一清洗设备状态：去除两端的 | 与空白字符，空值返回 '正常'。"""
    if status is None:
        return "正常"
    s = str(status).strip().lstrip("|").rstrip("|").strip()
    return s or "正常"


def _clean_dev_request_fields(data: dict) -> dict:
    """清洗 MES 需求 / BUG 等业务字段中多余的 | 前缀。"""
    data = dict(data)
    for field in ("status", "priority", "severity"):
        if field in data and data[field] is not None:
            data[field] = str(data[field]).strip().lstrip("|").rstrip("|").strip()
    return data


def create_aoi_device(db: Session, data: dict) -> AoiAiDevice:
    data = dict(data)
    if "status" in data:
        data["status"] = _clean_device_status(data["status"])
    device = AoiAiDevice(**data)
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def update_aoi_device(db: Session, device_id_or_pk, data: dict) -> Optional[AoiAiDevice]:
    """编辑设备，支持按主键id(int)或业务device_id(str)查找"""
    if isinstance(device_id_or_pk, int):
        device = db.query(AoiAiDevice).filter(AoiAiDevice.id == device_id_or_pk).first()
    else:
        device = db.query(AoiAiDevice).filter(AoiAiDevice.device_id == device_id_or_pk).first()
    if not device:
        return None
    for key, value in data.items():
        if value is not None and hasattr(device, key):
            if key == "status":
                value = _clean_device_status(value)
            setattr(device, key, value)
    db.commit()
    db.refresh(device)
    return device


def delete_aoi_device(db: Session, device_id_or_pk) -> bool:
    """删除设备，支持按主键id(int)或业务device_id(str)"""
    if isinstance(device_id_or_pk, int):
        device = db.query(AoiAiDevice).filter(AoiAiDevice.id == device_id_or_pk).first()
    else:
        device = db.query(AoiAiDevice).filter(AoiAiDevice.device_id == device_id_or_pk).first()
    if not device:
        return False
    db.delete(device)
    db.commit()
    return True


def get_aoi_device_by_pk(db: Session, device_pk: int) -> Optional[AoiAiDevice]:
    """按主键id查询设备"""
    return db.query(AoiAiDevice).filter(AoiAiDevice.id == device_pk).first()


def get_aoi_device_by_id(db: Session, device_id: str) -> Optional[AoiAiDevice]:
    """按业务设备ID查询设备（用于唯一性校验）"""
    return db.query(AoiAiDevice).filter(AoiAiDevice.device_id == device_id).first()


# ============================================================
# 周报 CRUD
# ============================================================
def get_weekly_production_by_id(db: Session, record_id: int) -> Optional[WeeklyProduction]:
    return db.query(WeeklyProduction).filter(WeeklyProduction.id == record_id).first()


def get_weekly_production_paginated(
    db: Session, page: int = 1, page_size: int = 20,
    year: Optional[int] = None, week: Optional[int] = None,
    production_line: Optional[str] = None, project: Optional[str] = None,
) -> Tuple[List[WeeklyProduction], int]:
    query = db.query(WeeklyProduction)
    if year:
        query = query.filter(WeeklyProduction.year == year)
    if week:
        query = query.filter(WeeklyProduction.week_number == week)
    if production_line:
        query = query.filter(WeeklyProduction.production_line == production_line)
    if project:
        query = query.filter(WeeklyProduction.project == project)

    total = query.count()
    items = query.order_by(WeeklyProduction.year.desc(), WeeklyProduction.week_number.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def create_weekly_production(db: Session, data: dict) -> WeeklyProduction:
    record = WeeklyProduction(**data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_weekly_production(db: Session, record_id: int, data: dict) -> Optional[WeeklyProduction]:
    record = db.query(WeeklyProduction).filter(WeeklyProduction.id == record_id).first()
    if not record:
        return None
    for key, value in data.items():
        if value is not None and hasattr(record, key):
            setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


def delete_weekly_production(db: Session, record_id: int) -> bool:
    record = db.query(WeeklyProduction).filter(WeeklyProduction.id == record_id).first()
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True


# ============================================================
# 月报 CRUD
# ============================================================
def get_monthly_production_paginated(
    db: Session, page: int = 1, page_size: int = 20,
    year: Optional[int] = None, month: Optional[int] = None,
    production_line: Optional[str] = None, project: Optional[str] = None,
) -> Tuple[List[MonthlyProduction], int]:
    """月报分页：每月每项目只有一条记录，直接查询即可"""
    query = db.query(MonthlyProduction)
    if year:
        query = query.filter(MonthlyProduction.year == year)
    if month:
        query = query.filter(MonthlyProduction.month == month)
    if project:
        query = query.filter(MonthlyProduction.project == project)

    total = query.count()
    items = query.order_by(MonthlyProduction.year.desc(), MonthlyProduction.month.desc(), MonthlyProduction.project).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_monthly_summary_stats(
    db: Session, year: Optional[int] = None, month: Optional[int] = None,
) -> dict:
    """月报总数统计：总产量、总合格数、总直通率（可筛选年/月）"""
    q = db.query(
        func.sum(MonthlyProduction.monthly_total_output),
        func.sum(MonthlyProduction.monthly_qualified_count),
    )
    if year:
        q = q.filter(MonthlyProduction.year == year)
    if month:
        q = q.filter(MonthlyProduction.month == month)
    row = q.first()
    total_output = int(row[0] or 0)
    total_qualified = int(row[1] or 0)
    yield_rate = round(total_qualified / total_output * 100, 2) if total_output > 0 else 0
    return {"total_output": total_output, "total_qualified": total_qualified, "yield_rate": yield_rate}


def get_monthly_trend(
    db: Session, year: Optional[int] = None,
) -> list:
    """按 (年,月) 聚合每月的总产量、直通率，返回按时间升序的趋势数据。
    口径与列表页一致：sum(monthly_total_output) / sum(monthly_qualified_count) 计算直通率。
    """
    q = db.query(
        MonthlyProduction.year,
        MonthlyProduction.month,
        func.sum(MonthlyProduction.monthly_total_output).label("out"),
        func.sum(MonthlyProduction.monthly_qualified_count).label("q"),
    ).group_by(MonthlyProduction.year, MonthlyProduction.month)
    if year:
        q = q.filter(MonthlyProduction.year == year)
    q = q.order_by(MonthlyProduction.year, MonthlyProduction.month)
    rows = q.all()
    result = []
    for y, m, o, qty in rows:
        o_i   = int(o or 0)
        q_i   = int(qty or 0)
        rate  = round(q_i / o_i * 100, 2) if o_i > 0 else 0
        result.append({
            "year": y,
            "month": m,
            "label": f"{y}年{m}月",
            "total_output": o_i,
            "total_qualified": q_i,
            "yield_rate": rate,
        })
    return result


# ============================================================
# MES 看板汇总
# ============================================================
# 图例词汇表（与前端堆叠柱 legend 一一对应，缺失状态补 0）
BUG_STATUS_ORDER   = ["确认新增", "修复中", "解决关闭"]
REQ_STATUS_ORDER   = ["收集评估", "开发测试中", "上线"]
# 将库里的 BUG 状态映射到图例词汇（库里目前只有「解决关闭」这一种存量值，future 状态兼容）
_BUG_STATUS_MAP = {
    "新建":      "确认新增",
    "确认":      "确认新增",
    "确认新增":  "确认新增",
    "修复中":    "修复中",
    "已解决":    "解决关闭",
    "关闭":      "解决关闭",
    "解决关闭":  "解决关闭",
}
_REQ_STATUS_MAP = {
    "收集评估":   "收集评估",
    "待评估":     "收集评估",
    "开发测试中": "开发测试中",
    "开发中":     "开发测试中",
    "测试中":     "开发测试中",
    "上线":       "上线",
    "已上线":     "上线",
    "完成上线":   "上线",
}


def get_mes_dashboard(db: Session) -> dict:
    """MES 看板聚合：
    - BUG修复率、需求完成率
    - 月度 BUG / 需求 状态堆叠分布（按 created_date / created_at 业务月份）
    - 风险 TOP：高危 BUG（严重/致命/P0）+ 逾期需求（期望日期已过且未上线，优先高优）
    - 里程碑：前 5 条状态=上线 的需求标题（按最近更新时间降序）
    """
    from datetime import date
    from models import Bug, DevRequest
    today = date.today()

    bugs_all = db.query(Bug).all()
    reqs_all = db.query(DevRequest).all()

    bug_total = len(bugs_all)
    req_total = len(reqs_all)

    bug_fixed  = sum(1 for b in bugs_all if _BUG_STATUS_MAP.get((b.status or "").strip()) == "解决关闭")
    req_online = sum(1 for r in reqs_all if _REQ_STATUS_MAP.get((r.status or "").strip()) == "上线")
    fix_rate      = round(bug_fixed  / bug_total * 100, 1) if bug_total else 0
    delivery_rate = round(req_online / req_total * 100, 1) if req_total else 0

    # -------- BUG 月度堆叠 --------
    def bug_month_key(b):
        d = b.created_date or (b.created_at.date() if b.created_at else None)
        return (d.year, d.month) if d else (0, 0)
    bug_month_grouped = {}
    for b in bugs_all:
        k = bug_month_key(b)
        if k == (0, 0): continue
        bucket = bug_month_grouped.setdefault(k, {s: 0 for s in BUG_STATUS_ORDER})
        s = _BUG_STATUS_MAP.get((b.status or "").strip())
        if s in bucket:
            bucket[s] += 1
    bug_monthly = []
    for k in sorted(bug_month_grouped):
        y, m = k
        bug_monthly.append({
            "year": y, "month": m,
            "label": f"{y}M{m:02d}",
            **bug_month_grouped[k],
        })

    # -------- REQ 月度堆叠 --------
    def req_month_key(r):
        d = r.created_at or r.updated_at
        return (d.year, d.month) if d else (0, 0)
    req_month_grouped = {}
    for r in reqs_all:
        k = req_month_key(r)
        if k == (0, 0): continue
        bucket = req_month_grouped.setdefault(k, {s: 0 for s in REQ_STATUS_ORDER})
        s = _REQ_STATUS_MAP.get((r.status or "").strip())
        if s in bucket:
            bucket[s] += 1
    req_monthly = []
    for k in sorted(req_month_grouped):
        y, m = k
        req_monthly.append({
            "year": y, "month": m,
            "label": f"{y}M{m:02d}",
            **req_month_grouped[k],
        })

    # -------- 风险 TOP（至少 2 块：高危 BUG + 延期需求；每块最多列 3 条样例标题） --------
    def severity_rank(sev: str):
        return {"致命": 0, "P0": 0, "严重": 1, "P1": 1, "一般": 2, "P2": 2, "建议": 3, "P3": 3}.get((sev or "").strip(), 9)
    high_bugs = sorted(
        [b for b in bugs_all if severity_rank(b.severity) <= 1],
        key=lambda b: (severity_rank(b.severity), -b.id)
    )[:3]
    overdue = []
    for r in reqs_all:
        status_val = _REQ_STATUS_MAP.get((r.status or "").strip())
        if status_val == "上线":
            continue
        exp = r.expected_date
        if not exp:
            continue
        if hasattr(exp, "date"):
            exp = exp.date()
        if exp < today:
            overdue.append(r)
    # 先高优、再逾期更早
    pri_rank = {"紧急": 0, "高": 1, "中": 2, "普通": 3, "低": 4}
    overdue.sort(key=lambda r: (pri_rank.get((r.priority or "").strip(), 5),
                                r.expected_date or today))
    overdue = overdue[:3]

    risks = [
        {
            "icon":  "p0_bug",
            "label": "P0级BUG",
            "unit":  "个",
            "value": len(high_bugs),
            "items": [b.title or b.bug_id for b in high_bugs] if high_bugs else [],
        },
        {
            "icon":  "overdue_req",
            "label": "延期需求",
            "unit":  "个",
            "value": len(overdue),
            "items": [r.title or r.request_id for r in overdue] if overdue else [],
        },
    ]

    # -------- 里程碑：已上线需求前 5 条（最近更新在前） --------
    online = [r for r in reqs_all if _REQ_STATUS_MAP.get((r.status or "").strip()) == "上线"]
    online.sort(key=lambda r: r.updated_at or r.created_at, reverse=True)
    top_online = online[:5]
    milestones = {
        "label": "已完成上线",
        "unit":  "个需求",
        "count": len(top_online),
        "items": [r.title or r.request_id for r in top_online],
    }

    return {
        "bug_count":       bug_total,
        "req_count":       req_total,
        "fix_rate":        fix_rate,
        "delivery_rate":   delivery_rate,
        "bug_fixed":       bug_fixed,
        "req_online":      req_online,
        "bug_monthly":     bug_monthly,
        "req_monthly":     req_monthly,
        "bug_status_order":BUG_STATUS_ORDER,
        "req_status_order":REQ_STATUS_ORDER,
        "risks":           risks,
        "milestones":      milestones,
    }


def create_monthly_production(db: Session, data: dict) -> MonthlyProduction:
    record = MonthlyProduction(**data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_monthly_production(db: Session, record_id: int, data: dict) -> Optional[MonthlyProduction]:
    record = db.query(MonthlyProduction).filter(MonthlyProduction.id == record_id).first()
    if not record:
        return None
    for key, value in data.items():
        if value is not None and hasattr(record, key):
            setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


def delete_monthly_production(db: Session, record_id: int) -> bool:
    record = db.query(MonthlyProduction).filter(MonthlyProduction.id == record_id).first()
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True


def generate_monthly_from_weekly(db: Session, year: int, month: int, recorder: str):
    """
    根据指定月份的周报数据自动汇总生成月报
    通过计算该月第一天和最后一天所在的ISO周来筛选周数据
    """
    import calendar
    from datetime import date

    # 计算该月包含的ISO周范围
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    first_week = first_day.isocalendar()[1]
    last_week = last_day.isocalendar()[1]

    # 处理跨年周（12月可能有第1周）
    if first_week > last_week:
        week_filter = or_(
            and_(WeeklyProduction.year == year, WeeklyProduction.week_number >= first_week),
            and_(WeeklyProduction.year == year + 1, WeeklyProduction.week_number <= last_week),
        )
    else:
        week_filter = and_(
            WeeklyProduction.year == year,
            WeeklyProduction.week_number >= first_week,
            WeeklyProduction.week_number <= last_week,
        )

    # 先删除该月已有数据（覆盖模式），flush 确保 delete 先执行避免 PK 冲突
    db.query(MonthlyProduction).filter(
        MonthlyProduction.year == year,
        MonthlyProduction.month == month
    ).delete()
    db.flush()

    results = (
        db.query(
            WeeklyProduction.project,
            func.sum(WeeklyProduction.total_output),
            func.sum(WeeklyProduction.qualified_count),
        )
        .filter(week_filter)
        .group_by(WeeklyProduction.project)
        .all()
    )

    generated_count = 0
    for project, total_out, qual_count in results:
        m = MonthlyProduction(
            year=year,
            month=month,
            production_line="",  # 月报不区分产线
            project=project,
            monthly_total_output=int(total_out or 0),
            monthly_qualified_count=int(qual_count or 0),
            recorder=recorder,
        )
        db.add(m)
        generated_count += 1

    db.commit()
    return generated_count


# ============================================================
# 服务器 CRUD
# ============================================================
def get_servers_paginated(
    db: Session, page: int = 1, page_size: int = 20,
    keyword: Optional[str] = None, production_line: Optional[str] = None,
    status: Optional[str] = None,
) -> Tuple[List[Server], int]:
    query = db.query(Server)
    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(or_(Server.name.like(kw), Server.server_id.like(kw), Server.ip_address.like(kw)))
    if production_line:
        query = query.filter(Server.production_line == production_line)
    if status:
        query = query.filter(Server.status == status)
    total = query.count()
    items = query.order_by(Server.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def create_server(db: Session, data: dict) -> Server:
    server = Server(**data)
    db.add(server)
    db.commit()
    db.refresh(server)
    return server


def update_server(db: Session, server_id: str, data: dict) -> Optional[Server]:
    server = db.query(Server).filter(Server.server_id == server_id).first()
    if not server:
        try:
            pk = int(server_id)
            server = db.query(Server).filter(Server.id == pk).first()
        except (ValueError, TypeError):
            pass
    if not server:
        return None
    for key, value in data.items():
        if value is not None and hasattr(server, key):
            setattr(server, key, value)
    db.commit()
    db.refresh(server)
    return server


def delete_server(db: Session, server_id: str) -> bool:
    server = db.query(Server).filter(Server.server_id == server_id).first()
    if not server:
        try:
            pk = int(server_id)
            server = db.query(Server).filter(Server.id == pk).first()
        except (ValueError, TypeError):
            pass
    if not server:
        return False
    db.delete(server)
    db.commit()
    return True


# ============================================================
# 老化架 CRUD
# ============================================================
def get_aging_racks_paginated(
    db: Session, page: int = 1, page_size: int = 20,
    keyword: Optional[str] = None, production_line: Optional[str] = None,
    status: Optional[str] = None,
) -> Tuple[List[AgingRack], int]:
    query = db.query(AgingRack)
    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(or_(AgingRack.name.like(kw), AgingRack.rack_id.like(kw)))
    if production_line:
        query = query.filter(AgingRack.production_line == production_line)
    if status:
        query = query.filter(AgingRack.status == status)
    total = query.count()
    items = query.order_by(AgingRack.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def create_aging_rack(db: Session, data: dict) -> AgingRack:
    rack = AgingRack(**data)
    db.add(rack)
    db.commit()
    db.refresh(rack)
    return rack


def update_aging_rack(db: Session, rack_id: str, data: dict) -> Optional[AgingRack]:
    rack = db.query(AgingRack).filter(AgingRack.rack_id == rack_id).first()
    if not rack:
        try:
            pk = int(rack_id)
            rack = db.query(AgingRack).filter(AgingRack.id == pk).first()
        except (ValueError, TypeError):
            pass
    if not rack:
        return None
    for key, value in data.items():
        if value is not None and hasattr(rack, key):
            setattr(rack, key, value)
    db.commit()
    db.refresh(rack)
    return rack


def delete_aging_rack(db: Session, rack_id: str) -> bool:
    rack = db.query(AgingRack).filter(AgingRack.rack_id == rack_id).first()
    if not rack:
        try:
            pk = int(rack_id)
            rack = db.query(AgingRack).filter(AgingRack.id == pk).first()
        except (ValueError, TypeError):
            pass
    if not rack:
        return False
    db.delete(rack)
    db.commit()
    return True


# ============================================================
# WiFi AP CRUD
# ============================================================
def get_wifi_aps_paginated(
    db: Session, page: int = 1, page_size: int = 20,
    keyword: Optional[str] = None, production_line: Optional[str] = None,
    status: Optional[str] = None,
) -> Tuple[List[WifiAp], int]:
    query = db.query(WifiAp)
    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(or_(WifiAp.ssid.like(kw), WifiAp.ap_id.like(kw)))
    if production_line:
        query = query.filter(WifiAp.production_line == production_line)
    if status:
        query = query.filter(WifiAp.status == status)
    total = query.count()
    items = query.order_by(WifiAp.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def create_wifi_ap(db: Session, data: dict) -> WifiAp:
    ap = WifiAp(**data)
    db.add(ap)
    db.commit()
    db.refresh(ap)
    return ap


def update_wifi_ap(db: Session, ap_id: str, data: dict) -> Optional[WifiAp]:
    ap = db.query(WifiAp).filter(WifiAp.ap_id == ap_id).first()
    if not ap:
        try:
            pk = int(ap_id)
            ap = db.query(WifiAp).filter(WifiAp.id == pk).first()
        except (ValueError, TypeError):
            pass
    if not ap:
        return None
    for key, value in data.items():
        if value is not None and hasattr(ap, key):
            setattr(ap, key, value)
    db.commit()
    db.refresh(ap)
    return ap


def delete_wifi_ap(db: Session, ap_id: str) -> bool:
    ap = db.query(WifiAp).filter(WifiAp.ap_id == ap_id).first()
    if not ap:
        try:
            pk = int(ap_id)
            ap = db.query(WifiAp).filter(WifiAp.id == pk).first()
        except (ValueError, TypeError):
            pass
    if not ap:
        return False
    db.delete(ap)
    db.commit()
    return True


# ============================================================
# 工单 CRUD
# ============================================================
def get_work_orders_paginated(
    db: Session, page: int = 1, page_size: int = 20,
    keyword: Optional[str] = None, status: Optional[str] = None,
    priority: Optional[str] = None, order_type: Optional[str] = None,
) -> Tuple[List[WorkOrder], int]:
    query = db.query(WorkOrder)
    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(or_(WorkOrder.order_number.like(kw), WorkOrder.product_name.like(kw)))
    if status:
        query = query.filter(WorkOrder.status == status)
    if priority:
        query = query.filter(WorkOrder.priority == priority)
    if order_type:
        query = query.filter(WorkOrder.order_type == order_type)
    total = query.count()
    items = query.order_by(WorkOrder.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def create_work_order(db: Session, data: dict) -> WorkOrder:
    order = WorkOrder(**data)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def update_work_order(db: Session, order_number: str, data: dict) -> Optional[WorkOrder]:
    order = db.query(WorkOrder).filter(WorkOrder.order_number == order_number).first()
    if not order:
        return None
    for key, value in data.items():
        if value is not None and hasattr(order, key):
            setattr(order, key, value)
    db.commit()
    db.refresh(order)
    return order


def delete_work_order(db: Session, order_number: str) -> bool:
    order = db.query(WorkOrder).filter(WorkOrder.order_number == order_number).first()
    if not order:
        return False
    db.delete(order)
    db.commit()
    return True


# ============================================================
# BUG CRUD
# ============================================================
def get_bugs_paginated(
    db: Session, page: int = 1, page_size: int = 20,
    keyword: Optional[str] = None, status: Optional[str] = None,
    severity: Optional[str] = None,
) -> Tuple[List[Bug], int]:
    query = db.query(Bug)
    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(or_(Bug.title.like(kw), Bug.bug_id.like(kw)))
    if status:
        query = query.filter(Bug.status.like(f"%{status}%"))
    if severity:
        query = query.filter(Bug.severity.like(f"%{severity}%"))
    total = query.count()
    # 按「紧急程度」排序：综合 严重等级 + 截止日期 + 是否已关闭
    # ① 已关闭 BUG 放最后（解决关闭 / 关闭 / 已解决 / 解决 → 1，其它 → 0）
    # ② 严重等级：致命 0 > 严重 1 > 一般 2 > 建议 3 > 其它 9（越严重越靠前）
    # ③ 截止日：未设截止日放最后；其余按距今天数升序（越早过期越靠前，负数即已过期的排最前）
    # ④ 兜底：同紧急度按 id 倒序（新创建在前）
    now = date.today()
    _closed_statuses = ["解决关闭", "关闭", "已解决", "解决"]
    items = (
        query.order_by(
            # status/severity 可能是脏值（两端 | 和空格，见 _bug_to_dict 清洗），排序里的
            # 精确 == / in_ 会匹配不到 → 用 LIKE 兼容，保证「已关闭下沉、严重度优先」正常生效
            case(
                (or_(*[Bug.status.like(f"%{s}%") for s in _closed_statuses]), 1),
                else_=0,
            ).asc(),
            case(
                (Bug.severity.like("%致命%"), 0),
                (Bug.severity.like("%严重%"), 1),
                (Bug.severity.like("%一般%"), 2),
                (Bug.severity.like("%建议%"), 3),
                else_=9,
            ).asc(),
            case(
                (Bug.deadline.is_(None), 1),
                else_=0,
            ).asc(),
            func.datediff(text("day"), func.cast(now, DateType), Bug.deadline).asc(),
            Bug.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def create_bug(db: Session, data: dict) -> Bug:
    # bug_id 自增生成规则：BG-YYYYMMDD-N，每天从 001 开始递增
    # 若调用方显式传入 bug_id 则保持不变（兼容手工指定）
    if not data.get("bug_id"):
        today = date.today().strftime("%Y%m%d")
        prefix = f"BG-{today}-"
        # 在事务内加行锁级查询，避免并发冲突
        latest = (
            db.query(Bug.bug_id)
            .with_for_update()
            .filter(Bug.bug_id.like(prefix + "%"))
            .order_by(Bug.id.desc())
            .first()
        )
        next_seq = 1
        if latest and latest[0]:
            m = __import__("re").match(rf"^{prefix}(\d+)$", latest[0])
            if m:
                try:
                    next_seq = int(m.group(1)) + 1
                except (TypeError, ValueError):
                    next_seq = 1
        # 避免最终值重复：若当日同序号已被插入（手工/并发），循环递增
        while True:
            candidate = f"{prefix}{next_seq:03d}"
            exists = db.query(Bug.id).filter(Bug.bug_id == candidate).first()
            if not exists:
                break
            next_seq += 1
        data["bug_id"] = candidate
    data = _clean_dev_request_fields(data)
    bug = Bug(**data)
    db.add(bug)
    db.commit()
    db.refresh(bug)
    return bug


def update_bug(db: Session, bug_id: str, data: dict) -> Optional[Bug]:
    bug = db.query(Bug).filter(Bug.bug_id == bug_id).first()
    if not bug:
        return None
    data = _clean_dev_request_fields(data)
    for key, value in data.items():
        if value is not None and hasattr(bug, key):
            setattr(bug, key, value)
    db.commit()
    db.refresh(bug)
    return bug


def delete_bug(db: Session, bug_id: str) -> bool:
    bug = db.query(Bug).filter(Bug.bug_id == bug_id).first()
    if not bug:
        return False
    db.delete(bug)
    db.commit()
    return True


# ============================================================
# 二次开发需求 CRUD
# ============================================================
def get_dev_requests_paginated(
    db: Session, page: int = 1, page_size: int = 20,
    keyword: Optional[str] = None, status: Optional[str] = None,
    priority: Optional[str] = None,
) -> Tuple[List[DevRequest], int]:
    query = db.query(DevRequest)
    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(or_(DevRequest.title.like(kw), DevRequest.request_id.like(kw)))
    # 数据库中 status/priority 存的是脏值（如 "|开发中|"，见 routers/mes.py 的 _req_to_dict 会剔除两端 | 和空格），
    # 用精确 == 会匹配不到 → 筛选结果为空、表现为“筛选不生效”；改用 LIKE 包含匹配兼容脏值。
    # （status/priority 的枚举值互不为子串，不会产生误匹配）
    if status:
        query = query.filter(DevRequest.status.like(f"%{status}%"))
    if priority:
        query = query.filter(DevRequest.priority.like(f"%{priority}%"))
    total = query.count()
    # 按「优先级（紧急情况）」排序：priority → 状态 → 期望交付日期 → id
    # ① 优先级：紧急 0 > 高 1 > 中 2 > 低 3 > 其它 9
    # ② 已完成状态（上线/关闭）下沉，未完成需求排前
    # ③ 期望交付日期：未设的放最后，其余越临近越优先（过期的排最前）
    # ④ 兜底：id 倒序（新创建在前）
    now = date.today()
    _done_statuses = ["上线", "关闭", "已上线", "已完成"]
    items = (
        query.order_by(
            # priority/status 可能是脏值（两端 | 和空格，见 _req_to_dict 清洗），排序里的
            # 精确 == / in_ 会匹配不到 → 用 LIKE 兼容，保证「优先级、已完成下沉」正常生效
            case(
                (DevRequest.priority.like("%紧急%"), 0),
                (DevRequest.priority.like("%高%"), 1),
                (DevRequest.priority.like("%中%"), 2),
                (DevRequest.priority.like("%低%"), 3),
                else_=9,
            ).asc(),
            case(
                (or_(*[DevRequest.status.like(f"%{s}%") for s in _done_statuses]), 1),
                else_=0,
            ).asc(),
            case(
                (DevRequest.expected_date.is_(None), 1),
                else_=0,
            ).asc(),
            func.datediff(text("day"), func.cast(now, DateType), DevRequest.expected_date).asc(),
            DevRequest.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def create_dev_request(db: Session, data: dict) -> DevRequest:
    data = _clean_dev_request_fields(data)
    req = DevRequest(**data)
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def update_dev_request(db: Session, request_id: str, data: dict) -> Optional[DevRequest]:
    req = db.query(DevRequest).filter(DevRequest.request_id == request_id).first()
    if not req:
        return None
    data = _clean_dev_request_fields(data)
    for key, value in data.items():
        if value is not None and hasattr(req, key):
            setattr(req, key, value)
    db.commit()
    db.refresh(req)
    return req


def delete_dev_request(db: Session, request_id: str) -> bool:
    req = db.query(DevRequest).filter(DevRequest.request_id == request_id).first()
    if not req:
        return False
    db.delete(req)
    db.commit()
    return True


# ============================================================
# 批量导入（通用）
# ============================================================
def batch_import_devices(db: Session, rows: List[dict]) -> int:
    """批量导入设备，使用 merge 避免主键冲突"""
    count = 0
    for row in rows:
        row = dict(row)
        if "status" in row:
            row["status"] = _clean_device_status(row["status"])
        existing = db.query(AoiAiDevice).filter(AoiAiDevice.device_id == row.get("device_id")).first()
        if existing:
            for k, v in row.items():
                if v is not None and hasattr(existing, k):
                    if k == "status":
                        v = _clean_device_status(v)
                    setattr(existing, k, v)
        else:
            db.add(AoiAiDevice(**row))
        count += 1
    db.commit()
    return count


def batch_import_weekly(db: Session, rows: List[dict]) -> int:
    count = 0
    for row in rows:
        # 显式计算 defect_count 和 yield_rate（数据库列非 Computed，需手动赋值）
        total = int(row.get("total_output") or 0)
        qualified = int(row.get("qualified_count") or 0)
        row["defect_count"] = total - qualified
        row["yield_rate"] = round(qualified / total * 100, 2) if total > 0 else 0

        existing = db.query(WeeklyProduction).filter(
            WeeklyProduction.year == row.get("year"),
            WeeklyProduction.week_number == row.get("week_number"),
            WeeklyProduction.production_line == row.get("production_line"),
            WeeklyProduction.project == row.get("project"),
        ).first()
        if existing:
            for k, v in row.items():
                if v is not None and k not in ("year", "week_number", "production_line", "project") and hasattr(existing, k):
                    setattr(existing, k, v)
        else:
            db.add(WeeklyProduction(**row))
        count += 1
    db.commit()
    return count


# ============================================================
# 项目 CRUD
# ============================================================
def get_projects(db: Session, include_inactive: bool = False) -> List[Project]:
    """获取所有项目列表"""
    query = db.query(Project)
    if not include_inactive:
        query = query.filter(Project.is_active == True)
    return query.order_by(Project.project_code).all()


def create_project(db: Session, data: dict) -> Project:
    project = Project(**data)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project_by_id(db: Session, project_id: int) -> Optional[Project]:
    return db.query(Project).filter(Project.id == project_id).first()


def update_project(db: Session, project_id: int, data: dict) -> Optional[Project]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None
    for key, value in data.items():
        if value is not None and hasattr(project, key):
            setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int) -> bool:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return False
    db.delete(project)
    db.commit()
    return True


# ============================================================
# ESOP 料号 CRUD
# ============================================================
def get_esop_parts_paginated(
    db: Session, page: int = 1, page_size: int = 20,
    keyword: Optional[str] = None, station_name: Optional[str] = None,
    process_name: Optional[str] = None, file_name: Optional[str] = None,
) -> Tuple[List[EsopPart], int]:
    query = db.query(EsopPart)
    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(
            or_(EsopPart.station_name.like(kw), EsopPart.process_name.like(kw), EsopPart.part_number.like(kw))
        )
    if station_name:
        query = query.filter(EsopPart.station_name == station_name)
    if process_name:
        query = query.filter(EsopPart.process_name.like(f"%{process_name}%"))
    if file_name:
        query = query.filter(EsopPart.file_name.like(f"%{file_name}%"))
    total = query.count()
    items = query.order_by(EsopPart.id.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def create_esop_part(db: Session, data: dict) -> EsopPart:
    part = EsopPart(**data)
    db.add(part)
    db.commit()
    db.refresh(part)
    return part


def update_esop_part(db: Session, part_id: int, data: dict) -> Optional[EsopPart]:
    part = db.query(EsopPart).filter(EsopPart.id == part_id).first()
    if not part:
        return None
    for key, value in data.items():
        if value is not None and hasattr(part, key):
            setattr(part, key, value)
    db.commit()
    db.refresh(part)
    return part


def delete_esop_part(db: Session, part_id: int) -> bool:
    part = db.query(EsopPart).filter(EsopPart.id == part_id).first()
    if not part:
        return False
    db.delete(part)
    db.commit()
    return True
