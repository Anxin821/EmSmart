from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas import ApiResponse
from app.services import dashboard_service as service

router = APIRouter(prefix="/dashboard", tags=["数据看板"])


@router.get("/device-summary")
def device_summary(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return ApiResponse(data=service.device_summary(db))


@router.get("/production-trend")
def production_trend(
    mode: str = Query("weekly", description="weekly 或 monthly"),
    production_line: Optional[str] = None,
    project: Optional[str] = None,
    limit: int = Query(20, ge=1, le=52),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(data=service.production_trend(db, mode=mode, production_line=production_line, project=project, limit=limit))


@router.get("/yield-compare")
def yield_compare(
    mode: str = Query("weekly", description="weekly 或 monthly"),
    production_line: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(data=service.yield_compare(db, mode=mode, production_line=production_line))


@router.get("/recent-table")
def recent_table(
    mode: str = Query("weekly", description="weekly 或 monthly"),
    production_line: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(data=service.recent_table(db, mode=mode, production_line=production_line))


@router.get("/aoi-devices-location")
def aoi_devices_location(
    production_line: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(data=service.aoi_devices_location(db, production_line=production_line))


@router.get("/network-summary")
def network_summary(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return ApiResponse(data=service.network_summary(db))


@router.get("/network-devices-detail")
def network_devices_detail(
    production_line: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(data=service.network_devices_detail(db, production_line=production_line))


@router.get("/monthly-output-trend")
def monthly_output_trend(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(data=service.monthly_output_trend(db, year=year))


@router.get("/monthly-yield-trend")
def monthly_yield_trend(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(data=service.monthly_yield_trend(db, year=year))


@router.get("/mes-summary")
def mes_summary(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return ApiResponse(data=service.mes_summary(db))


@router.get("/bug-burndown")
def bug_burndown(
    months: int = Query(3, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(data=service.bug_burndown(db, months=months))


@router.get("/dev-request-gantt")
def dev_request_gantt(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(data=service.dev_request_gantt(db))


@router.get("/network")
def network_dashboard(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return ApiResponse(data=service.network_dashboard(db))
