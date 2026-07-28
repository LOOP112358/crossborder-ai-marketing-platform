import base64
import os
import uuid
from io import BytesIO
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image


def _scene_hint(category: str, product_name: str = "", brand: str = "", product_type: str = "") -> str:
    blob = f"{category} {product_name} {brand} {product_type}".lower()
    if any(k in blob for k in ("tablet", "kindle", "sleeve", "case", "phone", "protective", "ipad")):
        return (
            "modern desk or lifestyle shelf for electronics accessories, "
            "soft daylight, wood or matte desk surface, shallow depth of field"
        )
    if any(k in blob for k in ("headphone", "earbud", "earphone")):
        return "clean desk with soft audio lifestyle mood, no devices shown"
    if any(k in blob for k in ("shoe", "sneaker")):
        return "minimal footwear pedestal, concrete or soft fabric ground, fashion studio"
    if any(k in blob for k in ("sofa", "chair", "table", "furniture")):
        return "bright Scandinavian home interior corner, empty floor or table surface for placement"
    if any(k in blob for k in ("watch", "jewelry")):
        return "luxury jewelry display surface, soft dark gradient, premium lighting"
    if category:
        return f"e-commerce scene suitable for {category} product placement"
    return "premium empty e-commerce product display environment"


def _style_label(style: str) -> str:
    mapping = {
        "outdoor": "outdoor natural environment",
        "minimalist": "minimalist solid clean studio",
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
            "The background should match this product context, but do not draw the product itself: "
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
        "Create an empty commercial e-commerce background only. "
        f"{product_line}"
        f"Scene direction: {scene}. "
        f"Visual style: {_style_label(style)}. "
        f"Color tone: {color_hint or 'soft neutral'}. "
        f"{extra_block} "
        "Leave a large clean central area for later product placement. "
        "Realistic lighting and soft contact-shadow-friendly ground plane. "
        "Do not generate any product, packaging, person, animal, text, watermark, or logo. "
        "High quality advertising photography background."
    )


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
    # 优先 lite（更快更便宜）；未开通时自动回退 pro
    primary = os.getenv("ARK_MODEL") or "doubao-seedream-5-0-lite-260128"
    fallback = os.getenv("ARK_MODEL_FALLBACK") or "doubao-seedream-5-0-pro-260628"
    models = [primary]
    if fallback and fallback != primary:
        models.append(fallback)
    size = os.getenv("BG_IMAGE_SIZE", "1024x1024")
    timeout = int(os.getenv("BG_API_TIMEOUT", "180"))
    if not (api_key and base_url):
        raise ValueError("ARK_API_KEY and ARK_BASE_URL must be configured")

    url = f"{base_url.rstrip('/')}/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_error = None
    for model in models:
        payload = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "n": 1,
            "response_format": "url",
            "watermark": False,
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        except requests.exceptions.Timeout as exc:
            last_error = TimeoutError(
                f"Seedream 生成超时（>{timeout}s，模型 {model}）。"
                "可开通 doubao-seedream-5-0-lite-260128 加速，或增大 BG_API_TIMEOUT。"
            )
            raise last_error from exc

        if response.status_code >= 400:
            err_text = response.text[:1000]
            print(f"[seedream] model={model} status={response.status_code} {err_text}")
            # 未开通 / 不存在：尝试下一个模型
            if response.status_code == 404 and (
                "ModelNotOpen" in err_text or "NotFound" in err_text
            ):
                last_error = RuntimeError(err_text)
                continue
            # 参数不兼容时去掉 watermark / response_format 再试一次
            soft = {k: v for k, v in payload.items() if k not in ("watermark", "response_format")}
            try:
                response = requests.post(url, headers=headers, json=soft, timeout=timeout)
            except requests.exceptions.Timeout as exc:
                raise TimeoutError(
                    f"Seedream 生成超时（>{timeout}s，模型 {model}）。"
                ) from exc
            if response.status_code >= 400:
                print(response.text[:1000])
                last_error = RuntimeError(response.text[:500])
                continue

        response.raise_for_status()
        result = response.json()
        item = (result.get("data") or [{}])[0]
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{uuid.uuid4().hex}_seedream_background.jpg"

        if item.get("b64_json"):
            output_path.write_bytes(base64.b64decode(item["b64_json"]))
            print(f"[seedream] ok model={model} path={output_path.name}")
            return output_path

        image_url = item.get("url")
        if not image_url:
            last_error = ValueError(f"Seedream returned no image: {result}")
            continue
        image_response = requests.get(image_url, timeout=60)
        image_response.raise_for_status()
        output_path.write_bytes(image_response.content)
        print(f"[seedream] ok model={model} path={output_path.name}")
        return output_path

    raise RuntimeError(
        f"Seedream 生成失败。请在火山方舟开通 {primary}（推荐，更快），"
        f"或确认 {fallback} 可用。详情: {last_error}"
    )


def _encode_image_data_uri(image_path: Path, max_side: int = 1280) -> str:
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    scale = min(1.0, float(max_side) / max(width, height))
    if scale < 1.0:
        img = img.resize(
            (max(1, int(width * scale)), max(1, int(height * scale))),
            Image.Resampling.LANCZOS,
        )

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=88)
    b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def refine_composite_with_seedream(
    image_path: Path,
    output_dir: Path,
    *,
    prompt: str = "",
    size: str = "1024x1024",
) -> Path:
    load_dotenv()
    api_key = os.getenv("ARK_API_KEY")
    base_url = os.getenv("ARK_BASE_URL")
    model = os.getenv("ARK_MODEL") or "doubao-seedream-5-0-lite-260128"
    fallback = os.getenv("ARK_MODEL_FALLBACK") or "doubao-seedream-5-0-pro-260628"
    if not (api_key and base_url):
        raise ValueError("ARK_API_KEY and ARK_BASE_URL must be configured")

    refine_prompt = prompt or (
        "Lightly refine this commercial product composite photo. "
        "Keep the exact product identity, shape, logo and packaging text unchanged. "
        "Only improve edge blend into the background, add soft realistic contact shadow, "
        "and match lighting color temperature. No extra objects, no new text, no watermark, no redesign."
    )
    data_uri = _encode_image_data_uri(Path(image_path))
    url = f"{base_url.rstrip('/')}/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    models = [model] + ([fallback] if fallback and fallback != model else [])
    response = None
    for mid in models:
        payload = {
            "model": mid,
            "prompt": refine_prompt,
            "image": data_uri,
            "size": size,
            "n": 1,
            "response_format": "url",
            "watermark": False,
        }
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        print(f"Seedream refine status model={mid}:", response.status_code)
        if response.status_code >= 400:
            print(response.text[:800])
            if response.status_code == 404 and (
                "ModelNotOpen" in response.text or "NotFound" in response.text
            ):
                continue
            payload["image"] = [data_uri]
            response = requests.post(url, headers=headers, json=payload, timeout=180)
            print("Seedream refine retry(array) status:", response.status_code)
            if response.status_code >= 400:
                print(response.text[:800])
                if response.status_code == 404:
                    continue
        if response.status_code < 400:
            break
    if response is None or response.status_code >= 400:
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
    image_response = requests.get(image_url, timeout=60)
    image_response.raise_for_status()
    output_path.write_bytes(image_response.content)
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
    # 兼容旧前端传 seedance
    return refine_composite_with_seedream(image_path, output_dir, prompt=prompt, size=size)


def super_resolution(image_path: Path, output_dir: Path):
    img = Image.open(image_path)
    result = img.resize((img.width * 2, img.height * 2))
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / image_path.name.replace(".png", "_2x.png")
    result.save(output)
    return output
