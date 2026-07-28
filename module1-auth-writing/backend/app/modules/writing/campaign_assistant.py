"""活动选品助手：主题活动 → 货盘匹配 → 营销角度与执行建议。"""
from __future__ import annotations

import random
import re
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.models.chat import AboProduct
from app.modules.writing.product_utils import serialize_product, feature_list, display_name

# 中文补充词 → 英文 ABO 文本同义词（让「轻便/降噪」等真正能命中英文货盘）
KEYWORD_ALIASES: Dict[str, List[str]] = {
    "轻便": ["lightweight", "light", "portable", "compact"],
    "便携": ["portable", "travel", "compact"],
    "送礼": ["gift", "present", "luxury", "elegant"],
    "礼物": ["gift", "present"],
    "降噪": ["noise", "cancelling", "canceling", "anc", "noise-cancelling"],
    "宿舍": ["dorm", "student", "campus", "school", "college"],
    "防水": ["waterproof", "water resistant", "water-resistant"],
    "透气": ["breathable", "mesh", "ventilat"],
    "舒适": ["comfort", "comfortable", "soft", "cushion"],
    "无线": ["wireless", "bluetooth"],
    "蓝牙": ["bluetooth", "wireless"],
    "运动": ["sport", "running", "training", "fitness", "athletic"],
    "跑步": ["running", "jog", "athletic"],
    "母婴": ["baby", "kids", "infant", "children"],
    "儿童": ["kids", "children", "child"],
    "宠物": ["pet", "dog", "cat"],
    "猫": ["cat", "kitten"],
    "狗": ["dog", "puppy"],
    "家居": ["home", "decor", "furniture", "sofa"],
    "沙发": ["sofa", "couch"],
    "开学": ["school", "student", "backpack", "campus"],
    "书包": ["backpack", "school bag"],
    "高颜值": ["premium", "elegant", "design", "stylish"],
    "耐用": ["durable", "sturdy", "long-lasting"],
    "收纳": ["storage", "organize", "organizer"],
}


def _tokenize_theme(text: str) -> List[str]:
    return re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,}", (text or "").strip())[:12]


def _expand_keywords(raw: List[str]) -> List[str]:
    """补充词扩展：保留原文 + 英文同义词，便于命中 ABO 英文字段。"""
    out: List[str] = []
    seen = set()
    for kw in raw:
        k = (kw or "").strip()
        if not k:
            continue
        candidates = [k] + KEYWORD_ALIASES.get(k, []) + KEYWORD_ALIASES.get(k.lower(), [])
        for c in candidates:
            cl = c.lower()
            if cl in seen:
                continue
            seen.add(cl)
            out.append(c)
    return out[:28]

