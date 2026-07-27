"""Background generation routes.

Generates two background candidates:
- Doubao Seedream as the primary image.
- Stability AI Stable Diffusion as the enhanced image.
"""
import importlib.util
import os
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException
from PIL import Image, ImageDraw
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.background import BackgroundCache, BackgroundHistory
from app.models.user import User

router = APIRouter(prefix="/api/background", tags=["background"])

ROOT = Path(__file__).resolve().parents[5]
STATIC_DIR = ROOT / "static" / "background"
GENERATED_DIR = STATIC_DIR / "generated"
ENHANCED_DIR = STATIC_DIR / "enhanced"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
ENHANCED_DIR.mkdir(parents=True, exist_ok=True)

_SERVICES_PATH = ROOT / "module3-background" / "app" / "services.py"


def _load_services():
    """Load the module-owned services.py so the merged backend reuses one implementation."""
    if not _SERVICES_PATH.exists():
        raise FileNotFoundError(f"Background services file not found: {_SERVICES_PATH}")
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
    img = Image.new("RGB", (1024, 1024), (232, 232, 228))
    draw = ImageDraw.Draw(img)
    draw.text((72, 450), f"Mock background\n{prompt[:90]}", fill=(20, 20, 20))
    img.save(path)
    return path


def _mock_forced() -> bool:
    return os.getenv("BG_MOCK_MODE", "").strip() == "1"


def _sd_enabled(request_flag: Optional[bool] = None) -> bool:
    """是否调用 Stability。请求参数优先；否则看 BG_USE_SD（默认 0=关闭，省额度）。"""
    if request_flag is not None:
        return bool(request_flag)
    return os.getenv("BG_USE_SD", "0").strip() in ("1", "true", "True", "yes")


def _run_seedream(prompt: str) -> Path:
    if _mock_forced():
        print("[background] BG_MOCK_MODE=1; using Seedream mock image.")
        return _mock_image(prompt, GENERATED_DIR, "seedream_mock")
    if not all(os.getenv(name) for name in ("ARK_API_KEY", "ARK_BASE_URL", "ARK_MODEL")):
        print("[background] ARK_* is not configured; using Seedream mock image.")
        return _mock_image(prompt, GENERATED_DIR, "seedream_mock")
    try:
        return _svc.generate_seedream(prompt, GENERATED_DIR)
    except Exception as exc:
        print(f"[background] Seedream failed; using mock image: {exc}")
        return _mock_image(prompt, GENERATED_DIR, "seedream_mock")


def _run_sd(prompt: str) -> Path:
    if _mock_forced():
        print("[background] BG_MOCK_MODE=1; using Stable Diffusion mock image.")
        return _mock_image(prompt, ENHANCED_DIR, "sd_mock")
    if not os.getenv("STABILITY_API_KEY"):
        print("[background] STABILITY_API_KEY is not configured; using Stable Diffusion mock image.")
        return _mock_image(prompt, ENHANCED_DIR, "sd_mock")
    try:
        return _svc.generate_stable_diffusion(prompt, ENHANCED_DIR)
    except Exception as exc:
        # 额度不足 / 402 / 429 等：不要误当成成功，交由上层回退到 Seedream
        print(f"[background] Stable Diffusion failed: {exc}")
        raise


def _serialize_record(record: BackgroundHistory, cached: bool):
    return {
        "id": record.id,
        "product_category": record.product_category,
        "style": record.style,
        "color_hint": record.color_hint,
        "prompt_used": record.prompt_used,
        "bg_url": record.bg_url,
        "enhanced_url": record.enhanced_url,
        "cached": cached,
        "created_at": str(record.created_at) if record.created_at else "",
    }


