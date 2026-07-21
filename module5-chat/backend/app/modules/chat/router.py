import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.security import get_current_user
from app.models.user import User
from app.core.database import get_db
from app.models.chat import ChatSession, ChatMessage, ChatFeedback, AboProduct
from app.modules.chat.schemas import SessionCreate, SessionOut, MessageCreate, MessageOut, MessageResponse, FeedbackCreate, FeedbackOut
from app.modules.chat.services.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, UPLOAD_DIR
from app.modules.chat.services.document_parser import parse_document, chunk_text
from app.modules.chat.services.rag_service import build_session_index, retrieve_context
from app.modules.chat.services.llm_service import generate_bilingual_reply
from app.modules.chat.services.stats_service import refresh_daily_stats
from app.modules.chat.services.product_search import (
    detect_product_types,
    local_english_keywords,
    search_products_by_type,
    search_products_by_keywords,
    format_product_answer,
    resolve_language,
)

_FALLBACK_USER_ID = 1

def _ok(d=None, m="success"):
    return {"code": 200, "message": m, "data": d}

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _get_recent_history(db: Session, session_id: int, limit: int = 6) -> str:
    """获取最近 N 条对话历史，用于上下文理解"""
    msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    msgs = list(reversed(msgs))  # 时间正序
    lines = []
    for m in msgs:
        role = "用户" if m.role == "user" else "客服"
        lines.append(f"{role}: {m.content}")
    return "\n".join(lines)


# 中文品类名 → ABO 英文 product_type 映射
CN_TO_EN_CATEGORY = {
    "运动鞋": "TECHNICAL_SPORT_SHOE",
    "跑鞋": "TECHNICAL_SPORT_SHOE",
    "篮球鞋": "TECHNICAL_SPORT_SHOE",
    "足球鞋": "TECHNICAL_SPORT_SHOE",
    "手机壳": "CELLULAR_PHONE_CASE",
    "手机套": "CELLULAR_PHONE_CASE",
    "凉鞋": "SANDAL",
    "拖鞋": "SANDAL",
    "靴子": "BOOT",
    "靴": "BOOT",
    "鞋垫": "SHOE_INSERT",
    "鞋子": "SHOES",
    "鞋": "SHOES",
    "耳机": "HEADPHONES",
    "耳麦": "HEADPHONES",
    "手表": "WRIST_WATCH",
    "手环": "WRIST_WATCH",
    "戒指": "FINE_RING",
    "项链": "FINE_NECKLACE",
    "耳环": "FINE_EARRING",
    "手链": "FINE_BRACELET",
    "椅子": "CHAIR",
    "办公椅": "CHAIR",
    "沙发": "SOFA",
    "灯": "LIGHT_FIXTURE",
    "台灯": "LIGHT_FIXTURE",
    "家具": "HOME_FURNITURE_AND_DECOR",
    "办公用品": "OFFICE_PRODUCTS",
    "3d打印": "MECHANICAL_COMPONENTS",
    "五金": "MECHANICAL_COMPONENTS",
    "零食": "GROCERY",
    "薯片": "GROCERY",
    "坚果": "GROCERY",
    "小吃": "GROCERY",
    "食品": "GROCERY",
    "杂货": "GROCERY",
    "浴室": "HOME_BED_AND_BATH",
    "浴巾": "HOME_BED_AND_BATH",
    "床品": "HOME_BED_AND_BATH",
    "电脑": "PERSONAL_COMPUTER",
    "笔记本": "NOTEBOOK",
    "平板": "TABLET",
    "键盘": "KEYBOARD",
    "鼠标": "MOUSE",
    "背包": "BACKPACK",
    "包": "BACKPACK",
    "行李箱": "SUITCASE",
    "杯子": "DRINKING_CUP",
    "保温杯": "DRINKING_CUP",
    "水瓶": "DRINKING_CUP",
}


def _search_by_product_type(db: Session, query: str) -> list:
    """用中文品类名直接查数据库，补充 FAISS 检索"""
    results = []
    for cn_name, en_type in CN_TO_EN_CATEGORY.items():
        if cn_name in query:
            products = (
                db.query(AboProduct)
                .filter(AboProduct.product_type == en_type)
                .limit(5)
                .all()
            )
            for p in products:
                if p.faq_text not in results:
                    results.append(p.faq_text)
            if results:
                break  # 只匹配第一个命中的品类
    return results


async def _translate_query_for_search(query: str, history: str = "") -> str:
    """用 LLM 把中文查询翻译为英文检索关键词，结合对话历史理解上下文"""
    import httpx

    if not OPENAI_API_KEY:
        return ""

    history_block = f"Conversation history:\n{history}\n\n" if history else ""
    prompt = (
        "You are a search query translator for an e-commerce product database. "
        "Generate MULTIPLE English keywords (synonyms, related terms, broader/narrower categories) "
        "to maximize search recall. Include product type names, attributes, and related words.\n"
        "Example: '运动鞋' -> 'SNEAKER SHOES ATHLETIC RUNNING SPORT TECHNICAL_SPORT_SHOE'\n"
        "Example: '薯片' -> 'SNACK_CHIP_AND_CRISP CHIPS CRISPS SNACK GROCERY CRACKER POPCORN'\n"
        "Example: '手机壳' -> 'CELLULAR_PHONE_CASE PHONE CASE COVER ACCESSORY'\n\n"
        f"{history_block}"
        "If the user says '还有别的吗' or 'anything else', use the previous topic from the history.\n"
        "Return ONLY English keywords separated by spaces, nothing else.\n\n"
        f"User query: {query}\n"
        "English keywords:"
    )
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={"model": OPENAI_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0},
            )
            resp.raise_for_status()
            keywords = resp.json()["choices"][0]["message"]["content"].strip()
            if keywords:
                return keywords
    except Exception:
        pass
    return ""