# 预设活动（前端卡片 + 后端匹配共用）
CAMPAIGNS: List[Dict[str, Any]] = [
    {
        "id": "black_friday",
        "name": "黑五爆款冲刺",
        "tagline": "高转化折扣叙事 · 限时紧迫感",
        "audience": "价格敏感的跨境剁手党",
        "season": "11月",
        "types": ["HEADPHONES", "SHOES", "TECHNICAL_SPORT_SHOE", "WRIST_WATCH", "BACKPACK", "CELLULAR_PHONE_CASE", "SPORTING_GOODS"],
        "keywords": ["wireless", "bluetooth", "leather", "memory foam", "premium", "durable", "折扣", "爆款", "防水", "降噪"],
        "avoid": [],
        "language": "en",
        "platforms": ["TikTok", "Amazon", "Instagram"],
        "style": "casual",
        "poster_mood": "高对比促销海报 · 大折扣角标",
        "hooks": ["限时直降，手慢无", "黑五同款心智占位", "客单价友好的礼物清单"],
        "cta": "Shop the Deal",
        "checklist": ["突出折扣数字", "强调库存紧迫", "英文主文案 + 多平台短视频钩子"],
    },
    {
        "id": "back_to_school",
        "name": "开学焕新季",
        "tagline": "宿舍/通勤场景 · 轻便耐用",
        "audience": "学生与家长",
        "season": "8–9月",
        "types": ["BACKPACK", "SHOES", "TECHNICAL_SPORT_SHOE", "HEADPHONES", "OFFICE_PRODUCTS", "TABLE", "CHAIR"],
        "keywords": ["backpack", "school", "laptop", "lightweight", "durable", "student", "书包", "轻便", "宿舍"],
        "avoid": ["GROCERY"],
        "language": "zh",
        "platforms": ["TikTok", "Instagram"],
        "style": "casual",
        "poster_mood": "清新校园色 · 清单式卖点",
        "hooks": ["开学装备一次配齐", "轻便耐造，通勤不累", "宿舍桌面焕新三件套"],
        "cta": "开学季入手",
        "checklist": ["强调轻便/收纳", "场景化文案（宿舍/教室）", "种草口吻优于硬广"],
    },
    {
        "id": "maternity",
        "name": "母婴亲子精选",
        "tagline": "安心材质 · 情感共鸣",
        "audience": "新手爸妈与送礼亲友",
        "season": "全年",
        "types": ["HOME_BED_AND_BATH", "HOME", "CHAIR", "GROCERY", "HEALTH_PERSONAL_CARE", "PET_SUPPLIES"],
        "keywords": ["soft", "organic", "cotton", "gentle", "baby", "kids", "儿童", "柔软", "亲肤", "安全"],
        "avoid": ["CELLULAR_PHONE_CASE"],
        "language": "zh",
        "platforms": ["Instagram", "TikTok"],
        "style": "emotional",
        "poster_mood": "柔光亲子氛围 · 安心背书",
        "hooks": ["给宝宝更安心的日常", "礼物清单：实用又走心", "亲肤触感看得见"],
        "cta": "为家人选好",
        "checklist": ["避免夸张医疗承诺", "突出材质与安全", "情感向标题优先"],
    },
    {
        "id": "spring_festival",
        "name": "新春送礼指南",
        "tagline": "体面感 + 仪式感",
        "audience": "走亲访友的送礼人群",
        "season": "1–2月",
        "types": ["WRIST_WATCH", "FINERING", "FINEEARRING", "FINENECKLACEBRACELETANKLET", "HOME_FURNITURE_AND_DECOR", "RUG", "HOME"],
        "keywords": ["gift", "luxury", "silver", "gold", "elegant", "礼盒", "送礼", "典雅", "收藏"],
        "avoid": [],
        "language": "zh",
        "platforms": ["Instagram", "Amazon"],
        "style": "luxury",
        "poster_mood": "红金点缀 · 礼赠主视觉",
        "hooks": ["体面见面礼", "年味氛围感拉满", "开箱即高级"],
        "cta": "礼赠佳选",
        "checklist": ["强调礼盒感/高级感", "适合长辈/伴侣分层话术", "短标题利于海报叠字"],
    },
    {
        "id": "summer",
        "name": "夏日出行灵感",
        "tagline": "轻装上阵 · 户外与度假",
        "audience": "度假与城市漫步用户",
        "season": "6–8月",
        "types": ["SANDAL", "SHOES", "TECHNICAL_SPORT_SHOE", "BACKPACK", "SPORTING_GOODS", "HEADPHONES"],
        "keywords": ["sandal", "breathable", "waterproof", "travel", "summer", "轻便", "透气", "度假", "户外"],
        "avoid": ["BOOT"],
        "language": "en",
        "platforms": ["TikTok", "Instagram"],
        "style": "casual",
        "poster_mood": "高饱和夏日色 · 场景大片",
        "hooks": ["一双鞋走完假期", "轻装出门不将就", "海边到城市随心拍"],
        "cta": "Pack Light",
        "checklist": ["强调透气/便携", "英文短视频钩子", "场景图优先于白底图"],
    },
    {
        "id": "home_refresh",
        "name": "家居焕新计划",
        "tagline": "空间改造 · 氛围感家居",
        "audience": "租房与自住焕新人群",
        "season": "春季/搬家季",
        "types": ["SOFA", "CHAIR", "TABLE", "RUG", "HOME", "HOME_FURNITURE_AND_DECOR", "HOME_BED_AND_BATH", "LAMP"],
        "keywords": ["sofa", "oak", "modern", "decor", "rug", "comfort", "家居", "沙发", "氛围", "实木"],
        "avoid": ["CELLULAR_PHONE_CASE"],
        "language": "zh",
        "platforms": ["Instagram", "Amazon"],
        "style": "minimalist",
        "poster_mood": "空间感大图 · 尺寸卖点清晰",
        "hooks": ["一角空间立刻像样", "材质细节撑起高级感", "小改造大氛围"],
        "cta": "焕新这一角",
        "checklist": ["写清尺寸/材质", "极简文案风格", "海报突出空间场景"],
    },
    {
        "id": "fitness",
        "name": "运动健身燃脂季",
        "tagline": "表现力与坚持感",
        "audience": "健身入门与进阶用户",
        "season": "年初/夏前",
        "types": ["TECHNICAL_SPORT_SHOE", "SHOES", "SPORTING_GOODS", "HEADPHONES", "BACKPACK", "HEALTH_PERSONAL_CARE"],
        "keywords": ["sport", "running", "training", "fitness", "breathable", "运动", "跑步", "训练", "减震"],
        "avoid": ["GROCERY"],
        "language": "en",
        "platforms": ["TikTok", "Instagram"],
        "style": "professional",
        "poster_mood": "动感斜切构图 · 数据化卖点",
        "hooks": ["开练第一件装备", "减震透气不耽误", "训练日必备"],
        "cta": "Train Ready",
        "checklist": ["突出功能参数", "短句有力", "适合挑战赛话题"],
    },
    {
        "id": "pet",
        "name": "萌宠好物周",
        "tagline": "宠物主人的品质日常",
        "audience": "养宠家庭",
        "season": "全年",
        "types": ["PET_SUPPLIES"],
        "keywords": ["pet", "dog", "cat", "宠物", "猫", "狗", "耐磨", "防水"],
        "avoid": [],
        "language": "zh",
        "platforms": ["TikTok", "Instagram"],
        "style": "humorous",
        "poster_mood": "萌宠出镜 · 轻松配色",
        "hooks": ["主子同款生活质感", "耐造又好收拾", "开箱给毛孩子惊喜"],
        "cta": "给主子安排",
        "checklist": ["可爱语气但信息清楚", "突出耐用/易清洁", "适合短视频口播"],
    },
    {
        "id": "gift",
        "name": "节日礼赠精选",
        "tagline": "好送、好开箱、好晒图",
        "audience": "送礼困难户",
        "season": "节日节点",
        "types": ["WRIST_WATCH", "HEADPHONES", "FINERING", "FINEEARRING", "ACCESSORY", "HOME", "BACKPACK"],
        "keywords": ["gift", "premium", "elegant", "wireless", "礼", "精致", "高颜值"],
        "avoid": [],
        "language": "zh",
        "platforms": ["Instagram", "TikTok", "Amazon"],
        "style": "emotional",
        "poster_mood": "开箱仪式感 · 礼物丝带元素",
        "hooks": ["不会错的见面礼", "开箱瞬间有仪式感", "颜值与实用兼得"],
        "cta": "送给重要的人",
        "checklist": ["按预算分层推荐", "强调开箱体验", "适合节日话题标签"],
    },
]


