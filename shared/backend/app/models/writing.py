"""文案生成历史模型"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class WritingHistory(Base):
    __tablename__ = "history_writing"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_name = Column(String(200), nullable=False)
    product_features = Column(Text)
    platform = Column(String(50))
    title = Column(Text)
    body = Column(Text)
    tags = Column(String(500))
    language = Column(String(20), default="zh")
    style = Column(String(20), default="default")
    created_at = Column(DateTime, server_default=func.now())
