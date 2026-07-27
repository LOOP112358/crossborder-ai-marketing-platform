"""启动时填充演示数据，并尝试导入 ABO 知识库。"""
import random
from datetime import date, datetime, timedelta, time

from typing import List, Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.writing import WritingHistory
from app.models.matte import MatteHistory
from app.models.background import BackgroundHistory
from app.models.poster import PosterHistory, Template
from app.models.chat import (
    AboProduct,
    ChatSession,
    ChatMessage,
    ChatFeedback,
    SystemDailyStat,
    ModuleError,
)
from app.modules.chat.services.rag_service import build_global_abo_index


SAMPLE_PRODUCTS = [
    {
        "item_id": "B000000001",
        "item_name": "Wireless Bluetooth Headphones",
        "item_name_zh": "无线蓝牙耳机",
        "brand": "SoundMax",
        "brand_zh": "声迈",
        "product_type": "ELECTRONICS",
        "product_type_zh": "电子产品",
        "bullet_points": "Active noise cancelling|30-hour battery life|IPX5 waterproof|Bluetooth 5.3",
        "bullet_points_zh": "主动降噪|30小时续航|IPX5防水|蓝牙5.3",
        "material": "Plastic, Memory Foam",
        "material_zh": "塑料, 记忆海绵",
        "color": "Black",
        "image_path": "/static/demo-products/headphones.svg",
    },
    {
        "item_id": "B000000002",
        "item_name": "Organic Cotton T-Shirt",
        "item_name_zh": "有机棉T恤",
        "brand": "EcoWear",
        "brand_zh": "环保衣着",
        "product_type": "APPAREL",
        "product_type_zh": "服装",
        "bullet_points": "100% organic cotton|Breathable fabric|Machine washable|Unisex fit",
        "bullet_points_zh": "100%有机棉|透气面料|可机洗|男女同款",
        "material": "Organic Cotton",
        "material_zh": "有机棉",
        "color": "White",
        "image_path": "/static/demo-products/apparel.svg",
    },
    {
        "item_id": "B000000003",
        "item_name": "Stainless Steel Water Bottle",
        "item_name_zh": "不锈钢保温杯",
        "brand": "HydroLife",
        "brand_zh": "水活",
        "product_type": "KITCHEN",
        "product_type_zh": "厨房用品",
        "bullet_points": "Double-wall insulation|Keeps cold 24h|BPA-free|750ml capacity",
        "bullet_points_zh": "双层真空隔热|保冷24小时|不含BPA|750毫升容量",
        "material": "Stainless Steel",
        "material_zh": "不锈钢",
        "color": "Silver",
        "image_path": "/static/demo-products/bottle.svg",
    },
    {
        "item_id": "B000000004",
        "item_name": "LED Desk Lamp",
        "item_name_zh": "LED台灯",
        "brand": "BrightHome",
        "brand_zh": "明家",
        "product_type": "HOME",
        "product_type_zh": "家居",
        "bullet_points": "3 color temperatures|Touch dimming|USB charging port|Eye-care technology",
        "bullet_points_zh": "三档色温|触摸调光|USB充电口|护眼技术",
        "material": "Aluminum, ABS",
        "material_zh": "铝合金, ABS",
        "color": "White",
        "image_path": "/static/demo-products/home.svg",
    },
    {
        "item_id": "B000000005",
        "item_name": "Running Shoes",
        "item_name_zh": "跑步鞋",
        "brand": "SpeedRun",
        "brand_zh": "速跑",
        "product_type": "FOOTWEAR",
        "product_type_zh": "鞋类",
        "bullet_points": "Lightweight mesh upper|Responsive cushioning|Anti-slip sole|Size US 7-12",
        "bullet_points_zh": "轻量网面鞋面|反应灵敏缓震|防滑鞋底|尺码7-12",
        "material": "Mesh, Rubber",
        "material_zh": "网面, 橡胶",
        "color": "Blue",
        "image_path": "/static/demo-products/shoes.svg",
    },
]

CATEGORIES = [
    ("电子产品", "ELECTRONICS"),
    ("服装", "APPAREL"),
    ("厨房用品", "KITCHEN"),
    ("家居", "HOME"),
    ("鞋类", "FOOTWEAR"),
]

WRITING_PRODUCTS = [
    ("无线蓝牙耳机", "主动降噪, 长续航", "Amazon", "专业商务"),
    ("有机棉T恤", "透气亲肤, 可机洗", "Shopee", "活泼种草"),
    ("不锈钢保温杯", "保冷24小时", "TikTok", "极简高级"),
    ("LED护眼台灯", "三档色温, USB充电", "Amazon", "情感共鸣"),
    ("轻量跑步鞋", "缓震防滑", "eBay", "幽默风趣"),
    ("便携咖啡杯", "防漏设计", "Shopify", "奢华高端"),
    ("无线充电器", "15W快充", "Amazon", "专业商务"),
    ("瑜伽垫", "防滑加厚", "Shopee", "活泼种草"),
]

