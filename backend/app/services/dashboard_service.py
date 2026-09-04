from typing import Optional, Any, Dict, List
from sqlalchemy.orm import Session

from app.repositories import dashboard_repository as repo


def device_summary(db: Session) -> Dict[str, Any]:
    return repo.device_summary(db)


def production_trend(db: Session, mode: str = "weekly", production_line: Optional[str] = None, project: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
    return repo.production_trend(db, mode=mode, production_line=production_line, project=project, limit=limit)


def yield_compare(db: Session, mode: str = "weekly", production_line: Optional[str] = None) -> List[Dict[str, Any]]:
    return repo.yield_compare(db, mode=mode, production_line=production_line)


def recent_table(db: Session, mode: str = "weekly", production_line: Optional[str] = None) -> List[Dict[str, Any]]:
    return repo.recent_table(db, mode=mode, production_line=production_line)


def aoi_devices_location(db: Session, production_line: Optional[str] = None) -> List[Dict[str, Any]]:
    return repo.aoi_devices_location(db, production_line=production_line)


def network_summary(db: Session) -> Dict[str, Any]:
    return repo.network_summary(db)


def network_devices_detail(db: Session, production_line: Optional[str] = None) -> Dict[str, Any]:
    return repo.network_devices_detail(db, production_line=production_line)


def monthly_output_trend(db: Session, year: Optional[int] = None) -> List[Dict[str, Any]]:
    return repo.monthly_output_trend(db, year=year)


def monthly_yield_trend(db: Session, year: Optional[int] = None) -> List[Dict[str, Any]]:
    return repo.monthly_yield_trend(db, year=year)


def mes_summary(db: Session) -> Dict[str, Any]:
    return repo.mes_summary(db)


def bug_burndown(db: Session, months: int = 3) -> List[Dict[str, Any]]:
    return repo.bug_burndown(db, months=months)


def dev_request_gantt(db: Session) -> List[Dict[str, Any]]:
    return repo.dev_request_gantt(db)


def network_dashboard(db: Session) -> Dict[str, Any]:
    return repo.network_dashboard(db)
