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


def _demo_image_for_type(product_type: Optional[str]) -> str:
    """无 ABO 实图时的本地演示缩略图（商家选品中心 / 文案共用）。"""
    pt = (product_type or "").upper()
    if any(k in pt for k in ("HEADPHONE", "EARPHONE", "EARBUD", "AUDIO", "ELECTRONIC")):
        name = "headphones.svg"
    elif any(k in pt for k in ("SHOE", "FOOTWEAR", "SANDAL", "BOOT", "SNEAKER")):
        name = "shoes.svg"
    elif any(k in pt for k in ("BOTTLE", "KITCHEN", "CUP", "MUG")):
        name = "bottle.svg"
    elif any(k in pt for k in ("APPAREL", "SHIRT", "DRESS", "CLOTH")):
        name = "apparel.svg"
    elif any(k in pt for k in ("HOME", "LAMP", "FURNITURE", "SOFA", "CHAIR", "TABLE", "RUG")):
        name = "home.svg"
    else:
        name = "product.svg"
    return f"/static/demo-products/{name}"


def resolve_product_image_url(p: AboProduct) -> Optional[str]:
    url = getattr(p, "image_url", None)
    if url:
        return url
    path = (getattr(p, "image_path", None) or "").strip()
    if path.startswith("http://") or path.startswith("https://") or path.startswith("/static/"):
        return path
    return _demo_image_for_type(getattr(p, "product_type", None))


def serialize_product(p: AboProduct) -> Dict[str, Any]:
    name = display_name(p)
    feats = feature_list(p)
    cat_zh = type_to_zh(p.product_type)
    image_url = resolve_product_image_url(p)
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
        "image_url": image_url,
        "label": f"{name}" + (f" · {cat_zh}" if cat_zh else ""),
        "has_image": bool(p.image_path),
    }


_SIMILAR_STOP = {
    "the", "and", "for", "with", "from", "amazon", "brand", "color", "size",
    "品牌", "颜色", "材质", "品类", "商品", "官方",
}


def _similarity_tokens(text: str) -> set:
    blob = (text or "").lower()
    tokens = re.findall(r"[a-z0-9]{2,}|[\u4e00-\u9fff]{2,}", blob)
    return {t for t in tokens if t not in _SIMILAR_STOP}


def _product_text_blob(p: AboProduct) -> str:
    return " ".join(
        filter(
            None,
            [
                display_name(p),
                p.item_name or "",
                p.item_name_zh or "",
                p.bullet_points or "",
                p.bullet_points_zh or "",
                p.color or "",
                p.material or "",
                p.material_zh or "",
            ],
        )
    )


def similarity_score(source: AboProduct, candidate: AboProduct) -> float:
    """同款延伸打分：品类接近 + 品牌加成 + 名称/卖点词重叠，有主图加分。"""
    score = 0.0
    src_type = (source.product_type or "").strip().upper()
    cand_type = (candidate.product_type or "").strip().upper()
    if src_type and cand_type:
        if src_type == cand_type:
            score += 40
        elif src_type in cand_type or cand_type in src_type:
            score += 25

    src_brand = (source.brand_zh or source.brand or "").strip().lower()
    cand_brand = (candidate.brand_zh or candidate.brand or "").strip().lower()
    if src_brand and cand_brand:
        if src_brand == cand_brand or src_brand in cand_brand or cand_brand in src_brand:
            score += 20

    src_tokens = _similarity_tokens(_product_text_blob(source))
    cand_tokens = _similarity_tokens(_product_text_blob(candidate))
    if src_tokens and cand_tokens:
        overlap = len(src_tokens & cand_tokens)
        score += min(30.0, overlap * 5.0)

    if getattr(candidate, "image_path", None):
        score += 15

    return score