BG_STYLES = ["户外自然", "简约白底", "科技感", "奢华质感", "生活场景"]

CHAT_QA = [
    ("这款耳机续航多久？", "根据商品信息，该无线蓝牙耳机续航约 30 小时，支持主动降噪与 IPX5 防水。"),
    ("保温杯能保冷多久？", "双层真空隔热设计，官方卖点为保冷约 24 小时，容量 750ml，不含 BPA。"),
    ("T恤材质是什么？", "采用 100% 有机棉，透气可机洗，男女同款剪裁。"),
    ("台灯有几档色温？", "支持三档色温与触摸调光，并带 USB 充电口与护眼技术。"),
    ("跑步鞋有哪些尺码？", "常见尺码覆盖 US 7–12，鞋面为轻量网面，鞋底防滑并带缓震。"),
]


def _build_faq(p: dict) -> str:
    bullets = p.get("bullet_points", "").replace("|", "; ")
    bullets_zh = p.get("bullet_points_zh", "").replace("|", "；")
    return (
        f"商品ID: {p['item_id']}\n"
        f"商品名称(英文): {p['item_name']}\n"
        f"商品名称(中文): {p.get('item_name_zh', p['item_name'])}\n"
        f"品牌(英文): {p.get('brand', '')}\n"
        f"品牌(中文): {p.get('brand_zh', p.get('brand', ''))}\n"
        f"品类(英文): {p.get('product_type', '')}\n"
        f"品类(中文): {p.get('product_type_zh', p.get('product_type', ''))}\n"
        f"材质: {p.get('material_zh', p.get('material', ''))}\n"
        f"颜色: {p.get('color', '')}\n"
        f"卖点特征(英文): {bullets}\n"
        f"卖点特征(中文): {bullets_zh}"
    )


def _rand_dt(day: date) -> datetime:
    """某天内的随机时间，方便看板按 date(created_at) 汇总。"""
    return datetime.combine(
        day,
        time(hour=random.randint(8, 22), minute=random.randint(0, 59), second=random.randint(0, 59)),
    )


def _ensure_demo_users(db: Session) -> List[User]:
    """确保有可登录的演示账号 + 若干用户，让总用户数好看。"""
    specs = [
        ("demo", "demo123"),
        ("seller_alice", "pass1234"),
        ("seller_bob", "pass1234"),
        ("ops_chen", "pass1234"),
        ("ops_wang", "pass1234"),
        ("shop_li", "pass1234"),
        ("shop_zhao", "pass1234"),
        ("brand_sun", "pass1234"),
        ("brand_zhou", "pass1234"),
        ("agency_wu", "pass1234"),
        ("agency_zheng", "pass1234"),
        ("intern_xu", "pass1234"),
    ]
    users: List[User] = []
    for username, password in specs:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            user = User(username=username, password_hash=hash_password(password), role="user")
            db.add(user)
            db.flush()
        elif user.password_hash in ("demo_hash", "", None) or not str(user.password_hash).startswith("$2"):
            # 旧种子写了无效 hash，补成可登录
            user.password_hash = hash_password(password)
        users.append(user)
    db.commit()
    return users


def _count_on_day(db: Session, table: str, day: date) -> int:
    row = db.execute(
        text(f"SELECT COUNT(*) FROM {table} WHERE date(created_at) = :d"),
        {"d": day.isoformat()},
    ).scalar()
    return int(row or 0)


def _rebuild_daily_stats(db: Session, days: int = 7) -> None:
    """按历史表回填近 N 天 system_daily_stats，供趋势图使用。"""
    total_users = db.query(func.count(User.id)).scalar() or 0
    today = date.today()

    for i in range(days):
        d = today - timedelta(days=i)
        writing = _count_on_day(db, "history_writing", d)
        matte = _count_on_day(db, "history_matte", d)
        bg = _count_on_day(db, "history_background", d)
        poster = _count_on_day(db, "history_poster", d)
        chat = _count_on_day(db, "chat_messages", d) // 2
        errors = _count_on_day(db, "module_errors", d)

        stat = db.query(SystemDailyStat).filter(SystemDailyStat.stat_date == d).first()
        if not stat:
            stat = SystemDailyStat(stat_date=d)
            db.add(stat)
        stat.total_users = total_users
        stat.writing_calls = writing
        stat.matte_calls = matte
        stat.bg_calls = bg
        stat.poster_calls = poster
        stat.chat_calls = chat
        stat.error_count = errors

    db.commit()


