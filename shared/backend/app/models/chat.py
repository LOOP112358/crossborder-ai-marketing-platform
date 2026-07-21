"""模块5 智能客服 + 运营看板 数据模型"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Date, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), default="新会话")
    doc_name = Column(String(200))
    faiss_index_path = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(10), default="zh")
    created_at = Column(DateTime, server_default=func.now())


class ChatFeedback(Base):
    __tablename__ = "chat_feedback"
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feedback_type = Column(String(10), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class SystemDailyStat(Base):
    __tablename__ = "system_daily_stats"
    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(Date, unique=True, nullable=False)
    total_users = Column(Integer, default=0)
    writing_calls = Column(Integer, default=0)
    matte_calls = Column(Integer, default=0)
    bg_calls = Column(Integer, default=0)
    poster_calls = Column(Integer, default=0)
    chat_calls = Column(Integer, default=0)
    error_count = Column(Integer, default=0)


class ModuleError(Base):
    """各模块错误记录"""
    __tablename__ = "module_errors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    module_name = Column(String(50), nullable=False)
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class AboProduct(Base):
    """ABO商品知识库"""
    __tablename__ = "abo_products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String(20), unique=True, nullable=False, index=True)
    item_name = Column(Text)
    item_name_zh = Column(Text)
    brand = Column(Text)
    brand_zh = Column(Text)
    product_type = Column(String(200))
    bullet_points = Column(Text)
    bullet_points_zh = Column(Text)
    material = Column(Text)
    material_zh = Column(Text)
    color = Column(Text)
    main_image_id = Column(String(64), index=True)
    image_path = Column(String(260))  # 相对 images/small 的路径，如 14/14fe8812.jpg
    faq_text = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    @property
    def image_url(self) -> str | None:
        if not self.image_path:
            return None
        # 由 main.py 挂载 /static/abo-images → ABO_IMAGES_DIR
        return f"/static/abo-images/images/small/{self.image_path.replace(chr(92), '/')}"

