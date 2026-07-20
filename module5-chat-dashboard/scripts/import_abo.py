"""
从 Amazon Berkeley Objects (ABO) listings 导入商品 FAQ 知识库。

用法:
  python scripts/import_abo.py
  python scripts/import_abo.py --limit 2000

数据路径（默认）:
  ../abo-listings/listings/metadata/listings_*.json.gz
"""
import argparse
import gzip
import json
import sys
from pathlib import Path

# 将 backend 加入 path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.config import ABO_METADATA_DIR, ABO_IMPORT_LIMIT, BASE_DIR
from app.database import init_db, SessionLocal
from app.models import AboProduct
from app.services.rag_service import build_global_abo_index


def _pick_lang(items: list, tag: str = "en_US") -> str:
    """提取多语言字段的值，优先匹配指定语言，否则返回第一个可用值"""
    if not items:
        return ""
    for item in items:
        if isinstance(item, str):
            return item
        if item.get("language_tag") == tag:
            return item.get("value", "")
    # fallback
    for item in items:
        if isinstance(item, str):
            return item
        if item.get("value"):
            return item.get("value", "")
    return ""


def _all_langs(items: list) -> str:
    """提取多语言字段的所有语言版本，用于丰富检索"""
    if not items:
        return ""
    values = []
    for item in items:
        if isinstance(item, str):
            values.append(item)
        else:
            v = item.get("value", "")
            if v:
                tag = item.get("language_tag", "")
                values.append(f"{v}" if not tag else v)
    return " ; ".join(values)


def _extract_keywords(record: dict) -> str:
    """提取所有可用于搜索的关键词"""
    kw = []
    for item in record.get("item_keywords", []):
        v = item.get("value", "") if isinstance(item, dict) else item
        if v:
            kw.append(v)
    return " ; ".join(kw)


def _extract_category(record: dict) -> str:
    """提取分类路径"""
    nodes = record.get("node", [])
    paths = []
    for n in nodes:
        name = n.get("node_name", "") if isinstance(n, dict) else ""
        if name:
            paths.append(name)
    return " > ".join(paths)


def _build_faq(record: dict) -> dict:
    item_id = record.get("item_id", "")
    item_name = _pick_lang(record.get("item_name", []))
    item_name_all = _all_langs(record.get("item_name", []))
    brand = _pick_lang(record.get("brand", []))
    brand_all = _all_langs(record.get("brand", []))
    product_type = _pick_lang(record.get("product_type", []))
    bullets = record.get("bullet_point", [])
    bullet_text = " | ".join(
        b if isinstance(b, str) else b.get("value", "")
        for b in bullets[:8]
    )
    bullet_all = _all_langs(record.get("bullet_point", []))
    material = _pick_lang(record.get("material", []))
    color = _pick_lang(record.get("color", []))
    style = _pick_lang(record.get("style", []))
    keywords = _extract_keywords(record)
    category = _extract_category(record)
    model_name = _pick_lang(record.get("model_name", []))
    model_year = _pick_lang(record.get("model_year", []))
    country = record.get("country", "")
    marketplace = record.get("marketplace", "")

    # 构建丰富的商品描述
    parts = []
    parts.append(f"【商品名称】{item_name}")
    if brand:
        parts.append(f"【品牌】{brand}")
    parts.append(f"【ASIN编码】{item_id}")
    parts.append(f"【商品品类】{product_type}")
    if category:
        parts.append(f"【分类路径】{category}")
    if style:
        parts.append(f"【款式】{style}")
    if model_name:
        parts.append(f"【型号】{model_name}")
    if model_year:
        parts.append(f"【年份】{model_year}")
    if color:
        parts.append(f"【颜色】{color}")
    if material:
        parts.append(f"【材质】{material}")
    if bullet_text:
        parts.append(f"【商品卖点】{bullet_text}")
    if keywords:
        parts.append(f"【搜索关键词】{keywords}")
    if country or marketplace:
        parts.append(f"【上架平台】{marketplace} ({country})")
    # 附加多语言名称和卖点（增加多语言检索命中率）
    if item_name_all and item_name_all != item_name:
        parts.append(f"【多语言名称】{item_name_all}")
    if bullet_all and bullet_all != bullet_text:
        parts.append(f"【多语言描述】{bullet_all}")
    if brand_all and brand_all != brand:
        parts.append(f"【多语言品牌】{brand_all}")

    faq_text = "\n".join(parts)

    return {
        "item_id": item_id,
        "item_name": item_name,
        "brand": brand,
        "product_type": product_type,
        "bullet_points": bullet_text,
        "material": material,
        "color": color,
        "faq_text": faq_text,
    }


def import_abo_listings(db, limit: int = ABO_IMPORT_LIMIT) -> int:
    metadata_dir = ABO_METADATA_DIR
    if not metadata_dir.exists():
        print(f"[warn] ABO metadata 目录不存在: {metadata_dir}")
        print("请解压 abo-listings.tar 到 ../abo-listings/")
        return 0

    files = sorted(metadata_dir.glob("listings_*.json.gz"))
    if not files:
        print(f"[warn] 未找到 listings_*.json.gz 文件于 {metadata_dir}")
        return 0

    imported = 0
    seen_ids = set()
    for fp in files:
        print(f"正在导入: {fp.name}")
        with gzip.open(fp, "rt", encoding="utf-8") as f:
            for line in f:
                if imported >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                item_id = record.get("item_id")
                if not item_id:
                    continue
                if item_id in seen_ids:
                    continue
                seen_ids.add(item_id)
                data = _build_faq(record)
                if not data["item_name"]:
                    continue
                db.add(AboProduct(**data))
                imported += 1
                if imported % 500 == 0:
                    db.commit()
                    print(f"  已导入 {imported} 条...")
        if imported >= limit:
            break

    db.commit()
    print(f"ABO 导入完成，共 {imported} 条")

    if imported > 0:
        products = db.query(AboProduct).all()
        chunks = [p.faq_text for p in products]
        build_global_abo_index(chunks)
        print("FAISS 全局索引已重建")

    return imported


def main():
    parser = argparse.ArgumentParser(description="导入 ABO 商品 FAQ 知识库")
    parser.add_argument("--limit", type=int, default=ABO_IMPORT_LIMIT)
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        import_abo_listings(db, limit=args.limit)
    finally:
        db.close()


if __name__ == "__main__":
    main()
