from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEMO_DIR = BASE_DIR / "static" / "demo"
DEMO_DIR.mkdir(parents=True, exist_ok=True)


def load_font(size: int):
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for p in font_paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


# 1. 生成背景图
bg = Image.new("RGB", (1080, 1080), "#2E6BFF")
draw = ImageDraw.Draw(bg)

# 简单做一个渐变/装饰效果
for y in range(1080):
    color = (
        int(46 + y * 0.04),
        int(107 + y * 0.02),
        int(255 - y * 0.08),
    )
    draw.line([(0, y), (1080, y)], fill=color)

draw.ellipse((760, 80, 1180, 500), fill=(255, 255, 255, 40))
bg.save(DEMO_DIR / "background.png")


# 2. 生成一个模拟商品透明图
product = Image.new("RGBA", (600, 600), (0, 0, 0, 0))
draw = ImageDraw.Draw(product)

# 画一个“商品”
draw.rounded_rectangle((160, 120, 440, 500), radius=60, fill="#FFFFFF", outline="#333333", width=6)
draw.rounded_rectangle((210, 80, 390, 170), radius=50, fill="#EEEEEE", outline="#333333", width=4)
draw.ellipse((235, 230, 365, 360), fill="#FFCC00", outline="#333333", width=4)

font = load_font(42)
draw.text((220, 390), "ITEM", fill="#222222", font=font)

product.save(DEMO_DIR / "product.png")

print("测试素材生成完成：")
print(DEMO_DIR / "background.png")
print(DEMO_DIR / "product.png")