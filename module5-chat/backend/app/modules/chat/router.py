"""智能客服路由 — JWT + 统一返回格式"""
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage, ChatFeedback
from app.modules.chat.schemas import SessionCreate, MessageCreate, FeedbackCreate
from app.modules.chat.services.config import UPLOAD_DIR
from app.modules.chat.services.document_parser import parse_document, chunk_text
from app.modules.chat.services.rag_service import build_session_index, retrieve_context
from app.modules.chat.services.llm_service import generate_bilingual_reply
from app.modules.chat.services.stats_service import refresh_daily_stats

router = APIRouter(prefix="/api/chat", tags=["智能客服"])


def _ok(data=None, message="success"):
    return {"code": 200, "message": message, "data": data}


def _get_recent_history(db: Session, session_id: int, limit: int = 6) -> str:
    msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit).all()
    )
    lines = []
    for m in reversed(msgs):
        role = "用户" if m.role == "user" else "客服"
        lines.append(f"{role}: {m.content}")
    return "\n".join(lines)


# ─── 会话管理 ──────────────────────────────────────────

@router.post("/sessions")
def create_session(
    body: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = ChatSession(user_id=current_user.id, title=body.title or "新会话")
    db.add(s); db.commit(); db.refresh(s)
    return _ok({
        "id": s.id, "title": s.title, "doc_name": s.doc_name,
        "created_at": str(s.created_at) if s.created_at else "",
    }, "会话创建成功")


@router.get("/sessions")
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc()).all()
    )
    return _ok([{
        "id": s.id, "title": s.title, "doc_name": s.doc_name,
        "created_at": str(s.created_at) if s.created_at else "",
    } for s in sessions])


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = db.query(ChatSession).filter(
        ChatSession.id == session_id, ChatSession.user_id == current_user.id
    ).first()
    if not s:
        raise HTTPException(404, "会话不存在")
    db.delete(s); db.commit()
    return _ok(None, "会话已删除")


# ─── 消息 ──────────────────────────────────────────────

@router.get("/messages/{session_id}")
def get_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "会话不存在")
    msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at).all()
    )
    result = []
    for msg in msgs:
        item = {
            "id": msg.id, "session_id": msg.session_id,
            "role": msg.role, "content": msg.content,
            "language": msg.language,
            "created_at": str(msg.created_at) if msg.created_at else "",
            "feedback": None,
        }
        if msg.role == "assistant":
            fb = db.query(ChatFeedback).filter(ChatFeedback.message_id == msg.id).first()
            if fb: item["feedback"] = fb.feedback_type
        result.append(item)
    return _ok(result)


# ─── 文档上传 ──────────────────────────────────────────

@router.post("/upload")
async def upload_doc(
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
        raise HTTPException(400, "文档内容为空")

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
        "session_id": session_id, "doc_name": file.filename, "chunks": len(chunks),
    }, "文档上传成功，索引已建立")


# ─── 发送消息（RAG核心流程）────────────────────────────

@router.post("/message")
async def send_message(
    body: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(ChatSession.id == body.session_id).first()
    if not session:
        raise HTTPException(404, "会话不存在")

    user_msg = ChatMessage(
        session_id=body.session_id, role="user",
        content=body.content, language=body.language,
    )
    db.add(user_msg); db.commit(); db.refresh(user_msg)

    history = _get_recent_history(db, body.session_id, limit=6)
    search_query = body.content

    # 中文查询 → LLM翻译为英文关键词提升检索命中率
    if any('一' <= c <= '鿿' for c in body.content):
        try:
            from app.modules.chat.services.llm_service import (
                _translate_query_for_search, OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
            )
            import httpx
            if OPENAI_API_KEY:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
                        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                        json={"model": OPENAI_MODEL, "messages": [{"role": "user", "content": (
                            "Translate this query to English keywords for e-commerce search. "
                            f"Return ONLY keywords separated by spaces.\nQuery: {body.content}"
                        )}], "temperature": 0},
                    )
                    if resp.status_code == 200:
                        translated = resp.json()["choices"][0]["message"]["content"].strip()
                        if translated: search_query = translated
        except Exception:
            pass

    contexts = retrieve_context(body.session_id, search_query)
    answer = await generate_bilingual_reply(body.content, contexts, body.language)

    assistant_msg = ChatMessage(
        session_id=body.session_id, role="assistant",
        content=answer, language=body.language,
    )
    db.add(assistant_msg); db.commit(); db.refresh(assistant_msg)
    refresh_daily_stats(db)

    return _ok({
        "user_message": {
            "id": user_msg.id, "role": "user", "content": user_msg.content,
            "language": user_msg.language,
            "created_at": str(user_msg.created_at) if user_msg.created_at else "",
        },
        "assistant_message": {
            "id": assistant_msg.id, "role": "assistant", "content": answer,
            "language": body.language,
            "created_at": str(assistant_msg.created_at) if assistant_msg.created_at else "",
        },
        "sources": contexts[:3],
    }, "回复成功")


# ─── 反馈 ──────────────────────────────────────────────

@router.post("/feedback")
def submit_feedback(
    body: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    msg = db.query(ChatMessage).filter(ChatMessage.id == body.message_id).first()
    if not msg or msg.role != "assistant":
        raise HTTPException(404, "消息不存在或不可评价")

    existing = db.query(ChatFeedback).filter(
        ChatFeedback.message_id == body.message_id,
        ChatFeedback.user_id == current_user.id,
    ).first()
    if existing:
        existing.feedback_type = body.feedback_type
        db.commit(); db.refresh(existing)
        return _ok({"id": existing.id, "feedback_type": existing.feedback_type})

    fb = ChatFeedback(message_id=body.message_id, user_id=current_user.id, feedback_type=body.feedback_type)
    db.add(fb); db.commit(); db.refresh(fb)
    return _ok({"id": fb.id, "feedback_type": fb.feedback_type}, "反馈提交成功")
