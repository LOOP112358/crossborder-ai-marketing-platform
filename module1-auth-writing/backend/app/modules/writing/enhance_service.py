"""智能文案增强：ABO 检索增强 + 多版生成 + 合规过滤 + 简易评分。"""
from __future__ import annotations

import re
from typing import Any, Optional

from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.models.chat import AboProduct
from app.modules.writing.product_utils import (
    find_similar_products,
    serialize_product,
)

# 夸大 / 违规倾向词（演示级规则，可继续扩展）
_BANNED = [
    r"根治",
    r"百分之百",
    r"100\s*%",
    r"绝对",
    r"第一品牌",
    r"国家级",
    r"祖传",
    r"特效",
    r"包治",
    r"永久",
    r"最好",
    r"最强",
    r"#?1\b",
    r"no\.?\s*1",
    r"cure\s+all",
    r"guaranteed\s+results?",
]

_ANGLE_HINTS = {
    "zh": {
        "hook": "侧重开头钩子与停留感，3 秒抓住注意力",
        "benefit": "侧重核心卖点与使用收益，理性说服",
        "social": "侧重口碑种草与场景共鸣，推动下单",
    },
    "en": {
        "hook": "Focus on a strong hook in the first line",
        "benefit": "Focus on concrete benefits and proof points",
        "social": "Focus on social proof and lifestyle scene",
    },
}


def _lang_bucket(language: str) -> str:
    return "en" if (language or "").startswith("en") else "zh"


