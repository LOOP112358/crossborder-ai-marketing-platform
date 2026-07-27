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
import sqlite3
from pathlib import Path
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.chat import AboProduct
from app.modules.chat.services.config import (
    ABO_IMPORT_LIMIT,
    ABO_IMAGES_DIR,
    ABO_IMAGES_SMALL_DIR,
    ABO_METADATA_DIR,
)
from app.modules.chat.services.rag_service import build_global_abo_index

# 磁盘索引：避免把整份 images.csv 装进 dict（云主机易 OOM / exit 137）
_IMAGE_MAP_CONN: Optional[sqlite3.Connection] = None
_IMAGE_MAP_DB = ABO_IMAGES_DIR / "images" / "metadata" / "image_id_map.sqlite"


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


def _image_map_ready(db_path: Path) -> bool:
    if not db_path.exists() or db_path.stat().st_size < 1024:
        return False
    try:
        conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
        try:
            row = conn.execute("SELECT COUNT(*) FROM map").fetchone()
            return bool(row and row[0] > 0)
        finally:
            conn.close()
    except sqlite3.Error:
        return False


def ensure_image_id_db(force: bool = False) -> Optional[Path]:
    """
    把 images.csv 流式写入 SQLite（image_id → path），避免整表进内存。
    对应磁盘文件：ABO_IMAGES_DIR/images/small/{path}
    """
    db_path = _IMAGE_MAP_DB
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if not force and _image_map_ready(db_path):
        print(f"[abo] 使用已有图片索引 {db_path}")
        return db_path

    fh = _open_images_csv()
    if fh is None:
        print(f"[warn] 未找到 images.csv / images.csv.gz 于 {ABO_IMAGES_DIR / 'images' / 'metadata'}")
        return None

    tmp_path = db_path.with_suffix(".sqlite.tmp")
    if tmp_path.exists():
        tmp_path.unlink()
    print(f"[abo] 构建图片索引（低内存流式）→ {db_path.name} …")
    conn = sqlite3.connect(str(tmp_path))
    try:
        conn.execute("PRAGMA journal_mode=OFF")
        conn.execute("PRAGMA synchronous=OFF")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("CREATE TABLE map (image_id TEXT PRIMARY KEY, path TEXT NOT NULL)")
        batch = []
        n = 0
        with fh:
            reader = csv.DictReader(fh)
            for row in reader:
                image_id = (row.get("image_id") or "").strip()
                path = (row.get("path") or "").strip().replace("\\", "/")
                if not image_id or not path:
                    continue
                batch.append((image_id, path))
                if len(batch) >= 5000:
                    conn.executemany("INSERT OR REPLACE INTO map(image_id, path) VALUES (?, ?)", batch)
                    n += len(batch)
                    batch.clear()
                    if n % 100000 == 0:
                        conn.commit()
                        print(f"  已写入 {n} 条…")
            if batch:
                conn.executemany("INSERT OR REPLACE INTO map(image_id, path) VALUES (?, ?)", batch)
                n += len(batch)
                batch.clear()
        conn.commit()
    finally:
        conn.close()
        fh.close()

    if db_path.exists():
        db_path.unlink()
    tmp_path.replace(db_path)
    print(f"[abo] 图片索引完成，共 {n} 条")
    return db_path


def _get_image_map_conn() -> Optional[sqlite3.Connection]:
    global _IMAGE_MAP_CONN
    if _IMAGE_MAP_CONN is not None:
        return _IMAGE_MAP_CONN
    db_path = ensure_image_id_db()
    if not db_path:
        return None
    _IMAGE_MAP_CONN = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    _IMAGE_MAP_CONN.row_factory = sqlite3.Row
    return _IMAGE_MAP_CONN


def lookup_image_path(image_id: str) -> Optional[str]:
    mid = (image_id or "").strip()
    if not mid:
        return None
    conn = _get_image_map_conn()
    if conn is None:
        return None
    row = conn.execute("SELECT path FROM map WHERE image_id = ? LIMIT 1", (mid,)).fetchone()
    return row["path"] if row else None


def load_image_id_map() -> None:
    """兼容旧调用：预热磁盘索引（不再返回巨型 dict）。"""
    ensure_image_id_db()


