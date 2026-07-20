from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import uuid

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
POSTER_DIR = STATIC_DIR / "posters"
POSTER_DIR.mkdir(parents=True, exist_ok=True)


def load_font(size: int):
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]

    for path in font_paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


def url_to_path(url: str) -> Path:
    if url.startswith("/static/"):
        relative = url.replace("/static/", "")
        return STATIC_DIR / relative

    return Path(url)


def compose_poster(
    matted_url: str,
    bg_url: str,
    template_config: dict,
    title: str,
    discount: str,
    price: str,
):
    config = template_config

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

    draw = ImageDraw.Draw(bg)

    title_cfg = config["title"]
    discount_cfg = config["discount"]
    price_cfg = config["price"]

    draw.text(
        (title_cfg["x"], title_cfg["y"]),
        title,
        fill=title_cfg["color"],
        font=load_font(title_cfg["font_size"])
    )

    draw.text(
        (discount_cfg["x"], discount_cfg["y"]),
        discount,
        fill=discount_cfg["color"],
        font=load_font(discount_cfg["font_size"])
    )

    draw.text(
        (price_cfg["x"], price_cfg["y"]),
        price,
        fill=price_cfg["color"],
        font=load_font(price_cfg["font_size"])
    )

    filename = f"poster_{uuid.uuid4().hex}.png"
    save_path = POSTER_DIR / filename

    bg.convert("RGB").save(save_path, quality=95)

    return f"/static/posters/{filename}"