def retrieve_abo_context(
    db: Session,
    *,
    product_name: str,
    product_features: str = "",
    product_id: Optional[int] = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """从 ABO 货盘检索相似商品，作为生成参考（轻量 RAG）。"""
    refs: list[AboProduct] = []
    source = None
    if product_id:
        source = db.query(AboProduct).filter(AboProduct.id == product_id).first()
        if source:
            refs = find_similar_products(db, source, limit=limit)

    if not refs:
        tokens = re.findall(r"[\w\u4e00-\u9fff]{2,}", f"{product_name} {product_features}")[:5]
        q = db.query(AboProduct)
        if tokens:
            likes = []
            for t in tokens:
                pat = f"%{t}%"
                likes.append(
                    or_(
                        AboProduct.item_name.ilike(pat),
                        AboProduct.item_name_zh.ilike(pat),
                        AboProduct.brand.ilike(pat),
                        AboProduct.brand_zh.ilike(pat),
                        AboProduct.bullet_points.ilike(pat),
                        AboProduct.bullet_points_zh.ilike(pat),
                        AboProduct.product_type.ilike(pat),
                    )
                )
            q = q.filter(or_(*likes))
        rows = (
            q.order_by(AboProduct.image_path.isnot(None).desc(), func.random())
            .limit(limit)
            .all()
        )
        refs = rows

    out = []
    for p in refs[:limit]:
        sp = serialize_product(p)
        out.append(
            {
                "id": sp.get("id"),
                "name": sp.get("name") or sp.get("item_name") or "",
                "brand": sp.get("brand") or "",
                "product_type": sp.get("product_type") or sp.get("category") or "",
                "features": (sp.get("features") or "")[:180],
            }
        )
    return out


def build_rag_feature_block(features: str, refs: list[dict], language: str) -> str:
    base = (features or "").strip()
    if not refs:
        return base
    zh = _lang_bucket(language) == "zh"
    lines = []
    for i, r in enumerate(refs, 1):
        lines.append(
            f"{i}. {r.get('brand','')} {r.get('name','')} | {r.get('product_type','')} | {r.get('features','')}"
        )
    block = ("【货盘相似款参考，勿照抄标题】\n" if zh else "[Similar catalog refs, do not copy titles]\n") + "\n".join(lines)
    return f"{base}\n\n{block}".strip() if base else block


def scan_compliance(text: str) -> list[str]:
    hits = []
    raw = text or ""
    for pat in _BANNED:
        if re.search(pat, raw, flags=re.IGNORECASE):
            hits.append(pat.replace(r"\s+", " ").replace(r"\b", "").replace("\\", ""))
    # dedupe keep order
    seen = set()
    out = []
    for h in hits:
        key = h.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
    return out


def sanitize_copy(title: str, body: str, tags: str) -> tuple[str, str, str, list[str]]:
    hits = scan_compliance(f"{title}\n{body}\n{tags}")
    cleaned_title, cleaned_body, cleaned_tags = title or "", body or "", tags or ""
    for h in hits:
        try:
            cleaned_title = re.sub(h, "★★", cleaned_title, flags=re.IGNORECASE)
            cleaned_body = re.sub(h, "★★", cleaned_body, flags=re.IGNORECASE)
            cleaned_tags = re.sub(h, "", cleaned_tags, flags=re.IGNORECASE)
        except re.error:
            cleaned_title = cleaned_title.replace(h, "★★")
            cleaned_body = cleaned_body.replace(h, "★★")
    cleaned_tags = re.sub(r",{2,}", ",", cleaned_tags).strip(" ,")
    return cleaned_title, cleaned_body, cleaned_tags, hits


def score_variant(
    *,
    title: str,
    body: str,
    tags: str,
    platform: str,
    banned_hits: list[str],
) -> dict[str, Any]:
    title = title or ""
    body = body or ""
    tags = tags or ""

    # 钩子分：标题长度适中 + 有情绪/数字/问句
    hook = 55
    tl = len(title)
    if 8 <= tl <= 40:
        hook += 15
    elif tl > 50:
        hook -= 10
    if re.search(r"[!?？！]|你|吗|吗\？|\d|%|超|绝|香", title):
        hook += 15
    if title:
        hook += 5

    # 平台适配：正文长度粗分
    fit = 60
    bl = len(body)
    if platform == "TikTok":
        fit += 20 if 40 <= bl <= 180 else (-10 if bl > 280 else 0)
    elif platform == "Instagram":
        fit += 20 if 60 <= bl <= 260 else (-8 if bl < 30 else 0)
    elif platform == "Amazon":
        fit += 20 if 80 <= bl <= 400 else (-8 if bl < 40 else 0)
    else:
        fit += 10 if bl >= 40 else 0
    if tags and ("," in tags or "#" in tags or "，" in tags):
        fit += 8

    # 合规分
    compliance = 100 - min(80, len(banned_hits) * 25)

    # 完整度
    completeness = 40
    if title:
        completeness += 20
    if body:
        completeness += 25
    if tags:
        completeness += 15

    overall = int(round(hook * 0.3 + fit * 0.3 + compliance * 0.25 + completeness * 0.15))
    overall = max(0, min(100, overall))
    return {
        "hook": max(0, min(100, int(hook))),
        "platform_fit": max(0, min(100, int(fit))),
        "compliance": max(0, min(100, int(compliance))),
        "completeness": max(0, min(100, int(completeness))),
        "overall": overall,
    }


async def generate_enhanced_copies(
    client,
    *,
    db: Session,
    product_name: str,
    product_features: str,
    platforms: list[str],
    language: str,
    style: str,
    product_id: Optional[int] = None,
    variant_count: int = 3,
) -> dict[str, Any]:
    refs = retrieve_abo_context(
        db,
        product_name=product_name,
        product_features=product_features,
        product_id=product_id,
        limit=3,
    )
    enriched = build_rag_feature_block(product_features, refs, language)
    platform = (platforms or ["TikTok"])[0]
    angles = list(_ANGLE_HINTS.get(_lang_bucket(language), _ANGLE_HINTS["zh"]).items())
    variant_count = max(1, min(int(variant_count or 3), 3))
    angles = angles[:variant_count]

    variants = []
    for key, hint in angles:
        feat = f"{enriched}\n\n【增强角度】{hint}" if _lang_bucket(language) == "zh" else f"{enriched}\n\n[Angle] {hint}"
        if hasattr(client, "generate") and __import__("asyncio").iscoroutinefunction(client.generate):
            raw = await client.generate(
                product_name=product_name,
                features=feat,
                platform=platform,
                language=language,
                style=style,
            )
        else:
            raw = client.generate(
                product_name=product_name,
                features=feat,
                platform=platform,
                language=language,
                style=style,
            )
        title, body, tags, hits = sanitize_copy(
            raw.get("title", ""),
            raw.get("body", ""),
            raw.get("tags", ""),
        )
        scores = score_variant(
            title=title,
            body=body,
            tags=tags,
            platform=platform,
            banned_hits=hits,
        )
        variants.append(
            {
                "angle": key,
                "angle_hint": hint,
                "platform": platform,
                "title": title,
                "body": body,
                "tags": tags,
                "language": language,
                "style": style,
                "banned_hits": hits,
                "scores": scores,
            }
        )

    variants.sort(key=lambda v: v["scores"]["overall"], reverse=True)
    for i, v in enumerate(variants):
        v["rank"] = i + 1
        v["is_best"] = i == 0

    return {
        "rag_refs": refs,
        "platform": platform,
        "variants": variants,
        "best": variants[0] if variants else None,
        "pipeline": ["abo_retrieve", "multi_variant_generate", "compliance_filter", "score_rank"],
    }
