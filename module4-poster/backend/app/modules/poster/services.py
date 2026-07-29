"""海报合成引擎 —— 对接 poster_module 完整能力（排版 / Seedream 精修）"""
import importlib.util
import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

# module4-poster/backend/app/modules/poster/services.py → 仓库根
REPO_ROOT = Path(__file__).resolve().parents[5]
STATIC_DIR = REPO_ROOT / "static"
POSTER_DIR = STATIC_DIR / "poster"
POSTER_DIR.mkdir(parents=True, exist_ok=True)

# 精简模板（仅表为空时灌库；有完整模板时不会覆盖）
TEMPLATE_DATA = [
    {
        "id": 1, "name": "商品居中模板",
        "preview_url": "/static/poster/templates/template_1.png",
        "config": {
            "canvas": {"width": 1080, "height": 1080},
            "product": {"x": 260, "y": 360, "w": 560, "h": 560},
            "title": {"x": 80, "y": 90, "font_size": 64, "color": "#FFFFFF"},
            "discount": {"x": 80, "y": 180, "font_size": 84, "color": "#FFD700"},
            "price": {"x": 80, "y": 290, "font_size": 56, "color": "#FFFFFF"},
        },
    },
]


@lru_cache(maxsize=1)
def _poster_engine():
    svc_path = REPO_ROOT / "module4-poster" / "poster_module" / "poster_service.py"
    spec = importlib.util.spec_from_file_location("poster_engine_svc", svc_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # 统一写到仓库根 static/poster，与 FastAPI 静态挂载一致
    mod.STATIC_DIR = STATIC_DIR
    mod.POSTER_DIR = POSTER_DIR
    POSTER_DIR.mkdir(parents=True, exist_ok=True)
    return mod


def compose_poster(
    matted_url: str,
    bg_url: str,
    template_config: dict,
    title: str = "",
    discount: str = "",
    price: str = "",
    style_options: Optional[dict] = None,
) -> str:
    """合成海报，返回 /static/poster/... URL"""
    engine = _poster_engine()
    return engine.compose_poster(
        matted_url=matted_url,
        bg_url=bg_url,
        template_config=template_config,
        title=title,
        discount=discount,
        price=price,
        style_options=style_options or {},
    )


def clear_poster_engine_cache():
    _poster_engine.cache_clear()


def init_templates(db):
    """初始化/更新模板数据到数据库（按 id upsert，便于迭代模板样式）"""
    from app.models.poster import Template

    templates_path = REPO_ROOT / "module4-poster" / "poster_module" / "templates_data.py"
    items = TEMPLATE_DATA
    if templates_path.exists():
        try:
            spec = importlib.util.spec_from_file_location("poster_templates_data", templates_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if getattr(mod, "TEMPLATES", None):
                items = mod.TEMPLATES
            elif getattr(mod, "TEMPLATE_DATA", None):
                items = mod.TEMPLATE_DATA
        except Exception as exc:
            print(f"[poster] load templates_data failed: {exc}")

    for t in items:
        cfg = t.get("config") or t.get("config_json") or {}
        if isinstance(cfg, str):
            cfg_json = cfg
        else:
            cfg_json = json.dumps(cfg, ensure_ascii=False)
        tid = t.get("id")
        name = t.get("name") or f"模板{tid}"
        preview = t.get("preview_url") or ""
        existing = db.query(Template).filter(Template.id == tid).first() if tid is not None else None
        if existing:
            existing.name = name
            existing.preview_url = preview
            existing.config_json = cfg_json
            existing.is_active = True
        else:
            db.add(Template(
                id=tid,
                name=name,
                preview_url=preview,
                config_json=cfg_json,
            ))
    db.commit()
