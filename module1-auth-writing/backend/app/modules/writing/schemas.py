"""文案生成模块 Pydantic 模型"""
from typing import Optional, List
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=200, description="商品名称")
    product_features: str = Field("", max_length=500, description="商品卖点/特点")
    platforms: List[str] = Field(
        default=["TikTok"],
        description="目标平台列表：TikTok, Instagram, Amazon"
    )
    language: str = Field(default="zh", description="语言代码：zh/en/ja/ko/es")
    style: str = Field(default="professional", description="文案风格：professional/casual/minimalist/emotional/humorous/luxury")


class CopyResult(BaseModel):
    platform: str
    title: str
    body: str
    tags: str
    language: str
    style: str


class GenerateResponse(BaseModel):
    results: List[CopyResult]
    id: int


class HistoryItem(BaseModel):
    id: int
    product_name: str
    product_features: Optional[str]
    platform: Optional[str]
    title: Optional[str]
    body: Optional[str]
    tags: Optional[str]
    language: Optional[str]
    style: Optional[str]
    created_at: str

    class Config:
        from_attributes = True
