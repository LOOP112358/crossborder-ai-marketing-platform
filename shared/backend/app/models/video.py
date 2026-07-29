"""短视频脚本 / 分镜试运营历史"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class VideoHistory(Base):
    __tablename__ = "history_video"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, nullable=True, index=True)
    product_name = Column(String(200), nullable=False)
    product_features = Column(Text, default="")
    platform = Column(String(50), default="TikTok")
    language = Column(String(20), default="zh")
    duration_sec = Column(Integer, default=15)
    hook = Column(String(300), default="")
    voiceover = Column(Text, default="")
    cta = Column(String(300), default="")
    hashtags = Column(String(500), default="")
    storyboard_json = Column(Text, default="[]")
    raw_json = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())
