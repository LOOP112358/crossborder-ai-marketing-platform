"""海报合成 Pydantic 模型"""
from typing import Optional
from pydantic import BaseModel, Field


class ComposeRequest(BaseModel):
    matted_url: str = Field(..., description="商品抠图结果URL")
    bg_url: str = Field(..., description="背景图URL")
    template_id: int = Field(..., description="模板ID")
    title: str = Field("", max_length=200)
    discount: str = Field("", max_length=50)
    price: str = Field("", max_length=50)
    ratio: str = Field("1:1", description="宽高比：1:1, 9:16, 16:9 等")


class TemplateItem(BaseModel):
    id: int
    name: str
    preview_url: Optional[str] = None
    usage_count: int = 0
