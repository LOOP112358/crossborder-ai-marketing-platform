"""商品抠图历史模型"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class MatteHistory(Base):
    __tablename__ = "history_matte"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    original_url = Column(String(500), nullable=False)
    matted_url = Column(String(500), nullable=False)
    category = Column(String(100))
    category_en = Column(String(100))
    confidence = Column(Float)
    attributes = Column(Text)  # JSON字符串
    file_size = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
