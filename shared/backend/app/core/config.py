"""应用配置"""
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # JWT 配置
    SECRET_KEY: str = "ecommerce-tools-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时

    # 数据库 (SQLite，每个成员一个db文件)
    DATABASE_URL: str = "sqlite:///./data/module1.db"

    # LLM API 配置（可选，不配则使用 Mock）
    LLM_API_KEY: str = ""
    LLM_API_URL: str = "https://api.openai.com/v1/chat/completions"
    LLM_MODEL: str = "gpt-4o-mini"

    # 应用
    APP_NAME: str = "AI电商营销工具平台"
    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# 确保 data 目录存在
os.makedirs("data", exist_ok=True)
