"""海报合成引擎 — 桥接成员4原始 poster_module，统一 static 路径"""
import importlib.util
import json
from pathlib import Path

# services.py → poster → modules → app → backend → module4-poster → repo
REPO_ROOT = Path(__file__).resolve().parents[5]
STATIC_DIR = REPO_ROOT / "static"
POSTER_DIR = STATIC_DIR / "poster"
UPLOAD_DIR = POSTER_DIR / "uploads"
POSTER_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATE_DATA = [
    {
        "id": 2,
        "name": "左文右图 · 详情种草",
        "preview_url": "/static/poster/templates/template_2.png",
        "config": {
            "purpose": "种草详情卡",
            "canvas": {"width": 1080, "height": 1080},
            "overlays": [{"type": "left_panel", "ratio": 0.46, "color": [255, 255, 255, 200]}],
            "product_shadow": True,
            "product": {"x": 520, "y": 260, "w": 500, "h": 560},
            "text_defaults": {
                "title": {"x": 56, "y": 120, "font_size": 48, "color": "#1C2A32", "art_style": "normal"},
                "subtitle": {"x": 56, "y": 220, "font_size": 30, "color": "#C45C26", "art_style": "normal"},
                "selling_point_1": {"x": 56, "y": 320, "font_size": 28, "color": "#243038", "art_style": "normal"},
                "selling_point_2": {"x": 56, "y": 380, "font_size": 28, "color": "#243038", "art_style": "normal"},
                "cta_text": {"x": 56, "y": 880, "font_size": 34, "color": "#FFFFFF", "button_color": "#C45C26"},
            },
        },
    },
    {
        "id": 3,
        "name": "上文下图 · 清新上新",
        "preview_url": "/static/poster/templates/template_3.png",
        "config": {
            "purpose": "上新宣传",
            "canvas": {"width": 1080, "height": 1080},
            "overlays": [{"type": "top_band", "ratio": 0.34, "color": [47, 111, 106, 150]}],
            "product_shadow": True,
            "product": {"x": 210, "y": 400, "w": 660, "h": 560},
            "text_defaults": {
                "title": {"x": 80, "y": 70, "font_size": 56, "color": "#FFFFFF", "art_style": "shadow"},
                "subtitle": {"x": 80, "y": 160, "font_size": 34, "color": "#E8FFF8", "art_style": "normal"},
                "cta_text": {"x": 80, "y": 280, "font_size": 32, "color": "#2F6F6A", "button_color": "#FFFFFF"},
            },
        },
    },
    {
        "id": 4,
        "name": "竖版故事 · 短视频封面",
        "preview_url": "/static/poster/templates/template_4.png",
        "config": {
            "purpose": "短视频/Story封面",
            "canvas": {"width": 1080, "height": 1920},
            "overlays": [
                {"type": "top_band", "ratio": 0.18, "color": [15, 20, 28, 120]},
                {"type": "bottom_band", "ratio": 0.2, "color": [15, 20, 28, 150]},
            ],
            "product_shadow": True,
            "product": {"x": 140, "y": 520, "w": 800, "h": 800},
            "text_defaults": {
                "title": {"x": 70, "y": 120, "font_size": 64, "color": "#FFFFFF", "art_style": "stroke_shadow"},
                "subtitle": {"x": 70, "y": 240, "font_size": 40, "color": "#F6C177", "art_style": "normal"},
                "cta_text": {"x": 70, "y": 1680, "font_size": 42, "color": "#111111", "button_color": "#F6C177"},
            },
        },
    },
    {
        "id": 5,
        "name": "大促爆款 · 折扣突出",
        "preview_url": "/static/poster/templates/template_5.png",
        "config": {
            "purpose": "大促/折扣",
            "canvas": {"width": 1080, "height": 1080},
            "overlays": [
                {"type": "bottom_band", "ratio": 0.3, "color": [180, 40, 40, 180]},
                {"type": "vignette"},
            ],
            "product_shadow": True,
            "product": {"x": 260, "y": 180, "w": 560, "h": 560},
            "text_defaults": {
                "title": {"x": 70, "y": 780, "font_size": 48, "color": "#FFFFFF", "art_style": "shadow"},
                "subtitle": {"x": 70, "y": 860, "font_size": 56, "color": "#FFE566", "art_style": "stroke_shadow"},
                "cta_text": {"x": 70, "y": 960, "font_size": 34, "color": "#B02828", "button_color": "#FFFFFF"},
            },
        },
    },
    {
        "id": 6,
        "name": "极简白底 · Amazon主图风",
        "preview_url": "/static/poster/templates/template_6.png",
        "config": {
            "purpose": "Amazon主图/白底",
            "canvas": {"width": 1080, "height": 1080},
            "overlays": [{"type": "rect", "x": 0, "y": 0, "w": 1080, "h": 1080, "color": [248, 248, 246, 255]}],
            "product_shadow": False,
            "product": {"x": 190, "y": 140, "w": 700, "h": 700},
            "text_defaults": {
                "title": {"x": 70, "y": 880, "font_size": 40, "color": "#222222", "art_style": "normal"},
                "subtitle": {"x": 70, "y": 940, "font_size": 28, "color": "#666666", "art_style": "normal"},
                "cta_text": {"x": 700, "y": 920, "font_size": 28, "color": "#FFFFFF", "button_color": "#111111"},
            },
        },
    },
    {
        "id": 7,
        "name": "社交方形 · 种草分享",
        "preview_url": "/static/poster/templates/template_7.png",
        "config": {
            "purpose": "小红书/Ins方图",
            "canvas": {"width": 1080, "height": 1080},
            "overlays": [
                {"type": "bottom_band", "ratio": 0.34, "color": [255, 255, 255, 210]},
                {"type": "vignette"},
            ],
            "product_shadow": True,
            "product": {"x": 220, "y": 80, "w": 640, "h": 640},
            "text_defaults": {
                "title": {"x": 64, "y": 760, "font_size": 44, "color": "#1C2A32", "art_style": "normal"},
                "subtitle": {"x": 64, "y": 830, "font_size": 30, "color": "#2F6F6A", "art_style": "normal"},
                "selling_point_1": {"x": 64, "y": 900, "font_size": 26, "color": "#4A5A63", "art_style": "normal"},
                "cta_text": {"x": 64, "y": 970, "font_size": 30, "color": "#FFFFFF", "button_color": "#2F6F6A"},
            },
        },
    },
    {
        "id": 8,
        "name": "横幅促销 · 店铺顶栏",
        "preview_url": "/static/poster/templates/template_8.png",
        "config": {
            "purpose": "店铺横幅",
            "canvas": {"width": 1500, "height": 500},
            "overlays": [{"type": "left_panel", "ratio": 0.55, "color": [36, 48, 56, 170]}],
            "product_shadow": True,
            "product": {"x": 900, "y": 40, "w": 520, "h": 420},
            "text_defaults": {
                "title": {"x": 60, "y": 90, "font_size": 56, "color": "#FFFFFF", "art_style": "shadow"},
                "subtitle": {"x": 60, "y": 190, "font_size": 34, "color": "#F2D6A2", "art_style": "normal"},
                "cta_text": {"x": 60, "y": 320, "font_size": 32, "color": "#243038", "button_color": "#F2D6A2"},
            },
        },
    },
]


