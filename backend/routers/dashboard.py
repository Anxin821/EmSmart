"""
智能工厂工作任务管理平台 - 数据看板聚合 API
提供各模块看板所需的数据聚合查询
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case, extract, and_, or_
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from core.database import get_db
from core.auth import get_current_user
from schemas import ApiResponse
from models import (
    AoiAiDevice, WeeklyProduction, MonthlyProduction,
    Server, AgingRack, WifiAp,
    WorkOrder, Bug, DevRequest,
)

router = APIRouter(prefix="/dashboard", tags=["数据看板"])


# ============================================================
# AOI&AI 看板 API
# ============================================================
@router.get("/device-summary")
def device_summary(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    设备状态汇总：总数/正常/故障/保养中（前端 stat-card 平铺用）
    """
    total = db.query(func.count(AoiAiDevice.id)).scalar() or 0
    normal_count = db.query(func.count(AoiAiDevice.id)).filter(AoiAiDevice.status == "正常").scalar() or 0
    fault_count = db.query(func.count(AoiAiDevice.id)).filter(AoiAiDevice.status == "故障").scalar() or 0
    maintenance_count = db.query(func.count(AoiAiDevice.id)).filter(AoiAiDevice.status == "保养中").scalar() or 0

    # 按产线明细（供后续扩展，暂不破坏现有 frontend）
    results = (
        db.query(AoiAiDevice.production_line, AoiAiDevice.status, func.count(AoiAiDevice.id))
        .group_by(AoiAiDevice.production_line, AoiAiDevice.status).all()
    )
    lines_map = {}
    for line, status, cnt in results:
        lines_map.setdefault(line, {"line": line, "total": 0, "normal": 0, "fault": 0, "maintenance": 0})
        lines_map[line]["total"] += cnt
        if status == "正常": lines_map[line]["normal"] = cnt
        elif status == "故障": lines_map[line]["fault"] = cnt
        elif status == "保养中": lines_map[line]["maintenance"] = cnt

    return ApiResponse(data={
        "total": total,
        "normal_count": normal_count,
        "fault_count": fault_count,
        "maintenance_count": maintenance_count,
        "lines": list(lines_map.values()),
    })