def _build_catalog_summary(db: Session) -> str:
    """构建商品目录概况，让 LLM 知道真实的库存规模"""
    total = db.query(func.count(AboProduct.id)).scalar() or 0
    if total == 0:
        return ""

    # Top 10 categories with counts
    cats = (
        db.query(AboProduct.product_type, func.count(AboProduct.id))
        .filter(AboProduct.product_type != "", AboProduct.product_type.isnot(None))
        .group_by(AboProduct.product_type)
        .order_by(func.count(AboProduct.id).desc())
        .limit(10)
        .all()
    )
    cat_lines = "\n".join(f"  - {c}: {n} 件" for c, n in cats)

    return (
        f"平台共有 {total} 件在售商品。\n"
        f"主要品类分布：\n{cat_lines}"
    )


@router.post("/sessions", response_model=SessionOut)
def create_session(body: SessionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = ChatSession(user_id=current_user.id, title=body.title or "新会话")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )


@router.get("/messages/{session_id}", response_model=list[MessageOut])
def get_messages(session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "会话不存在")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    result = []
    for msg in messages:
        out = MessageOut.model_validate(msg)
        if msg.role == "assistant":
            fb = (
                db.query(ChatFeedback)
                .filter(ChatFeedback.message_id == msg.id)
                .first()
            )
            if fb:
                out.feedback = fb.feedback_type
        result.append(out)
    return result


@router.post("/upload")
async def upload_document(
    session_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "会话不存在")

    content = await file.read()
    try:
        text = parse_document(file.filename, content)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(400, f"文档解析失败: {e}")

    if not text.strip():
        raise HTTPException(400, "文档内容为空，无法建立索引")

    save_path = UPLOAD_DIR / f"{session_id}_{file.filename}"
    save_path.write_bytes(content)

    chunks = chunk_text(text)
    index_path = build_session_index(session_id, chunks)

    session.doc_name = file.filename
    session.faiss_index_path = str(index_path)
    if session.title == "新会话":
        session.title = Path(file.filename).stem[:50]
    db.commit()

    return {
        "message": "文档上传成功，FAISS 索引已建立",
        "session_id": session_id,
        "doc_name": file.filename,
        "chunks": len(chunks),
    }


@router.post("/message", response_model=MessageResponse)
async def send_message(body: MessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == body.session_id).first()
    if not session:
        raise HTTPException(404, "会话不存在")

    lang = resolve_language(body.language, body.content)

    user_msg = ChatMessage(
        session_id=body.session_id,
        role="user",
        content=body.content,
        language=lang,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    history = _get_recent_history(db, body.session_id, limit=6)

    # 1) 中文品类优先（不依赖 LLM / FAISS）
    product_types = detect_product_types(body.content)
    products = search_products_by_type(db, product_types, limit=8)

    # 2) 本地关键词 / LLM 翻译关键词
    translated = local_english_keywords(body.content)
    if not translated and any("\u4e00" <= c <= "\u9fff" for c in body.content):
        translated = await _translate_query_for_search(body.content, history)
    if translated and not products:
        products = search_products_by_keywords(db, translated, limit=8)

    # 3) FAISS 仅作补充（中文直接搜英文库效果差，有品类命中时不再用它污染结果）
    contexts: list[str] = []
    if products:
        contexts = [p.faq_text for p in products if p.faq_text]
    else:
        search_query = translated or body.content
        contexts = retrieve_context(body.session_id, search_query)
        # 翻译结果里的 product_type 再补一轮
        if translated:
            import re as _re
            db_types = set(_re.findall(r"[A-Z_]{4,}", translated))
            if db_types:
                more = search_products_by_type(db, list(db_types), limit=5)
                for p in more:
                    if p.faq_text and p.faq_text not in contexts:
                        contexts.insert(0, p.faq_text)
                if more and not products:
                    products = more

    catalog_summary = _build_catalog_summary(db)

    # 有明确商品命中时，优先用结构化回复（接近成员5演示效果）；有 LLM 再润色
    if products and not OPENAI_API_KEY:
        answer = format_product_answer(body.content, products, lang)
    else:
        answer = await generate_bilingual_reply(
            body.content, contexts, lang, catalog_summary, history
        )
        # LLM 失败或空回复时兜底
        if (not answer or "未在知识库" in answer or "couldn't find" in answer.lower()) and products:
            answer = format_product_answer(body.content, products, lang)

    assistant_msg = ChatMessage(
        session_id=body.session_id,
        role="assistant",
        content=answer,
        language=lang,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    refresh_daily_stats(db)

    return MessageResponse(
        user_message=MessageOut.model_validate(user_msg),
        assistant_message=MessageOut.model_validate(assistant_msg),
        sources=contexts[:3],
    )


@router.post("/feedback", response_model=FeedbackOut)
def submit_feedback(body: FeedbackCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    msg = db.query(ChatMessage).filter(ChatMessage.id == body.message_id).first()
    if not msg or msg.role != "assistant":
        raise HTTPException(404, "消息不存在或不可评价")

    existing = (
        db.query(ChatFeedback)
        .filter(
            ChatFeedback.message_id == body.message_id,
            ChatFeedback.user_id == current_user.id,
        )
        .first()
    )
    if existing:
        existing.feedback_type = body.feedback_type
        db.commit()
        db.refresh(existing)
        return existing

    fb = ChatFeedback(
        message_id=body.message_id,
        user_id=current_user.id,
        feedback_type=body.feedback_type,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb
