"""文案生成路由"""
import asyncio

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.writing import WritingHistory
from app.models.chat import AboProduct
from app.modules.writing.schemas import GenerateRequest, EnhanceRequest
from app.modules.writing.llm_client import get_llm_client
from app.modules.writing.enhance_service import generate_enhanced_copies
from app.modules.writing.product_utils import (
    serialize_product,
    build_poster_copy,
    find_similar_products,
    TYPE_ZH,
)
from app.modules.writing.campaign_assistant import list_campaigns, recommend_campaign

router = APIRouter(prefix="/api/writing", tags=["文案生成"])

# 中文检索词 → ABO product_type
_CN_TYPE_HINTS = {
    "耳机": "HEADPHONES",
    "蓝牙耳机": "HEADPHONES",
    "手机壳": "CELLULAR_PHONE_CASE",
    "手机套": "CELLULAR_PHONE_CASE",
    "运动鞋": "TECHNICAL_SPORT_SHOE",
    "跑鞋": "TECHNICAL_SPORT_SHOE",
    "鞋": "SHOES",
    "凉鞋": "SANDAL",
    "拖鞋": "SANDAL",
    "靴子": "BOOT",
    "沙发": "SOFA",
    "椅子": "CHAIR",
    "手表": "WRIST_WATCH",
    "背包": "BACKPACK",
    "零食": "GROCERY",
}
# 反向补全：中文品类名
for _en, _zh in TYPE_ZH.items():
    _CN_TYPE_HINTS.setdefault(_zh, _en)


# 浏览时用于「多样化」抽样的品类（避开手机壳垄断）
_DIVERSE_TYPES = [
    "SHOES",
    "TECHNICAL_SPORT_SHOE",
    "SANDAL",
    "BOOT",
    "SOFA",
    "CHAIR",
    "TABLE",
    "GROCERY",
    "HEADPHONES",
    "WRIST_WATCH",
    "BACKPACK",
    "HOME",
    "HOME_FURNITURE_AND_DECOR",
    "PET_SUPPLIES",
    "SPORTING_GOODS",
    "RUG",
    "CELLULAR_PHONE_CASE",  # 少量保留
]


def _base_product_query(db: Session, has_image: bool):
    query = db.query(AboProduct)
    if has_image:
        query = query.filter(AboProduct.image_path.isnot(None), AboProduct.image_path != "")
    return query


