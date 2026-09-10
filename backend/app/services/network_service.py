import platform
import subprocess
from io import BytesIO
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from openpyxl import Workbook, load_workbook
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories import network_repository as repo
from app.core.crud import write_operation_log
from app.core.timeutil import beijing_now
from app.core.dingtalk import send_dingtalk
from app.models import Server, AgingRack, WifiAp, NetworkAlert, Setting


def _ping_device(ip: str) -> bool:
    if not ip or not isinstance(ip, str):
        return False
    ip = ip.strip()
    try:
        import socket
        socket.inet_aton(ip)
    except (OSError, ValueError):
        return False
    try:
        if platform.system().lower() == "windows":
            result = subprocess.run(["ping", "-n", "1", "-w", "2000", ip], capture_output=True, timeout=5, shell=False)
        else:
            result = subprocess.run(["ping", "-c", "1", "-W", "2", ip], capture_output=True, timeout=5, shell=False)
        return result.returncode == 0
    except Exception:
        return False


def _server_to_dict(d) -> Dict[str, Any]:
    return {
        "id": d.id, "server_id": d.server_id, "name": d.name,
        "production_line": d.production_line, "rack_location": d.rack_location,
        "ip_address": d.ip_address, "model": d.model, "os": d.os,
        "status": d.status, "cpu_usage": d.cpu_usage, "memory_usage": d.memory_usage,
        "disk_usage": d.disk_usage, "responsible_person": d.responsible_person,
        "last_check_time": d.last_check_time.isoformat() if d.last_check_time else None,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }


def _rack_to_dict(d) -> Dict[str, Any]:
    return {
        "id": d.id, "rack_id": d.rack_id, "name": d.name,
        "production_line": d.production_line, "location": d.location,
        "ip_address": d.ip_address, "total_slots": d.total_slots,
        "used_slots": d.used_slots, "status": d.status,
        "responsible_person": d.responsible_person,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }


def _ap_to_dict(d) -> Dict[str, Any]:
    return {
        "id": d.id, "ap_id": d.ap_id, "ssid": d.ssid,
        "production_line": d.production_line, "ip_address": d.ip_address,
        "mac_address": d.mac_address,
        "location": d.location, "channel": d.channel,
        "connected_devices": d.connected_devices, "status": d.status,
        "responsible_person": d.responsible_person,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }


# Servers

def list_servers(db: Session, page: int =1, page_size: int =20, keyword: Optional[str]=None, production_line: Optional[str]=None, status: Optional[str]=None):
    items, total = repo.list_servers(db, page=page, page_size=page_size, keyword=keyword, production_line=production_line, status=status)
    return ([_server_to_dict(d) for d in items], total)


def add_server(db: Session, data: dict, request, username: str):
    server = repo.create_server_repo(db, data)
    write_operation_log(db, username, "CREATE", "server", data.get("server_id"), f"新增服务器: {data.get('name')}", request)
    return _server_to_dict(server)


def edit_server(db: Session, server_id: str, data: dict, request, username: str):
    server = repo.update_server_repo(db, server_id, data)
    if not server:
        return None
    write_operation_log(db, username, "UPDATE", "server", server_id, "更新服务器", request)
    return _server_to_dict(server)


def remove_server(db: Session, server_id: str, request, username: str):
    ok = repo.delete_server_repo(db, server_id)
    if not ok:
        return False
    write_operation_log(db, username, "DELETE", "server", server_id, "删除服务器", request)
    return True


