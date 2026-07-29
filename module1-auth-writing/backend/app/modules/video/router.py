"""Short-video script trial-operation API."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.video import VideoHistory
from app.modules.video.schemas import VideoGenerateRequest
from app.modules.video.services import generate_video_plan

router = APIRouter(prefix="/api/video", tags=["视频脚本试运营"])


def _ok(data=None, message="success"):
    return {"code": 200, "message": message, "data": data}


def _item(record: VideoHistory) -> dict:
    try:
        storyboard = json.loads(record.storyboard_json or "[]")
    except Exception:
        storyboard = []
    return {
        "id": record.id,
        "product_id": record.product_id,
        "product_name": record.product_name,
        "product_features": record.product_features or "",
        "platform": record.platform,
        "language": record.language,
        "duration_sec": record.duration_sec,
        "hook": record.hook or "",
        "voiceover": record.voiceover or "",
        "cta": record.cta or "",
        "hashtags": record.hashtags or "",
        "storyboard": storyboard,
        "created_at": str(record.created_at) if record.created_at else "",
    }


@router.post("/generate")
async def generate_video(
    req: VideoGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plan = await generate_video_plan(
        product_name=req.product_name.strip(),
        features=req.product_features,
        platform=req.platform,
        language=req.language,
        duration_sec=req.duration_sec,
        style=req.style,
    )
    record = VideoHistory(
        user_id=current_user.id,
        product_id=req.product_id,
        product_name=req.product_name.strip(),
        product_features=req.product_features or "",
        platform=req.platform,
        language=req.language,
        duration_sec=req.duration_sec,
        hook=plan.get("hook") or "",
        voiceover=plan.get("voiceover") or "",
        cta=plan.get("cta") or "",
        hashtags=plan.get("hashtags") or "",
        storyboard_json=json.dumps(plan.get("storyboard") or [], ensure_ascii=False),
        raw_json=json.dumps(plan, ensure_ascii=False),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _ok(_item(record), "视频脚本生成成功")


@router.get("/history")
def list_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(VideoHistory)
        .filter(VideoHistory.user_id == current_user.id)
        .order_by(desc(VideoHistory.id))
    )
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return _ok({"items": [_item(item) for item in items], "total": total, "page": page, "page_size": page_size})


@router.get("/history/{history_id}")
def get_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(VideoHistory)
        .filter(VideoHistory.id == history_id, VideoHistory.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return _ok(_item(record))


@router.delete("/history/{history_id}")
def delete_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(VideoHistory)
        .filter(VideoHistory.id == history_id, VideoHistory.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(record)
    db.commit()
    return _ok(None, "已删除")