def list_campaigns() -> List[Dict[str, Any]]:
    return [
        {
            "id": c["id"],
            "name": c["name"],
            "tagline": c["tagline"],
            "audience": c["audience"],
            "season": c["season"],
            "language": c["language"],
            "platforms": c["platforms"],
            "style": c["style"],
            "poster_mood": c["poster_mood"],
            "hooks": c["hooks"],
            "cta": c["cta"],
        }
        for c in CAMPAIGNS
    ]


def _get_campaign(campaign_id: str) -> Optional[Dict[str, Any]]:
    for c in CAMPAIGNS:
        if c["id"] == campaign_id:
            return c
    return None


def _blob(p: AboProduct) -> str:
    parts = [
        p.item_name or "",
        p.item_name_zh or "",
        p.brand or "",
        p.brand_zh or "",
        p.product_type or "",
        p.bullet_points or "",
        p.bullet_points_zh or "",
        p.material or "",
        p.color or "",
    ]
    return " ".join(parts).lower()


def _type_hit(product_type: str, wanted: List[str]) -> bool:
    pt = (product_type or "").upper()
    if not pt:
        return False
    for w in wanted:
        wu = w.upper()
        if wu in pt or pt in wu:
            return True
    return False


def _score_product(p: AboProduct, campaign: Dict[str, Any], custom_keywords: List[str]) -> Tuple[float, List[str]]:
    reasons: List[str] = []
    score = 22.0
    blob = _blob(p)
    pt = p.product_type or ""
    expanded_custom = _expand_keywords(custom_keywords)

    if _type_hit(pt, campaign.get("types") or []):
        score += 32
        reasons.append("品类与活动主题高度契合")
    elif any(k.lower() in blob for k in (campaign.get("keywords") or [])[:8]):
        score += 14
        reasons.append("卖点关键词命中活动叙事")

    for bad in campaign.get("avoid") or []:
        if _type_hit(pt, [bad]) or bad.lower() in blob:
            score -= 22
            reasons.append("与活动主线略有偏离，谨慎投放")
            break

    # 用户补充词：强加权（这是「补充关键词」的核心价值）
    custom_hits = 0
    hit_labels = []
    for kw in expanded_custom:
        if kw and kw.lower() in blob:
            custom_hits += 1
            if kw in custom_keywords or any(kw in KEYWORD_ALIASES.get(c, []) for c in custom_keywords):
                hit_labels.append(kw)
    if custom_hits:
        score += min(36, 10 + custom_hits * 5)
        show = "、".join((hit_labels or expanded_custom)[:3])
        reasons.append(f"命中补充词：{show}")

    kw_hits = 0
    for kw in campaign.get("keywords") or []:
        if kw and kw.lower() in blob:
            kw_hits += 1
    if kw_hits and not custom_hits:
        score += min(14, kw_hits * 2.5)
        reasons.append(f"命中 {kw_hits} 个主题关键词")

    feats = feature_list(p, 6)
    if len(feats) >= 3:
        score += 8
        reasons.append("卖点完整，便于种草文案展开")
    elif feats:
        score += 3

    if p.brand or p.brand_zh:
        score += 4

    if p.image_path:
        score += 14
        reasons.append("有官方主图，海报链路更顺")
    else:
        score -= 4

    name = display_name(p)
    if name and len(name) >= 12:
        score += 2

    # 用户给了补充词却完全没命中：明显降权，避免「看起来没作用」
    if expanded_custom and custom_hits == 0:
        score -= 16
        reasons.append("未命中你的补充词，仅作品类兜底")

    score += random.uniform(-1.8, 1.8)
    score = max(8.0, min(98.0, score))

    if not reasons:
        reasons.append("可作为活动货盘补充款")
    return score, reasons[:3]


