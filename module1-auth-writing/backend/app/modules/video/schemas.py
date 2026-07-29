from pydantic import BaseModel, Field
from typing import List, Optional


class VideoGenerateRequest(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=200)
    product_features: str = Field("", max_length=800)
    product_id: Optional[int] = None
    platform: str = Field(default="TikTok", max_length=50)
    language: str = Field(default="zh", max_length=20)
    duration_sec: int = Field(default=15, ge=10, le=60)
    style: str = Field(default="casual", max_length=40)


class StoryboardShot(BaseModel):
    idx: int
    start_sec: int
    end_sec: int
    visual: str
    voiceover: str
    on_screen_text: str = ""


class VideoGenerateResult(BaseModel):
    hook: str
    voiceover: str
    cta: str
    hashtags: str
    storyboard: List[StoryboardShot]
