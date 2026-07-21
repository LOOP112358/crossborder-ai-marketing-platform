"""商品抠图模块 Pydantic 模型"""
from typing import Optional
from pydantic import BaseModel, Field


class MatteResponse(BaseModel):
    id: int
    user_id: int
    original_url: str
    matted_url: str
    category: Optional[str] = None
    category_en: Optional[str] = None
    confidence: Optional[float] = None
    attributes: Optional[dict] = None
    file_size: Optional[int] = None
    created_at: Optional[str] = None


class HistoryItem(BaseModel):
    id: int
    original_url: str
    matted_url: str
    category: Optional[str] = None
    category_en: Optional[str] = None
    confidence: Optional[float] = None
    attributes: Optional[dict] = None
    file_size: Optional[int] = None
    created_at: str
