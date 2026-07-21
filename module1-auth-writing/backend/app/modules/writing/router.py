"""文案生成路由"""
import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.writing import WritingHistory
from app.modules.writing.schemas import GenerateRequest, GenerateResponse, CopyResult, HistoryItem
from app.modules.writing.llm_client import get_llm_client

router = APIRouter(prefix="/api/writing", tags=["文案生成"])


@router.post("/generate", response_model=dict)
async def generate(req: GenerateRequest,
                   current_user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """生成营销文案（支持多平台批量生成）"""
    client = get_llm_client()

    # 并发或串行生成各平台文案
    results = []
    for platform in req.platforms:
        if hasattr(client, 'generate') and asyncio.iscoroutinefunction(client.generate):
            result = await client.generate(
                product_name=req.product_name,
                features=req.product_features,
                platform=platform,
                language=req.language,
                style=req.style,
            )
        else:
            result = client.generate(
                product_name=req.product_name,
                features=req.product_features,
                platform=platform,
                language=req.language,
                style=req.style,
            )
        results.append(result)

    # 保存第一条结果到历史（多个平台合并存储）
    first = results[0]
    history = WritingHistory(
        user_id=current_user.id,
        product_name=req.product_name,
        product_features=req.product_features,
        platform=", ".join(req.platforms),
        title=first["title"],
        body=first["body"],
        tags=first["tags"],
        language=req.language,
        style=req.style,
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    return {
        "code": 200,
        "message": "文案生成成功",
        "data": {
            "results": results,
            "id": history.id,
        },
    }


@router.get("/history", response_model=dict)
def get_history(page: int = 1, page_size: int = 20,
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """获取当前用户的文案生成历史（分页）"""
    query = db.query(WritingHistory).filter(
        WritingHistory.user_id == current_user.id
    ).order_by(desc(WritingHistory.created_at))

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "code": 200,
        "message": "ok",
        "data": {
            "items": [
                {
                    "id": item.id,
                    "product_name": item.product_name,
                    "product_features": item.product_features,
                    "platform": item.platform,
                    "title": item.title,
                    "body": item.body,
                    "tags": item.tags,
                    "language": item.language,
                    "style": item.style,
                    "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else "",
                }
                for item in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }
