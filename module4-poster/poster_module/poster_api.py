import json
from pathlib import Path
from fastapi import UploadFile, File
import shutil
import uuid
from fastapi import FastAPI, HTTPException, Depends
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
    title: str
    discount: str
    price: str
    ratio: str = "1:1"


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

        poster_url = compose_poster(
            matted_url=req.matted_url,
            bg_url=req.bg_url,
            template_config=template_config,
            title=req.title,
            discount=req.discount,
            price=req.price
        )

        record = HistoryPoster(
            user_id=req.user_id,
            matted_url=req.matted_url,
            bg_url=req.bg_url,
            template_id=req.template_id,
            poster_url=poster_url,
            title=req.title,
            discount=req.discount,
            price=req.price,
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
class FavoriteRequest(BaseModel):
    user_id: int = 1

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