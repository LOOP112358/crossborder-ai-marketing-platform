"""应用配置"""
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # 允许 .env 里有客服/ABO 等其它模块的变量
    )

    # JWT 配置
    SECRET_KEY: str = "ecommerce-tools-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时

    # 数据库 (SQLite，每个成员一个db文件)
    DATABASE_URL: str = "sqlite:///./data/module1.db"

    # LLM API 配置（可选，不配则使用 Mock）
    LLM_API_KEY: str = ""
    LLM_API_URL: str = "https://api.deepseek.com/v1/chat/completions"
    LLM_MODEL: str = "deepseek-chat"

    # 应用
    APP_NAME: str = "AI电商营销工具平台"
    APP_VERSION: str = "1.0.0"


settings = Settings()

# 客服与文案共用 DeepSeek key：只配 OPENAI_API_KEY 也能驱动文案模块
if not settings.LLM_API_KEY:
    settings.LLM_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 确保 data 目录存在
os.makedirs("data", exist_ok=True)