def _seed_activity_for_day(
    db: Session,
    day: date,
    *,
    user_ids: List[int],
    primary_user_id: int,
    template_id: Optional[int],
    scale: float = 1.0,
    tag: str = "demo",
) -> None:
    """为指定日期写入一批模块调用记录。"""
    n_writing = max(3, int(random.randint(6, 12) * scale))
    n_matte = max(3, int(random.randint(5, 11) * scale))
    n_bg = max(2, int(random.randint(4, 9) * scale))
    n_poster = max(2, int(random.randint(3, 8) * scale))
    n_chat = max(2, int(random.randint(3, 7) * scale))
    day_tag = day.isoformat().replace("-", "")

    for _ in range(n_writing):
        name, feats, platform, style = random.choice(WRITING_PRODUCTS)
        db.add(
            WritingHistory(
                user_id=random.choice(user_ids),
                product_name=name,
                product_features=feats,
                platform=platform,
                title=f"【热卖】{name}｜跨境爆款推荐",
                body=f"{name}主打{feats}，适合多平台投放，点击转化表现稳定。",
                tags="跨境,爆款,AI文案",
                language=random.choice(["zh", "en", "ja"]),
                style=style,
                created_at=_rand_dt(day),
            )
        )

    for _ in range(n_matte):
        cat_zh, cat_en = random.choice(CATEGORIES)
        idx = random.randint(100, 999)
        db.add(
            MatteHistory(
                user_id=random.choice(user_ids),
                original_url=f"/static/matte/{tag}_orig_{day_tag}_{idx}.jpg",
                matted_url=f"/static/matte/{tag}_matted_{day_tag}_{idx}.png",
                category=cat_zh,
                category_en=cat_en,
                confidence=round(random.uniform(0.86, 0.99), 2),
                attributes='{"demo": true}',
                file_size=random.randint(80_000, 420_000),
                created_at=_rand_dt(day),
            )
        )

    for _ in range(n_bg):
        cat_zh, _ = random.choice(CATEGORIES)
        style = random.choice(BG_STYLES)
        idx = random.randint(100, 999)
        db.add(
            BackgroundHistory(
                user_id=random.choice(user_ids),
                product_category=cat_zh,
                style=style,
                color_hint=random.choice(["暖色", "冷色", "中性", ""]),
                prompt_used=f"{cat_zh} product on {style} background, ecommerce photography",
                bg_url=f"/static/background/{tag}_bg_{day_tag}_{idx}.png",
                enhanced_url=f"/static/background/{tag}_bg_hq_{day_tag}_{idx}.png",
                scale_factor=2,
                created_at=_rand_dt(day),
            )
        )

    for _ in range(n_poster):
        name, _, _, _ = random.choice(WRITING_PRODUCTS)
        idx = random.randint(100, 999)
        db.add(
            PosterHistory(
                user_id=random.choice(user_ids),
                matted_url=f"/static/matte/{tag}_matted_{day_tag}_{idx}.png",
                bg_url=f"/static/background/{tag}_bg_hq_{day_tag}_{idx}.png",
                template_id=template_id,
                poster_url=f"/static/poster/{tag}_poster_{day_tag}_{idx}.png",
                title=name,
                discount=random.choice(["20% OFF", "限时特惠", "买一送一", "Flash Sale"]),
                price=random.choice(["$19.99", "$29.90", "¥99", "¥199"]),
                ratio=random.choice(["1:1", "4:5", "9:16"]),
                downloads=random.randint(0, 12),
                created_at=_rand_dt(day),
            )
        )

    for _ in range(n_chat):
        q, a = random.choice(CHAT_QA)
        session = ChatSession(
            user_id=random.choice(user_ids),
            title=q[:18] + ("…" if len(q) > 18 else ""),
            created_at=_rand_dt(day),
        )
        db.add(session)
        db.flush()
        t0 = _rand_dt(day)
        user_msg = ChatMessage(
            session_id=session.id,
            role="user",
            content=q,
            language="zh",
            created_at=t0,
        )
        asst_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=a,
            language="zh",
            created_at=t0 + timedelta(seconds=random.randint(2, 20)),
        )
        db.add(user_msg)
        db.add(asst_msg)
        db.flush()
        fb_type = "like" if random.random() < 0.82 else "dislike"
        db.add(
            ChatFeedback(
                message_id=asst_msg.id,
                user_id=primary_user_id,
                feedback_type=fb_type,
                created_at=asst_msg.created_at + timedelta(seconds=5),
            )
        )


