"""海报合成路由 — 完整对接成员4原始功能"""
import json, uuid, shutil
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
    matted_url: str; bg_url: str; template_id: int
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
    text_stroke_enabled:bool=True;text_stroke_color:str="#FFF";text_stroke_width:int=2;text_shadow_enabled:bool=True

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
    template=db.query(Template).filter(Template.id==req.template_id,Template.is_active==True).first()
    if not template: raise HTTPException(404,"模板不存在")
    try:
        style_options = {
            "text_stroke_enabled": req.text_stroke_enabled,
            "text_stroke_color": req.text_stroke_color,
            "text_stroke_width": req.text_stroke_width,
            "text_shadow_enabled": req.text_shadow_enabled,
            "text_layers": [
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
            matted_url=req.matted_url,
            bg_url=req.bg_url,
            template_config=json.loads(template.config_json),
            title=req.title,
            discount=req.subtitle or req.discount,
            price=req.cta_text or req.price,
            style_options=style_options,
        )
    except FileNotFoundError as e: raise HTTPException(400,str(e))
    record=PosterHistory(user_id=current_user.id,matted_url=req.matted_url,bg_url=req.bg_url,
        template_id=req.template_id,poster_url=poster_url,title=req.title,
        discount=req.subtitle or req.discount,price=req.cta_text or req.price,ratio=req.ratio,downloads=0)
    template.usage_count+=1;db.add(record);db.commit();db.refresh(record)
    return _ok({"id":record.id,"poster_url":poster_url,"title":record.title,"discount":record.discount,"price":record.price,"created_at":str(record.created_at) if record.created_at else ""},"海报合成成功")

@router.get("/history")
def get_history(page:int=1,page_size:int=20,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    q=db.query(PosterHistory).filter(PosterHistory.user_id==current_user.id).order_by(desc(PosterHistory.id))
    total=q.count();items=q.offset((page-1)*page_size).limit(page_size).all()
    return _ok({"items":[{"id":r.id,"poster_url":r.poster_url,"title":r.title or "","discount":r.discount or "","price":r.price or "","downloads":r.downloads,"created_at":str(r.created_at) if r.created_at else ""} for r in items],"total":total,"page":page,"page_size":page_size})

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
    if fav: db.delete(fav);db.commit();return _ok({"is_favorite":False},"已取消收藏")
    db.add(Favorite(user_id=current_user.id,poster_id=pid));db.commit()
    return _ok({"is_favorite":True},"收藏成功")

@router.get("/favorites")
def get_favs(current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    rows=db.query(Favorite,PosterHistory).join(PosterHistory).filter(Favorite.user_id==current_user.id).order_by(desc(Favorite.id)).all()
    return _ok([{"favorite_id":fav.id,"poster_id":poster.id,"poster_url":poster.poster_url,"title":poster.title or "","downloads":poster.downloads,"created_at":str(fav.created_at) if fav.created_at else ""} for fav,poster in rows])

@router.get("/init-templates")
def api_init(db:Session=Depends(get_db)): init_templates(db);return _ok(None,"初始化完成")