@router.get("/production-trend")
def production_trend(
    mode: str = Query("weekly", description="weekly 或 monthly"),
    production_line: Optional[str] = None,
    project: Optional[str] = None,
    limit: int = Query(20, ge=1, le=52),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    产量/直通率趋势数据（双Y轴）
    mode=weekly: 返回最近N周数据，按年份+周号分组
    mode=monthly: 返回最近N月数据，按年份+月份分组
    - 若不指定产线/项目，则按产线+项目聚合
    """
    # 查询所有数据，前端可按项目分层展示
    if mode == "weekly":
        query = db.query(
            WeeklyProduction.year,
            WeeklyProduction.week_number,
            WeeklyProduction.production_line,
            WeeklyProduction.project,
            func.sum(WeeklyProduction.total_output).label("total"),
            func.avg(WeeklyProduction.yield_rate).label("yield"),
        ).group_by(
            WeeklyProduction.year, WeeklyProduction.week_number,
            WeeklyProduction.production_line, WeeklyProduction.project,
        ).order_by(
            WeeklyProduction.year.desc(), WeeklyProduction.week_number.desc()
        )
        if production_line:
            query = query.filter(WeeklyProduction.production_line == production_line)
        if project:
            query = query.filter(WeeklyProduction.project == project)
        results = query.limit(limit * 3).all()  # 3 projects per line

        # 转换为前端可用格式
        data = {}
        for year, week, line, proj, total, yield_rate in results:
            key = f"{year}W{week}"
            if key not in data:
                data[key] = {"period": key, "year": year, "week": week}
            label = f"{line}-{proj}"
            data[key][f"output_{label}"] = total or 0
            data[key][f"yield_{label}"] = round(float(yield_rate or 0), 2)

        return ApiResponse(data={
            "periods": sorted(data.values(), key=lambda x: (x["year"], x["week"])),
            "mode": "weekly",
        })

    else:
        query = db.query(
            MonthlyProduction.year,
            MonthlyProduction.month,
            MonthlyProduction.production_line,
            MonthlyProduction.project,
            func.sum(MonthlyProduction.monthly_total_output).label("total"),
            func.avg(MonthlyProduction.monthly_yield_rate).label("yield"),
        ).group_by(
            MonthlyProduction.year, MonthlyProduction.month,
            MonthlyProduction.production_line, MonthlyProduction.project,
        ).order_by(
            MonthlyProduction.year.desc(), MonthlyProduction.month.desc()
        )
        if production_line:
            query = query.filter(MonthlyProduction.production_line == production_line)
        if project:
            query = query.filter(MonthlyProduction.project == project)
        results = query.limit(limit * 3).all()

        data = {}
        for year, month, line, proj, total, yield_rate in results:
            key = f"{year}M{month}"
            if key not in data:
                data[key] = {"period": key, "year": year, "month": month}
            label = f"{line}-{proj}"
            data[key][f"output_{label}"] = total or 0
            data[key][f"yield_{label}"] = round(float(yield_rate or 0), 2)

        return ApiResponse(data={
            "periods": sorted(data.values(), key=lambda x: (x["year"], x["month"])),
            "mode": "monthly",
        })


@router.get("/yield-compare")
def yield_compare(
    mode: str = Query("weekly", description="weekly 或 monthly"),
    production_line: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    项目合格率对比数据（用于柱状图），动态从 Project 表获取项目列表
    """
    from models import Project
    projects = [p.project_code for p in db.query(Project).filter(Project.is_active == True).order_by(Project.id).all()]
    if not projects:
        projects = ["A", "B", "C"]  # 兜底

    if mode == "weekly":
        query = (
            db.query(
                WeeklyProduction.project,
                func.sum(WeeklyProduction.total_output).label("total"),
                func.sum(WeeklyProduction.qualified_count).label("qualified"),
            )
        )
        if production_line:
            query = query.filter(WeeklyProduction.production_line == production_line)
        results = query.group_by(WeeklyProduction.project).all()
    else:
        query = (
            db.query(
                MonthlyProduction.project,
                func.sum(MonthlyProduction.monthly_total_output).label("total"),
                func.sum(MonthlyProduction.monthly_qualified_count).label("qualified"),
            )
        )
        if production_line:
            query = query.filter(MonthlyProduction.production_line == production_line)
        results = query.group_by(MonthlyProduction.project).all()

    result_map = {r[0]: {"total": r[1] or 0, "qualified": r[2] or 0} for r in results}
    compare_data = []
    for p in projects:
        d = result_map.get(p, {"total": 0, "qualified": 0})
        yield_rate = round(d["qualified"] / d["total"] * 100, 2) if d["total"] > 0 else 0
        compare_data.append({"project": p, "total": d["total"], "qualified": d["qualified"], "yield_rate": yield_rate})

    return ApiResponse(data=compare_data)


@router.get("/recent-table")
def recent_table(
    mode: str = Query("weekly", description="weekly 或 monthly"),
    production_line: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    近4周/4月数据快照表格 — 以当前日期为基准向前4个周期
    """
    from datetime import date, timedelta

    if mode == "weekly":
        # 当前ISO周及前3周
        today = date.today()
        cy, cw, _ = today.isocalendar()
        weeks = []
        for i in range(4):
            d = today - timedelta(weeks=i)
            wy, ww, _ = d.isocalendar()
            weeks.append((wy, ww))
        conditions = [and_(WeeklyProduction.year == wy, WeeklyProduction.week_number == ww) for wy, ww in weeks]

        results = (
            db.query(
                WeeklyProduction.production_line,
                WeeklyProduction.project,
                func.sum(WeeklyProduction.total_output),
                func.sum(WeeklyProduction.qualified_count),
            )
            .filter(or_(*conditions))
            .group_by(WeeklyProduction.production_line, WeeklyProduction.project)
            .order_by(WeeklyProduction.production_line, WeeklyProduction.project)
            .all()
        )
        items = [{
            "production_line": ln or "",
            "project": pj or "",
            "total_output": int(t or 0),
            "qualified_count": int(q or 0),
            "yield_rate": round(int(q or 0) / int(t or 0) * 100, 2) if (t or 0) > 0 else 0,
        } for ln, pj, t, q in results]
        items.sort(key=lambda x: x["yield_rate"], reverse=True)
        items = items[:8]
        return ApiResponse(data=items)
    else:
        # 当前月及前3月（跨年处理）
        today = date.today()
        months = []
        for i in range(4):
            yr = today.year
            mo = today.month - i
            while mo <= 0:
                yr -= 1
                mo += 12
            months.append((yr, mo))
        conditions = [and_(MonthlyProduction.year == yr, MonthlyProduction.month == mo) for yr, mo in months]

        results = (
            db.query(
                MonthlyProduction.production_line,
                MonthlyProduction.project,
                func.sum(MonthlyProduction.monthly_total_output),
                func.sum(MonthlyProduction.monthly_qualified_count),
            )
            .filter(or_(*conditions))
            .group_by(MonthlyProduction.production_line, MonthlyProduction.project)
            .order_by(MonthlyProduction.production_line, MonthlyProduction.project)
            .all()
        )
        items = [{
            "production_line": ln or "",
            "project": pj or "",
            "total_output": int(t or 0),
            "qualified_count": int(q or 0),
            "yield_rate": round(int(q or 0) / int(t or 0) * 100, 2) if (t or 0) > 0 else 0,
        } for ln, pj, t, q in results]
        items.sort(key=lambda x: x["yield_rate"], reverse=True)
        items = items[:8]
        return ApiResponse(data=items)


@router.get("/aoi-devices-location")
def aoi_devices_location(
    production_line: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取设备位置信息（用于产线设备位置示意图）
    """
    query = db.query(AoiAiDevice)
    if production_line:
        query = query.filter(AoiAiDevice.production_line == production_line)
    devices = query.all()
    return ApiResponse(data=[{
        "device_id": d.device_id, "name": d.name, "device_type": d.device_type,
        "production_line": d.production_line, "location": d.location,
        "status": d.status, "ip_address": d.ip_address, "responsible_person": d.responsible_person,
    } for d in devices])


# ============================================================
# 车间网络看板 API
# ============================================================
@router.get("/network-summary")
def network_summary(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    按线体聚合网络设备状态
    """
    # 服务器按产线聚合
    server_data = (
        db.query(Server.production_line, Server.status, func.count(Server.id))
        .group_by(Server.production_line, Server.status).all()
    )
    aging_data = (
        db.query(AgingRack.production_line, AgingRack.status, func.count(AgingRack.id))
        .group_by(AgingRack.production_line, AgingRack.status).all()
    )
    ap_data = (
        db.query(WifiAp.production_line, WifiAp.status, func.count(WifiAp.id))
        .group_by(WifiAp.production_line, WifiAp.status).all()
    )

    # 合并为按线体的结构
    lines = ["1线", "2线", "3线", "4线", "5线", "6线", "7线", "8线"]
    result = {}
    for line in lines:
        result[line] = {
            "line": line,
            "servers": {"total": 0, "online": 0, "offline": 0, "maintenance": 0},
            "aging_racks": {"total": 0, "normal": 0, "fault": 0},
            "wifi_aps": {"total": 0, "online": 0, "offline": 0},
        }

    for line, status, cnt in server_data:
        if line in result:
            result[line]["servers"]["total"] += cnt
            if status == "在线":
                result[line]["servers"]["online"] += cnt
            elif status == "离线":
                result[line]["servers"]["offline"] += cnt
            elif status == "维护":
                result[line]["servers"]["maintenance"] += cnt

    for line, status, cnt in aging_data:
        if line in result:
            result[line]["aging_racks"]["total"] += cnt
            if status == "正常":
                result[line]["aging_racks"]["normal"] += cnt
            else:
                result[line]["aging_racks"]["fault"] += cnt

    for line, status, cnt in ap_data:
        if line in result:
            result[line]["wifi_aps"]["total"] += cnt
            if status == "在线":
                result[line]["wifi_aps"]["online"] += cnt
            elif status == "离线":
                result[line]["wifi_aps"]["offline"] += cnt

    total_online = sum(v["servers"]["online"] + v["aging_racks"]["normal"] + v["wifi_aps"]["online"] for v in result.values())
    total_all = sum(v["servers"]["total"] + v["aging_racks"]["total"] + v["wifi_aps"]["total"] for v in result.values())

    return ApiResponse(data={
        "lines": list(result.values()),
        "global_rate": round(total_online / total_all * 100, 2) if total_all > 0 else 100,
        "total_devices": total_all,
        "online_devices": total_online,
    })


@router.get("/network-devices-detail")
def network_devices_detail(
    production_line: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取所有网络设备详情（用于拓扑图绘制）
    """
    servers = db.query(Server).all()
    aging = db.query(AgingRack).all()
    aps = db.query(WifiAp).all()

    if production_line:
        servers = [s for s in servers if s.production_line == production_line]
        aging = [a for a in aging if a.production_line == production_line]
        aps = [a for a in aps if a.production_line == production_line]

    return ApiResponse(data={
        "servers": [_srv_dict(s) for s in servers],
        "aging_racks": [_rack_dict(a) for a in aging],
        "wifi_aps": [_ap_dict(a) for a in aps],
    })


def _srv_dict(s):
    return {"id": s.server_id, "name": s.name, "line": s.production_line,
            "ip": s.ip_address, "status": s.status, "rack": s.rack_location}


def _rack_dict(a):
    return {"id": a.rack_id, "name": a.name, "line": a.production_line,
            "status": a.status, "slots": f"{a.used_slots}/{a.total_slots}"}


def _ap_dict(a):
    return {"id": a.ap_id, "ssid": a.ssid, "line": a.production_line,
            "ip": a.ip_address, "status": a.status, "location": a.location}


# ============================================================
# 月份产量 & 直通率趋势图
# ============================================================
@router.get("/monthly-output-trend")
def monthly_output_trend(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """当年每月总产量柱状图数据"""
    from models import MonthlyProduction
    import datetime
    if not year:
        year = datetime.date.today().year
    results = (
        db.query(
            MonthlyProduction.month,
            func.sum(MonthlyProduction.monthly_total_output),
        )
        .filter(MonthlyProduction.year == year)
        .group_by(MonthlyProduction.month)
        .order_by(MonthlyProduction.month)
        .all()
    )
    data = [{"month": m, "total_output": int(t or 0)} for m, t in results]
    return ApiResponse(data=data)


@router.get("/monthly-yield-trend")
def monthly_yield_trend(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """当年每月总直通率折线图数据"""
    from models import MonthlyProduction
    import datetime
    if not year:
        year = datetime.date.today().year
    results = (
        db.query(
            MonthlyProduction.month,
            func.sum(MonthlyProduction.monthly_total_output),
            func.sum(MonthlyProduction.monthly_qualified_count),
        )
        .filter(MonthlyProduction.year == year)
        .group_by(MonthlyProduction.month)
        .order_by(MonthlyProduction.month)
        .all()
    )
    data = []
    for month, total, qualified in results:
        t = int(total or 0)
        q = int(qualified or 0)
        y = round(q / t * 100, 2) if t > 0 else 0
        data.append({"month": month, "yield_rate": y})
    return ApiResponse(data=data)


# ============================================================
# MES 系统看板 API
# ============================================================
@router.get("/mes-summary")
def mes_summary(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    MES 概览统计
    """
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 工单统计
    order_status = (
        db.query(WorkOrder.status, func.count(WorkOrder.id))
        .group_by(WorkOrder.status).all()
    )
    order_total = sum(c for _, c in order_status)
    overdue_orders = (
        db.query(func.count(WorkOrder.id))
        .filter(WorkOrder.status.in_(["待开始", "进行中"]), WorkOrder.planned_end < now)
        .scalar() or 0
    )

    # BUG统计
    bug_status = (
        db.query(Bug.status, func.count(Bug.id))
        .group_by(Bug.status).all()
    )
    bug_severity = (
        db.query(Bug.severity, func.count(Bug.id))
        .group_by(Bug.severity).all()
    )
    bug_monthly_new = (
        db.query(func.count(Bug.id))
        .filter(Bug.created_date >= month_start.date())
        .scalar() or 0
    )
    bug_monthly_closed = (
        db.query(func.count(Bug.id))
        .filter(Bug.status == "关闭", Bug.updated_at >= month_start)
        .scalar() or 0
    )

    # 需求统计
    req_status = (
        db.query(DevRequest.status, func.count(DevRequest.id))
        .group_by(DevRequest.status).all()
    )

    return ApiResponse(data={
        "orders": {
            "total": order_total,
            "by_status": {s: c for s, c in order_status},
            "overdue": overdue_orders,
        },
        "bugs": {
            "by_status": {s: c for s, c in bug_status},
            "by_severity": {s: c for s, c in bug_severity},
            "monthly_new": bug_monthly_new,
            "monthly_closed": bug_monthly_closed,
        },
        "dev_requests": {
            "by_status": {s: c for s, c in req_status},
        },
    })


@router.get("/bug-burndown")
def bug_burndown(
    months: int = Query(3, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    BUG 燃尽图数据
    返回每月新建/关闭/累计未关闭数
    """
    now = datetime.utcnow()
    data = []
    for i in range(months - 1, -1, -1):
        target = now.replace(day=1) - timedelta(days=i * 31)
        target = target.replace(day=1)
        next_month = (target.replace(day=28) + timedelta(days=4)).replace(day=1)
        month_label = f"{target.year}M{target.month}"

        new_count = (
            db.query(func.count(Bug.id))
            .filter(Bug.created_date >= target.date(), Bug.created_date < next_month.date())
            .scalar() or 0
        )
        closed_count = (
            db.query(func.count(Bug.id))
            .filter(Bug.status == "关闭", Bug.updated_at >= target, Bug.updated_at < next_month)
            .scalar() or 0
        )
        # 月末累计未关闭 = 月初未关闭 + 新建 - 关闭（简化逻辑）
        # 这里直接用截止当月创建的未关闭数
        outstanding = (
            db.query(func.count(Bug.id))
            .filter(Bug.created_date < next_month.date(), Bug.status != "关闭")
            .scalar() or 0
        )
        data.append({
            "month": month_label, "new": new_count,
            "closed": closed_count, "outstanding": outstanding,
        })

    return ApiResponse(data=data)


@router.get("/dev-request-gantt")
def dev_request_gantt(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    二次开发需求甘特图数据（简化版）
    """
    requests = (
        db.query(DevRequest)
        .filter(DevRequest.status.in_(["收集", "评估", "开发中", "测试"]))
        .order_by(DevRequest.priority, DevRequest.expected_date)
        .all()
    )
    data = []
    for r in requests:
        data.append({
            "id": r.request_id, "title": r.title, "priority": r.priority,
            "status": r.status, "progress": r.progress,
            "expected_date": r.expected_date.isoformat() if r.expected_date else None,
            "responsible_person": r.responsible_person,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return ApiResponse(data=data)


# ============================================================
# 车间网络看板（综合数据）
# ============================================================
@router.get("/network")
def network_dashboard(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    车间网络看板综合数据：
    - 全局在线/离线设备数 + 在线率
    - 按线体拓扑（服务器/老化架/AP 明细）
    - 离线设备列表
    """
    lines = ["1线", "2线", "3线", "4线", "5线", "6线", "7线", "8线"]

    servers = db.query(Server).all()
    aging_racks = db.query(AgingRack).all()
    wifi_aps = db.query(WifiAp).all()

    # ---- 按线体聚合 ----
    line_map = {}
    for line in lines:
        line_map[line] = {
            "line": line,
            "servers": [],
            "aging_racks": [],
            "wifi_aps": [],
        }

    for s in servers:
        ln = s.production_line or ""
        if ln in line_map:
            line_map[ln]["servers"].append({
                "id": s.server_id,
                "name": s.name,
                "status": s.status,
                "ip": s.ip_address,
                "rack": s.rack_location,
                "os": s.os,
            })

    for a in aging_racks:
        ln = a.production_line or ""
        if ln in line_map:
            line_map[ln]["aging_racks"].append({
                "id": a.rack_id,
                "name": a.name,
                "status": a.status,
                "slots": f"{a.used_slots}/{a.total_slots}" if a.total_slots else "",
                "ip": a.ip_address,
            })

    for ap in wifi_aps:
        ln = ap.production_line or ""
        if ln in line_map:
            line_map[ln]["wifi_aps"].append({
                "id": ap.ap_id,
                "ssid": ap.ssid,
                "status": ap.status,
                "ip": ap.ip_address,
                "channel": ap.channel,
                "connected_devices": ap.connected_devices,
            })

    # ---- 全局统计 ----
    online_servers = sum(1 for s in servers if s.status == "在线")
    offline_servers = sum(1 for s in servers if s.status == "离线")
    online_aging = sum(1 for a in aging_racks if a.status == "正常")
    offline_aging = sum(1 for a in aging_racks if a.status != "正常")
    online_aps = sum(1 for ap in wifi_aps if ap.status == "在线")
    offline_aps = sum(1 for ap in wifi_aps if ap.status == "离线")

    online_total = online_servers + online_aging + online_aps
    offline_total = offline_servers + offline_aging + offline_aps
    total_devices = len(servers) + len(aging_racks) + len(wifi_aps)
    online_rate = round(online_total / total_devices * 100, 1) if total_devices > 0 else 100.0

    # ---- 离线设备列表 ----
    offline_list = []
    for s in servers:
        if s.status == "离线":
            offline_list.append({
                "type": "服务器",
                "name": s.name,
                "line": s.production_line,
                "status": s.status,
                "ip": s.ip_address,
            })
    for a in aging_racks:
        if a.status != "正常":
            offline_list.append({
                "type": "老化架",
                "name": a.name,
                "line": a.production_line,
                "status": a.status,
                "ip": a.ip_address,
            })
    for ap in wifi_aps:
        if ap.status == "离线":
            offline_list.append({
                "type": "WiFi AP",
                "name": ap.ssid,
                "line": ap.production_line,
                "status": ap.status,
                "ip": ap.ip_address,
            })

    return ApiResponse(data={
        "online_devices": online_total,
        "offline_devices": offline_total,
        "total_devices": total_devices,
        "online_rate": online_rate,
        "lines": list(line_map.values()),
        "offline_list": offline_list,
    })