def ensure_today_demo_activity(db: Session) -> bool:
    """跨天后「今日调用」会归零：若今天还没有记录，自动补一批。"""
    today = date.today()
    if _count_on_day(db, "history_writing", today) > 0:
        return False

    users = _ensure_demo_users(db)
    user_ids = [u.id for u in users]
    templates = db.query(Template).filter(Template.is_active.is_(True)).all()
    template_id = templates[0].id if templates else None

    _seed_activity_for_day(
        db,
        today,
        user_ids=user_ids,
        primary_user_id=user_ids[0],
        template_id=template_id,
        scale=1.15,
        tag="today",
    )
    # 今日少量错误，方便异常预警有内容但不刷屏
    db.add(
        ModuleError(
            module_name="background",
            error_message="上游图像 API 超时（演示数据）",
            created_at=_rand_dt(today),
        )
    )
    db.add(
        ModuleError(
            module_name="matte",
            error_message="上传图片格式不支持（演示数据）",
            created_at=_rand_dt(today),
        )
    )
    db.commit()
    _rebuild_daily_stats(db, days=7)
    print(f"[seed] 已补齐今日({today.isoformat()})演示调用数据")
    return True


def seed_demo_history(db: Session, *, force: bool = False) -> bool:
    """填充各模块调用历史，让运营看板有可演示的数据。

    默认仅在几乎无历史时写入；force=True 时再追加近 7 天。
    无论是否跳过，都会确保「今天」有数据（跨天自动补齐）。
    """
    existing = db.query(func.count(WritingHistory.id)).scalar() or 0
    wrote = False

    if existing >= 8 and not force:
        print(f"[seed] 历史调用已存在（文案 {existing} 条），检查今日数据…")
    else:
        users = _ensure_demo_users(db)
        user_ids = [u.id for u in users]
        primary = user_ids[0]
        templates = db.query(Template).filter(Template.is_active.is_(True)).all()
        template_id = templates[0].id if templates else None

        today = date.today()
        for day_offset in range(7):
            day = today - timedelta(days=day_offset)
            # 已有今天数据时跳过该天，避免 force 以外重复刷
            if not force and _count_on_day(db, "history_writing", day) > 0:
                continue
            weekday = day.weekday()
            scale = 0.55 if weekday >= 5 else 1.0
            _seed_activity_for_day(
                db,
                day,
                user_ids=user_ids,
                primary_user_id=primary,
                template_id=template_id,
                scale=scale,
                tag=f"d{day_offset}",
            )

        for day_offset in range(3):
            day = today - timedelta(days=day_offset)
            db.add(
                ModuleError(
                    module_name="background",
                    error_message="上游图像 API 超时（演示数据）",
                    created_at=_rand_dt(day),
                )
            )
        db.add(
            ModuleError(
                module_name="matte",
                error_message="上传图片格式不支持（演示数据）",
                created_at=_rand_dt(today),
            )
        )
        db.commit()
        _rebuild_daily_stats(db, days=7)
        print("[seed] 已写入近 7 天调用历史（文案/抠图/背景/海报/客服）与看板日统计")
        wrote = True

    if ensure_today_demo_activity(db):
        wrote = True
    return wrote


def _import_abo_products(db: Session) -> int:
    """从本地 ABO listings 导入；失败则用示例商品。"""
    count = db.query(AboProduct).count()
    if count > 0:
        return count

    try:
        from app.modules.chat.services.import_abo import import_abo_listings

        count = import_abo_listings(db)
        if count > 0:
            return count
        print("[seed] ABO 导入为 0，使用示例数据")
    except Exception as e:
        print(f"[seed] ABO 导入异常: {e}，使用示例数据")

    for p in SAMPLE_PRODUCTS:
        db.add(
            AboProduct(
                item_id=p["item_id"],
                item_name=p["item_name"],
                item_name_zh=p.get("item_name_zh"),
                brand=p.get("brand"),
                brand_zh=p.get("brand_zh"),
                product_type=p.get("product_type"),
                bullet_points=p.get("bullet_points"),
                bullet_points_zh=p.get("bullet_points_zh"),
                material=p.get("material"),
                material_zh=p.get("material_zh"),
                color=p.get("color"),
                image_path=p.get("image_path"),
                faq_text=_build_faq(p),
            )
        )
    db.commit()
    return len(SAMPLE_PRODUCTS)


def _rebuild_abo_index(db: Session) -> None:
    products = db.query(AboProduct).all()
    chunks = [p.faq_text for p in products if p.faq_text]
    if chunks:
        build_global_abo_index(chunks)


def seed_if_empty() -> None:
    db = SessionLocal()
    try:
        # 演示账号 + 调用历史（看板用）
        seed_demo_history(db, force=False)

        count = _import_abo_products(db)
        # 数据量大时跳过全局 FAISS 重建，避免 OOM
        if count < 5000:
            _rebuild_abo_index(db)
        print(f"[seed] ABO 知识库已就绪，共 {count} 条商品")
    finally:
        db.close()
