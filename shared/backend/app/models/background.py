"""背景生成历史 / 缓存模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class BackgroundHistory(Base):
    __tablename__ = "history_background"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_category = Column(Text, nullable=False)
    style = Column(String(50))
    color_hint = Column(String(50))
    prompt_used = Column(Text)
    bg_url = Column(String(500))
    enhanced_url = Column(String(500))
    scale_factor = Column(Integer, default=2)
    created_at = Column(DateTime, server_default=func.now())


class BackgroundCache(Base):
    """按 category + style + color_hint 缓存双模型结果，避免重复调 API。"""
    __tablename__ = "background_cache"
    __table_args__ = (UniqueConstraint("cache_key", name="uq_background_cache_key"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(300), nullable=False, index=True)
    category = Column(String(200))
    style = Column(String(100))
    color_hint = Column(String(100))
    bg_url = Column(String(500), nullable=False)
    enhanced_url = Column(String(500), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