def _ilike_pattern(value: str) -> str:
    """Escape LIKE wildcards so brand/type literals don't broaden or break the query."""
    escaped = (
        (value or "")
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
    return f"%{escaped}%"


def find_similar_products(
    db,
    source: AboProduct,
    *,
    limit: int = 8,
    pool_size: int = 80,
) -> List[AboProduct]:
    """在 ABO 库中找相似款：同/近品类优先，有图优先，排除自身。"""
    from sqlalchemy import or_, func

    limit = max(1, min(int(limit or 8), 12))
    pool_size = max(limit, min(int(pool_size or 80), 120))
    product_type = (source.product_type or "").strip()
    brand = (source.brand_zh or source.brand or "").strip()

    base = db.query(AboProduct).filter(AboProduct.id != source.id)
    candidates: List[AboProduct] = []
    seen = set()

    def _extend(rows):
        for p in rows:
            if p.id in seen:
                continue
            seen.add(p.id)
            candidates.append(p)

    if product_type:
        typed_q = base.filter(AboProduct.product_type.ilike(_ilike_pattern(product_type), escape="\\"))
        # 先取有主图的同品类，不够再补无图
        imaged = (
            typed_q.filter(AboProduct.image_path.isnot(None), AboProduct.image_path != "")
            .order_by(func.random())
            .limit(pool_size)
            .all()
        )
        _extend(imaged)
        if len(candidates) < pool_size:
            more_typed = (
                typed_q.order_by(AboProduct.image_path.isnot(None).desc())
                .limit(pool_size)
                .all()
            )
            _extend(more_typed)

    if brand and len(candidates) < pool_size:
        brand_pat = _ilike_pattern(brand)
        branded = (
            base.filter(
                or_(
                    AboProduct.brand.ilike(brand_pat, escape="\\"),
                    AboProduct.brand_zh.ilike(brand_pat, escape="\\"),
                )
            )
            .order_by(AboProduct.image_path.isnot(None).desc())
            .limit(pool_size - len(candidates))
            .all()
        )
        _extend(branded)

    if len(candidates) < limit:
        # 词重叠兜底：用名称关键词扩池
        tokens = list(_similarity_tokens(_product_text_blob(source)))[:4]
        if tokens:
            likes = [
                or_(
                    AboProduct.item_name.ilike(_ilike_pattern(t), escape="\\"),
                    AboProduct.item_name_zh.ilike(_ilike_pattern(t), escape="\\"),
                    AboProduct.bullet_points.ilike(_ilike_pattern(t), escape="\\"),
                    AboProduct.bullet_points_zh.ilike(_ilike_pattern(t), escape="\\"),
                )
                for t in tokens
            ]
            more = (
                base.filter(or_(*likes))
                .order_by(AboProduct.image_path.isnot(None).desc())
                .limit(pool_size)
                .all()
            )
            _extend(more)

    if not candidates:
        return []

    ranked = sorted(
        candidates,
        key=lambda p: (
            similarity_score(source, p),
            1 if (getattr(p, "image_path", None) or "").strip() else 0,
        ),
        reverse=True,
    )
    # 至少要有一定相关性，避免乱推
    filtered = [p for p in ranked if similarity_score(source, p) >= 15]
    return (filtered or ranked)[:limit]


def _clip(text: str, n: int, ellipsis: bool = False) -> str:
    """按长度裁剪；英文在空格处断开，避免 Darjeeling Te… 这种半词。"""
    text = (text or "").strip()
    if len(text) <= n:
        return text
    cut = text[:n]
    has_cjk = any("\u4e00" <= c <= "\u9fff" for c in cut)
    if not has_cjk and " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    cut = cut.rstrip(" .,;:|-–—/")
    if not cut:
        cut = text[: max(1, n - (1 if ellipsis else 0))]
    return f"{cut}…" if ellipsis else cut


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
    # 海报标题交给排版换行，这里只做软裁剪且不打断英文单词、不加省略号
    limit = 40 if language != "en" else 56
    return _clip(raw or name, limit, ellipsis=False)


def _infer_category_zh(p: AboProduct) -> str:
    """优先从商品名推断品类，避免 ABO product_type 误标。"""
    name = f"{display_name(p)} {(p.item_name or '')}".lower()
    hints = [
        (("parmesan", "cheese", "奶酪", "芝士", "butter", "黄油", "snack", "零食", "coffee", "咖啡", "tea", "茶叶", "darjeeling"), "食品"),
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
        subtitle, sp1, sp2 = _clip(subtitle, 48, False), _clip(sp1, 64, False), _clip(sp2, 64, False)
    else:
        cat = _infer_category_zh(p)
        if brand and cat:
            subtitle = f"{brand} · {cat}"
        else:
            subtitle = brand or cat or (p.color or "精选好物")
        sp1 = pure[0] if pure else (p.color or "品质精选")
        sp2 = pure[1] if len(pure) > 1 else ((p.material or cat) or "热销推荐")
        subtitle, sp1, sp2 = _clip(subtitle, 40, False), _clip(sp1, 56, False), _clip(sp2, 56, False)
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
                "title": _clip(str(data.get("title") or base["title"]), 48, False),
                "subtitle": _clip(str(data.get("subtitle") or base["subtitle"]), 56, False),
                "selling_point_1": _clip(str(data.get("selling_point_1") or base["selling_point_1"]), 64, False),
                "selling_point_2": _clip(str(data.get("selling_point_2") or base["selling_point_2"]), 64, False),
                "cta_text": _clip(str(data.get("cta_text") or base["cta_text"]), 12, False),
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
