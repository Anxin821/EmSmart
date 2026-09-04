"""ESOP 料号 Schema。"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EsopPartBase(BaseModel):
    station_name: str
    process_name: str
    part_number: str
    file_name: Optional[str] = None


class EsopPartCreate(EsopPartBase):
    pass


class EsopPartUpdate(BaseModel):
    station_name: Optional[str] = None
    process_name: Optional[str] = None
    part_number: Optional[str] = None
    file_name: Optional[str] = None


class EsopPartOut(EsopPartBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
