import shutil, re, httpx
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.security import get_current_user
from app.models.user import User
from app.core.database import get_db
from app.models.chat import ChatSession, ChatMessage, ChatFeedback, AboProduct
from app.modules.chat.schemas import SessionCreate, SessionOut, MessageCreate, MessageOut, MessageResponse, FeedbackCreate, FeedbackOut
from app.modules.chat.services.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, UPLOAD_DIR, FAISS_DIR
from app.modules.chat.services.document_parser import parse_document, chunk_text
from app.modules.chat.services.rag_service import build_session_index, retrieve_context
from app.modules.chat.services.llm_service import generate_bilingual_reply
from app.modules.chat.services.stats_service import refresh_daily_stats

_FALLBACK_USER_ID = 1

def _ok(d=None, m="success"):
    return {"code": 200, "message": m, "data": d}

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _get_recent_history(db: Session, session_id: int, limit: int = 6) -> str:
    msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    msgs = list(reversed(msgs))
    lines = []
    for m in msgs:
        role = "用户" if m.role == "user" else "客服"
        lines.append(f"{role}: {m.content}")
    return "\n".join(lines)


async def _translate_query_for_search(query: str, history: str = "") -> str:
    if not OPENAI_API_KEY:
        return ""

    history_block = f"Conversation history:\n{history}\n\n" if history else ""
    prompt = (
        "You are a search query translator for an e-commerce product database. "
        "Generate MULTIPLE English keywords (synonyms, related terms, broader/narrower categories) "
        "to maximize search recall. Include product type names, attributes, and related words.\n"
        "Example: '运动鞋' -> 'SNEAKER SHOES ATHLETIC RUNNING SPORT TECHNICAL_SPORT_SHOE'\n"
        "Example: '薯片' -> 'SNACK_CHIP_AND_CRISP CHIPS CRISPS SNACK GROCERY CRACKER POPCORN'\n"
        "Example: '耳机' -> 'HEADPHONES EARPHONE EARBUDS BLUETOOTH HEADSET AUDIO WIRELESS'\n"
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
    total = db.query(func.count(AboProduct.id)).scalar() or 0
    if total == 0:
        return ""

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


@router.post("/sessions")
def create_session(body: SessionCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = ChatSession(user_id=current_user.id, title=body.title or "新会话")
    db.add(session); db.commit(); db.refresh(session)
    return _ok(SessionOut.model_validate(session).model_dump(), "会话创建成功")


@router.get("/sessions")
def list_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return _ok([SessionOut.model_validate(s).model_dump() for s in sessions])


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(404, "会话不存在")

    msg_ids = [
        m.id
        for m in db.query(ChatMessage.id).filter(ChatMessage.session_id == session_id).all()
    ]
    if msg_ids:
        db.query(ChatFeedback).filter(ChatFeedback.message_id.in_(msg_ids)).delete(synchronize_session=False)
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete(synchronize_session=False)

    # 清理会话 FAISS 索引文件
    for suffix in (".faiss", ".pkl"):
        p = FAISS_DIR / f"session_{session_id}{suffix}"
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass
    # 兼容旧路径字段
    if session.faiss_index_path:
        base = Path(session.faiss_index_path)
        for candidate in (base.with_suffix(".faiss"), base.with_suffix(".pkl"), Path(str(base) + ".faiss"), Path(str(base) + ".pkl")):
            if candidate.exists():
                try:
                    candidate.unlink()
                except OSError:
                    pass

    db.delete(session)
    db.commit()
    return _ok({"id": session_id}, "会话已删除")


@router.get("/messages/{session_id}")
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
            fb = db.query(ChatFeedback).filter(ChatFeedback.message_id == msg.id).first()
            if fb: out.feedback = fb.feedback_type
        result.append(out.model_dump())
    return _ok(result)


@router.post("/upload")
async def upload_document(
    session_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
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

    return _ok({
        "session_id": session_id,
        "doc_name": file.filename,
        "chunks": len(chunks),
    }, "文档上传成功，FAISS 索引已建立")


@router.post("/message")
async def send_message(body: MessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == body.session_id).first()
    if not session:
        raise HTTPException(404, "会话不存在")

    user_msg = ChatMessage(
        session_id=body.session_id,
        role="user",
        content=body.content,
        language=body.language,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    history = _get_recent_history(db, body.session_id, limit=6)

    # LLM 翻译中文查询为英文关键词，然后直接 SQLite LIKE 搜
    search_query = body.content
    translated = ""
    if any("一" <= c <= "鿿" for c in body.content):
        translated = await _translate_query_for_search(body.content, history)
    if translated:
        search_query = translated

    # FAISS 向量检索（主）
    contexts = retrieve_context(body.session_id, search_query)

    # 补充：翻译结果中的 product_type 精确匹配，直接查 DB
    if translated:
        keywords = set(re.findall(r"[A-Z_]{4,}", translated))
        if keywords:
            valid_types = set(
                r[0] for r in db.query(AboProduct.product_type)
                .filter(AboProduct.product_type.in_(keywords)).all()
            )
            seen_ids = set()
            for pt in valid_types:
                products = db.query(AboProduct).filter(AboProduct.product_type == pt).limit(5).all()
                for p in products:
                    if p.item_id not in seen_ids and p.faq_text not in contexts:
                        seen_ids.add(p.item_id)
                        contexts.insert(0, p.faq_text)

    catalog_summary = _build_catalog_summary(db)

    answer = await generate_bilingual_reply(body.content, contexts, body.language, catalog_summary, history)

    assistant_msg = ChatMessage(
        session_id=body.session_id,
        role="assistant",
        content=answer,
        language=body.language,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    refresh_daily_stats(db)

    return _ok({
        "user_message": MessageOut.model_validate(user_msg).model_dump(),
        "assistant_message": MessageOut.model_validate(assistant_msg).model_dump(),
        "sources": contexts[:3],
    }, "回复成功")


@router.post("/feedback")
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
        db.commit(); db.refresh(existing)
        return _ok(FeedbackOut.model_validate(existing).model_dump())

    fb = ChatFeedback(
        message_id=body.message_id,
        user_id=current_user.id,
        feedback_type=body.feedback_type,
    )
    db.add(fb); db.commit(); db.refresh(fb)
    return _ok(FeedbackOut.model_validate(fb).model_dump(), "反馈成功")
