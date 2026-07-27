import base64
import os
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image


def _scene_hint(category: str, product_name: str = "", brand: str = "", product_type: str = "") -> str:
    blob = f"{category} {product_name} {brand} {product_type}".lower()
    if any(k in blob for k in ("tablet", "kindle", "sleeve", "case", "phone", "保护套", "手机壳", "平板")):
        return (
            "modern desk / lifestyle shelf for electronics accessories, "
            "soft daylight, wood or matte desk surface, shallow depth of field"
        )
    if any(k in blob for k in ("headphone", "earbud", "耳机")):
        return "clean desk with soft speakers vibe, lifestyle audio scene, no devices shown"
    if any(k in blob for k in ("shoe", "sneaker", "鞋")):
        return "minimal footwear pedestal, concrete or soft fabric ground, fashion studio"
    if any(k in blob for k in ("sofa", "chair", "table", "家具", "沙发", "椅子", "桌子")):
        return "bright Scandinavian home interior corner, empty floor/table surface for placement"
    if any(k in blob for k in ("watch", "手表")):
        return "luxury jewelry display surface, soft dark gradient, premium lighting"
    if category:
        return f"e-commerce scene suitable for {category} product placement"
    return "premium empty e-commerce product display environment"


def _style_label(style: str) -> str:
    mapping = {
        "outdoor": "outdoor natural environment",
        "minimalist": "minimalist solid / clean studio",
        "luxury": "luxury premium interior",
        "tech": "tech futuristic showroom",
        "warm": "warm cozy home atmosphere",
        "scandi": "Scandinavian bright home",
        "industrial": "industrial loft concrete texture",
        "default": "modern commercial",
    }
    return mapping.get((style or "").strip().lower(), style or "modern commercial")


def build_prompt(
    category,
    style,
    color_hint,
    product_name: str = "",
    brand: str = "",
    product_type: str = "",
    scene_preset: str = "",
    lighting: str = "",
    mood: str = "",
    camera: str = "",
    extra_note: str = "",
):
    scene = scene_preset.strip() or _scene_hint(category, product_name, brand, product_type)
    product_line = ""
    if product_name or brand or product_type:
        product_line = (
            f"The background should match this product context "
            f"(do NOT draw the product itself): "
            f"name={product_name or 'n/a'}, brand={brand or 'n/a'}, "
            f"type={product_type or category or 'n/a'}. "
        )
    extras = []
    if lighting:
        extras.append(f"Lighting: {lighting}.")
    if mood:
        extras.append(f"Mood: {mood}.")
    if camera:
        extras.append(f"Camera/composition: {camera}.")
    if extra_note:
        extras.append(f"Additional direction: {extra_note}.")
    extra_block = (" " + " ".join(extras)) if extras else ""
    return (
        "Create an EMPTY commercial e-commerce background only. "
        f"{product_line}"
        f"Scene direction: {scene}. "
        f"Visual style: {_style_label(style)}. "
        f"Color tone: {color_hint or 'soft neutral'}. "
        f"{extra_block} "
        "Leave a large clean central area for later product placement. "
        "Realistic lighting and soft contact-shadow-friendly ground plane. "
        "Do NOT generate any product, packaging, person, animal, text, watermark, or logo. "
        "High quality advertising photography background."
    )


def build_sd_prompt(
    category,
    style,
    color_hint,
    product_name: str = "",
    brand: str = "",
    product_type: str = "",
    scene_preset: str = "",
    lighting: str = "",
    mood: str = "",
    camera: str = "",
    extra_note: str = "",
):
    scene = scene_preset.strip() or _scene_hint(category, product_name, brand, product_type)
    return f"""
Professional empty e-commerce background photography.

Product context (do NOT render the product):
- name: {product_name or 'unknown'}
- brand: {brand or 'unknown'}
- type/category: {product_type or category or 'general'}

Scene:
{scene}

Style: {_style_label(style)}
Color palette: {color_hint or 'soft complementary tones'}
Lighting: {lighting or 'soft realistic commercial light'}
Mood: {mood or 'premium clean'}
Camera: {camera or 'eye-level, product-placement friendly'}
Extra: {extra_note or 'none'}

Hard requirements:
- empty scene, no main subject object
- large clean central placement area
- realistic lighting and soft floor/table shadows
- premium advertising look
- no people, text, logos, packaging, or brand marks

Only output an empty background environment.
"""


