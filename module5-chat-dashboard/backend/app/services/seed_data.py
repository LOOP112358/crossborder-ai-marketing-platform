"""启动时填充演示数据，并尝试导入 ABO 知识库。"""
import random
from datetime import date, timedelta, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import User, AboProduct
from .rag_service import build_global_abo_index


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
    },
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


def _seed_demo_history(db: Session) -> None:
    """填充各成员历史表，让看板有真实统计数据。"""
    today = date.today()
    for i in range(7):
        d = today - timedelta(days=i)
        db.execute(
            text(
                """
                INSERT OR IGNORE INTO system_daily_stats
                (stat_date, total_users, writing_calls, matte_calls, bg_calls, poster_calls, chat_calls, error_count)
                VALUES (:d, :u, :w, :m, :b, :p, :c, :e)
                """
            ),
            {
                "d": d.isoformat(),
                "u": 5 + i,
                "w": random.randint(3, 15),
                "m": random.randint(2, 12),
                "b": random.randint(2, 10),
                "p": random.randint(1, 8),
                "c": random.randint(1, 6),
                "e": random.randint(0, 2),
            },
        )

    categories = [
        ("ELECTRONICS", "电子产品"),
        ("APPAREL", "服装"),
        ("KITCHEN", "厨房用品"),
        ("HOME", "家居"),
        ("FOOTWEAR", "鞋类"),
    ]
    for i, (cat_en, cat_zh) in enumerate(categories):
        for j in range(random.randint(2, 5)):
            db.execute(
                text(
                    """
                    INSERT INTO history_matte (user_id, original_url, matted_url, category, category_en, confidence)
                    VALUES (1, :o, :m, :c, :ce, :conf)
                    """
                ),
                {
                    "o": f"/static/orig_{i}_{j}.jpg",
                    "m": f"/static/matte_{i}_{j}.png",
                    "c": cat_zh,
                    "ce": cat_en,
                    "conf": round(random.uniform(0.85, 0.99), 2),
                },
            )

    for i in range(10):
        db.execute(
            text(
                """
                INSERT INTO history_writing (user_id, product_name, platform, title, body)
                VALUES (1, :pn, 'Amazon', :t, :b)
                """
            ),
            {
                "pn": f"Product {i+1}",
                "t": f"Title for product {i+1}",
                "b": f"Description body for product {i+1}",
            },
        )


def _import_abo_products(db: Session) -> int:
    """尝试从 scripts/import_abo 导入，失败则用 sample。"""
    count = db.query(AboProduct).count()
    if count > 0:
        return count

    try:
        from pathlib import Path
        import sys
        scripts_dir = Path(__file__).resolve().parent.parent.parent.parent / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        from import_abo import import_abo_listings
        count = import_abo_listings(db)
        if count == 0:
            print("[seed] ABO 导入失败，使用示例数据")
            for p in SAMPLE_PRODUCTS:
                db.add(AboProduct(
                    item_id=p["item_id"],
                    item_name=p["item_name"],
                    item_name_zh=p.get("item_name_zh"),
                    brand=p.get("brand"),
                    brand_zh=p.get("brand_zh"),
                    product_type=p.get("product_type"),
                    product_type_zh=p.get("product_type_zh"),
                    bullet_points=p.get("bullet_points"),
                    bullet_points_zh=p.get("bullet_points_zh"),
                    material=p.get("material"),
                    material_zh=p.get("material_zh"),
                    color=p.get("color"),
                    faq_text=_build_faq(p),
                ))
            db.commit()
            return len(SAMPLE_PRODUCTS)
        return count
    except Exception as e:
        print(f"[seed] ABO 导入异常: {e}，使用示例数据")
        for p in SAMPLE_PRODUCTS:
            db.add(AboProduct(
                item_id=p["item_id"],
                item_name=p["item_name"],
                brand=p.get("brand"),
                product_type=p.get("product_type"),
                bullet_points=p.get("bullet_points"),
                material=p.get("material"),
                color=p.get("color"),
                faq_text=_build_faq(p),
            ))
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
        user = db.query(User).filter(User.username == "demo").first()
        if not user:
            db.add(User(username="demo", password_hash="demo_hash", role="user"))
            db.commit()

        # 只导入 ABO 知识库商品，不再填充假统计数据
        # 看板数据完全由 refresh_daily_stats 从真实调用记录中汇总
        count = _import_abo_products(db)
        _rebuild_abo_index(db)
        print(f"[seed] ABO 知识库已就绪，共 {count} 条商品")
    finally:
        db.close()
