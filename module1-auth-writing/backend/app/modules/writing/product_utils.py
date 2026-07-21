"""ABO 商品序列化 & 海报文案辅助（文案/海报/抠图共用）"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.models.chat import AboProduct

# 英文 product_type → 中文品类（海报/背景用）
TYPE_ZH = {
    "CELLULAR_PHONE_CASE": "手机壳",
    "HEADPHONES": "耳机",
    "SHOES": "鞋子",
    "TECHNICAL_SPORT_SHOE": "运动鞋",
    "SANDAL": "凉鞋",
    "BOOT": "靴子",
    "SOFA": "沙发",
    "CHAIR": "椅子",
    "TABLE": "桌子",
    "WRIST_WATCH": "手表",
    "BACKPACK": "背包",
    "GROCERY": "食品",
    "HOME": "家居",
    "HOME_BED_AND_BATH": "床品卫浴",
    "HOME_FURNITURE_AND_DECOR": "家具装饰",
    "FINERING": "戒指",
    "FINEEARRING": "耳环",
    "FINENECKLACEBRACELETANKLET": "项链手链",
    "OFFICE_PRODUCTS": "办公用品",
    "PET_SUPPLIES": "宠物用品",
    "SPORTING_GOODS": "运动用品",
    "RUG": "地毯",
    "ACCESSORY": "配饰",
    "HEALTH_PERSONAL_CARE": "个护健康",
}


def type_to_zh(product_type: Optional[str]) -> str:
    if not product_type:
        return "商品"
    key = product_type.strip().upper()
    if key in TYPE_ZH:
        return TYPE_ZH[key]
    # 模糊
    for en, zh in TYPE_ZH.items():
        if en in key or key in en:
            return zh
    return product_type.replace("_", " ").title()


def display_name(p: AboProduct) -> str:
    return (p.item_name_zh or p.item_name or p.item_id or "").strip()


def feature_list(p: AboProduct, limit: int = 6) -> List[str]:
    parts: List[str] = []
    bullets = (p.bullet_points_zh or p.bullet_points or "").strip()
    if bullets:
        for piece in re.split(r"\s*\|\s*", bullets):
            piece = piece.strip()
            if piece:
                parts.append(piece)
    if p.brand_zh or p.brand:
        parts.append(f"品牌：{(p.brand_zh or p.brand).strip()}")
    if p.material_zh or p.material:
        parts.append(f"材质：{(p.material_zh or p.material).strip()}")
    if p.color:
        parts.append(f"颜色：{p.color.strip()}")
    if p.product_type:
        parts.append(f"品类：{p.product_type}")
    seen = set()
    uniq = []
    for x in parts:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq[:limit]


def features_text(p: AboProduct) -> str:
    return "；".join(feature_list(p, 8))[:500]


def serialize_product(p: AboProduct) -> Dict[str, Any]:
    name = display_name(p)
    feats = feature_list(p)
    cat_zh = type_to_zh(p.product_type)
    return {
        "id": p.id,
        "item_id": p.item_id,
        "name": name,
        "item_name": p.item_name or "",
        "item_name_zh": p.item_name_zh or "",
        "brand": (p.brand_zh or p.brand or "") or "",
        "product_type": p.product_type or "",
        "category": cat_zh,
        "category_en": (p.product_type or "product").lower(),
        "color": p.color or "",
        "material": (p.material_zh or p.material or "") or "",
        "features": features_text(p),
        "feature_list": feats,
        "main_image_id": p.main_image_id or "",
        "image_path": p.image_path or "",
        "image_url": p.image_url,
        "label": f"{name}" + (f" · {cat_zh}" if cat_zh else ""),
        "has_image": bool(p.image_path),
    }


def build_poster_copy(p: AboProduct, language: str = "zh") -> Dict[str, str]:
    """根据库内字段直接生成海报文案（不依赖 LLM，可即时填入）。"""
    name = display_name(p)
    title = name if len(name) <= 36 else (name[:34] + "…")
    brand = (p.brand_zh or p.brand or "").strip()
    feats = feature_list(p, 8)
    # 只要真实卖点句，去掉结构化前缀
    skip_prefix = ("品牌：", "品类：", "颜色：", "材质：")
    pure = [f for f in feats if not f.startswith(skip_prefix)]
    if not pure and p.bullet_points:
        pure = [x.strip() for x in re.split(r"\s*\|\s*", p.bullet_points) if x.strip()][:4]

    if language == "en":
        subtitle = brand or (pure[0] if pure else (p.color or "Premium Pick"))
        sp1 = pure[0] if pure else (p.color or "Quality Materials")
        sp2 = pure[1] if len(pure) > 1 else (p.material or type_to_zh(p.product_type) or "Everyday Essential")
        cta = "Shop Now"
    else:
        subtitle = brand or type_to_zh(p.product_type) or (p.color or "精选好物")
        if len(subtitle) > 28:
            subtitle = subtitle[:26] + "…"
        sp1 = pure[0] if pure else (p.color or "品质精选")
        sp2 = pure[1] if len(pure) > 1 else ((p.material or type_to_zh(p.product_type)) or "热销推荐")
        if len(sp1) > 28:
            sp1 = sp1[:26] + "…"
        if len(sp2) > 28:
            sp2 = sp2[:26] + "…"
        cta = "立即购买"
    return {
        "title": title,
        "subtitle": subtitle,
        "selling_point_1": sp1,
        "selling_point_2": sp2,
        "cta_text": cta,
        "discount": "",
        "price": cta,
    }
