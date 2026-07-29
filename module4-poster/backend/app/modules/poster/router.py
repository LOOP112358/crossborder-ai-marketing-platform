"""海报合成路由 — 完整对接成员4原始功能"""
import json, uuid, shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.poster import Template, PosterHistory, Favorite
from app.modules.poster.services import compose_poster as do_compose, init_templates

router = APIRouter(prefix="/api/poster", tags=["海报合成"])
STATIC_ROOT = Path(__file__).resolve().parents[5] / "static"
UPLOAD_DIR = STATIC_ROOT / "poster" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def _ok(d=None, m="success"): return {"code":200,"message":m,"data":d}

class ComposeRequest(BaseModel):
    matted_url: str = ""
    bg_url: str = ""
    template_id: Optional[int] = None
    title: str = ""; subtitle: str = ""; selling_point_1: str = ""; selling_point_2: str = ""; cta_text: str = ""
    discount: str = ""; price: str = ""; ratio: str = "1:1"
    title_color:str="#111";title_font_name:str="msyh";title_art_style:Optional[str]="stroke_shadow"
    title_x:Optional[int]=None;title_y:Optional[int]=None;title_font_size:Optional[int]=None
    subtitle_color:str="#D81B60";subtitle_font_name:str="msyh";subtitle_art_style:Optional[str]="stroke_shadow"
    subtitle_x:Optional[int]=None;subtitle_y:Optional[int]=None;subtitle_font_size:Optional[int]=None
    selling_point_1_color:str="#111";selling_point_1_font_name:str="msyh";selling_point_1_art_style:Optional[str]="shadow"
    selling_point_1_x:Optional[int]=None;selling_point_1_y:Optional[int]=None;selling_point_1_font_size:Optional[int]=None
    selling_point_2_color:str="#111";selling_point_2_font_name:str="msyh";selling_point_2_art_style:Optional[str]="shadow"
    selling_point_2_x:Optional[int]=None;selling_point_2_y:Optional[int]=None;selling_point_2_font_size:Optional[int]=None
    cta_text_color:str="#FFF";cta_button_color:str="#111";cta_text_font_name:str="msyh";cta_text_art_style:Optional[str]="normal"
    cta_text_x:Optional[int]=None;cta_text_y:Optional[int]=None;cta_text_font_size:Optional[int]=None
    text_stroke_enabled:bool=False;text_stroke_color:str="#FFF";text_stroke_width:int=2;text_shadow_enabled:bool=True
    auto_layout:bool=True
    sd_refine:bool=False
    sd_refine_strength:float=0.28
    refine_enabled:bool=False
    refine_engine:str="seedream"
    product_hint:str=""
    skip_text: bool = False
    parent_id: Optional[int] = None
    base_poster_url: Optional[str] = None


def _asset_kind(record) -> str:
    kind = getattr(record, "asset_kind", None) or "final"
    return kind if kind in ("base", "final") else "final"


def _history_item(r) -> dict:
    return {
        "id": r.id,
        "poster_url": r.poster_url,
        "title": r.title or "",
        "discount": r.discount or "",
        "price": r.price or "",
        "downloads": r.downloads or 0,
        "is_public": bool(r.is_public),
        "published_at": str(r.published_at) if r.published_at else "",
        "created_at": str(r.created_at) if r.created_at else "",
        "asset_kind": _asset_kind(r),
        "parent_id": getattr(r, "parent_id", None),
        "template_id": r.template_id,
        "matted_url": r.matted_url or "",
        "bg_url": r.bg_url or "",
    }

@router.post("/upload/image")
def upload_image(file:UploadFile=File(...),current_user:User=Depends(get_current_user)):
    if file.content_type not in {"image/png","image/jpeg","image/jpg","image/webp"}: raise HTTPException(400,"仅支持png/jpg/jpeg/webp")
    ext=Path(file.filename).suffix if file.filename else ".png";fn=f"upload_{uuid.uuid4().hex}{ext}"
    with open(UPLOAD_DIR/fn,"wb") as f: shutil.copyfileobj(file.file,f)
    return _ok({"url":f"/static/poster/uploads/{fn}"},"上传成功")

