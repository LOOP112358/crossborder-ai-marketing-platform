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
    if any(k in blob for k in ("tablet", "kindle", "sleeve", "case", "phone", "protective", "ipad", "数码", "保护套")):
        return (
            "empty modern desk surface and soft lifestyle shelf, soft daylight, "
            "wood or matte desk plane only, shallow depth of field, nothing resting on the desk"
        )
    if any(k in blob for k in ("headphone", "earbud", "earphone", "耳机")):
        return "empty clean desk with soft audio lifestyle mood, blank surface, no devices"
    if any(k in blob for k in ("shoe", "sneaker", "boot", "sandal", "footwear", "鞋", "靴")):
        return (
            "empty fashion photography studio with soft seamless backdrop and clean floor plane, "
            "optional empty low pedestal with nothing on it, space reserved for a product overlay later"
        )
    if any(k in blob for k in ("sofa", "chair", "table", "furniture", "沙发", "桌", "椅")):
        return "bright Scandinavian home interior corner with empty floor or empty table surface for placement"
    if any(k in blob for k in ("watch", "jewelry", "手表", "珠宝")):
        return "empty luxury display surface with soft dark gradient and premium lighting, nothing on the surface"
    if category:
        return f"empty e-commerce photography environment suitable for {category} ads, clear center stage, no merchandise"
    return "premium empty e-commerce product display environment, blank central stage"


def _style_label(style: str) -> str:
    mapping = {
        "outdoor": "outdoor natural environment",
        "minimalist": "minimalist solid clean studio",
        "luxury": "luxury premium interior",
        "tech": "tech futuristic showroom",
        "warm": "warm cozy home atmosphere",
        "scandi": "Scandinavian bright home",
        "industrial": "industrial loft concrete texture",
        "default": "clean modern commercial photography",
    }
    return mapping.get((style or "").strip().lower(), style or "clean modern commercial photography")


_NEGATIVE_SUBJECTS = (
    "no product, no merchandise, no shoes, no sneakers, no boots, no sandals, no footwear, "
    "no clothing, no bags, no electronics, no phone, no tablet, no headphones, no watch, "
    "no jewelry, no packaging, no box, no bottle, no mannequin, no person, no hands, "
    "no animal, no logo, no watermark, no text, no brand mark, no floating object on the pedestal"
)


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
    # 只用品类/类型做氛围，不写具体商品名——写全名容易让模型画出主体
    vibe = (product_type or category or "").strip() or "general merchandise"
    product_line = (
        f"This is a BACKGROUND-ONLY plate for a later {vibe} composite. "
        "The scene must stay empty: do not invent or draw any sellable item. "
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
        "Generate an EMPTY commercial e-commerce background photograph only. "
        f"{product_line}"
        f"Scene direction: {scene}. "
        f"Visual style: {_style_label(style)}. "
        f"Color tone: {color_hint or 'soft neutral'}. "
        f"{extra_block} "
        "Composition: large clean central negative space for later product placement; "
        "soft contact-shadow-friendly ground or table plane; realistic advertising lighting. "
        f"Strict exclusions: {_NEGATIVE_SUBJECTS}. "
        "Background plate only — environment and surfaces, nothing to sell."
    )


def build_negative_prompt() -> str:
    return (
        "product, merchandise, shoes, sneakers, boots, sandals, footwear, clothing, bag, "
        "electronics, phone, tablet, headphones, watch, jewelry, packaging, box, bottle, "
        "mannequin, person, hands, animal, logo, watermark, text, brand, object on pedestal, "
        "hero product, still life product shot"
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
    negative = build_negative_prompt()
    for model in models:
        payload = {
            "model": model,
            "prompt": prompt,
            "negative_prompt": negative,
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
            # 参数不兼容时逐步去掉可选字段再试
            for drop in (
                ("negative_prompt", "watermark", "response_format"),
                ("watermark", "response_format"),
                ("negative_prompt",),
            ):
                soft = {k: v for k, v in payload.items() if k not in drop}
                try:
                    response = requests.post(url, headers=headers, json=soft, timeout=timeout)
                except requests.exceptions.Timeout as exc:
                    raise TimeoutError(
                        f"Seedream 生成超时（>{timeout}s，模型 {model}）。"
                    ) from exc
                if response.status_code < 400:
                    break
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
