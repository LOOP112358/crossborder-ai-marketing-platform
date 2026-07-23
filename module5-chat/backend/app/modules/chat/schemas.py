"""模块5 智能客服 + 运营看板 Pydantic 模型"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    title: Optional[str] = "新会话"


class SessionOut(BaseModel):
    id: int
    title: str
    doc_name: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    session_id: int
    content: str
    language: str = "zh"


class MessageOut(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    language: str
    created_at: Optional[str] = None
    feedback: Optional[str] = None

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    user_message: dict
    assistant_message: dict
    sources: List[str] = []


class FeedbackCreate(BaseModel):
    message_id: int
    feedback_type: str = Field(..., pattern="^(like|dislike)$")


class DashboardStats(BaseModel):
    total_users: int
    today_calls: int
    feature_usage: Dict[str, int]
    feature_ratio: Dict[str, float]
    hot_categories: List[Dict[str, Any]]
    error_alerts: List[Dict[str, Any]]
    chat_feedback_stats: Dict[str, int]


class TrendPoint(BaseModel):
    stat_date: str
    writing_calls: int
    matte_calls: int
    bg_calls: int
    poster_calls: int
    chat_calls: int
    error_count: int


class AdviceResponse(BaseModel):
    advice: str
    generated_at: datetime
