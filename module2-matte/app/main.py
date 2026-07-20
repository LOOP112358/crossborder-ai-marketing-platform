import io
import os
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError

from .database import MatteRepository
from .services import recognize, remove_background


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
MATTE_DIR = STATIC / "matte"
MATTE_DIR.mkdir(parents=True, exist_ok=True)
repo = MatteRepository(ROOT / "data" / "matte.db")

app = FastAPI(title="商品抠图与智能识别 API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def ok(data=None, message="success"):
    return {"code": 0, "message": message, "data": data}


@app.get("/", response_class=HTMLResponse)
def home():
    return (ROOT / "frontend" / "demo.html").read_text(encoding="utf-8")


@app.get("/api/matte/health")
def health():
    return ok({"mock_mode": os.getenv("MATTE_MOCK_MODE") == "1", "status": "ready"})


@app.post("/api/matte/process")
async def process_matte(
    file: UploadFile = File(...),
    user_id: int = Form(1),
    edge_smoothing: int = Form(1),
):
    raw = await file.read()
    if not raw or len(raw) > 10 * 1024 * 1024:
        raise HTTPException(400, "图片不能为空且大小不能超过10MB")
    try:
        image = Image.open(io.BytesIO(raw))
        image.verify()
    except UnidentifiedImageError as exc:
        raise HTTPException(400, "仅支持有效的JPG、PNG或WEBP图片") from exc
    ext = Path(file.filename or "image.jpg").suffix.lower()
    ext = ext if ext in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"
    token = uuid.uuid4().hex
    original = MATTE_DIR / f"{token}_original{ext}"
    output = MATTE_DIR / f"{token}_matted.png"
    original.write_bytes(raw)
    result = remove_background(raw, max(0, min(edge_smoothing, 2)))
    result.save(output, "PNG", optimize=True)
    detected = await recognize(raw)
    record = repo.create({
        "user_id": user_id,
        "original_url": f"/static/matte/{original.name}",
        "matted_url": f"/static/matte/{output.name}",
        "file_size": len(raw),
        **detected,
    })
    return ok(record, "抠图与识别完成")


@app.get("/api/matte/history")
def history(user_id: int = 1, limit: int = 50):
    return ok(repo.list(user_id, max(1, min(limit, 100))))


@app.get("/api/matte/download/{record_id}")
def download(record_id: int):
    record = repo.get(record_id)
    if not record:
        raise HTTPException(404, "记录不存在")
    path = ROOT / record["matted_url"].lstrip("/")
    if not path.exists():
        raise HTTPException(404, "结果文件不存在")
    return FileResponse(path, media_type="image/png", filename=f"product-matte-{record_id}.png")

