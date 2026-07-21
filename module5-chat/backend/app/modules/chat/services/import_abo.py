"""
从 Amazon Berkeley Objects (ABO) listings 导入商品 FAQ 知识库，
并用 images/metadata/images.csv(.gz) 把 main_image_id 映射到本地 jpg。

用法（在项目根目录）:
  python scripts/import_abo_kb.py
  python scripts/import_abo_kb.py --limit 8000
  python scripts/import_abo_kb.py --backfill-images
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.chat import AboProduct
from app.modules.chat.services.config import (
    ABO_IMPORT_LIMIT,
    ABO_IMAGES_DIR,
    ABO_IMAGES_SMALL_DIR,
    ABO_METADATA_DIR,
)
from app.modules.chat.services.rag_service import build_global_abo_index


def _pick_lang(items: list, tag: str = "en_US") -> str:
    if not items:
        return ""
    for item in items:
        if isinstance(item, str):
            return item
        if isinstance(item, dict) and item.get("language_tag") == tag:
            return item.get("value", "") or ""
    for item in items:
        if isinstance(item, str):
            return item
        if isinstance(item, dict) and item.get("value"):
            return item.get("value", "") or ""
    return ""


def _all_langs(items: list) -> str:
    if not items:
        return ""
    values = []
    for item in items:
        if isinstance(item, str):
            values.append(item)
        elif isinstance(item, dict):
            v = item.get("value", "")
            if v:
                values.append(v)
    return " ; ".join(values)


def _extract_keywords(record: dict) -> str:
    kw = []
    for item in record.get("item_keywords", []) or []:
        v = item.get("value", "") if isinstance(item, dict) else item
        if v:
            kw.append(v)
    return " ; ".join(kw)


def _extract_category(record: dict) -> str:
    paths = []
    for n in record.get("node", []) or []:
        name = n.get("node_name", "") if isinstance(n, dict) else ""
        if name:
            paths.append(name)
    return " > ".join(paths)


def _open_images_csv():
    """优先用非空的 images.csv，否则用 images.csv.gz。"""
    meta = ABO_IMAGES_DIR / "images" / "metadata"
    csv_path = meta / "images.csv"
    gz_path = meta / "images.csv.gz"
    if csv_path.exists() and csv_path.stat().st_size > 0:
        return csv_path.open("rt", encoding="utf-8", newline="")
    if gz_path.exists():
        return gzip.open(gz_path, "rt", encoding="utf-8", newline="")
    return None


@lru_cache(maxsize=1)
def load_image_id_map() -> Dict[str, str]:
    """
    image_id → 相对 path（如 14/14fe8812.jpg）
    对应磁盘文件：ABO_IMAGES_DIR/images/small/{path}
    """
    mapping: Dict[str, str] = {}
    fh = _open_images_csv()
    if fh is None:
        print(f"[warn] 未找到 images.csv / images.csv.gz 于 {ABO_IMAGES_DIR / 'images' / 'metadata'}")
        return mapping
    with fh:
        reader = csv.DictReader(fh)
        for row in reader:
            image_id = (row.get("image_id") or "").strip()
            path = (row.get("path") or "").strip().replace("\\", "/")
            if image_id and path:
                mapping[image_id] = path
    print(f"[abo] 已加载图片映射 {len(mapping)} 条")
    return mapping


def resolve_image_fields(main_image_id: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """返回 (main_image_id, image_path, image_url)。"""
    if not main_image_id:
        return None, None, None
    mid = str(main_image_id).strip()
    path = load_image_id_map().get(mid)
    if not path:
        # 兼容旧约定：直接用 id.jpg
        candidate = ABO_IMAGES_SMALL_DIR / mid[:2].lower() / f"{mid}.jpg"
        if candidate.exists():
            path = f"{mid[:2].lower()}/{mid}.jpg"
    if not path:
        return mid, None, None
    disk = ABO_IMAGES_SMALL_DIR / path
    if not disk.exists():
        return mid, path, None
    url = f"/static/abo-images/images/small/{path}"
    return mid, path, url


def resolve_image_url(main_image_id: Optional[str]) -> Optional[str]:
    _, _, url = resolve_image_fields(main_image_id)
    return url


def _build_faq(record: dict) -> dict:
    item_id = record.get("item_id", "")
    item_name = _pick_lang(record.get("item_name", []))
    item_name_zh = _pick_lang(record.get("item_name", []), "zh_CN")
    brand = _pick_lang(record.get("brand", []))
    brand_zh = _pick_lang(record.get("brand", []), "zh_CN")
    product_type = _pick_lang(record.get("product_type", []))
    bullets = record.get("bullet_point", []) or []
    en_bullets = []
    any_bullets = []
    for b in bullets[:12]:
        if isinstance(b, str):
            if b.strip():
                en_bullets.append(b.strip())
                any_bullets.append(b.strip())
        elif isinstance(b, dict):
            v = (b.get("value") or "").strip()
            if not v:
                continue
            any_bullets.append(v)
            tag = b.get("language_tag") or ""
            if tag.startswith("en"):
                en_bullets.append(v)
    bullet_text = " | ".join((en_bullets or any_bullets)[:8])
    material = _pick_lang(record.get("material", []))
    color = _pick_lang(record.get("color", []))
    style = _pick_lang(record.get("style", []))
    keywords = _extract_keywords(record)
    category = _extract_category(record)
    model_name = _pick_lang(record.get("model_name", []))
    main_image_id = record.get("main_image_id") or ""
    _, image_path, _ = resolve_image_fields(main_image_id)

    faq_text = "\n".join(
        [
            f"Item ID: {item_id}",
            f"Product Name: {item_name}",
            f"Product Name ZH: {item_name_zh}",
            f"Brand: {brand}",
            f"Product Type: {product_type}",
            f"Category: {category}",
            f"Model: {model_name}",
            f"Color: {color}",
            f"Material: {material}",
            f"Style: {style}",
            f"Keywords: {keywords}",
            f"Bullet Points: {bullet_text}",
            f"Main Image ID: {main_image_id}",
            f"Also known as: {_all_langs(record.get('item_name', []))}",
        ]
    )

    return {
        "item_id": item_id,
        "item_name": item_name,
        "item_name_zh": item_name_zh or None,
        "brand": brand,
        "brand_zh": brand_zh or None,
        "product_type": product_type,
        "bullet_points": bullet_text,
        "material": material,
        "color": color,
        "main_image_id": main_image_id or None,
        "image_path": image_path,
        "faq_text": faq_text,
    }


def import_abo_listings(db: Session, limit: int = ABO_IMPORT_LIMIT) -> int:
    # 预热映射表
    load_image_id_map()

    metadata_dir = ABO_METADATA_DIR
    if not metadata_dir.exists():
        print(f"[warn] ABO metadata 目录不存在: {metadata_dir}")
        print("请设置环境变量 ABO_LISTINGS_DIR 指向解压后的 abo-listings 目录")
        return 0

    files = sorted(metadata_dir.glob("listings_*.json.gz"))
    if not files:
        print(f"[warn] 未找到 listings_*.json.gz 于 {metadata_dir}")
        return 0

    existing = {r[0] for r in db.query(AboProduct.item_id).all()}
    imported = 0
    with_image = 0
    seen_ids = set(existing)

    for fp in files:
        print(f"[abo] 导入文件: {fp.name}")
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
                if not item_id or item_id in seen_ids:
                    continue
                data = _build_faq(record)
                if not data["item_name"]:
                    continue
                db.add(
                    AboProduct(
                        item_id=data["item_id"],
                        item_name=data["item_name"],
                        item_name_zh=data["item_name_zh"],
                        brand=data["brand"],
                        brand_zh=data["brand_zh"],
                        product_type=data["product_type"],
                        bullet_points=data["bullet_points"],
                        material=data["material"],
                        color=data["color"],
                        main_image_id=data["main_image_id"],
                        image_path=data["image_path"],
                        faq_text=data["faq_text"],
                    )
                )
                if data["image_path"]:
                    with_image += 1
                seen_ids.add(item_id)
                imported += 1
                if imported % 500 == 0:
                    db.commit()
                    print(f"  已导入 {imported} 条（含图 {with_image}）...")
        if imported >= limit:
            break

    db.commit()
    print(f"[abo] 本次新增 {imported} 条，其中有图 {with_image} 条（库内原有 {len(existing)} 条）")

    total = db.query(AboProduct).count()
    if total > 0:
        products = db.query(AboProduct).all()
        chunks = [p.faq_text for p in products if p.faq_text]
        if chunks:
            build_global_abo_index(chunks)
            print(f"[abo] FAISS 全局索引已重建，共 {len(chunks)} 条")

    return total


def backfill_abo_images(db: Session) -> int:
    """为已有商品按 listings 回填 main_image_id / image_path。"""
    load_image_id_map()
    metadata_dir = ABO_METADATA_DIR
    if not metadata_dir.exists():
        print(f"[warn] ABO metadata 不存在: {metadata_dir}")
        return 0

    products = {p.item_id: p for p in db.query(AboProduct).all()}
    if not products:
        print("[abo] 库中无商品，跳过回填")
        return 0

    updated = 0
    checked = 0
    for fp in sorted(metadata_dir.glob("listings_*.json.gz")):
        print(f"[abo] 回填扫描: {fp.name}")
        with gzip.open(fp, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                item_id = record.get("item_id")
                p = products.get(item_id)
                if not p:
                    continue
                checked += 1
                mid = record.get("main_image_id") or ""
                _, path, _ = resolve_image_fields(mid)
                changed = False
                if mid and p.main_image_id != mid:
                    p.main_image_id = mid
                    changed = True
                if path and p.image_path != path:
                    p.image_path = path
                    changed = True
                # 补颜色等若为空
                if not p.color:
                    c = _pick_lang(record.get("color", []))
                    if c:
                        p.color = c
                        changed = True
                if changed:
                    updated += 1
                if updated and updated % 500 == 0:
                    db.commit()
                    print(f"  已更新 {updated} 条...")
    db.commit()
    with_img = db.query(AboProduct).filter(AboProduct.image_path.isnot(None), AboProduct.image_path != "").count()
    print(f"[abo] 回填完成：扫描命中 {checked}，更新 {updated}，当前有图 {with_img}/{len(products)}")
    return updated


def main():
    parser = argparse.ArgumentParser(description="导入 ABO 商品 FAQ 知识库")
    parser.add_argument("--limit", type=int, default=ABO_IMPORT_LIMIT)
    parser.add_argument("--rebuild-only", action="store_true", help="只重建 FAISS，不重新读 gzip")
    parser.add_argument("--backfill-images", action="store_true", help="仅为已有商品回填图片路径")
    args = parser.parse_args()

    from app.core.database import SessionLocal, init_db

    init_db()
    db = SessionLocal()
    try:
        if args.backfill_images:
            backfill_abo_images(db)
        elif args.rebuild_only:
            products = db.query(AboProduct).all()
            chunks = [p.faq_text for p in products if p.faq_text]
            if chunks:
                build_global_abo_index(chunks)
                print(f"[abo] 仅重建索引，共 {len(chunks)} 条")
            else:
                print("[abo] 库中无商品，无法重建")
        else:
            import_abo_listings(db, limit=args.limit)
    finally:
        db.close()


if __name__ == "__main__":
    main()
