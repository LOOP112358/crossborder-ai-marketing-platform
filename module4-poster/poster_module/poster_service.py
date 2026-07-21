from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import Optional
import uuid

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
POSTER_DIR = STATIC_DIR / "posters"
POSTER_DIR.mkdir(parents=True, exist_ok=True)


FONT_MAP = {
    "msyh": "C:/Windows/Fonts/msyh.ttc",
    "simhei": "C:/Windows/Fonts/simhei.ttf",
    "simsun": "C:/Windows/Fonts/simsun.ttc",
    "kaiti": "C:/Windows/Fonts/simkai.ttf",
    "arial": "C:/Windows/Fonts/arial.ttf",
    "impact": "C:/Windows/Fonts/impact.ttf",
}


def load_font(size: int, font_name: str = "msyh"):
    font_path = FONT_MAP.get(font_name)

    if font_path and Path(font_path).exists():
        return ImageFont.truetype(font_path, size)

    fallback_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]

    for path in fallback_paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


def url_to_path(url: str) -> Path:
    if url.startswith("/static/"):
        relative = url.replace("/static/", "")
        return STATIC_DIR / relative

    return Path(url)


def draw_text_with_art_style(
    draw,
    text: str,
    x: int,
    y: int,
    font,
    fill: str,
    art_style: str = "stroke_shadow",
    stroke_enabled: bool = True,
    stroke_color: str = "#FFFFFF",
    stroke_width: int = 2,
    shadow_enabled: bool = True
):
    if not text:
        return

    art_style = art_style or "normal"

    use_stroke = False
    use_shadow = False

    if art_style == "normal":
        use_stroke = False
        use_shadow = False

    elif art_style == "stroke":
        use_stroke = True
        use_shadow = False

    elif art_style == "shadow":
        use_stroke = False
        use_shadow = True

    elif art_style == "stroke_shadow":
        use_stroke = True
        use_shadow = True

    elif art_style == "glow":
        use_stroke = True
        use_shadow = True

    elif art_style == "strong":
        use_stroke = True
        use_shadow = False

    if not stroke_enabled:
        use_stroke = False

    if not shadow_enabled:
        use_shadow = False

    if use_shadow:
        draw.text(
            (x + 4, y + 4),
            text,
            fill=(0, 0, 0, 120),
            font=font
        )

    if art_style == "glow":
        for offset in [8, 5, 3]:
            draw.text(
                (x, y),
                text,
                fill=fill,
                font=font,
                stroke_width=offset,
                stroke_fill=stroke_color
            )

    if art_style == "strong":
        offsets = [
            (0, 0), (1, 0), (0, 1), (1, 1),
            (-1, 0), (0, -1)
        ]

        for dx, dy in offsets:
            draw.text(
                (x + dx, y + dy),
                text,
                fill=fill,
                font=font,
                stroke_width=stroke_width if use_stroke else 0,
                stroke_fill=stroke_color
            )

        return

    draw.text(
        (x, y),
        text,
        fill=fill,
        font=font,
        stroke_width=stroke_width if use_stroke else 0,
        stroke_fill=stroke_color
    )


def draw_cta_button(
    draw,
    text: str,
    x: int,
    y: int,
    font,
    text_color: str,
    button_color: str,
    art_style: str = "normal"
):
    if not text:
        return

    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    padding_x = 34
    padding_y = 18

    button_w = text_w + padding_x * 2
    button_h = text_h + padding_y * 2

    if art_style in ["shadow", "stroke_shadow", "glow"]:
        draw.rounded_rectangle(
            (x + 5, y + 5, x + button_w + 5, y + button_h + 5),
            radius=26,
            fill=(0, 0, 0, 90)
        )

    draw.rounded_rectangle(
        (x, y, x + button_w, y + button_h),
        radius=26,
        fill=button_color
    )

    draw.text(
        (x + padding_x, y + padding_y - 4),
        text,
        fill=text_color,
        font=font
    )


