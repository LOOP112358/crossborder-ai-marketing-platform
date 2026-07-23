from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import uuid

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DEMO_DIR = STATIC_DIR / "demo"
POSTER_DIR = STATIC_DIR / "posters"
POSTER_DIR.mkdir(parents=True, exist_ok=True)


def load_font(size: int):
    """
    优先加载 Windows 中文字体，保证中文和英文都能显示。
    """
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]

    for path in font_paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


def compose_demo_poster():
    bg_path = DEMO_DIR / "background.png"
    product_path = DEMO_DIR / "product.png"

    # 1. 打开背景图
    bg = Image.open(bg_path).convert("RGBA")
    bg = bg.resize((1080, 1080))

    # 2. 打开商品图
    product = Image.open(product_path).convert("RGBA")
    product = product.resize((560, 560))

    # 3. 把商品图贴到背景图上
    product_x = 260
    product_y = 360
    bg.alpha_composite(product, (product_x, product_y))

    # 4. 写文字
    draw = ImageDraw.Draw(bg)

    title_font = load_font(64)
    discount_font = load_font(84)
    price_font = load_font(56)

    draw.text((80, 90), "Portable Blender", fill="#FFFFFF", font=title_font)
    draw.text((80, 180), "30% OFF", fill="#FFD700", font=discount_font)
    draw.text((80, 290), "$19.99", fill="#FFFFFF", font=price_font)

    # 5. 保存结果
    filename = f"poster_test_{uuid.uuid4().hex[:8]}.png"
    output_path = POSTER_DIR / filename
    bg.convert("RGB").save(output_path, quality=95)

    print("海报生成成功：")
    print(output_path)


if __name__ == "__main__":
    compose_demo_poster()