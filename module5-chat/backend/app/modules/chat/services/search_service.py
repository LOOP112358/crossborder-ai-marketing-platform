"""SQL LIKE 备选搜索（来自 feature/module5 二轮优化）。"""
import re
from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session


def search_products_like(db: Session, query: str, limit: int = 5) -> List[str]:
    """
    直接用 SQLite LIKE 搜索商品 faq_text。
    跨语言匹配由上游 LLM 翻译 query 为英文关键词来保证。
    """
    keywords = re.findall(r"[A-Za-z0-9_]{2,}", query)
    if not keywords:
        keywords = [query.strip()] if query.strip() else []
    if not keywords:
        return []

    conditions = " OR ".join([f"faq_text LIKE :kw{i}" for i in range(len(keywords))])
    sql = f"""
        SELECT DISTINCT faq_text FROM abo_products
        WHERE {conditions}
        LIMIT :limit
    """
    params = {f"kw{i}": f"%{kw}%" for i, kw in enumerate(keywords)}
    params["limit"] = limit
    rows = db.execute(text(sql), params).fetchall()
    return [r[0] for r in rows if r[0]]