def get_default_layer_config(canvas_w: int, canvas_h: int):
    return {
        "title": {
            "x": 80,
            "y": 80,
            "font_size": 64,
            "color": "#111111",
            "font_name": "msyh",
            "art_style": "stroke_shadow"
        },
        "subtitle": {
            "x": 80,
            "y": 165,
            "font_size": 42,
            "color": "#D81B60",
            "font_name": "msyh",
            "art_style": "stroke_shadow"
        },
        "selling_point_1": {
            "x": 80,
            "y": 240,
            "font_size": 34,
            "color": "#111111",
            "font_name": "msyh",
            "art_style": "shadow"
        },
        "selling_point_2": {
            "x": 80,
            "y": 295,
            "font_size": 34,
            "color": "#111111",
            "font_name": "msyh",
            "art_style": "shadow"
        },
        "cta_text": {
            "x": 80,
            "y": canvas_h - 170,
            "font_size": 42,
            "color": "#FFFFFF",
            "font_name": "msyh",
            "art_style": "normal",
            "button_color": "#111111"
        }
    }


def compose_poster(
    matted_url: str,
    bg_url: str,
    template_config: dict,
    title: str = "",
    discount: str = "",
    price: str = "",
    style_options: Optional[dict] = None
):
    config = template_config
    style_options = style_options or {}

    canvas_w = config["canvas"]["width"]
    canvas_h = config["canvas"]["height"]

    bg_path = url_to_path(bg_url)
    product_path = url_to_path(matted_url)

    if not bg_path.exists():
        raise FileNotFoundError(f"背景图不存在：{bg_path}")

    if not product_path.exists():
        raise FileNotFoundError(f"商品图不存在：{product_path}")

    bg = Image.open(bg_path).convert("RGBA")
    bg = bg.resize((canvas_w, canvas_h))

    product = Image.open(product_path).convert("RGBA")
    product_cfg = config["product"]
    product = product.resize((product_cfg["w"], product_cfg["h"]))

    bg.alpha_composite(product, (product_cfg["x"], product_cfg["y"]))

    draw = ImageDraw.Draw(bg, "RGBA")

    stroke_enabled = style_options.get("text_stroke_enabled", True)
    stroke_color = style_options.get("text_stroke_color", "#FFFFFF")
    stroke_width = style_options.get("text_stroke_width", 2)
    shadow_enabled = style_options.get("text_shadow_enabled", True)

    default_layer_config = get_default_layer_config(canvas_w, canvas_h)

    text_layers = style_options.get("text_layers")

    if not text_layers:
        text_layers = [
            {"key": "title", "text": title},
            {"key": "subtitle", "text": discount},
            {"key": "cta_text", "text": price}
        ]

    for layer in text_layers:
        text = layer.get("text", "")
        if not text:
            continue

        key = layer.get("key")
        default_cfg = default_layer_config.get(key, default_layer_config["title"])

        x = layer.get("x") if layer.get("x") is not None else default_cfg["x"]
        y = layer.get("y") if layer.get("y") is not None else default_cfg["y"]
        font_size = layer.get("font_size") if layer.get("font_size") is not None else default_cfg["font_size"]
        color = layer.get("color") or default_cfg["color"]
        font_name = layer.get("font_name") or default_cfg.get("font_name", "msyh")
        art_style = layer.get("art_style") or default_cfg.get("art_style", "normal")

        font = load_font(font_size, font_name)

        if key == "cta_text":
            button_color = layer.get("button_color") or default_cfg.get("button_color", "#111111")

            draw_cta_button(
                draw=draw,
                text=text,
                x=x,
                y=y,
                font=font,
                text_color=color,
                button_color=button_color,
                art_style=art_style
            )
        else:
            draw_text_with_art_style(
                draw=draw,
                text=text,
                x=x,
                y=y,
                font=font,
                fill=color,
                art_style=art_style,
                stroke_enabled=stroke_enabled,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                shadow_enabled=shadow_enabled
            )

    filename = f"poster_{uuid.uuid4().hex}.png"
    save_path = POSTER_DIR / filename

    bg.convert("RGB").save(save_path, quality=95)

    return f"/static/posters/{filename}"