import base64
import io
import json
import os
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageFilter, ImageStat


def dominant_color(image: Image.Image) -> tuple[str, str, str]:
    rgb = image.convert("RGB").resize((64, 64))
    colors = rgb.quantize(colors=5).convert("RGB").getcolors(4096) or []
    colors.sort(reverse=True)
    candidates = [c for _, c in colors if not (min(c) > 235 or max(c) < 20)]
    r, g, b = candidates[0] if candidates else ImageStat.Stat(rgb).mean[:3]
    names = [
        ((255, 255, 255), "白色", "white"), ((20, 20, 20), "黑色", "black"),
        ((220, 45, 45), "红色", "red"), ((45, 90, 210), "蓝色", "blue"),
        ((50, 160, 80), "绿色", "green"), ((240, 190, 35), "黄色", "yellow"),
        ((245, 135, 35), "橙色", "orange"), ((150, 75, 180), "紫色", "purple"),
        ((150, 100, 65), "棕色", "brown"), ((140, 140, 140), "灰色", "gray"),
    ]
    _, zh, en = min(names, key=lambda item: sum((a - b) ** 2 for a, b in zip((r, g, b), item[0])))
    return zh, en, f"#{int(r):02X}{int(g):02X}{int(b):02X}"


def lightweight_attributes(image: Image.Image) -> dict[str, Any]:
    color_zh, color_en, color_hex = dominant_color(image)
    brightness = sum(ImageStat.Stat(image.convert("RGB")).mean) / 3
    style = "明亮简约" if brightness >= 165 else "沉稳深色"
    return {
        "color": color_zh,
        "color_en": color_en,
        "color_hex": color_hex,
        "style": style,
        "material": "待视觉模型识别",
        "recognition_source": "lightweight",
    }


async def ollama_recognize(image_bytes: bytes) -> dict[str, Any] | None:
    model = os.getenv("OLLAMA_VISION_MODEL", "").strip()
    if not model:
        return None
    import httpx
    url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/") + "/api/chat"
    prompt = (
        "识别图片中的主要商品。只输出JSON，字段为category中文类别、category_en英文类别、"
        "confidence(0到1)、color、style、material。不要输出Markdown。"
    )
    payload = {
        "model": model,
        "stream": False,
        "messages": [{"role": "user", "content": prompt,
                      "images": [base64.b64encode(image_bytes).decode("ascii")]}],
        "options": {"temperature": 0},
    }
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
        content = response.json()["message"]["content"].strip().strip("`")
        if content.startswith("json"):
            content = content[4:].strip()
        return json.loads(content)
    except (httpx.HTTPError, KeyError, json.JSONDecodeError):
        return None


def _mock_remove(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = []
    for r, g, b, a in rgba.getdata():
        whiteness = min(r, g, b)
        spread = max(r, g, b) - whiteness
        alpha = 0 if whiteness > 245 and spread < 12 else a
        pixels.append((r, g, b, alpha))
    rgba.putdata(pixels)
    return rgba


def remove_background(image_bytes: bytes, edge_smoothing: int = 1) -> Image.Image:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    if os.getenv("MATTE_MOCK_MODE") == "1":
        result = _mock_remove(image)
    else:
        from rembg import remove
        output = remove(image_bytes)
        result = Image.open(io.BytesIO(output)).convert("RGBA")
    if edge_smoothing:
        alpha = result.getchannel("A")
        alpha = alpha.filter(ImageFilter.MedianFilter(3))
        if edge_smoothing >= 2:
            alpha = alpha.filter(ImageFilter.GaussianBlur(0.7))
        result.putalpha(alpha)
    return result


async def recognize(image_bytes: bytes) -> dict[str, Any]:
    image = Image.open(io.BytesIO(image_bytes))
    attrs = lightweight_attributes(image)
    vision = await ollama_recognize(image_bytes)
    if not vision:
        return {"category": "商品", "category_en": "product", "confidence": 0.55,
                "attributes": attrs}
    attrs.update({k: v for k, v in vision.items() if k in {"color", "style", "material"}})
    attrs["recognition_source"] = "ollama"
    return {
        "category": str(vision.get("category", "商品")),
        "category_en": str(vision.get("category_en", "product")),
        "confidence": max(0.0, min(1.0, float(vision.get("confidence", 0.8)))),
        "attributes": attrs,
    }
