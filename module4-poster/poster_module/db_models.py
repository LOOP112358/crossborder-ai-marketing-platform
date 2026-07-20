from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from .database import Base


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    preview_url = Column(String(500))
    config_json = Column(Text, nullable=False)
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class HistoryPoster(Base):
    __tablename__ = "history_poster"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, default=1)
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

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, default=1)
    poster_id = Column(Integer, ForeignKey("history_poster.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "poster_id", name="uq_user_poster_favorite"),
    )