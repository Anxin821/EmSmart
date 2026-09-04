"""schemas 通用基类与共享符号。"""
from datetime import date, datetime
from typing import Optional, Any
from pydantic import BaseModel

__all__ = ["date", "datetime", "Optional", "Any", "BaseModel"]


class ApiResponse(BaseModel):
    """统一 API 响应格式"""
    code: int = 200
    message: str = "success"
    data: Any = None


class PaginatedData(BaseModel):
    """分页数据"""
    total: int
    page: int
    page_size: int
    items: list
    extra: Optional[dict] = None