def _angle_for(p: AboProduct, campaign: Dict[str, Any], reasons: List[str]) -> str:
    hooks = campaign.get("hooks") or ["活动主推"]
    cat = (p.product_type or "商品").replace("_", " ").title()
    brand = (p.brand_zh or p.brand or "").strip()
    base = random.choice(hooks)
    if brand:
        return f"{base} · {brand} {cat}"
    return f"{base} · {cat}"


def _fit_level(score: float) -> str:
    if score >= 78:
        return "高匹配"
    if score >= 58:
        return "可主推"
    return "备选"


def _build_custom_campaign(theme: str, market: str) -> Dict[str, Any]:
    theme = (theme or "").strip() or "自定义活动"
    market_lang = {"us": "en", "uk": "en", "jp": "ja", "kr": "ko", "cn": "zh", "es": "es"}.get(market, "zh")
    # 从主题里猜品类
    type_guess = []
    mapping = [
        (("鞋", "shoe", "sneaker", "靴"), ["SHOES", "TECHNICAL_SPORT_SHOE", "BOOT", "SANDAL"]),
        (("家", "sofa", "家具", "rug"), ["SOFA", "CHAIR", "TABLE", "RUG", "HOME", "HOME_FURNITURE_AND_DECOR"]),
        (("耳机", "headphone", "audio"), ["HEADPHONES"]),
        (("宠", "pet", "猫", "狗"), ["PET_SUPPLIES"]),
        (("礼", "gift", "表", "饰"), ["WRIST_WATCH", "FINERING", "ACCESSORY", "HEADPHONES"]),
        (("运动", "健身", "sport", "fit"), ["SPORTING_GOODS", "TECHNICAL_SPORT_SHOE"]),
        (("开学", "书包", "school"), ["BACKPACK", "OFFICE_PRODUCTS", "SHOES"]),
        (("母婴", "宝宝", "baby"), ["HOME_BED_AND_BATH", "HEALTH_PERSONAL_CARE"]),
    ]
    low = theme.lower()
    for keys, types in mapping:
        if any(k in low for k in keys):
            type_guess.extend(types)
    if not type_guess:
        type_guess = ["SHOES", "HEADPHONES", "HOME", "BACKPACK", "GROCERY", "SPORTING_GOODS"]

    kws = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,}", theme)
    return {
        "id": "custom",
        "name": f"自定义 · {theme[:18]}",
        "tagline": "按你的主题即时匹配货盘",
        "audience": "活动目标人群（自定义）",
        "season": "即时",
        "types": list(dict.fromkeys(type_guess)),
        "keywords": kws[:12] or [theme[:20]],
        "avoid": [],
        "language": market_lang,
        "platforms": ["TikTok", "Instagram", "Amazon"],
        "style": "casual",
        "poster_mood": "主题氛围海报 · 突出活动名",
        "hooks": [f"{theme}主推卖点", f"围绕「{theme}」讲场景故事", "清单式种草更容易转化"],
        "cta": "马上参与",
        "checklist": ["核对目标市场语言", "标题短、卖点清", "海报与文案同一叙事"],
    }


