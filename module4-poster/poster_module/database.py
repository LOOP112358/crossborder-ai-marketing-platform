import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
ENV_PATH = PROJECT_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "ai_marketing")

if not MYSQL_USER:
    raise RuntimeError(f"没有读取到 MYSQL_USER，请检查 .env 文件位置：{ENV_PATH}")

if not MYSQL_PASSWORD:
    raise RuntimeError(f"没有读取到 MYSQL_PASSWORD，请检查 .env 文件位置：{ENV_PATH}")

DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args={"ssl_disabled": True}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()