def build_cache_key(
    category,
    style,
    color_hint,
    product_name: str = "",
    brand: str = "",
    scene_preset: str = "",
    lighting: str = "",
    mood: str = "",
    camera: str = "",
    extra_note: str = "",
):
    return "_".join(
        [
            str(category).strip().lower(),
            str(style).strip().lower(),
            str(color_hint).strip().lower(),
            str(product_name).strip().lower()[:40],
            str(brand).strip().lower()[:20],
            str(scene_preset).strip().lower()[:40],
            str(lighting).strip().lower()[:24],
            str(mood).strip().lower()[:24],
            str(camera).strip().lower()[:24],
            str(extra_note).strip().lower()[:40],
        ]
    )


def generate_background(prompt, output_dir: Path):
    return generate_seedream(prompt, output_dir)


def generate_seedream(prompt, output_dir: Path):
    load_dotenv()

    api_key = os.getenv("ARK_API_KEY")
    base_url = os.getenv("ARK_BASE_URL")
    model = os.getenv("ARK_MODEL")
    if not (api_key and base_url and model):
        raise ValueError("ARK_API_KEY, ARK_BASE_URL, and ARK_MODEL must be configured")

    url = f"{base_url.rstrip('/')}/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "size": "1024x1024",
        "n": 1,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=120)
    if response.status_code >= 400:
        print(response.text)
    response.raise_for_status()

    result = response.json()
    image_url = result["data"][0]["url"]
    image_response = requests.get(image_url, timeout=120)
    image_response.raise_for_status()

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{uuid.uuid4().hex}_background.jpg"
    with open(output_path, "wb") as file:
        file.write(image_response.content)

    return output_path


def generate_stable_diffusion(prompt, output_dir: Path):
    load_dotenv()

    api_key = os.getenv("STABILITY_API_KEY")
    if not api_key:
        raise ValueError("STABILITY_API_KEY is not configured")

    model = os.getenv("STABILITY_MODEL", "sd3.5-medium")
    output_format = os.getenv("STABILITY_OUTPUT_FORMAT", "png")

    if model in ["sd3.5-flash", "sd3.5-medium", "sd3.5-large"]:
        url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"
        files = {
            "prompt": (None, prompt),
            "output_format": (None, output_format),
            "model": (None, model),
        }
    elif model == "core":
        url = "https://api.stability.ai/v2beta/stable-image/generate/core"
        files = {
            "prompt": (None, prompt),
            "output_format": (None, output_format),
        }
    else:
        raise ValueError(f"Unsupported Stability model: {model}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "image/*",
    }

    response = requests.post(url, headers=headers, files=files, timeout=120)
    print("Stability status:", response.status_code)
    if response.status_code >= 400:
        print(response.text)
    response.raise_for_status()

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{uuid.uuid4().hex}_sd_background.{output_format}"
    with open(output_path, "wb") as file:
        file.write(response.content)

    return output_path


def refine_composite_with_sd(
    image_path: Path,
    output_dir: Path,
    *,
    prompt: str = "",
    strength: float = 0.28,
) -> Path:
    """
    用 Stability image-to-image 轻量精修合成图：柔化抠图白边、增强接触阴影。
    strength 宜小（0.2~0.35），过大易改坏商品外形。
    """
    load_dotenv()
    api_key = os.getenv("STABILITY_API_KEY")
    if not api_key:
        raise ValueError("STABILITY_API_KEY is not configured")

    model = os.getenv("STABILITY_MODEL", "sd3.5-medium")
    output_format = "png"
    url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"
    refine_prompt = prompt or (
        "Seamless commercial product poster photo, natural contact shadow under the product, "
        "soft edge blending with background, realistic lighting, keep the exact product shape "
        "and branding readable, no extra objects, no text, no watermark"
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "image/*",
    }
    with open(image_path, "rb") as f:
        files = {
            "prompt": (None, refine_prompt),
            "mode": (None, "image-to-image"),
            "strength": (None, str(max(0.05, min(0.6, float(strength))))),
            "output_format": (None, output_format),
            "model": (None, model),
            "image": ("compose.png", f, "image/png"),
        }
        response = requests.post(url, headers=headers, files=files, timeout=120)

    print("Stability refine status:", response.status_code)
    if response.status_code >= 400:
        print(response.text)
    response.raise_for_status()

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{uuid.uuid4().hex}_refined.png"
    output_path.write_bytes(response.content)
    return output_path


def _encode_image_data_uri(image_path: Path, max_side: int = 1280) -> str:
    """本地图压成 jpeg data-uri，便于 Seedream 图生图上传。"""
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    scale = min(1.0, float(max_side) / max(w, h))
    if scale < 1.0:
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
    from io import BytesIO

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def refine_composite_with_seedream(
    image_path: Path,
    output_dir: Path,
    *,
    prompt: str = "",
    size: str = "1024x1024",
) -> Path:
    """
    用豆包 Seedream 图生图轻量精修合成图（不依赖 Stability 额度）。
    提示词强调：保持商品外形/品牌，仅柔化边缘与接触阴影。
    """
    load_dotenv()
    api_key = os.getenv("ARK_API_KEY")
    base_url = os.getenv("ARK_BASE_URL")
    model = os.getenv("ARK_MODEL")
    if not (api_key and base_url and model):
        raise ValueError("ARK_API_KEY, ARK_BASE_URL, and ARK_MODEL must be configured")

    refine_prompt = prompt or (
        "Lightly refine this commercial product composite photo. "
        "Keep the exact product identity, shape, logo and packaging text unchanged. "
        "Only improve edge blend into the background, add soft realistic contact shadow, "
        "match lighting color temperature. No extra objects, no new text, no watermark, no redesign."
    )
    data_uri = _encode_image_data_uri(Path(image_path))
    url = f"{base_url.rstrip('/')}/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    # 兼容 image 字符串 / 数组两种网关形态
    payload = {
        "model": model,
        "prompt": refine_prompt,
        "image": data_uri,
        "size": size,
        "n": 1,
        "response_format": "url",
        "watermark": False,
    }
    response = requests.post(url, headers=headers, json=payload, timeout=180)
    print("Seedream refine status:", response.status_code)
    if response.status_code >= 400:
        # 部分网关要求 image 为数组
        print(response.text[:800])
        payload["image"] = [data_uri]
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        print("Seedream refine retry(array) status:", response.status_code)
        if response.status_code >= 400:
            print(response.text[:800])
    response.raise_for_status()

    result = response.json()
    item = (result.get("data") or [{}])[0]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{uuid.uuid4().hex}_seedream_refined.jpg"

    if item.get("b64_json"):
        output_path.write_bytes(base64.b64decode(item["b64_json"]))
        return output_path
    image_url = item.get("url")
    if not image_url:
        raise ValueError(f"Seedream refine returned no image: {result}")
    img_resp = requests.get(image_url, timeout=120)
    img_resp.raise_for_status()
    output_path.write_bytes(img_resp.content)
    return output_path


def refine_composite(
    image_path: Path,
    output_dir: Path,
    *,
    engine: str = "seedream",
    prompt: str = "",
    strength: float = 0.28,
    size: str = "1024x1024",
) -> Path:
    """统一精修入口：seedream（默认）或 sd。"""
    eng = (engine or "seedream").strip().lower()
    if eng in ("sd", "stability", "stable"):
        return refine_composite_with_sd(image_path, output_dir, prompt=prompt, strength=strength)
    return refine_composite_with_seedream(image_path, output_dir, prompt=prompt, size=size)


def super_resolution(image_path: Path, output_dir: Path):
    img = Image.open(image_path)
    result = img.resize((img.width * 2, img.height * 2))
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / image_path.name.replace(".png", "_2x.png")
    result.save(output)
    return output
