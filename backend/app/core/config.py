"""
智能工厂工作任务管理平台 - 配置模块
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 数据库配置
    DB_SERVER: str = "localhost"
    DB_PORT: int = 1433
    DB_NAME: str = "WorkTaskDB"
    DB_USER: str = "sa"
    DB_PASSWORD: str = "!Admin123456"
    DB_DRIVER: str = "ODBC Driver 17 for SQL Server"

    # JWT 配置
    SECRET_KEY: str = "worktask-platform-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # 应用配置
    APP_TITLE: str = "智能工厂工作任务管理平台"
    APP_VERSION: str = "1.0.0"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8001
    DEBUG: bool = True


    @property
    def odbc_connect_str(self) -> str:
        """构建原生 ODBC 连接字符串 - 支持Windows身份验证"""
        # 如果用户名是空或sa密码不对，使用Windows身份验证
        if not self.DB_USER or not self.DB_PASSWORD or self.DB_PASSWORD == "!Admin123456":
            return (
                f"DRIVER={{{self.DB_DRIVER}}};"
                f"SERVER={self.DB_SERVER};"
                f"DATABASE={self.DB_NAME};"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;"
            )
        else:
            return (
                f"DRIVER={{{self.DB_DRIVER}}};"
                f"SERVER={self.DB_SERVER};"
                f"DATABASE={self.DB_NAME};"
                f"UID={self.DB_USER};"
                f"PWD={self.DB_PASSWORD};"
                f"TrustServerCertificate=yes;"
            )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
