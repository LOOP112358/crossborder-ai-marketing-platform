"""背景生成历史模型"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
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
