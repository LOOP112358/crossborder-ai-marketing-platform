import json
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .poster_service import compose_poster
from .database import get_db
from .db_models import Template, HistoryPoster, Favorite


app = FastAPI(title="海报合成模块 API")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class PosterComposeRequest(BaseModel):
    user_id: int = 1
    matted_url: str
    bg_url: str
    template_id: int

    # 五个通用文字层，全部可选
    title: str = ""
    subtitle: str = ""
    selling_point_1: str = ""
    selling_point_2: str = ""
    cta_text: str = ""

    # 兼容旧字段，不改数据库表结构
    discount: str = ""
    price: str = ""

    ratio: str = "1:1"

    # 主标题样式
    title_x: int | None = None
    title_y: int | None = None
    title_font_size: int | None = None
    title_color: str = "#111111"
    title_font_name: str = "msyh"
    title_art_style: str = "stroke_shadow"

    # 副标题样式
    subtitle_x: int | None = None
    subtitle_y: int | None = None
    subtitle_font_size: int | None = None
    subtitle_color: str = "#D81B60"
    subtitle_font_name: str = "msyh"
    subtitle_art_style: str = "stroke_shadow"

    # 卖点1样式
    selling_point_1_x: int | None = None
    selling_point_1_y: int | None = None
    selling_point_1_font_size: int | None = None
    selling_point_1_color: str = "#111111"
    selling_point_1_font_name: str = "msyh"
    selling_point_1_art_style: str = "shadow"

    # 卖点2样式
    selling_point_2_x: int | None = None
    selling_point_2_y: int | None = None
    selling_point_2_font_size: int | None = None
    selling_point_2_color: str = "#111111"
    selling_point_2_font_name: str = "msyh"
    selling_point_2_art_style: str = "shadow"

    # 按钮文案样式
    cta_text_x: int | None = None
    cta_text_y: int | None = None
    cta_text_font_size: int | None = None
    cta_text_color: str = "#FFFFFF"
    cta_text_font_name: str = "msyh"
    cta_text_art_style: str = "normal"
    cta_button_color: str = "#111111"

    # 全局文字效果
    text_stroke_enabled: bool = True
    text_stroke_color: str = "#FFFFFF"
    text_stroke_width: int = 2
    text_shadow_enabled: bool = True


class FavoriteRequest(BaseModel):
    user_id: int = 1


@app.get("/")
def root():
    return {
        "message": "海报合成模块启动成功",
        "docs": "/docs"
    }


@app.get("/api/templates")
def get_templates(db: Session = Depends(get_db)):
    templates = (
        db.query(Template)
        .filter(Template.is_active == True)
        .order_by(Template.id.asc())
        .all()
    )

    return [
        {
            "id": item.id,
            "name": item.name,
            "preview_url": item.preview_url,
            "usage_count": item.usage_count
        }
        for item in templates
    ]