def resolve_image_fields(
    main_image_id: Optional[str],
    *,
    require_file: bool = False,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """返回 (main_image_id, image_path, image_url)。

    require_file=True 时仅当 jpg 实际存在于 images/small 才返回 path（用于全量挂图）。
    """
    if not main_image_id:
        return None, None, None
    mid = str(main_image_id).strip()
    path = lookup_image_path(mid)
    if not path:
        # 兼容旧约定：直接用 id.jpg
        candidate = ABO_IMAGES_SMALL_DIR / mid[:2].lower() / f"{mid}.jpg"
        if candidate.exists():
            path = f"{mid[:2].lower()}/{mid}.jpg"
    if not path:
        return mid, None, None
    disk = ABO_IMAGES_SMALL_DIR / path
    if not disk.exists():
        if require_file:
            return mid, None, None
        return mid, path, None
    url = f"/static/abo-images/images/small/{path}"
    return mid, path, url


def resolve_image_url(main_image_id: Optional[str]) -> Optional[str]:
    _, _, url = resolve_image_fields(main_image_id)
    return url


def _build_faq(record: dict, *, resolve_images: bool = True) -> dict:
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
    image_path = None
    if resolve_images:
        _, image_path, _ = resolve_image_fields(main_image_id, require_file=True)

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


def import_abo_listings(
    db: Session,
    limit: int = ABO_IMPORT_LIMIT,
    *,
    resolve_images: bool = True,
    rebuild_index: bool = True,
) -> int:
    if resolve_images:
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
                data = _build_faq(record, resolve_images=resolve_images)
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
                if imported % 200 == 0:
                    db.commit()
                    print(f"  已导入 {imported} 条（含图 {with_image}）...")
        if imported >= limit:
            break

    db.commit()
    print(f"[abo] 本次新增 {imported} 条，其中有图 {with_image} 条（库内原有 {len(existing)} 条）")

    total = db.query(AboProduct).count()
    if rebuild_index and total > 0:
        _rebuild_faiss(db)
    return total


def _rebuild_faiss(db: Session) -> None:
    """分批取 faq_text，降低峰值内存。"""
    chunks = []
    q = db.query(AboProduct.faq_text).filter(AboProduct.faq_text.isnot(None), AboProduct.faq_text != "")
    for (text,) in q.yield_per(200):
        if text:
            chunks.append(text)
    if not chunks:
        print("[abo] 无 FAQ 文本，跳过 FAISS")
        return
    build_global_abo_index(chunks)
    print(f"[abo] FAISS 全局索引已重建，共 {len(chunks)} 条")


def backfill_abo_images(db: Session) -> int:
    """为已有商品按 listings / main_image_id 回填图片路径（要求 jpg 在磁盘上）。"""
    load_image_id_map()
    metadata_dir = ABO_METADATA_DIR
    if not metadata_dir.exists():
        print(f"[warn] ABO metadata 不存在: {metadata_dir}")
        return 0

    # Pass 1：已有 main_image_id 的直接解析（不依赖再扫 listings）
    updated = 0
    checked = 0
    print("[abo] Pass1: 按已有 main_image_id 挂图…")
    q = db.query(AboProduct).yield_per(300)
    for p in q:
        mid = (p.main_image_id or "").strip()
        if not mid:
            continue
        checked += 1
        _, path, _ = resolve_image_fields(mid, require_file=True)
        if path and p.image_path != path:
            p.image_path = path
            updated += 1
            if updated % 500 == 0:
                db.commit()
                print(f"  Pass1 已更新 {updated} 条…")
    db.commit()
    print(f"[abo] Pass1 完成：检查 {checked}，更新 {updated}")

    products = {p.item_id: p for p in db.query(AboProduct).all()}
    if not products:
        print("[abo] 库中无商品，跳过回填")
        return updated

    # Pass 2：扫 listings，补 main_image_id + 实图 path
    print("[abo] Pass2: 扫描 listings 回填…")
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
                _, path, _ = resolve_image_fields(mid, require_file=True)
                changed = False
                if mid and p.main_image_id != mid:
                    p.main_image_id = mid
                    changed = True
                if path and p.image_path != path:
                    p.image_path = path
                    changed = True
                if not p.color:
                    c = _pick_lang(record.get("color", []))
                    if c:
                        p.color = c
                        changed = True
                if changed:
                    updated += 1
                if updated and updated % 500 == 0:
                    db.commit()
                    print(f"  Pass2 已更新 {updated} 条…")
    db.commit()
    with_img = (
        db.query(AboProduct)
        .filter(AboProduct.image_path.isnot(None), AboProduct.image_path != "")
        .count()
    )
    print(f"[abo] 回填完成：累计检查/更新相关 {checked}/{updated}，当前有图 {with_img}/{len(products)}")
    return updated


def import_products_with_images(db: Session, limit: int = 0) -> int:
    """
    从 listings 导入「磁盘上确有 jpg」的商品；limit<=0 表示不设上限。
    用于把 3GB images-small 尽量挂满到可展示商品上。
    """
    load_image_id_map()
    metadata_dir = ABO_METADATA_DIR
    if not metadata_dir.exists():
        print(f"[warn] ABO metadata 目录不存在: {metadata_dir}")
        return 0

    files = sorted(metadata_dir.glob("listings_*.json.gz"))
    if not files:
        print(f"[warn] 未找到 listings_*.json.gz 于 {metadata_dir}")
        return 0

    existing = {r[0] for r in db.query(AboProduct.item_id).all()}
    imported = 0
    skipped_no_image = 0
    seen_ids = set(existing)
    unlimited = limit <= 0

    for fp in files:
        print(f"[abo] 有图导入: {fp.name}")
        with gzip.open(fp, "rt", encoding="utf-8") as f:
            for line in f:
                if not unlimited and imported >= limit:
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
                mid = record.get("main_image_id") or ""
                _, path, _ = resolve_image_fields(mid, require_file=True)
                if not path:
                    skipped_no_image += 1
                    continue
                data = _build_faq(record, resolve_images=False)
                if not data["item_name"]:
                    continue
                data["main_image_id"] = mid or None
                data["image_path"] = path
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
                seen_ids.add(item_id)
                imported += 1
                if imported % 300 == 0:
                    db.commit()
                    print(f"  已导入有图商品 {imported}（跳过无图 {skipped_no_image}）…")
        if not unlimited and imported >= limit:
            break

    db.commit()
    with_img = (
        db.query(AboProduct)
        .filter(AboProduct.image_path.isnot(None), AboProduct.image_path != "")
        .count()
    )
    total = db.query(AboProduct).count()
    print(
        f"[abo] 有图导入完成：新增 {imported}，跳过无盘图 {skipped_no_image}，"
        f"库内有图 {with_img}/{total}"
    )
    return imported


def main():
    global _IMAGE_MAP_CONN
    parser = argparse.ArgumentParser(description="导入 ABO 商品 FAQ 知识库")
    parser.add_argument("--limit", type=int, default=ABO_IMPORT_LIMIT)
    parser.add_argument("--rebuild-only", action="store_true", help="只重建 FAISS，不重新读 gzip")
    parser.add_argument("--backfill-images", action="store_true", help="仅为已有商品回填图片路径")
    parser.add_argument(
        "--import-with-images",
        action="store_true",
        help="只导入磁盘上确有 jpg 的商品；配合 --limit，0=不设上限",
    )
    parser.add_argument("--skip-index", action="store_true", help="导入时不重建 FAISS（省内存）")
    parser.add_argument("--skip-images", action="store_true", help="导入时不解析图片路径（稍后 --backfill-images）")
    parser.add_argument("--rebuild-image-index", action="store_true", help="强制重建 image_id SQLite 索引")
    args = parser.parse_args()

    from app.core.database import SessionLocal, init_db

    init_db()
    db = SessionLocal()
    try:
        if args.rebuild_image_index:
            ensure_image_id_db(force=True)
        elif args.backfill_images:
            backfill_abo_images(db)
        elif args.import_with_images:
            import_products_with_images(db, limit=args.limit)
        elif args.rebuild_only:
            _rebuild_faiss(db)
        else:
            import_abo_listings(
                db,
                limit=args.limit,
                resolve_images=not args.skip_images,
                rebuild_index=not args.skip_index,
            )
    finally:
        if _IMAGE_MAP_CONN is not None:
            _IMAGE_MAP_CONN.close()
            _IMAGE_MAP_CONN = None
        db.close()


if __name__ == "__main__":
    main()
