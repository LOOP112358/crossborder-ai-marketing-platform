import re
from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models import AboProduct


def search_products(db: Session, query: str, limit: int = 5) -> List[str]:
    """
    直接用 SQLite LIKE 搜索商品，简单粗暴。
    跨语言匹配由上游 LLM 翻译 query 为英文关键词来保证。
    """
    # 拆成单个关键词，每个词单独 LIKE 匹配
    keywords = re.findall(r'[A-Za-z0-9_]{2,}', query)
    if not keywords:
        keywords = [query]

    # 构建 OR 条件：每个关键词匹配 faq_text
    conditions = " OR ".join([f"faq_text LIKE :kw{i}" for i in range(len(keywords))])
    sql = f"""
        SELECT DISTINCT faq_text FROM abo_products
        WHERE {conditions}
        LIMIT :limit
    """
    params = {f"kw{i}": f"%{kw}%" for i, kw in enumerate(keywords)}
    params["limit"] = limit

    rows = db.execute(text(sql), params).fetchall()
    return [r[0] for r in rows]
