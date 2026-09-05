"""时间工具：全站以北京时间为准。

约定：数据库一律存北京时间 naive datetime；接口返回 naive ISO 字符串
（不带 Z/+08:00），前端 new Date(naive) + 本地显示会自我抵消，任何浏览器都
回显同一北京墙钟，因此无需前端做时区换算。
"""
from datetime import datetime, timezone, timedelta

_BJ = timezone(timedelta(hours=8))


def beijing_now():
    """当前北京时间，naive datetime（不依赖宿主系统时区）。"""
    return datetime.now(_BJ).replace(tzinfo=None)


def beijing_date():
    """当前北京时间（仅日期），供 Date 列默认值。"""
    return beijing_now().date()
