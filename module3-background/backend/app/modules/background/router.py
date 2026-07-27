"""背景生成路由 — 桥接成员3最新双模型实现 + JWT + 统一返回"""
import importlib.util
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException
from PIL import Image, ImageDraw
from sqlalchemy.orm import Session

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

_SERVICES_PATH = ROOT / "module3-background" / "app" / "services.py"


def _load_services():
    """动态加载成员3最新 services.py，避免复制逻辑漂移。"""
    if not _SERVICES_PATH.exists():
        raise FileNotFoundError(f"找不到背景服务: {_SERVICES_PATH}")
    spec = importlib.util.spec_from_file_location("m3_bg_services", _SERVICES_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


_svc = _load_services()


def _ok(data=None, message="success"):
    return {"code": 200, "message": message, "data": data}


def _mock_image(prompt: str, output_dir: Path, suffix: str) -> Path:
    filename = f"{uuid.uuid4().hex}_{suffix}.png"
    path = output_dir / filename
    img = Image.new("RGB", (1024, 1024), (230, 230, 230))
    draw = ImageDraw.Draw(img)
    draw.text((80, 450), f"Mock: {prompt[:70]}...", fill=(0, 0, 0))
    img.save(path)
    return path


def _run_seedream(prompt: str) -> Path:
    api_key = os.getenv("ARK_API_KEY", "")
    base_url = os.getenv("ARK_BASE_URL", "")
    model = os.getenv("ARK_MODEL", "")
    if not (api_key and base_url and model):
        print("[background] ARK_* 未配置，豆包走 Mock")
        return _mock_image(prompt, GENERATED_DIR, "seedream_mock")
    try:
        return _svc.generate_seedream(prompt, GENERATED_DIR)
    except Exception as e:
        print(f"[background] Seedream 失败，回退 Mock: {e}")
        return _mock_image(prompt, GENERATED_DIR, "seedream_mock")


def _run_sd(prompt: str) -> Path:
    api_key = os.getenv("STABILITY_API_KEY", "")
    if not api_key:
        print("[background] STABILITY_API_KEY 未配置，SD 走 Mock")
        return _mock_image(prompt, ENHANCED_DIR, "sd_mock")
    try:
        return _svc.generate_stable_diffusion(prompt, ENHANCED_DIR)
    except Exception as e:
        print(f"[background] Stability 失败，回退 Mock: {e}")
        return _mock_image(prompt, ENHANCED_DIR, "sd_mock")


def _generate_and_save(
    *,
    category: str,
    style: str,
    color_hint: str,
    current_user: User,
    db: Session,
):
    """双模型：豆包 Seedream → bg_url；Stable Diffusion → enhanced_url。"""
    prompt = _svc.build_prompt(category, style, color_hint)
    sd_prompt = _svc.build_sd_prompt(category, style, color_hint)

    bg_path = _run_seedream(prompt)
    sd_path = _run_sd(sd_prompt)

    bg_url = "/static/background/generated/" + bg_path.name
    enhanced_url = "/static/background/enhanced/" + sd_path.name
    prompt_used = f"Seedream Prompt:\n{prompt}\n\nSD Prompt:\n{sd_prompt}"

    record = BackgroundHistory(
        user_id=current_user.id,
        product_category=category,
        style=style,
        color_hint=color_hint,
        prompt_used=prompt_used,
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


@router.post("/generate")
async def generate(
    category: str = Form(...),
    style: str = Form("default"),
    color_hint: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _generate_and_save(
        category=category,
        style=style,
        color_hint=color_hint,
        current_user=current_user,
        db=db,
    )


@router.post("/generate_from_product")
async def generate_from_product(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """成员2 识别结果 → 背景生成。"""
    category = payload.get("category") or "unknown"
    attributes = payload.get("attributes") or {}
    style = attributes.get("style") or attributes.get("风格") or "modern commercial"
    color_hint = attributes.get("color") or attributes.get("颜色") or ""
    return _generate_and_save(
        category=category,
        style=style,
        color_hint=color_hint,
        current_user=current_user,
        db=db,
    )


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


@router.get("/history/{record_id}")
def get_history_item(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(BackgroundHistory).filter(
        BackgroundHistory.id == record_id,
        BackgroundHistory.user_id == current_user.id,
    ).first()
    if not r:
        raise HTTPException(404, "背景记录不存在")
    return _ok({
        "id": r.id,
        "product_category": r.product_category,
        "style": r.style,
        "color_hint": r.color_hint,
        "prompt_used": r.prompt_used,
        "bg_url": r.bg_url,
        "enhanced_url": r.enhanced_url,
        "created_at": str(r.created_at) if r.created_at else "",
    })
