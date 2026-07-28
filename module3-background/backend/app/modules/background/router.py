"""背景生成路由 — JWT + 统一返回格式（豆包 Seedream）"""
import importlib.util
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.background import BackgroundHistory

router = APIRouter(prefix="/api/background", tags=["背景生成"])

ROOT = Path(__file__).resolve().parents[5]
STATIC_DIR = ROOT / "static" / "background"
GENERATED_DIR = STATIC_DIR / "generated"
ENHANCED_DIR = STATIC_DIR / "enhanced"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
ENHANCED_DIR.mkdir(parents=True, exist_ok=True)

_SERVICES = None


def _ok(data=None, message="success"):
    return {"code": 200, "message": message, "data": data}


def _services():
    global _SERVICES
    if _SERVICES is not None:
        return _SERVICES
    svc_path = ROOT / "module3-background" / "app" / "services.py"
    spec = importlib.util.spec_from_file_location("m3_bg_services", svc_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _SERVICES = mod
    return mod


@router.get("/options")
def get_options():
    return _ok({
        "styles": [
            {"value": "warm", "label": "温暖居家"},
            {"value": "scandi", "label": "北欧明亮"},
            {"value": "minimalist", "label": "简约纯色"},
            {"value": "luxury", "label": "奢华质感"},
            {"value": "tech", "label": "科技感"},
            {"value": "outdoor", "label": "户外自然"},
            {"value": "industrial", "label": "工业 loft"},
            {"value": "default", "label": "通用"},
        ],
        "scenes": [
            {"value": "", "label": "自动按商品推断"},
            {"value": "bright living room corner with empty floor space", "label": "明亮客厅角落"},
            {"value": "modern desk lifestyle shelf, soft daylight", "label": "现代桌面陈列"},
            {"value": "minimal studio pedestal, soft fabric ground", "label": "极简展台"},
            {"value": "cozy cafe table corner, warm ambient light", "label": "咖啡馆一角"},
            {"value": "luxury dark gradient jewelry display surface", "label": "奢品展台"},
        ],
        "lightings": [
            {"value": "", "label": "请选择"},
            {"value": "soft daylight from large window", "label": "大窗柔光"},
            {"value": "warm golden hour side light", "label": "金色侧光"},
            {"value": "clean studio softbox lighting", "label": "影棚柔光"},
            {"value": "cool morning skylight", "label": "清晨冷光"},
        ],
        "moods": [
            {"value": "", "label": "请选择"},
            {"value": "fresh and airy", "label": "清新通透"},
            {"value": "cozy and inviting", "label": "温馨舒适"},
            {"value": "premium and calm", "label": "高级静谧"},
            {"value": "energetic lifestyle", "label": "活力生活"},
        ],
        "cameras": [
            {"value": "", "label": "请选择"},
            {"value": "eye-level three-quarter view", "label": "平视四分之三"},
            {"value": "slight high angle looking down", "label": "微俯视"},
            {"value": "wide establishing shot with empty center", "label": "广角留白中心"},
            {"value": "close tabletop surface focus", "label": "桌面特写"},
        ],
        "colors": [
            {"value": "", "label": "请选择"},
            {"value": "warm beige and oak", "label": "暖米色橡木"},
            {"value": "soft white and sage", "label": "柔白鼠尾草"},
            {"value": "cool gray concrete", "label": "冷灰水泥"},
            {"value": "deep charcoal and gold", "label": "深炭金"},
            {"value": "pastel blush pink", "label": "淡粉"},
        ],
    })


@router.get("/styles")
def get_styles():
    return _ok((get_options()["data"] or {}).get("styles") or [])


@router.post("/generate")
async def generate(
    category: str = Form(...),
    style: str = Form("warm"),
    color_hint: str = Form(""),
    product_name: str = Form(""),
    brand: str = Form(""),
    product_type: str = Form(""),
    scene_preset: str = Form(""),
    lighting: str = Form(""),
    mood: str = Form(""),
    camera: str = Form(""),
    extra_note: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = _services()
    prompt = svc.build_prompt(
        category,
        style,
        color_hint,
        product_name=product_name,
        brand=brand,
        product_type=product_type,
        scene_preset=scene_preset,
        lighting=lighting,
        mood=mood,
        camera=camera,
        extra_note=extra_note,
    )
    try:
        bg_path = svc.generate_seedream(prompt, GENERATED_DIR)
    except Exception as exc:
        raise HTTPException(500, f"Seedream 背景生成失败: {exc}") from exc

    # 不再做本地假 2× 放大，直接复用同一张图（省磁盘与返回时间）
    bg_url = "/static/background/generated/" + bg_path.name
    enhanced_url = bg_url

    record = BackgroundHistory(
        user_id=current_user.id,
        product_category=category,
        style=style,
        color_hint=color_hint,
        prompt_used=prompt,
        bg_url=bg_url,
        enhanced_url=enhanced_url,
        scale_factor=1,
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
        "engine": "seedream",
        "created_at": str(record.created_at) if record.created_at else "",
    }, "Seedream 背景生成完成")


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
