"""商品抠图路由 — 适配主项目标准（JWT + SQLAlchemy + 统一返回格式）"""
import io
import os
import uuid
import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.matte import MatteHistory
from app.modules.matte.services import remove_background, recognize

router = APIRouter(prefix="/api/matte", tags=["商品抠图"])

# 静态文件目录（仓库根 static/matte）
REPO_ROOT = Path(__file__).resolve().parents[5]
STATIC_DIR = REPO_ROOT / "static"
MATTE_DIR = STATIC_DIR / "matte"
MATTE_DIR.mkdir(parents=True, exist_ok=True)

# 文件大小限制
MAX_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def _ok(data=None, message="success"):
    return {"code": 200, "message": message, "data": data}


@router.get("/health")
def health():
    return _ok({"mock_mode": os.getenv("MATTE_MOCK_MODE") == "1", "status": "ready"})


def _resolve_local_image(url: str) -> Path:
    """把 /static/... 解析到仓库根或 ABO 目录。"""
    raw = (url or "").strip()
    if not raw:
        raise HTTPException(400, "image_url 不能为空")
    p = Path(raw)
    if p.is_file():
        return p
    if raw.startswith("/static/abo-images/"):
        rel = raw[len("/static/abo-images/") :].lstrip("/").replace("\\", "/")
        try:
            from app.modules.chat.services.config import ABO_IMAGES_DIR
            cand = ABO_IMAGES_DIR / rel
            if cand.is_file():
                return cand
        except Exception:
            pass
        raise HTTPException(404, f"ABO 图片不存在: {url}")
    if raw.startswith("/static/"):
        rel = raw[len("/static/") :].lstrip("/").replace("\\", "/")
        cand = STATIC_DIR / rel
        if cand.is_file():
            return cand
        raise HTTPException(404, f"静态图片不存在: {url}")
    raise HTTPException(400, "仅支持 /static/ 下的本地图片 URL")


async def _run_matte_pipeline(
    raw: bytes,
    filename: str,
    edge_smoothing: int,
    current_user: User,
    db: Session,
    category_hint: str | None = None,
    category_en_hint: str | None = None,
):
    if not raw or len(raw) > MAX_SIZE:
        raise HTTPException(400, "图片不能为空且大小不能超过10MB")
    try:
        image = Image.open(io.BytesIO(raw))
        image.verify()
    except UnidentifiedImageError:
        raise HTTPException(400, "仅支持有效的JPG、PNG或WEBP图片")

    ext = Path(filename or "image.jpg").suffix.lower()
    ext = ext if ext in ALLOWED_EXT else ".jpg"

    token = uuid.uuid4().hex
    original_path = MATTE_DIR / f"{token}_original{ext}"
    output_path = MATTE_DIR / f"{token}_matted.png"
    original_path.write_bytes(raw)

    result_image = remove_background(raw, max(0, min(edge_smoothing, 2)))
    result_image.save(output_path, "PNG", optimize=True)

    # 有品类提示（库内选品）时跳过 Ollama，避免卡住超时
    detected = await recognize(raw, skip_ollama=bool(category_hint or category_en_hint))
    if category_hint:
        detected["category"] = category_hint
        detected["confidence"] = max(float(detected.get("confidence") or 0), 0.95)
    if category_en_hint:
        detected["category_en"] = category_en_hint

    record = MatteHistory(
        user_id=current_user.id,
        original_url=f"/static/matte/{original_path.name}",
        matted_url=f"/static/matte/{output_path.name}",
        category=detected.get("category", "商品"),
        category_en=detected.get("category_en", "product"),
        confidence=detected.get("confidence", 0.55),
        attributes=json.dumps(detected.get("attributes", {}), ensure_ascii=False),
        file_size=len(raw),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    attrs = detected.get("attributes", {})
    return {
        "id": record.id,
        "original_url": record.original_url,
        "matted_url": record.matted_url,
        "category": record.category,
        "category_en": record.category_en,
        "confidence": record.confidence,
        "attributes": attrs,
        "file_size": record.file_size,
        "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S") if record.created_at else "",
    }


@router.post("/process")
async def process_matte(
    file: UploadFile = File(...),
    edge_smoothing: int = Form(1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传图片 → 抠图 → 识别 → 保存历史"""
    raw = await file.read()
    data = await _run_matte_pipeline(raw, file.filename or "image.jpg", edge_smoothing, current_user, db)
    return _ok(data, "抠图与识别完成")


@router.post("/process-url")
async def process_matte_url(
    image_url: str = Form(...),
    edge_smoothing: int = Form(1),
    category: str = Form(""),
    category_en: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """对库内商品主图 /static/... 执行抠图，供海报工作流第1步使用。"""
    path = _resolve_local_image(image_url)
    raw = path.read_bytes()
    data = await _run_matte_pipeline(
        raw,
        path.name,
        edge_smoothing,
        current_user,
        db,
        category_hint=category or None,
        category_en_hint=category_en or None,
    )
    return _ok(data, "库内商品抠图完成")


@router.get("/history")
def history(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的抠图历史（分页）"""
    query = db.query(MatteHistory).filter(
        MatteHistory.user_id == current_user.id
    ).order_by(MatteHistory.id.desc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return _ok({
        "items": [
            {
                "id": item.id,
                "original_url": item.original_url,
                "matted_url": item.matted_url,
                "category": item.category,
                "category_en": item.category_en,
                "confidence": item.confidence,
                "attributes": json.loads(item.attributes) if item.attributes else {},
                "file_size": item.file_size,
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else "",
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/download/{record_id}")
def download(record_id: int, db: Session = Depends(get_db)):
    """下载抠图结果"""
    record = db.query(MatteHistory).filter(MatteHistory.id == record_id).first()
    if not record:
        raise HTTPException(404, "记录不存在")

    path = (STATIC_DIR / record.matted_url.lstrip("/static/").lstrip("/"))
    if not path.exists():
        raise HTTPException(404, "结果文件不存在")

    return FileResponse(str(path), media_type="image/png", filename=f"product-matte-{record_id}.png")