def _candidate_query(
    db: Session,
    campaign: Dict[str, Any],
    *,
    custom_keywords: Optional[List[str]] = None,
    limit_pool: int = 260,
) -> List[AboProduct]:
    types = campaign.get("types") or []
    keywords = _expand_keywords(list(campaign.get("keywords") or []) + list(custom_keywords or []))
    has_img = AboProduct.image_path.isnot(None) & (AboProduct.image_path != "")

    type_filters = [AboProduct.product_type.ilike(f"%{t}%") for t in types]
    kw_filters = []
    for kw in keywords[:16]:
        like = f"%{kw}%"
        kw_filters.extend([
            AboProduct.item_name.ilike(like),
            AboProduct.item_name_zh.ilike(like),
            AboProduct.bullet_points.ilike(like),
            AboProduct.bullet_points_zh.ilike(like),
            AboProduct.brand.ilike(like),
            AboProduct.faq_text.ilike(like),
        ])

    rows: List[AboProduct] = []
    seen = set()

    def _add(batch: List[AboProduct]):
        for p in batch:
            if p.id in seen:
                continue
            seen.add(p.id)
            rows.append(p)

    # 1) 有补充词时：优先捞「补充词命中」的货（真正检索）
    if custom_keywords and kw_filters:
        focused = (
            db.query(AboProduct)
            .filter(or_(*kw_filters))
            .order_by(has_img.desc(), func.random())
            .limit(min(160, limit_pool))
            .all()
        )
        _add(focused)

    # 2) 品类池
    if type_filters and len(rows) < limit_pool:
        typed = (
            db.query(AboProduct)
            .filter(or_(*type_filters))
            .order_by(has_img.desc(), func.random())
            .limit(limit_pool - len(rows))
            .all()
        )
        _add(typed)

    # 3) 主题关键词兜底
    if kw_filters and len(rows) < 80:
        more = (
            db.query(AboProduct)
            .filter(or_(*kw_filters))
            .order_by(has_img.desc(), func.random())
            .limit(100)
            .all()
        )
        _add(more)

    if len(rows) < 40:
        extra = (
            db.query(AboProduct)
            .order_by(has_img.desc(), func.random())
            .limit(80)
            .all()
        )
        _add(extra)

    return rows[:limit_pool]


