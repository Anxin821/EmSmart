"""
ORM 基类。所有模型从这里的 Base 继承，便于 Base.metadata.create_all() 统一建表。
"""
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, Boolean, Computed  # 子模块统一复用


__all__ = [
    "Base",
    "Column",
    "Integer",
    "String",
    "Float",
    "Date",
    "DateTime",
    "Text",
    "Boolean",
    "Computed",
    "datetime",
]


class Base(DeclarativeBase):
    pass
