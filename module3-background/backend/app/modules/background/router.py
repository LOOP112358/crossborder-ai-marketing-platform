"""背景生成路由 — JWT + 统一返回格式"""
import uuid
import os
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from PIL import Image, ImageDraw
import requests

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.background import BackgroundHistory

router = APIRouter(prefix="/api/background", tags=["背景生成"])

ROOT = Path(__file__).resolve().parents[5]  # project root
STATIC_DIR = ROOT / "static" / "background"
GENERATED_DIR = STATIC_DIR / "generated"
ENHANCED_DIR = STATIC_DIR / "enhanced"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
ENHANCED_DIR.mkdir(parents=True, exist_ok=True)


def _ok(data=None, message="success"):
    return {"code": 200, "message": message, "data": data}


def build_prompt(category: str, style: str, color_hint: str) -> str:
    return (
        f"A high quality commercial background for {category}, "
        f"style is {style}, color tone is {color_hint}, "
        f"professional e-commerce photography"
    )


def generate_background(prompt: str, output_dir: Path) -> Path:
    """支持豆包 Seedream API 或 Mock 模式"""
    api_key = os.getenv("ARK_API_KEY", "")
    if api_key:
        return _generate_by_api(prompt, output_dir, api_key)
    return _mock_generate(prompt, output_dir)


def _generate_by_api(prompt: str, output_dir: Path, api_key: str) -> Path:
    base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    model = os.getenv("ARK_MODEL", "doubao-seedream-4-0-250828")
    url = base_url + "/images/generations"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "prompt": prompt, "size": "1024x1024", "n": 1},
        timeout=120,
    )
    resp.raise_for_status()
    image_url = resp.json()["data"][0]["url"]
    img_data = requests.get(image_url, timeout=120).content
    filename = uuid.uuid4().hex + "_background.jpg"
    output_path = output_dir / filename
    output_path.write_bytes(img_data)
    return output_path


def _mock_generate(prompt: str, output_dir: Path) -> Path:
    filename = uuid.uuid4().hex + "_background.png"
    path = output_dir / filename
    img = Image.new("RGB", (1024, 1024), (230, 230, 230))
    draw = ImageDraw.Draw(img)
    draw.text((100, 450), f"Mock: {prompt[:60]}...", fill=(0, 0, 0))
    img.save(path)
    return path


def super_resolution(image_path: Path, output_dir: Path) -> Path:
    """2x 超分（后续可替换为 Real-ESRGAN）"""
    img = Image.open(image_path)
    result = img.resize((img.width * 2, img.height * 2))
    output = output_dir / image_path.name.replace(".png", "_2x.png").replace(".jpg", "_2x.jpg")
    result.save(output)
    return output


@router.post("/generate")
async def generate(
    category: str = Form(...),
    style: str = Form("default"),
    color_hint: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prompt = build_prompt(category, style, color_hint)
    bg_path = generate_background(prompt, GENERATED_DIR)
    enhanced_path = super_resolution(bg_path, ENHANCED_DIR)

    bg_url = "/static/background/generated/" + bg_path.name
    enhanced_url = "/static/background/enhanced/" + enhanced_path.name

    record = BackgroundHistory(
        user_id=current_user.id,
        product_category=category,
        style=style,
        color_hint=color_hint,
        prompt_used=prompt,
        bg_url=bg_url,
        enhanced_url=enhanced_url,
        scale_factor=2,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return _ok({
        "id": record.id,
        "product_category": record.product_category,
        "style": record.style,
        "prompt_used": record.prompt_used,
        "bg_url": record.bg_url,
        "enhanced_url": record.enhanced_url,
        "created_at": str(record.created_at) if record.created_at else "",
    }, "背景生成完成")


@router.get("/styles")
def get_styles():
    return _ok([
        {"value": "outdoor", "label": "户外自然"},
        {"value": "minimalist", "label": "简约纯色"},
        {"value": "luxury", "label": "奢华质感"},
        {"value": "tech", "label": "科技感"},
        {"value": "warm", "label": "温暖居家"},
        {"value": "default", "label": "通用"},
    ])


@router.get("/history")
def history(
    page: int = 1, page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(BackgroundHistory).filter(
        BackgroundHistory.user_id == current_user.id
    ).order_by(BackgroundHistory.id.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return _ok({
        "items": [{
            "id": r.id, "product_category": r.product_category,
            "style": r.style, "bg_url": r.bg_url,
            "enhanced_url": r.enhanced_url,
            "created_at": str(r.created_at) if r.created_at else "",
        } for r in items],
        "total": total, "page": page, "page_size": page_size,
    })