def recommend_campaign(
    db: Session,
    *,
    campaign_id: str = "black_friday",
    theme: str = "",
    market: str = "cn",
    limit: int = 8,
) -> Dict[str, Any]:
    limit = max(3, min(16, int(limit or 8)))
    custom_keywords: List[str] = []

    if campaign_id == "custom" or (theme and campaign_id not in {c["id"] for c in CAMPAIGNS}):
        campaign = _build_custom_campaign(theme or campaign_id, market)
        custom_keywords = _tokenize_theme(theme or campaign_id)
    else:
        campaign = _get_campaign(campaign_id) or CAMPAIGNS[0]
        if theme.strip():
            custom_keywords = _tokenize_theme(theme)
            campaign = {
                **campaign,
                "keywords": list(campaign.get("keywords") or []) + custom_keywords,
            }

    market_lang = {"us": "en", "uk": "en", "jp": "ja", "kr": "ko", "cn": "zh", "es": "es"}.get(market)
    language = market_lang or campaign.get("language") or "zh"

    pool = _candidate_query(db, campaign, custom_keywords=custom_keywords)
    scored: List[Tuple[float, AboProduct, List[str]]] = []
    for p in pool:
        s, reasons = _score_product(p, campaign, custom_keywords)
        scored.append((s, p, reasons))
    scored.sort(key=lambda x: (x[0], 1 if x[1].image_path else 0), reverse=True)

    # 有补充词时：优先保留命中补充词的商品
    if custom_keywords:
        expanded = {k.lower() for k in _expand_keywords(custom_keywords)}
        hit_first = []
        rest = []
        for item in scored:
            blob = _blob(item[1])
            if any(k in blob for k in expanded):
                hit_first.append(item)
            else:
                rest.append(item)
        scored = hit_first + rest

    picked: List[Tuple[float, AboProduct, List[str]]] = []
    type_count: Dict[str, int] = {}
    for s, p, reasons in scored:
        key = (p.product_type or "OTHER").upper()
        if type_count.get(key, 0) >= 2:
            continue
        type_count[key] = type_count.get(key, 0) + 1
        picked.append((s, p, reasons))
        if len(picked) >= limit:
            break
    if len(picked) < limit:
        for s, p, reasons in scored:
            if any(p.id == x[1].id for x in picked):
                continue
            picked.append((s, p, reasons))
            if len(picked) >= limit:
                break

    items = []
    for s, p, reasons in picked:
        product = serialize_product(p)
        angle = _angle_for(p, campaign, reasons)
        items.append({
            "product": product,
            "score": int(round(s)),
            "fit_level": _fit_level(s),
            "reasons": reasons,
            "angle": angle,
            "platforms": list(campaign.get("platforms") or ["TikTok"]),
            "language": language,
            "style": campaign.get("style") or "casual",
            "poster_hook": f"{campaign['name']} · {(campaign.get('hooks') or ['主推'])[0]}",
            "cta": campaign.get("cta") or "立即了解",
            "poster_mood": campaign.get("poster_mood") or "",
        })

    brief = {
        "campaign_id": campaign["id"],
        "name": campaign["name"],
        "tagline": campaign.get("tagline") or "",
        "audience": campaign.get("audience") or "",
        "season": campaign.get("season") or "",
        "theme": theme.strip() or campaign["name"],
        "market": market,
        "language": language,
        "platforms": campaign.get("platforms") or [],
        "style": campaign.get("style") or "casual",
        "poster_mood": campaign.get("poster_mood") or "",
        "hooks": campaign.get("hooks") or [],
        "cta": campaign.get("cta") or "",
        "checklist": campaign.get("checklist") or [],
        "matched": len(items),
        "pool_scanned": len(pool),
        "supplement_keywords": custom_keywords,
        "expanded_keywords": _expand_keywords(custom_keywords)[:12],
    }
    return {"brief": brief, "items": items, "campaign": {
        "id": campaign["id"],
        "name": campaign["name"],
        "tagline": campaign.get("tagline"),
    }}