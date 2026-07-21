"""海报合成模型"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    preview_url = Column(String(500))
    config_json = Column(Text, nullable=False)
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class PosterHistory(Base):
    __tablename__ = "history_poster"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    matted_url = Column(String(500), nullable=False)
    bg_url = Column(String(500), nullable=False)
    template_id = Column(Integer, ForeignKey("templates.id"))
    poster_url = Column(String(500), nullable=False)
    title = Column(String(200))
    discount = Column(String(50))
    price = Column(String(50))
    ratio = Column(String(20), default="1:1")
    downloads = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    poster_id = Column(Integer, ForeignKey("history_poster.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "poster_id", name="uq_user_poster_favorite"),
    )
