"""数据库连接和会话管理"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite需要
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI依赖：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """创建所有表，并为已有 SQLite 表补齐新增列"""
    import app.models  # noqa: F401 — 注册全部模型（含 AboProduct）
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()


def _ensure_sqlite_columns():
    """SQLite 无自动迁移：给 abo_products 补 image 相关列。"""
    if not str(engine.url).startswith("sqlite"):
        return
    alters = [
        ("abo_products", "main_image_id", "VARCHAR(64)"),
        ("abo_products", "image_path", "VARCHAR(260)"),
    ]
    with engine.begin() as conn:
        for table, col, coltype in alters:
            rows = conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
            names = {r[1] for r in rows}
            if col not in names:
                conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")
                print(f"[db] 已为 {table} 添加列 {col}")