@app.post("/api/poster/compose")
def api_compose_poster(
    req: PosterComposeRequest,
    db: Session = Depends(get_db)
):
    try:
        template = (
            db.query(Template)
            .filter(Template.id == req.template_id, Template.is_active == True)
            .first()
        )

        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")

        template_config = json.loads(template.config_json)

        subtitle_text = req.subtitle or req.discount
        cta_text = req.cta_text or req.price

        summary_text = " | ".join(
            item for item in [
                req.selling_point_1,
                req.selling_point_2,
                cta_text
            ]
            if item
        )

        text_layers = [
            {
                "key": "title",
                "text": req.title,
                "x": req.title_x,
                "y": req.title_y,
                "font_size": req.title_font_size,
                "color": req.title_color,
                "font_name": req.title_font_name,
                "art_style": req.title_art_style
            },
            {
                "key": "subtitle",
                "text": subtitle_text,
                "x": req.subtitle_x,
                "y": req.subtitle_y,
                "font_size": req.subtitle_font_size,
                "color": req.subtitle_color,
                "font_name": req.subtitle_font_name,
                "art_style": req.subtitle_art_style
            },
            {
                "key": "selling_point_1",
                "text": req.selling_point_1,
                "x": req.selling_point_1_x,
                "y": req.selling_point_1_y,
                "font_size": req.selling_point_1_font_size,
                "color": req.selling_point_1_color,
                "font_name": req.selling_point_1_font_name,
                "art_style": req.selling_point_1_art_style
            },
            {
                "key": "selling_point_2",
                "text": req.selling_point_2,
                "x": req.selling_point_2_x,
                "y": req.selling_point_2_y,
                "font_size": req.selling_point_2_font_size,
                "color": req.selling_point_2_color,
                "font_name": req.selling_point_2_font_name,
                "art_style": req.selling_point_2_art_style
            },
            {
                "key": "cta_text",
                "text": cta_text,
                "x": req.cta_text_x,
                "y": req.cta_text_y,
                "font_size": req.cta_text_font_size,
                "color": req.cta_text_color,
                "font_name": req.cta_text_font_name,
                "art_style": req.cta_text_art_style,
                "button_color": req.cta_button_color
            }
        ]

        style_options = {
            "text_layers": text_layers,
            "text_stroke_enabled": req.text_stroke_enabled,
            "text_stroke_color": req.text_stroke_color,
            "text_stroke_width": req.text_stroke_width,
            "text_shadow_enabled": req.text_shadow_enabled,
        }

        poster_url = compose_poster(
            matted_url=req.matted_url,
            bg_url=req.bg_url,
            template_config=template_config,
            title=req.title,
            discount=subtitle_text,
            price=summary_text,
            style_options=style_options
        )

        record = HistoryPoster(
            user_id=req.user_id,
            matted_url=req.matted_url,
            bg_url=req.bg_url,
            template_id=req.template_id,
            poster_url=poster_url,
            title=req.title,
            discount=subtitle_text,
            price=summary_text,
            ratio=req.ratio,
            downloads=0
        )

        db.add(record)
        template.usage_count = template.usage_count + 1

        db.commit()
        db.refresh(record)

        return {
            "message": "海报合成成功",
            "poster_url": poster_url,
            "record": {
                "id": record.id,
                "user_id": record.user_id,
                "matted_url": record.matted_url,
                "bg_url": record.bg_url,
                "template_id": record.template_id,
                "poster_url": record.poster_url,
                "title": record.title,
                "subtitle": record.discount,
                "selling_point_1": req.selling_point_1,
                "selling_point_2": req.selling_point_2,
                "cta_text": cta_text,
                "selling_point_summary": record.price,
                "discount": record.discount,
                "price": record.price,
                "ratio": record.ratio,
                "downloads": record.downloads,
                "created_at": str(record.created_at)
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/poster/history")
def get_history(user_id: int = 1, db: Session = Depends(get_db)):
    records = (
        db.query(HistoryPoster)
        .filter(HistoryPoster.user_id == user_id)
        .order_by(HistoryPoster.id.desc())
        .all()
    )

    return [
        {
            "id": item.id,
            "user_id": item.user_id,
            "poster_url": item.poster_url,
            "title": item.title,
            "subtitle": item.discount,
            "selling_point_summary": item.price,
            "discount": item.discount,
            "price": item.price,
            "ratio": item.ratio,
            "downloads": item.downloads,
            "created_at": str(item.created_at)
        }
        for item in records
    ]


@app.get("/api/poster/download/{poster_id}")
def download_poster(poster_id: int, db: Session = Depends(get_db)):
    record = (
        db.query(HistoryPoster)
        .filter(HistoryPoster.id == poster_id)
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="海报记录不存在")

    poster_url = record.poster_url

    if not poster_url.startswith("/static/"):
        raise HTTPException(status_code=500, detail="海报路径格式错误")

    relative_path = poster_url.replace("/static/", "")
    file_path = STATIC_DIR / relative_path

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="海报图片文件不存在")

    record.downloads = record.downloads + 1
    db.commit()

    return FileResponse(
        path=file_path,
        media_type="image/png",
        filename=file_path.name
    )


@app.post("/api/poster/favorite/{poster_id}")
def toggle_favorite(
    poster_id: int,
    req: FavoriteRequest,
    db: Session = Depends(get_db)
):
    poster = (
        db.query(HistoryPoster)
        .filter(HistoryPoster.id == poster_id)
        .first()
    )

    if not poster:
        raise HTTPException(status_code=404, detail="海报记录不存在")

    favorite = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == req.user_id,
            Favorite.poster_id == poster_id
        )
        .first()
    )

    if favorite:
        db.delete(favorite)
        db.commit()

        return {
            "message": "已取消收藏",
            "poster_id": poster_id,
            "is_favorite": False
        }

    new_favorite = Favorite(
        user_id=req.user_id,
        poster_id=poster_id
    )

    db.add(new_favorite)
    db.commit()
    db.refresh(new_favorite)

    return {
        "message": "收藏成功",
        "poster_id": poster_id,
        "is_favorite": True
    }


@app.get("/api/poster/favorites")
def get_favorites(user_id: int = 1, db: Session = Depends(get_db)):
    favorites = (
        db.query(Favorite, HistoryPoster)
        .join(HistoryPoster, Favorite.poster_id == HistoryPoster.id)
        .filter(Favorite.user_id == user_id)
        .order_by(Favorite.id.desc())
        .all()
    )

    return [
        {
            "favorite_id": favorite.id,
            "poster_id": poster.id,
            "poster_url": poster.poster_url,
            "title": poster.title,
            "subtitle": poster.discount,
            "selling_point_summary": poster.price,
            "discount": poster.discount,
            "price": poster.price,
            "ratio": poster.ratio,
            "downloads": poster.downloads,
            "created_at": str(favorite.created_at)
        }
        for favorite, poster in favorites
    ]


@app.post("/api/upload/image")
def upload_image(file: UploadFile = File(...)):
    allow_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]

    if file.content_type not in allow_types:
        raise HTTPException(status_code=400, detail="只支持 png、jpg、jpeg、webp 图片")

    suffix = Path(file.filename).suffix
    filename = f"upload_{uuid.uuid4().hex}{suffix}"
    save_path = UPLOAD_DIR / filename

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "message": "上传成功",
        "url": f"/static/uploads/{filename}"
    }