def _ping_and_update_all(db: Session):
    """对登记了 IP 的服务器 / 老化架 / AP 并发执行 Ping 并回写状态（一键检测使用）。

    探测（线程池并发，互不阻塞）与写库（主线程批量提交）解耦；
    返回 (stats, results)，results 为每台设备的检测明细，离线设备排前面。
    """
    stats = {"servers_online": 0, "servers_offline": 0,
             "racks_online": 0, "racks_offline": 0,
             "aps_online": 0, "aps_offline": 0}
    # (设备类型, ORM对象, 展示名, IP, 产线)
    targets = []
    for s in db.query(Server).all():
        if s.ip_address:
            targets.append(("服务器", s, s.name or s.server_id, s.ip_address, s.production_line))
    for r in db.query(AgingRack).all():
        if r.ip_address and r.status != "维护":
            targets.append(("老化架", r, r.name or r.rack_id, r.ip_address, r.production_line))
    for ap in db.query(WifiAp).all():
        if ap.ip_address:
            targets.append(("WiFi AP", ap, ap.ssid or ap.ap_id or ap.mac_address, ap.ip_address, ap.production_line))

    results: List[Dict[str, Any]] = []

    def _probe(target):
        device_type, obj, name, ip, line = target
        return target, _ping_device(ip)

    if targets:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(16, len(targets))) as pool:
            probed = list(pool.map(_probe, targets))
        for (device_type, obj, name, ip, line), alive in probed:
            if device_type == "服务器":
                obj.status = "在线" if alive else "离线"
                obj.last_check_time = beijing_now()
                stats["servers_online" if alive else "servers_offline"] += 1
                status_text = "在线" if alive else "离线"
            elif device_type == "老化架":
                obj.status = "在线" if alive else "离线"
                stats["racks_online" if alive else "racks_offline"] += 1
                status_text = "在线" if alive else "离线"
            else:
                obj.status = "在线" if alive else "离线"
                stats["aps_online" if alive else "aps_offline"] += 1
                status_text = "在线" if alive else "离线"
            results.append({
                "device_type": device_type,
                "device_name": name,
                "ip_address": ip,
                "production_line": line,
                "alive": alive,
                "status": status_text,
            })
    db.commit()
    results.sort(key=lambda x: (x["alive"], x["device_type"], x["device_name"] or ""))
    return stats, results