@router.get("/templates")
def get_templates(db:Session=Depends(get_db)):
    items=[]
    for t in db.query(Template).filter(Template.is_active==True).order_by(Template.id.asc()).all():
        purpose=""
        try:
            cfg=json.loads(t.config_json or "{}")
            purpose=cfg.get("purpose","")
        except Exception:
            pass
        items.append({"id":t.id,"name":t.name,"preview_url":t.preview_url,"usage_count":t.usage_count,"purpose":purpose,"config":json.loads(t.config_json or "{}")})
    return items

@router.post("/compose")
def api_compose(req:ComposeRequest,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    parent = None
    base_poster_url = (req.base_poster_url or "").strip()
    if req.parent_id:
        parent = db.query(PosterHistory).filter(
            PosterHistory.id == req.parent_id,
            PosterHistory.user_id == current_user.id,
        ).first()
        if not parent:
            raise HTTPException(404, "底图记录不存在或无权使用")
        if _asset_kind(parent) != "base" and not base_poster_url:
            # 允许用成稿当参考底图，但优先用记录的 poster_url
            pass
        base_poster_url = base_poster_url or (parent.poster_url or "")

    template_id = req.template_id or (parent.template_id if parent else None)
    if not template_id:
        raise HTTPException(400, "请选择模板")
    template = db.query(Template).filter(Template.id == template_id, Template.is_active == True).first()  # noqa: E712
    if not template:
        raise HTTPException(404, "模板不存在")

    matted_url = (req.matted_url or (parent.matted_url if parent else "") or "").strip()
    bg_url = (req.bg_url or (parent.bg_url if parent else "") or "").strip()
    skip_text = bool(req.skip_text)
    text_on_base = bool(base_poster_url) and not skip_text

    if skip_text and (not matted_url or not bg_url):
        raise HTTPException(400, "生成无字底图需要商品图与背景图")
    if text_on_base and not base_poster_url:
        raise HTTPException(400, "加文案需要先选择底图")
    if not skip_text and not text_on_base and (not matted_url or not bg_url):
        raise HTTPException(400, "请提供商品图与背景图，或选择已有底图")

    try:
        style_options = {
            "text_stroke_enabled": req.text_stroke_enabled,
            "text_stroke_color": req.text_stroke_color,
            "text_stroke_width": req.text_stroke_width,
            "text_shadow_enabled": req.text_shadow_enabled,
            "auto_layout": req.auto_layout,
            "sd_refine": False if text_on_base else (req.sd_refine or req.refine_enabled),
            "sd_refine_strength": req.sd_refine_strength,
            "refine_enabled": False if text_on_base else (req.refine_enabled or req.sd_refine),
            "refine_engine": req.refine_engine or "seedream",
            "product_hint": req.product_hint,
            "skip_text": skip_text,
            "base_image_url": base_poster_url if text_on_base else "",
            "text_layers": [] if skip_text else [
                {
                    "key": "title",
                    "text": req.title,
                    "x": req.title_x,
                    "y": req.title_y,
                    "font_size": req.title_font_size,
                    "color": req.title_color,
                    "font_name": req.title_font_name,
                    "art_style": req.title_art_style,
                },
                {
                    "key": "subtitle",
                    "text": req.subtitle or req.discount,
                    "x": req.subtitle_x,
                    "y": req.subtitle_y,
                    "font_size": req.subtitle_font_size,
                    "color": req.subtitle_color,
                    "font_name": req.subtitle_font_name,
                    "art_style": req.subtitle_art_style,
                },
                {
                    "key": "selling_point_1",
                    "text": req.selling_point_1,
                    "x": req.selling_point_1_x,
                    "y": req.selling_point_1_y,
                    "font_size": req.selling_point_1_font_size,
                    "color": req.selling_point_1_color,
                    "font_name": req.selling_point_1_font_name,
                    "art_style": req.selling_point_1_art_style,
                },
                {
                    "key": "selling_point_2",
                    "text": req.selling_point_2,
                    "x": req.selling_point_2_x,
                    "y": req.selling_point_2_y,
                    "font_size": req.selling_point_2_font_size,
                    "color": req.selling_point_2_color,
                    "font_name": req.selling_point_2_font_name,
                    "art_style": req.selling_point_2_art_style,
                },
                {
                    "key": "cta_text",
                    "text": req.cta_text or req.price,
                    "x": req.cta_text_x,
                    "y": req.cta_text_y,
                    "font_size": req.cta_text_font_size,
                    "color": req.cta_text_color,
                    "font_name": req.cta_text_font_name,
                    "art_style": req.cta_text_art_style,
                    "button_color": req.cta_button_color,
                },
            ],
        }
        poster_url = do_compose(
            matted_url=matted_url or (parent.matted_url if parent else ""),
            bg_url=bg_url or (parent.bg_url if parent else ""),
            template_config=json.loads(template.config_json),
            title="" if skip_text else req.title,
            discount="" if skip_text else (req.subtitle or req.discount),
            price="" if skip_text else (req.cta_text or req.price),
            style_options=style_options,
        )
    except FileNotFoundError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    asset_kind = "base" if skip_text else "final"
    record = PosterHistory(
        user_id=current_user.id,
        matted_url=matted_url or (parent.matted_url if parent else ""),
        bg_url=bg_url or (parent.bg_url if parent else ""),
        template_id=template_id,
        poster_url=poster_url,
        title="" if skip_text else req.title,
        discount="" if skip_text else (req.subtitle or req.discount),
        price="" if skip_text else (req.cta_text or req.price),
        ratio=req.ratio,
        downloads=0,
        asset_kind=asset_kind,
        parent_id=parent.id if (parent and asset_kind == "final") else None,
    )
    template.usage_count += 1
    db.add(record)
    db.commit()
    db.refresh(record)
    msg = "无字底图生成成功" if skip_text else "海报合成成功"
    return _ok({
        **_history_item(record),
        "created_at": str(record.created_at) if record.created_at else "",
    }, msg)

@router.get("/history")
def get_history(
    page: int = 1,
    page_size: int = 20,
    asset_kind: str = "final",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(PosterHistory).filter(PosterHistory.user_id == current_user.id)
    kind = (asset_kind or "final").strip().lower()
    if kind in ("base", "final"):
        # 旧数据 asset_kind 为空时按 final 处理
        if kind == "final":
            q = q.filter((PosterHistory.asset_kind == "final") | (PosterHistory.asset_kind.is_(None)) | (PosterHistory.asset_kind == ""))
        else:
            q = q.filter(PosterHistory.asset_kind == "base")
    q = q.order_by(desc(PosterHistory.id))
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return _ok({
        "items": [_history_item(r) for r in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    })

@router.delete("/history/{pid}")
def delete_history(pid: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.query(PosterHistory).filter(
        PosterHistory.id == pid,
        PosterHistory.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(404, "海报记录不存在或无权删除")

    # 清掉所有用户对该海报的收藏
    db.query(Favorite).filter(Favorite.poster_id == pid).delete(synchronize_session=False)

    poster_url = record.poster_url or ""
    db.delete(record)
    db.commit()

    # 尽量删本地文件（失败不影响接口）
    if poster_url.startswith("/static/"):
        try:
            path = STATIC_ROOT / poster_url.replace("/static/", "").lstrip("/")
            if path.is_file():
                path.unlink()
        except Exception:
            pass

    return _ok({"id": pid}, "已删除海报")


@router.get("/gallery")
def get_gallery(page: int = 1, page_size: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    page = max(1, page)
    page_size = min(max(1, page_size), 60)
    q = (
        db.query(PosterHistory, User)
        .join(User, PosterHistory.user_id == User.id)
        .filter(PosterHistory.is_public == True)  # noqa: E712
        .filter((PosterHistory.asset_kind == "final") | (PosterHistory.asset_kind.is_(None)) | (PosterHistory.asset_kind == ""))
        .order_by(desc(PosterHistory.published_at), desc(PosterHistory.id))
    )
    total = q.count()
    rows = q.offset((page - 1) * page_size).limit(page_size).all()
    fav_ids = {
        f.poster_id
        for f in db.query(Favorite.poster_id).filter(
            Favorite.user_id == current_user.id,
            Favorite.poster_id.in_([p.id for p, _ in rows] or [-1]),
        ).all()
    }
    items = []
    for poster, author in rows:
        items.append({
            "id": poster.id,
            "poster_url": poster.poster_url,
            "title": poster.title or "",
            "discount": poster.discount or "",
            "price": poster.price or "",
            "downloads": poster.downloads or 0,
            "username": author.username,
            "is_own": poster.user_id == current_user.id,
            "is_favorite": poster.id in fav_ids,
            "published_at": str(poster.published_at) if poster.published_at else "",
            "created_at": str(poster.created_at) if poster.created_at else "",
        })
    return _ok({"items": items, "total": total, "page": page, "page_size": page_size})


@router.post("/{pid}/publish")
def publish_poster(pid: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.query(PosterHistory).filter(
        PosterHistory.id == pid,
        PosterHistory.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(404, "海报记录不存在或无权发布")
    if _asset_kind(record) == "base":
        raise HTTPException(400, "无字底图不能发布到作品广场，请先加文案生成成稿")
    record.is_public = True
    if not record.published_at:
        record.published_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    return _ok({
        "id": record.id,
        "is_public": True,
        "published_at": str(record.published_at) if record.published_at else "",
    }, "已发布到作品广场")


@router.post("/{pid}/unpublish")
def unpublish_poster(pid: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.query(PosterHistory).filter(
        PosterHistory.id == pid,
        PosterHistory.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(404, "海报记录不存在或无权操作")
    record.is_public = False
    db.commit()
    return _ok({"id": record.id, "is_public": False}, "已取消发布")


@router.get("/download/{pid}")
def download_poster(pid:int,db:Session=Depends(get_db)):
    r=db.query(PosterHistory).filter(PosterHistory.id==pid).first()
    if not r: raise HTTPException(404,"不存在")
    p=STATIC_ROOT/r.poster_url.replace("/static/","").lstrip("/")
    if not p.exists(): raise HTTPException(404,"文件不存在")
    r.downloads+=1;db.commit()
    return FileResponse(str(p),media_type="image/png",filename=p.name)

@router.post("/favorite/{pid}")
def toggle_fav(pid:int,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    poster=db.query(PosterHistory).filter(PosterHistory.id==pid).first()
    if not poster: raise HTTPException(404,"不存在")
    fav=db.query(Favorite).filter(Favorite.user_id==current_user.id,Favorite.poster_id==pid).first()
    if fav:
        db.delete(fav)
        db.commit()
        return _ok({"is_favorite": False}, "已取消收藏")
    # 仅可收藏：自己的作品，或他人已发布到广场的作品
    if poster.user_id != current_user.id and not poster.is_public:
        raise HTTPException(403, "只能收藏已发布到广场的作品")
    db.add(Favorite(user_id=current_user.id, poster_id=pid))
    db.commit()
    return _ok({"is_favorite": True}, "收藏成功")

@router.get("/favorites")
def get_favs(current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    rows = (
        db.query(Favorite, PosterHistory, User)
        .join(PosterHistory, Favorite.poster_id == PosterHistory.id)
        .join(User, PosterHistory.user_id == User.id)
        .filter(Favorite.user_id == current_user.id)
        .order_by(desc(Favorite.id))
        .all()
    )
    return _ok([{
        "favorite_id": fav.id,
        "poster_id": poster.id,
        "poster_url": poster.poster_url,
        "title": poster.title or "",
        "discount": poster.discount or "",
        "price": poster.price or "",
        "downloads": poster.downloads,
        "username": author.username,
        "is_own": poster.user_id == current_user.id,
        "is_public": bool(poster.is_public),
        "asset_kind": _asset_kind(poster),
        "parent_id": getattr(poster, "parent_id", None),
        "template_id": poster.template_id,
        "matted_url": poster.matted_url or "",
        "bg_url": poster.bg_url or "",
        "created_at": str(fav.created_at) if fav.created_at else "",
    } for fav, poster, author in rows])

@router.get("/init-templates")
def api_init(db:Session=Depends(get_db)): init_templates(db);return _ok(None,"初始化完成")