def _diverse_sample(db: Session, has_image: bool, limit: int) -> list:
    """每个热门品类抽几条，避免结果全是手机壳。"""
    per = max(1, limit // max(1, len(_DIVERSE_TYPES) - 1))
    phone_quota = max(1, limit // 10)
    collected = []
    seen = set()
    for pt in _DIVERSE_TYPES:
        q = _base_product_query(db, has_image).filter(AboProduct.product_type.ilike(f"%{pt}%"))
        n = phone_quota if pt == "CELLULAR_PHONE_CASE" else per
        rows = q.order_by(func.random()).limit(n).all()
        for p in rows:
            if p.id in seen:
                continue
            seen.add(p.id)
            collected.append(p)
            if len(collected) >= limit:
                return collected
    # 不够再随机补
    if len(collected) < limit:
        q = _base_product_query(db, has_image)
        if seen:
            q = q.filter(~AboProduct.id.in_(list(seen)))
        more = q.order_by(func.random()).limit(limit - len(collected)).all()
        collected.extend(more)
    return collected[:limit]


@router.get("/campaigns", response_model=dict)
def get_campaigns(current_user: User = Depends(get_current_user)):
    """活动选品助手：预设活动主题列表。"""
    return {"code": 200, "message": "ok", "data": {"items": list_campaigns()}}


@router.post("/campaigns/recommend", response_model=dict)
def post_campaign_recommend(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """按活动主题从 ABO 货盘生成选品方案（评分 + 营销角度）。"""
    campaign_id = str(payload.get("campaign_id") or "black_friday")
    theme = str(payload.get("theme") or "")
    market = str(payload.get("market") or "cn")
    limit = int(payload.get("limit") or 8)
    data = recommend_campaign(
        db,
        campaign_id=campaign_id,
        theme=theme,
        market=market,
        limit=limit,
    )
    return {"code": 200, "message": "ok", "data": data}


@router.get("/products/categories", response_model=dict)
def list_categories(
    has_image: bool = Query(False, description="仅统计有主图的品类"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """返回商品品类分布，供选品中心 / 海报工作流筛选。"""
    q = db.query(AboProduct.product_type, func.count(AboProduct.id)).filter(
        AboProduct.product_type.isnot(None), AboProduct.product_type != ""
    )
    if has_image:
        q = q.filter(AboProduct.image_path.isnot(None), AboProduct.image_path != "")
    rows = (
        q.group_by(AboProduct.product_type)
        .order_by(func.count(AboProduct.id).desc())
        .limit(40)
        .all()
    )
    items = []
    for pt, cnt in rows:
        items.append({
            "product_type": pt,
            "label": TYPE_ZH.get(pt.upper(), pt.replace("_", " ").title()),
            "count": cnt,
        })
    return {"code": 200, "message": "ok", "data": {"items": items}}


@router.get("/products/search", response_model=dict)
def search_products(
    q: str = Query("", max_length=100, description="关键词：商品名/品牌/品类"),
    limit: int = Query(20, ge=1, le=50),
    has_image: bool = Query(False, description="仅返回有主图的商品"),
    diverse: bool = Query(False, description="无关键词时按多品类抽样"),
    product_type: str = Query("", max_length=80, description="按 ABO product_type 筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """从 ABO 商品库搜索，供文案页 / 海报工作流选品。"""
    q = (q or "").strip()
    product_type = (product_type or "").strip()
    total = db.query(func.count(AboProduct.id)).scalar() or 0
    with_image = (
        db.query(func.count(AboProduct.id))
        .filter(AboProduct.image_path.isnot(None), AboProduct.image_path != "")
        .scalar()
        or 0
    )

    if product_type:
        rows = (
            _base_product_query(db, has_image)
            .filter(AboProduct.product_type.ilike(f"%{product_type}%"))
            .order_by(func.random())
            .limit(limit)
            .all()
        )
    elif q:
        like = f"%{q}%"
        filters = [
            AboProduct.item_name.ilike(like),
            AboProduct.item_name_zh.ilike(like),
            AboProduct.brand.ilike(like),
            AboProduct.brand_zh.ilike(like),
            AboProduct.product_type.ilike(like),
            AboProduct.bullet_points.ilike(like),
            AboProduct.bullet_points_zh.ilike(like),
            AboProduct.item_id.ilike(like),
            AboProduct.color.ilike(like),
        ]
        for cn, en in sorted(_CN_TYPE_HINTS.items(), key=lambda x: -len(x[0])):
            if cn in q:
                filters.append(AboProduct.product_type.ilike(f"%{en}%"))
                break
        rows = (
            _base_product_query(db, has_image)
            .filter(or_(*filters))
            .order_by(
                AboProduct.image_path.isnot(None).desc(),
                AboProduct.item_name.isnot(None).desc(),
            )
            .limit(limit)
            .all()
        )
    elif diverse or has_image:
        # 默认有图浏览走多样化，避免全是手机壳
        rows = _diverse_sample(db, has_image, limit)
    else:
        rows = _base_product_query(db, has_image).order_by(func.random()).limit(limit).all()

    return {
        "code": 200,
        "message": "ok",
        "data": {
            "items": [serialize_product(p) for p in rows],
            "catalog_total": total,
            "with_image": with_image,
            "query": q,
            "product_type": product_type,
        },
    }


# Static suffixes (/similar, /poster-copy) BEFORE bare /{product_id}
@router.get("/products/{product_id}/similar", response_model=dict)
def similar_products(
    product_id: str,
    limit: int = Query(8, ge=1, le=12, description="返回条数，建议 6–12"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """同款延伸：按品类/品牌/关键词重叠找相似货盘，优先有主图。

    product_id 支持数字主键 id，也兼容 ABO item_id（如 B07XXXX）。
    """
    pid = (product_id or "").strip()
    p = None
    if pid.isdigit():
        p = db.query(AboProduct).filter(AboProduct.id == int(pid)).first()
    if not p and pid:
        p = db.query(AboProduct).filter(AboProduct.item_id == pid).first()
    if not p:
        return {"code": 404, "message": "商品不存在", "data": None}
    try:
        rows = find_similar_products(db, p, limit=limit)
    except Exception as exc:
        # 避免 ilike/排序异常直接 500，前端可展示明确文案
        raise HTTPException(status_code=500, detail=f"相似款查询失败：{exc}") from exc
    return {
        "code": 200,
        "message": "ok",
        "data": {
            "source": serialize_product(p),
            "items": [serialize_product(x) for x in rows],
            "limit": limit,
        },
    }


@router.get("/products/{product_id}/poster-copy", response_model=dict)
async def get_poster_copy(
    product_id: int,
    language: str = Query("zh"),
    llm: bool = Query(False, description="是否用 DeepSeek 精炼为海报短文案"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """库内字段生成海报文案；llm=1 时再用 DeepSeek 压成适合叠字的短句。"""
    from app.modules.writing.product_utils import refine_poster_copy_with_llm

    p = db.query(AboProduct).filter(AboProduct.id == product_id).first()
    if not p:
        return {"code": 404, "message": "商品不存在", "data": None}
    base = build_poster_copy(p, language=language)
    poster_copy = await refine_poster_copy_with_llm(p, base, language) if llm else base
    from fastapi.responses import JSONResponse
    payload = {
        "code": 200,
        "message": "ok",
        "data": {
            "product": serialize_product(p),
            "poster_copy": poster_copy,
            "product_id": product_id,
        },
    }
    resp = JSONResponse(content=payload)
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    return resp


@router.get("/products/{product_id}", response_model=dict)
def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """按 id 取单条商品详情。"""
    p = db.query(AboProduct).filter(AboProduct.id == product_id).first()
    if not p:
        return {"code": 404, "message": "商品不存在", "data": None}
    return {"code": 200, "message": "ok", "data": serialize_product(p)}


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


@router.post("/generate-enhanced", response_model=dict)
async def generate_enhanced(
    req: EnhanceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """智能文案增强：ABO 检索增强 + 多版生成 + 合规过滤 + 评分排序。"""
    client = get_llm_client()
    data = await generate_enhanced_copies(
        client,
        db=db,
        product_name=req.product_name,
        product_features=req.product_features,
        platforms=req.platforms or ["TikTok"],
        language=req.language,
        style=req.style,
        product_id=req.product_id,
        variant_count=req.variant_count,
    )
    best = data.get("best") or {}
    history = WritingHistory(
        user_id=current_user.id,
        product_name=req.product_name,
        product_features=(req.product_features or "")[:500],
        platform=", ".join(req.platforms or ["TikTok"]),
        title=best.get("title") or "",
        body=best.get("body") or "",
        tags=best.get("tags") or "",
        language=req.language,
        style=f"{req.style}+enhanced",
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    data["id"] = history.id
    # 兼容旧前端 results 字段：默认取最优版
    data["results"] = [
        {
            "platform": best.get("platform") or (req.platforms or ["TikTok"])[0],
            "title": best.get("title") or "",
            "body": best.get("body") or "",
            "tags": best.get("tags") or "",
            "language": req.language,
            "style": req.style,
        }
    ] if best else []
    return {"code": 200, "message": "智能文案增强完成", "data": data}


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


@router.delete("/history/{history_id}", response_model=dict)
def delete_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除当前用户的一条文案历史"""
    record = db.query(WritingHistory).filter(
        WritingHistory.id == history_id,
        WritingHistory.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="文案记录不存在或无权删除")
    db.delete(record)
    db.commit()
    return {"code": 200, "message": "已删除文案", "data": {"id": history_id}}