def _load_poster_engine():
    module_path = Path(__file__).resolve().parents[4] / "poster_module" / "poster_service.py"
    spec = importlib.util.spec_from_file_location("poster_engine", module_path)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    engine.STATIC_DIR = STATIC_DIR
    engine.POSTER_DIR = POSTER_DIR
    POSTER_DIR.mkdir(parents=True, exist_ok=True)
    return engine


def compose_poster(
    matted_url: str,
    bg_url: str,
    template_config: dict,
    title: str = "",
    discount: str = "",
    price: str = "",
    style_options: dict | None = None,
) -> str:
    engine = _load_poster_engine()
    raw_url = engine.compose_poster(
        matted_url=matted_url,
        bg_url=bg_url,
        template_config=template_config,
        title=title,
        discount=discount,
        price=price,
        style_options=style_options or {},
    )
    if raw_url.startswith("/static/posters/"):
        filename = raw_url.rsplit("/", 1)[-1]
        src = Path(__file__).resolve().parents[4] / "poster_module" / "static" / "posters" / filename
        target = POSTER_DIR / filename
        if src.exists():
            target.write_bytes(src.read_bytes())
        elif (STATIC_DIR / "posters" / filename).exists():
            target.write_bytes((STATIC_DIR / "posters" / filename).read_bytes())
        return f"/static/poster/{filename}"
    if raw_url.startswith("/static/poster/"):
        return raw_url
    filename = raw_url.rsplit("/", 1)[-1]
    if (POSTER_DIR / filename).exists():
        return f"/static/poster/{filename}"
    return raw_url


def init_templates(db):
    """创建或更新模板（可重复执行，按 id upsert）。"""
    from app.models.poster import Template

    # 下线「居中主图」
    old = db.query(Template).filter(Template.id == 1).first()
    if old:
        old.is_active = False
        old.name = "（已下线）居中主图"

    for t in TEMPLATE_DATA:
        row = db.query(Template).filter(Template.id == t["id"]).first()
        cfg = json.dumps(t["config"], ensure_ascii=False)
        if row:
            row.name = t["name"]
            row.preview_url = t["preview_url"]
            row.config_json = cfg
            row.is_active = True
        else:
            db.add(
                Template(
                    id=t["id"],
                    name=t["name"],
                    preview_url=t["preview_url"],
                    config_json=cfg,
                )
            )
    db.commit()