def check_all_servers(db: Session, request, username: str):
    """一键检测：服务器 + 老化架 + AP 全量 Ping（ping 通=在线，不通=离线），
    并自动对账告警/钉钉通知。返回每台设备的检测明细供看板实时展示。

    函数名保持兼容（路由 /network/servers/check-all 与前端 networkApi.checkAll 均调用它）。
    """
    stats, results = _ping_and_update_all(db)
    sync = sync_alerts(db, notify=True)
    online = stats["servers_online"] + stats["racks_online"] + stats["aps_online"]
    offline = stats["servers_offline"] + stats["racks_offline"] + stats["aps_offline"]
    write_operation_log(
        db, username, "UPDATE", "network", None,
        f"一键检测: 在线{online} 离线{offline} 新增告警{sync['new_alerts']}", request,
    )
    return {
        "online": online, "offline": offline, "total": len(results), **stats,
        "new_alerts": sync["new_alerts"], "resolved_alerts": sync["resolved_alerts"],
        "results": results,
        "checked_at": beijing_now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def import_servers(db: Session, rows: List[dict], request, username: str):
    count = 0
    for r in rows:
        if r.get("server_id"):
            repo.create_server_repo(db, r)
            count += 1
    write_operation_log(db, username, "CREATE", "server", None, f"批量导入 {count} 台服务器", request)
    return count


def export_servers_rows(db: Session, items):
    wb = Workbook(); ws = wb.active; ws.title = "服务器"
    ws.append(["服务器ID","名称","产线","机柜位置","IP","型号","OS","状态","CPU%","内存%","硬盘%","负责人","最后检测"])
    for d in items:
        ws.append([d.get("server_id"), d.get("name"), d.get("production_line"), d.get("rack_location"), d.get("ip_address"),
                    d.get("model"), d.get("os"), d.get("status"), d.get("cpu_usage"), d.get("memory_usage"), d.get("disk_usage"),
                    d.get("responsible_person"), str(d.get("last_check_time"))])
    output = BytesIO(); wb.save(output); output.seek(0)
    return output

# Aging racks

def list_aging_racks(db: Session, page: int =1, page_size: int =20, keyword: Optional[str]=None, production_line: Optional[str]=None, status: Optional[str]=None):
    items, total = repo.list_aging_racks(db, page=page, page_size=page_size, keyword=keyword, production_line=production_line, status=status)
    return ([_rack_to_dict(d) for d in items], total)


def add_aging_rack(db: Session, data: dict, request, username: str):
    rack = repo.create_aging_rack_repo(db, data)
    write_operation_log(db, username, "CREATE", "aging_rack", data.get("rack_id"), f"新增老化架: {data.get('name')}", request)
    return _rack_to_dict(rack)


def edit_aging_rack(db: Session, rack_id: str, data: dict, request, username: str):
    rack = repo.update_aging_rack_repo(db, rack_id, data)
    if not rack:
        return None
    write_operation_log(db, username, "UPDATE", "aging_rack", rack_id, "更新老化架", request)
    return _rack_to_dict(rack)


def remove_aging_rack(db: Session, rack_id: str, request, username: str):
    ok = repo.delete_aging_rack_repo(db, rack_id)
    if not ok:
        return False
    write_operation_log(db, username, "DELETE", "aging_rack", rack_id, "删除老化架", request)
    return True


def export_aging_racks_rows(db: Session, items):
    wb = Workbook(); ws = wb.active; ws.title = "老化架"
    ws.append(["老化架ID","名称","产线","位置","IP","总槽位","在用槽位","状态","负责人"])
    for d in items:
        ws.append([d.get("rack_id"), d.get("name"), d.get("production_line"), d.get("location"), d.get("ip_address"), d.get("total_slots"), d.get("used_slots"), d.get("status"), d.get("responsible_person")])
    output = BytesIO(); wb.save(output); output.seek(0)
    return output

# WiFi APs

def list_wifi_aps(db: Session, page: int =1, page_size: int =20, keyword: Optional[str]=None, production_line: Optional[str]=None, status: Optional[str]=None):
    items, total = repo.list_wifi_aps(db, page=page, page_size=page_size, keyword=keyword, production_line=production_line, status=status)
    return ([_ap_to_dict(d) for d in items], total)


def add_wifi_ap(db: Session, data: dict, request, username: str):
    ap = repo.create_wifi_ap_repo(db, data)
    write_operation_log(db, username, "CREATE", "wifi_ap", data.get("ap_id"), f"新增AP: {data.get('ssid')}", request)
    return _ap_to_dict(ap)


def edit_wifi_ap(db: Session, ap_id: str, data: dict, request, username: str):
    ap = repo.update_wifi_ap_repo(db, ap_id, data)
    if not ap:
        return None
    write_operation_log(db, username, "UPDATE", "wifi_ap", ap_id, "更新AP", request)
    return _ap_to_dict(ap)


def remove_wifi_ap(db: Session, ap_id: str, request, username: str):
    ok = repo.delete_wifi_ap_repo(db, ap_id)
    if not ok:
        return False
    write_operation_log(db, username, "DELETE", "wifi_ap", ap_id, "删除AP", request)
    return True


def export_wifi_aps_rows(db: Session, items):
    wb = Workbook(); ws = wb.active; ws.title = "WiFi AP"
    ws.append(["AP_ID","SSID","产线","IP","MAC","位置","信道","连接设备","状态","负责人"])
    for d in items:
        ws.append([d.get("ap_id"), d.get("ssid"), d.get("production_line"), d.get("ip_address"), d.get("mac_address"), d.get("location"), d.get("channel"), d.get("connected_devices"), d.get("status"), d.get("responsible_person")])
    output = BytesIO(); wb.save(output); output.seek(0)
    return output


# ============================================================
# 网络监控设置（钉钉机器人 / Ping 间隔，迁移自 wifi-monitor）
# ============================================================
DEFAULT_SETTINGS = {
    "dingtalk_webhook": "",
    "dingtalk_secret": "",
    "ping_interval": "60",
    # Syslog UDP 日志监听（迁移自 wifi-monitor/syslog_listener.py）
    "syslog_enabled": "0",            # 默认关闭：Windows 绑定 514 需管理员权限
    "syslog_port": "514",
    "syslog_keywords": "登录,退出,error,失败,攻击,非法,警告,warning,critical",
}

# Syslog 严重等级（不依赖关键词，命中即告警）
SYSLOG_ALERT_LEVELS = {"notice", "warning", "error", "critical", "emergency", "alert"}


def ensure_default_settings(db: Session) -> None:
    """启动时补齐默认设置项（幂等）。"""
    existing = {s.key for s in db.query(Setting).all()}
    missing = [Setting(key=k, value=v) for k, v in DEFAULT_SETTINGS.items() if k not in existing]
    if missing:
        db.add_all(missing)
        db.commit()


def get_settings(db: Session) -> Dict[str, Any]:
    ensure_default_settings(db)
    m = {s.key: s.value for s in db.query(Setting).all()}
    try:
        interval = int(m.get("ping_interval") or 60)
    except (TypeError, ValueError):
        interval = 60
    try:
        syslog_port = int(m.get("syslog_port") or 514)
    except (TypeError, ValueError):
        syslog_port = 514
    return {
        "dingtalk_webhook": m.get("dingtalk_webhook") or "",
        "dingtalk_secret": m.get("dingtalk_secret") or "",
        "ping_interval": interval,
        "syslog_enabled": (m.get("syslog_enabled") or "0") in ("1", "true", "True", "on"),
        "syslog_port": syslog_port,
        "syslog_keywords": m.get("syslog_keywords") or "",
    }


def update_settings(db: Session, data: dict, request, username: str) -> Dict[str, Any]:
    for k in ("dingtalk_webhook", "dingtalk_secret", "ping_interval",
              "syslog_port", "syslog_keywords"):
        if k not in data or data[k] is None:
            continue
        val = str(data[k]).strip()
        obj = db.query(Setting).filter(Setting.key == k).first()
        if obj:
            obj.value = val
        else:
            db.add(Setting(key=k, value=val))
    # Syslog 开关：兼容布尔 / "1" / "on"
    if data.get("syslog_enabled") is not None:
        v = data.get("syslog_enabled")
        enabled = v is True or str(v).strip().lower() in ("1", "true", "on")
        obj = db.query(Setting).filter(Setting.key == "syslog_enabled").first()
        if obj:
            obj.value = "1" if enabled else "0"
        else:
            db.add(Setting(key="syslog_enabled", value="1" if enabled else "0"))
    db.commit()
    write_operation_log(db, username, "UPDATE", "setting", None, "更新网络监控设置（钉钉/Ping间隔/Syslog）", request)
    return get_settings(db)


def test_dingtalk(db: Session) -> Tuple[bool, str]:
    cfg = get_settings(db)
    text = "【EmSmart 车间网络监控】钉钉机器人测试消息：通知配置成功！"
    return send_dingtalk(cfg["dingtalk_webhook"], cfg["dingtalk_secret"], text)


# ============================================================
# 网络告警（离线检测落表 + 钉钉通知 + 恢复自动关闭）
# ============================================================
def _alert_to_dict(a: NetworkAlert) -> Dict[str, Any]:
    return {
        "id": a.id, "device_type": a.device_type, "device_name": a.device_name,
        "device_key": a.device_key, "production_line": a.production_line,
        "ip_address": a.ip_address, "alert_type": a.alert_type, "level": a.level,
        "message": a.message, "status": a.status,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
    }


def list_alerts(db: Session, page: int = 1, page_size: int = 20, status: Optional[str] = None):
    q = db.query(NetworkAlert)
    if status:
        q = q.filter(NetworkAlert.status == status)
    total = q.count()
    rows = (q.order_by(NetworkAlert.id.desc())
             .offset((page - 1) * page_size).limit(page_size).all())
    return [_alert_to_dict(a) for a in rows], total


def open_alert_count(db: Session) -> int:
    return db.query(NetworkAlert).filter(NetworkAlert.status == "未处理").count()


def resolve_alert(db: Session, alert_id: int, request, username: str) -> bool:
    a = db.query(NetworkAlert).filter(NetworkAlert.id == alert_id).first()
    if not a:
        return False
    if a.status != "已处理":
        a.status = "已处理"
        a.resolved_at = beijing_now()
        db.commit()
        write_operation_log(db, username, "UPDATE", "network_alert", str(alert_id), "处理网络告警", request)
    return True


def resolve_all_alerts(db: Session, request, username: str) -> int:
    rows = db.query(NetworkAlert).filter(NetworkAlert.status == "未处理").all()
    now = beijing_now()
    for a in rows:
        a.status = "已处理"
        a.resolved_at = now
    db.commit()
    if rows:
        write_operation_log(db, username, "UPDATE", "network_alert", None, f"批量处理 {len(rows)} 条网络告警", request)
    return len(rows)


def _network_device_states(db: Session):
    """当前全部网络设备监控状态：(设备类型, 去重键, 名称, 产线, IP, 是否离线)。"""
    states = []
    for s in db.query(Server).all():
        states.append(("服务器", f"服务器:{s.server_id}", s.name, s.production_line, s.ip_address, s.status == "离线"))
    for r in db.query(AgingRack).all():
        states.append(("老化架", f"老化架:{r.rack_id}", r.name, r.production_line, r.ip_address, r.status == "离线"))
    for ap in db.query(WifiAp).all():
        states.append(("WiFi AP", f"WiFi AP:{ap.ap_id}", ap.ssid, ap.production_line, ap.ip_address, ap.status == "离线"))
    return states


def _device_alert_title(device_type: str, name: str, line: str, ip: str = "") -> str:
    """告警标题：产线+设备名拼接（如"8线下载WiFi异常报警！！！"）。
    WiFi AP 名称通常已含"WiFi"（如"下载WiFi"），不再追加设备类型后缀。"""
    if device_type == "未知设备" or not name:
        return f"未知设备（{ip}）异常报警！！！"
    head = f"{line or ''}{name}"
    if device_type == "WiFi AP":
        return f"{head}异常报警！！！"
    kind = {"老化架": "老化架", "服务器": "服务器"}.get(device_type, device_type)
    return f"{head} {kind}异常报警！！！"


_LEVEL_CN = {
    "emergency": "紧急", "alert": "警戒", "critical": "严重", "error": "错误",
    "warning": "警告", "warn": "警告", "notice": "通知", "info": "信息",
    "information": "信息", "informational": "信息", "debug": "调试",
}


def _level_cn(level: str) -> str:
    return _LEVEL_CN.get((level or "").strip().lower(), level or "警告")


def _format_alert_text(title: str, ts: str, level_cn: str, ip: str, detail: str) -> str:
    """统一钉钉文本格式（\\n 换行，钉钉 text 消息原生支持）。"""
    return (
        f"⚠️ {title}\n"
        f"时间：{ts}\n"
        f"等级：{level_cn}\n"
        f"来源IP：{ip or 'N/A'}\n"
        f"日志详情：{detail}"
    )


def _build_alert_text(device_type: str, name: str, line: str, ip: str, ts: str) -> str:
    """设备离线告警文案。"""
    title = _device_alert_title(device_type, name, line, ip)
    return _format_alert_text(title, ts, "严重", ip, "设备离线（Ping 不可达）")


def _build_recover_text(device_type: str, name: str, line: str, ip: str, ts: str) -> str:
    """设备恢复在线通知文案：与离线告警标题对齐，仅把「异常报警」改为「已恢复在线」。"""
    if device_type == "未知设备" or not name:
        title = f"未知设备（{ip}）已恢复在线✅"
    else:
        head = f"{line or ''}{name}"
        if device_type == "WiFi AP":
            title = f"{head}已恢复在线✅"
        else:
            kind = {"老化架": "老化架", "服务器": "服务器"}.get(device_type, device_type)
            title = f"{head} {kind}已恢复在线✅"
    return _format_alert_text(title, ts, "信息", ip, "设备 Ping 恢复可达，告警自动关闭")


# Syslog 日志告警内存去重：key="IP|消息" → 上次告警的 time.time()
_SYSLOG_DEDUP: Dict[str, float] = {}
_SYSLOG_DEDUP_WINDOW = 60.0


def _find_device_by_ip(db: Session, ip: str):
    """按 IP 匹配已登记设备，返回 (类型, 名称, 业务ID, 产线)；未登记返回 None。"""
    srv = db.query(Server).filter(Server.ip_address == ip).first()
    if srv:
        return "服务器", srv.name, srv.server_id, srv.production_line
    rack = db.query(AgingRack).filter(AgingRack.ip_address == ip).first()
    if rack:
        return "老化架", rack.name, rack.rack_id, rack.production_line
    ap = db.query(WifiAp).filter(WifiAp.ip_address == ip).first()
    if ap:
        return "WiFi AP", ap.ssid, ap.ap_id, ap.production_line
    return None


def record_syslog_alert(db: Session, src_ip: str, parsed: dict) -> bool:
    """Syslog 命中告警规则后的统一处理：去重 → 落 network_alerts → 推钉钉。

    与离线告警的区别：
    - alert_type="日志告警"，device_key 带 :syslog 后缀，不参与 Ping 恢复自动关闭；
    - 同一来源 IP + 相同消息 60 秒内只告警一次（防止日志刷屏轰炸群聊）。
    """
    import time
    message = (parsed.get("message") or parsed.get("raw") or "").strip()
    if not message:
        return False
    message = message[:500]
    level = (parsed.get("level") or "warning").strip() or "warning"
    ts = parsed.get("timestamp") or beijing_now().strftime("%Y-%m-%d %H:%M:%S")

    dedup_key = f"{src_ip}|{message}"
    now_ts = time.time()
    last = _SYSLOG_DEDUP.get(dedup_key)
    if last is not None and now_ts - last < _SYSLOG_DEDUP_WINDOW:
        return False
    _SYSLOG_DEDUP[dedup_key] = now_ts
    if len(_SYSLOG_DEDUP) > 1000:   # 简单清理，避免长期运行内存膨胀
        for k in [k for k, v in _SYSLOG_DEDUP.items() if now_ts - v > _SYSLOG_DEDUP_WINDOW]:
            _SYSLOG_DEDUP.pop(k, None)

    dev = _find_device_by_ip(db, src_ip)
    if dev:
        dtype, name, biz_key, line = dev
    else:
        dtype, name, biz_key, line = "未知设备", src_ip, src_ip, ""

    sev = "critical" if level.lower() in ("error", "critical", "emergency", "alert") else "warning"
    alert = NetworkAlert(
        device_type=dtype, device_name=name,
        device_key=f"{dtype}:{biz_key}:syslog",
        production_line=line or None, ip_address=src_ip,
        alert_type="日志告警", level=sev,
        message=f"[{level}] {message}",
    )
    db.add(alert)
    db.commit()

    cfg = get_settings(db)
    if cfg.get("dingtalk_webhook"):
        title = _device_alert_title(dtype, name, line, src_ip)
        # 日志详情优先转发完整原始报文（含 <PRI> 头），无原始报文时用截断后的正文
        detail = (parsed.get("raw") or message).strip()
        text = _format_alert_text(title, ts, _level_cn(level), src_ip, detail)
        try:
            send_dingtalk(cfg["dingtalk_webhook"], cfg["dingtalk_secret"], text)
        except Exception:
            pass
    return True


def sync_alerts(db: Session, notify: bool = True) -> Dict[str, int]:
    """按设备当前状态对账告警表：

    - 新离线且无未处理告警 → 落库一条 critical 告警，并按设置推送钉钉（同设备去重，不重复轰炸）；
    - 恢复在线且存在未处理告警 → 自动标记已处理；
    - 未登记 IP 的设备不参与监控告警。
    """
    cfg = get_settings(db) if notify else None
    open_map = {
        a.device_key: a
        for a in db.query(NetworkAlert).filter(NetworkAlert.status == "未处理").all()
    }
    new_count = resolved_count = 0
    now = beijing_now()
    ts = now.strftime("%Y-%m-%d %H:%M:%S")
    for device_type, key, name, line, ip, offline in _network_device_states(db):
        if not ip:
            continue
        if offline:
            if key not in open_map:
                db.add(NetworkAlert(
                    device_type=device_type, device_name=name, device_key=key,
                    production_line=line, ip_address=ip,
                    alert_type="离线告警", level="critical",
                    message=f"{device_type} [{name}] Ping 不可达，判定离线（IP：{ip}）",
                ))
                new_count += 1
                if cfg and cfg.get("dingtalk_webhook"):
                    send_dingtalk(cfg["dingtalk_webhook"], cfg["dingtalk_secret"],
                                  _build_alert_text(device_type, name, line, ip, ts))
        elif key in open_map:
            # 设备恢复在线：自动关闭未处理告警，并推送「恢复在线」钉钉通知
            # （否则用户体感是「ping 通了也不通知」，必须先点开告警抽屉刷新才感知到）
            open_map[key].status = "已处理"
            open_map[key].resolved_at = now
            resolved_count += 1
            if cfg and cfg.get("dingtalk_webhook"):
                try:
                    send_dingtalk(cfg["dingtalk_webhook"], cfg["dingtalk_secret"],
                                  _build_recover_text(device_type, name, line, ip, ts))
                except Exception:
                    pass
    if new_count or resolved_count:
        db.commit()
    return {"new_alerts": new_count, "resolved_alerts": resolved_count}


def monitor_tick(db: Session) -> int:
    """后台定时任务每轮调用：Ping 老化架/AP（服务器由 server_health 守护任务检测），
    对账告警并推送钉钉，返回设置中的下一轮检测间隔（秒）。
    每轮无论设备状态是否变化都写入 last_monitor_tick 时间戳，供看板确认巡检在跑。
    """
    for r in db.query(AgingRack).all():
        if r.ip_address and r.status != "维护":
            r.status = "在线" if _ping_device(r.ip_address) else "离线"
    for ap in db.query(WifiAp).all():
        if ap.ip_address and ap.status != "维护":
            ap.status = "在线" if _ping_device(ap.ip_address) else "离线"
    tick_row = db.query(Setting).filter(Setting.key == "last_monitor_tick").first()
    if tick_row:
        tick_row.value = beijing_now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        db.add(Setting(key="last_monitor_tick", value=beijing_now().strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    sync_alerts(db, notify=True)
    return get_settings(db)["ping_interval"]