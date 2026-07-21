"""智能客服检索增强：品类优先 + 本地关键词 + FAISS 补充"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.chat import AboProduct


# 中文品类 → ABO product_type（按「更具体」优先：长词在前）
CN_TO_EN_CATEGORY = {
    "蓝牙耳机": "HEADPHONES",
    "无线耳机": "HEADPHONES",
    "头戴耳机": "HEADPHONES",
    "入耳式": "HEADPHONES",
    "耳机": "HEADPHONES",
    "耳麦": "HEADPHONES",
    "音箱": "PORTABLE_AUDIO",
    "音响": "PORTABLE_AUDIO",
    "运动鞋": "TECHNICAL_SPORT_SHOE",
    "跑鞋": "TECHNICAL_SPORT_SHOE",
    "篮球鞋": "TECHNICAL_SPORT_SHOE",
    "足球鞋": "TECHNICAL_SPORT_SHOE",
    "鞋子": "SHOES",
    "鞋": "SHOES",
    "手机壳": "CELLULAR_PHONE_CASE",
    "手机套": "CELLULAR_PHONE_CASE",
    "凉鞋": "SANDAL",
    "拖鞋": "SANDAL",
    "靴子": "BOOT",
    "靴": "BOOT",
    "沙发": "SOFA",
    "椅子": "CHAIR",
    "办公椅": "CHAIR",
    "手表": "WRIST_WATCH",
    "手环": "WRIST_WATCH",
    "戒指": "FINE_RING",
    "项链": "FINE_NECKLACE",
    "耳环": "FINE_EARRING",
    "背包": "BACKPACK",
    "零食": "GROCERY",
    "薯片": "GROCERY",
    "食品": "GROCERY",
}

# 无 LLM 时的本地英文检索词
LOCAL_EN_KEYWORDS = {
    "耳机": "HEADPHONES HEADPHONE EARPHONE EARBUD WIRELESS BLUETOOTH AUDIO",
    "蓝牙耳机": "HEADPHONES HEADPHONE BLUETOOTH WIRELESS EARBUDS",
    "运动鞋": "TECHNICAL_SPORT_SHOE SNEAKER ATHLETIC RUNNING SHOES",
    "手机壳": "CELLULAR_PHONE_CASE PHONE CASE COVER",
    "沙发": "SOFA COUCH FURNITURE",
    "鞋子": "SHOES FOOTWEAR",
    "手表": "WRIST_WATCH WATCH",
}


def detect_product_types(query: str) -> List[str]:
    """从中文问题中识别 ABO product_type，长关键词优先。"""
    hits: List[Tuple[int, str]] = []
    for cn, en in CN_TO_EN_CATEGORY.items():
        if cn in query:
            hits.append((len(cn), en))
    hits.sort(key=lambda x: -x[0])
    seen = set()
    types = []
    for _, en in hits:
        if en not in seen:
            seen.add(en)
            types.append(en)
    return types


def local_english_keywords(query: str) -> str:
    parts = []
    for cn, en in LOCAL_EN_KEYWORDS.items():
        if cn in query:
            parts.append(en)
    # 也保留原始英文词
    en_tokens = re.findall(r"[A-Za-z_]{3,}", query)
    if en_tokens:
        parts.append(" ".join(en_tokens))
    return " ".join(parts).strip()


def search_products_by_type(db: Session, product_types: List[str], limit: int = 8) -> List[AboProduct]:
    if not product_types:
        return []
    products: List[AboProduct] = []
    for pt in product_types:
        rows = (
            db.query(AboProduct)
            .filter(
                or_(
                    AboProduct.product_type == pt,
                    AboProduct.product_type.ilike(f"%{pt}%"),
                )
            )
            .limit(limit)
            .all()
        )
        for p in rows:
            if all(p.id != x.id for x in products):
                products.append(p)
        if products:
            break
    return products[:limit]


def search_products_by_keywords(db: Session, keywords: str, limit: int = 8) -> List[AboProduct]:
    tokens = [t for t in re.split(r"\s+", keywords.upper()) if len(t) >= 3]
    if not tokens:
        return []
    # 优先用 product_type / item_name / brand / faq_text 命中
    products: List[AboProduct] = []
    for tok in tokens[:6]:
        rows = (
            db.query(AboProduct)
            .filter(
                or_(
                    AboProduct.product_type.ilike(f"%{tok}%"),
                    AboProduct.item_name.ilike(f"%{tok}%"),
                    AboProduct.brand.ilike(f"%{tok}%"),
                    AboProduct.faq_text.ilike(f"%{tok}%"),
                )
            )
            .limit(limit)
            .all()
        )
        for p in rows:
            if all(p.id != x.id for x in products):
                products.append(p)
        if len(products) >= limit:
            break
    return products[:limit]


def parse_faq(faq_text: str) -> dict:
    data = {}
    for line in (faq_text or "").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            data[k.strip().lower()] = v.strip()
    return data


def format_product_answer(question: str, products: List[AboProduct], language: str = "zh") -> str:
    """结构化回复，接近成员5原版体验。"""
    if not products:
        if language == "en":
            return "Sorry, I couldn't find matching products. Try another category or brand."
        return "抱歉，没有找到相关商品。可以换个品类试试，例如：运动鞋、耳机、手机壳、沙发。"

    # 品牌汇总
    brands = []
    for p in products:
        b = (p.brand or "").strip()
        if b and b not in brands:
            brands.append(b)

    lines = []
    if language == "en":
        lines.append(f'Found {len(products)} product(s) related to "{question}".')
        if brands:
            lines.append("Brands: " + ", ".join(brands[:12]))
        lines.append("")
        for i, p in enumerate(products[:6], 1):
            faq = parse_faq(p.faq_text or "")
            lines.append(f"{i}. {p.item_name or 'Unnamed'}")
            lines.append(f"   - Type: {p.product_type or '-'}")
            lines.append(f"   - Brand: {p.brand or '-'}")
            if p.color:
                lines.append(f"   - Color: {p.color}")
            if p.material:
                lines.append(f"   - Material: {p.material}")
            bullets = (p.bullet_points or faq.get("bullet points", "")).strip()
            if bullets:
                tip = bullets.split("|")[0].strip()
                if tip:
                    lines.append(f"   - Highlight: {tip[:120]}")
            lines.append("")
        lines.append("Ask a brand name for more details.")
    else:
        lines.append(f"根据知识库，找到与「{question}」相关的 {len(products)} 件商品：")
        if brands:
            lines.append("可选品牌：" + "、".join(brands[:12]))
        lines.append("")
        for i, p in enumerate(products[:6], 1):
            faq = parse_faq(p.faq_text or "")
            lines.append(f"{i}. {p.item_name or '未命名商品'}")
            lines.append(f"   - 类型：{p.product_type or '-'}")
            lines.append(f"   - 品牌：{p.brand or '-'}")
            if p.color:
                lines.append(f"   - 颜色：{p.color}")
            if p.material:
                lines.append(f"   - 材质：{p.material}")
            bullets = (p.bullet_points or faq.get("bullet points", "")).strip()
            if bullets:
                tip = bullets.split("|")[0].strip()
                if tip:
                    lines.append(f"   - 卖点：{tip[:120]}")
            lines.append("")
        lines.append("可以继续问某个品牌，例如直接发品牌名。")
    return "\n".join(lines).strip()


def resolve_language(language: Optional[str], question: str) -> str:
    if language in ("zh", "en"):
        return language
    # auto
    if any("\u4e00" <= c <= "\u9fff" for c in question):
        return "zh"
    return "en"
