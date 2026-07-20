from datetime import datetime, date

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Date, ForeignKey

from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), default="新会话")
    doc_name = Column(String(200))
    faiss_index_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(10), default="zh")
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatFeedback(Base):
    __tablename__ = "chat_feedback"
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feedback_type = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemDailyStat(Base):
    __tablename__ = "system_daily_stats"
    id = Column(Integer, primary_key=True)
    stat_date = Column(Date, unique=True, nullable=False)
    total_users = Column(Integer, default=0)
    writing_calls = Column(Integer, default=0)
    matte_calls = Column(Integer, default=0)
    bg_calls = Column(Integer, default=0)
    poster_calls = Column(Integer, default=0)
    chat_calls = Column(Integer, default=0)
    error_count = Column(Integer, default=0)


class AboProduct(Base):
    __tablename__ = "abo_products"
    id = Column(Integer, primary_key=True)
    item_id = Column(String(20), unique=True, nullable=False)
    item_name = Column(Text)
    item_name_zh = Column(Text)
    brand = Column(Text)
    product_type = Column(String(200))
    bullet_points = Column(Text)
    bullet_points_zh = Column(Text)
    material = Column(Text)
    color = Column(Text)
    faq_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ModuleError(Base):
    __tablename__ = "module_errors"
    id = Column(Integer, primary_key=True)
    module_name = Column(String(50), nullable=False)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
