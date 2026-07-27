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
    "PORTABLE_ELECTRONIC_DEVICE_COVER": "数码保护套",
    "ELECTRONIC_DEVICE_COVER": "数码保护套",
    "TABLET_CASE": "平板保护套",
    "PHONE_CASE": "手机壳",
}


def type_to_zh(product_type: Optional[str]) -> str:
    if not product_type:
        return "商品"
    key = product_type.strip().upper()
    if key in TYPE_ZH:
        return TYPE_ZH[key]
    # 按 key 长度降序匹配，避免 TABLE 误匹配 TABLET / PORTABLE_TABLET 等
    for en, zh in sorted(TYPE_ZH.items(), key=lambda x: -len(x[0])):
        if key == en or key.startswith(en + "_") or key.endswith("_" + en) or f"_{en}_" in key:
            return zh
    return product_type.replace("_", " ").title()


def infer_scene_from_product(
    *,
    name: str = "",
    product_type: str = "",
    category: str = "",
) -> str:
    """根据商品名/类型推断更适合的背景场景（纠正误判品类）。"""
    blob = f"{name} {product_type} {category}".lower()
    rules = [
        (("tablet", "kindle", "ipad", "sleeve", "case", "phone", "手机", "平板", "保护套", "手机壳"), "数码配件陈列台 / desk for electronics accessories"),
        (("headphone", "earphone", "earbud", "耳机"), "现代桌面听歌场景 / modern desk audio lifestyle"),
        (("shoe", "sneaker", "boot", "sandal", "鞋"), "极简鞋履展台 / minimal footwear pedestal"),
        (("sofa", "chair", "table", "家具", "沙发", "椅子", "桌子"), "明亮家居空间 / bright home interior"),
        (("watch", "手表"), "高级腕表展柜 / luxury watch display"),
        (("bag", "backpack", "包"), "生活方式街拍背景 / lifestyle street backdrop"),
        (("food", "grocery", "食品"), "清新厨房台面 / fresh kitchen counter"),
        (("cosmetic", "beauty", "护肤", "美妆"), "柔光梳妆台 / soft vanity counter"),
    ]
    for keys, scene in rules:
        if any(k in blob for k in keys):
            return scene
    if category and category not in ("商品", "桌子"):
        return f"{category} 电商场景"
    if product_type:
        return f"{product_type.replace('_', ' ').title()} e-commerce display scene"
    return "premium e-commerce product display scene"


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


def _clip(text: str, n: int) -> str:
    text = (text or "").strip()
    if len(text) <= n:
        return text
    return text[: max(1, n - 1)] + "…"


def _sanitize_copy_text(text: str) -> str:
    """去掉 emoji/特殊符号，避免海报字体方框。"""
    if not text:
        return ""
    out = []
    for ch in str(text):
        o = ord(ch)
        if ch in " ··-–—&/|%+.,:;!?()[]【】「」《》…•":
            out.append(ch)
            continue
        if (
            ("0" <= ch <= "9")
            or ("a" <= ch <= "z")
            or ("A" <= ch <= "Z")
            or ("\u4e00" <= ch <= "\u9fff")
        ):
            out.append(ch)
            continue
        if o < 32 or o > 0xFFFF or (0x2000 <= o <= 0x2BFF) or (0xE000 <= o <= 0xF8FF):
            continue
    return re.sub(r"\s+", " ", "".join(out)).strip()


def _short_title_from_name(name: str, brand: str, language: str) -> str:
    """把过长商品名压成海报主标题：去掉品牌前缀/尺寸噪音，保留品类核心。"""
    raw = _sanitize_copy_text(name)
    if not raw:
        return "精选好物" if language != "en" else "Featured Pick"
    raw = re.sub(r"^(Amazon\s*品牌\s*[-–—]\s*|亚马逊.*?[-–—]\s*)", "", raw, flags=re.I)
    if brand and raw.lower().startswith(brand.lower()):
        raw = raw[len(brand) :].lstrip(" ··-–—:")
    raw = re.split(r"[，,。；（(]", raw)[0].strip()
    raw = re.sub(r"\d+(\.\d+)?\s*(厘米|cm|英寸|inch|mm)\b.*$", "", raw, flags=re.I).strip()
    # 英文标题放宽，避免 Darjeeling Te… 这种半词截断；布局侧再换行
    limit = 28 if language != "en" else 42
    return _clip(raw or name, limit)


def _infer_category_zh(p: AboProduct) -> str:
    """优先从商品名推断品类，避免 ABO product_type 误标。"""
    name = f"{display_name(p)} {(p.item_name or '')}".lower()
    hints = [
        (("parmesan", "cheese", "奶酪", "芝士", "butter", "黄油", "snack", "零食", "coffee", "咖啡"), "食品"),
        (("earbud", "earphone", "headphone", "耳机", "蓝牙耳机"), "耳机"),
        (("chair", "椅子", "sofa", "沙发", "table", "茶几", "桌子"), "家具"),
        (("kettle", "水壶", "thermos", "保温杯"), "家居日用"),
        (("shoe", "鞋", "sneaker", "跑鞋"), "鞋靴"),
        (("watch", "手表"), "手表"),
        (("phone case", "手机壳", "保护套"), "手机壳"),
    ]
    for keys, zh in hints:
        if any(k in name for k in keys):
            return zh
    return type_to_zh(p.product_type)