def _generate_and_save(
    *,
    category: str,
    style: str,
    color_hint: str,
    current_user: User,
    db: Session,
    product_name: str = "",
    brand: str = "",
    product_type: str = "",
    scene_preset: str = "",
    lighting: str = "",
    mood: str = "",
    camera: str = "",
    extra_note: str = "",
    use_sd: Optional[bool] = None,
):
    """Generate images, persist history, and reuse cached images for identical inputs."""
    cache_key = _svc.build_cache_key(
        category,
        style,
        color_hint or "",
        product_name=product_name,
        brand=brand,
        scene_preset=scene_preset,
        lighting=lighting,
        mood=mood,
        camera=camera,
        extra_note=extra_note,
    )
    # 是否走 SD 也纳入缓存区分，避免「仅 Seedream」命中旧的双图缓存
    sd_on = _sd_enabled(use_sd)
    cache_key = f"{cache_key}|sd={1 if sd_on else 0}"
    cached = db.query(BackgroundCache).filter(BackgroundCache.cache_key == cache_key).first()
    if cached:
        record = BackgroundHistory(
            user_id=current_user.id,
            product_category=category,
            style=style,
            color_hint=color_hint,
            prompt_used="(from cache)",
            bg_url=cached.bg_url,
            enhanced_url=cached.enhanced_url,
            scale_factor=2,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return _ok(_serialize_record(record, cached=True), "returned cached background")

    prompt_kwargs = dict(
        product_name=product_name,
        brand=brand,
        product_type=product_type,
        scene_preset=scene_preset,
        lighting=lighting,
        mood=mood,
        camera=camera,
        extra_note=extra_note,
    )
    seedream_prompt = _svc.build_prompt(category, style, color_hint, **prompt_kwargs)
    sd_prompt = _svc.build_sd_prompt(category, style, color_hint, **prompt_kwargs)

    print(
        f"[background] generating category={category!r} product={product_name!r} "
        f"brand={brand!r} use_sd={sd_on} …"
    )
    sd_path = None
    if sd_on:
        with ThreadPoolExecutor(max_workers=2) as pool:
            fut_bg = pool.submit(_run_seedream, seedream_prompt)
            fut_sd = pool.submit(_run_sd, sd_prompt)
            bg_path = fut_bg.result()
            try:
                sd_path = fut_sd.result()
            except Exception as exc:
                print(f"[background] SD skipped after failure (quota/error): {exc}")
                sd_path = None
    else:
        bg_path = _run_seedream(seedream_prompt)

    if sd_path is None:
        # 复用 Seedream 结果，避免额度不足时写入占位图误导用户
        ENHANCED_DIR.mkdir(parents=True, exist_ok=True)
        sd_path = ENHANCED_DIR / f"{uuid.uuid4().hex}_seedream_copy{bg_path.suffix}"
        shutil.copyfile(bg_path, sd_path)
        prompt_used = f"Seedream Prompt:\n{seedream_prompt}\n\n(Stable Diffusion skipped)"
    else:
        prompt_used = f"Seedream Prompt:\n{seedream_prompt}\n\nStable Diffusion Prompt:\n{sd_prompt}"

    print(f"[background] done: {bg_path.name} / {sd_path.name}")

    bg_url = f"/static/background/generated/{bg_path.name}"
    enhanced_url = f"/static/background/enhanced/{sd_path.name}"

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
    db.add(
        BackgroundCache(
            cache_key=cache_key,
            category=category,
            style=style,
            color_hint=color_hint,
            bg_url=bg_url,
            enhanced_url=enhanced_url,
        )
    )
    db.commit()
    db.refresh(record)

    return _ok(_serialize_record(record, cached=False), "background generated")


@router.post("/generate")
async def generate(
    category: str = Form(...),
    style: str = Form("default"),
    color_hint: str = Form(""),
    product_name: str = Form(""),
    brand: str = Form(""),
    product_type: str = Form(""),
    scene_preset: str = Form(""),
    lighting: str = Form(""),
    mood: str = Form(""),
    camera: str = Form(""),
    extra_note: str = Form(""),
    use_sd: str = Form("0"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    flag = use_sd.strip().lower() in ("1", "true", "yes", "on")
    return _generate_and_save(
        category=category.strip(),
        style=style.strip() or "default",
        color_hint=color_hint.strip(),
        product_name=product_name.strip(),
        brand=brand.strip(),
        product_type=product_type.strip(),
        scene_preset=scene_preset.strip(),
        lighting=lighting.strip(),
        mood=mood.strip(),
        camera=camera.strip(),
        extra_note=extra_note.strip(),
        use_sd=flag,
        current_user=current_user,
        db=db,
    )


@router.post("/generate_from_product")
async def generate_from_product(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a background from the product recognition result."""
    category = payload.get("category") or "unknown"
    attributes = payload.get("attributes") or {}
    style = attributes.get("style") or attributes.get("风格") or "modern commercial"
    color_hint = attributes.get("color") or attributes.get("颜色") or ""
    product_name = payload.get("product_name") or payload.get("name") or ""
    brand = payload.get("brand") or attributes.get("brand") or ""
    product_type = payload.get("product_type") or payload.get("category_en") or ""
    return _generate_and_save(
        category=str(category).strip(),
        style=str(style).strip() or "default",
        color_hint=str(color_hint).strip(),
        product_name=str(product_name).strip(),
        brand=str(brand).strip(),
        product_type=str(product_type).strip(),
        scene_preset=str(payload.get("scene_preset") or attributes.get("scene") or "").strip(),
        lighting=str(payload.get("lighting") or attributes.get("lighting") or "").strip(),
        mood=str(payload.get("mood") or attributes.get("mood") or "").strip(),
        camera=str(payload.get("camera") or "").strip(),
        extra_note=str(payload.get("extra_note") or "").strip(),
        current_user=current_user,
        db=db,
    )


@router.get("/styles")
def get_styles():
    return _ok(
        [
            {"value": "outdoor", "label": "户外自然"},
            {"value": "minimalist", "label": "简约纯色"},
            {"value": "luxury", "label": "奢华质感"},
            {"value": "tech", "label": "科技感"},
            {"value": "warm", "label": "温暖居家"},
            {"value": "scandi", "label": "北欧明亮"},
            {"value": "industrial", "label": "工业风"},
            {"value": "default", "label": "通用商业"},
        ]
    )


@router.get("/options")
def get_options():
    """背景生成可选项：场景 / 光照 / 氛围 / 机位。"""
    return _ok(
        {
            "styles": [
                {"value": "outdoor", "label": "户外自然"},
                {"value": "minimalist", "label": "简约纯色"},
                {"value": "luxury", "label": "奢华质感"},
                {"value": "tech", "label": "科技感"},
                {"value": "warm", "label": "温暖居家"},
                {"value": "scandi", "label": "北欧明亮"},
                {"value": "industrial", "label": "工业风"},
                {"value": "default", "label": "通用商业"},
            ],
            "scenes": [
                {"value": "", "label": "自动（按商品推断）"},
                {"value": "bright living room corner with empty floor space", "label": "明亮客厅一角"},
                {"value": "modern apartment dining area, empty central floor", "label": "现代餐厅空间"},
                {"value": "clean studio seamless backdrop with soft floor", "label": "影棚无缝背景"},
                {"value": "Scandinavian home interior with large window light", "label": "北欧窗边家居"},
                {"value": "wooden desk surface lifestyle shelf, shallow DOF", "label": "木质桌面陈列"},
                {"value": "outdoor patio with soft daylight, empty placement area", "label": "户外露台日光"},
                {"value": "luxury showroom pedestal environment, no product", "label": "奢华展台环境"},
                {"value": "cozy bedroom corner, empty floor for furniture", "label": "温馨卧室一角"},
            ],
            "lightings": [
                {"value": "", "label": "默认柔光"},
                {"value": "soft daylight from large window", "label": "窗边日光"},
                {"value": "warm golden hour light", "label": "暖金黄昏光"},
                {"value": "cool studio softbox lighting", "label": "影棚冷色柔光"},
                {"value": "dramatic side rim light", "label": "侧逆光戏剧光"},
                {"value": "bright even high-key lighting", "label": "高调均匀光"},
            ],
            "moods": [
                {"value": "", "label": "默认"},
                {"value": "fresh and airy", "label": "清新通透"},
                {"value": "cozy and inviting", "label": "温馨亲切"},
                {"value": "premium and elegant", "label": "高级优雅"},
                {"value": "minimal and calm", "label": "极简安静"},
                {"value": "vibrant lifestyle", "label": "活力生活"},
            ],
            "cameras": [
                {"value": "", "label": "默认平视"},
                {"value": "eye-level three-quarter view", "label": "平视三分视角"},
                {"value": "slightly elevated top-down angle", "label": "轻微俯拍"},
                {"value": "low angle heroic perspective", "label": "低角度仰拍"},
                {"value": "wide establishing shot with empty center", "label": "广角留白中心"},
            ],
            "colors": [
                {"value": "", "label": "跟随商品/自定义"},
                {"value": "soft blue and gray", "label": "柔蓝灰"},
                {"value": "warm beige and wood", "label": "暖米木色"},
                {"value": "white and light oak", "label": "白+浅橡木"},
                {"value": "deep charcoal and gold accent", "label": "深灰+金色"},
                {"value": "sage green natural tones", "label": "鼠尾草绿"},
            ],
        }
    )


@router.get("/history")
def history(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(BackgroundHistory)
        .filter(BackgroundHistory.user_id == current_user.id)
        .order_by(BackgroundHistory.id.desc())
    )
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return _ok(
        {
            "items": [
                {
                    "id": r.id,
                    "product_category": r.product_category,
                    "style": r.style,
                    "bg_url": r.bg_url,
                    "enhanced_url": r.enhanced_url,
                    "created_at": str(r.created_at) if r.created_at else "",
                }
                for r in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/history/{record_id}")
def get_history_item(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(BackgroundHistory)
        .filter(
            BackgroundHistory.id == record_id,
            BackgroundHistory.user_id == current_user.id,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Background record not found")
    return _ok(_serialize_record(record, cached=False))
