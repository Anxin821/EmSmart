"""
智能工厂工作任务管理平台 - 数据库连接模块
"""
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.base import Base  # 统一 ORM 基类：models 全部 15 张表注册于此，供 main 建表

# 使用 odbc_connect 直传原生 ODBC 连接串（避免 URL 编码问题）
quoted = urllib.parse.quote_plus(settings.odbc_connect_str)
engine = create_engine(
    f"mssql+pyodbc:///?odbc_connect={quoted}",
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 基类 —— 与 app/models/base.py 共用同一 DeclarativeBase（上方导入）。
# 历史遗留的独立 declarative_base() 已移除，此前它持有空 metadata，
# 导致 main.py 的 Base.metadata.create_all 实际建不出任何表。


def get_db():
    """获取数据库会话的依赖注入生成器，异常时自动回滚"""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