def build_poster_copy(p: AboProduct, language: str = "zh") -> Dict[str, str]:
    """根据库内字段直接生成海报文案（不依赖 LLM，可即时填入）。"""
    name = display_name(p)
    brand = (p.brand_zh or p.brand or "").strip()
    title = _short_title_from_name(name, brand, language)
    feats = feature_list(p, 8)
    skip_prefix = ("品牌：", "品类：", "颜色：", "材质：")
    pure = [f for f in feats if not f.startswith(skip_prefix)]
    if not pure and p.bullet_points:
        pure = [x.strip() for x in re.split(r"\s*\|\s*", p.bullet_points) if x.strip()][:4]

    if language == "en":
        subtitle = brand or (pure[0] if pure else (p.color or "Premium Pick"))
        sp1 = pure[0] if pure else (p.color or "Quality Materials")
        sp2 = pure[1] if len(pure) > 1 else (p.material or _infer_category_zh(p) or "Everyday Essential")
        cta = "Shop Now"
        subtitle, sp1, sp2 = _clip(subtitle, 40), _clip(sp1, 48), _clip(sp2, 48)
    else:
        cat = _infer_category_zh(p)
        if brand and cat:
            subtitle = f"{brand} · {cat}"
        else:
            subtitle = brand or cat or (p.color or "精选好物")
        sp1 = pure[0] if pure else (p.color or "品质精选")
        sp2 = pure[1] if len(pure) > 1 else ((p.material or cat) or "热销推荐")
        subtitle, sp1, sp2 = _clip(subtitle, 36), _clip(sp1, 40), _clip(sp2, 40)
        cta = "立即选购"
    return {
        "title": _sanitize_copy_text(title),
        "subtitle": _sanitize_copy_text(subtitle),
        "selling_point_1": _sanitize_copy_text(sp1),
        "selling_point_2": _sanitize_copy_text(sp2),
        "cta_text": cta,
        "discount": "",
        "price": cta,
        "source": "kb",
    }


async def refine_poster_copy_with_llm(
    p: AboProduct,
    base: Optional[Dict[str, str]] = None,
    language: str = "zh",
) -> Dict[str, str]:
    """知识库字段 + DeepSeek：压成适合海报叠字的短文案（失败则回退 base）。"""
    import json
    import httpx
    from app.core.config import settings

    base = dict(base or build_poster_copy(p, language))
    name = display_name(p)
    brand = (p.brand_zh or p.brand or "").strip()
    feats = features_text(p)
    if not settings.LLM_API_KEY:
        base["source"] = "kb"
        return base

    lang_label = "中文" if language != "en" else "English"
    system = (
        "你是电商海报文案专家。输出必须适合叠在商品海报上阅读："
        "短、有钩子、层次分明，不要长句和标点堆砌。"
        "只返回 JSON，不要 markdown。"
    )
    user = f"""根据商品信息，生成海报短文案（语言：{lang_label}）。

商品名：{name}
品牌：{brand or "未知"}
品类：{type_to_zh(p.product_type)}
卖点素材：{feats[:400]}
参考草稿：{json.dumps(base, ensure_ascii=False)}

字段要求：
- title：主标题，中文≤20字 / 英文≤36字符，完整单词，不要截断半词
- subtitle：副标题钩子，中文≤24字，可含品牌或场景感
- selling_point_1 / selling_point_2：各一条完整短卖点，中文≤24字 / 英文≤40字符，不要省略号
- cta_text：行动号召，中文≤6字（如「立即选购」），英文≤12字符

返回 JSON：
{{"title":"...","subtitle":"...","selling_point_1":"...","selling_point_2":"...","cta_text":"..."}}
"""
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                settings.LLM_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 400,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("\n```", 1)[0]
            data = json.loads(content)
            out = {
                "title": _clip(str(data.get("title") or base["title"]), 36 if language != "en" else 48),
                "subtitle": _clip(str(data.get("subtitle") or base["subtitle"]), 40 if language != "en" else 56),
                "selling_point_1": _clip(str(data.get("selling_point_1") or base["selling_point_1"]), 48),
                "selling_point_2": _clip(str(data.get("selling_point_2") or base["selling_point_2"]), 48),
                "cta_text": _clip(str(data.get("cta_text") or base["cta_text"]), 10 if language != "en" else 14),
                "discount": "",
                "price": "",
                "source": "kb+llm",
            }
            out["price"] = out["cta_text"]
            return out
    except Exception as exc:
        print(f"[poster-copy] LLM refine skipped: {exc}")
        base["source"] = "kb"
        return base
