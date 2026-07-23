import uuid
import os
import requests

from pathlib import Path

from dotenv import load_dotenv
from PIL import Image, ImageDraw

def build_prompt(
        category,
        style,
        color_hint
):

    prompt = (
        f"Create an empty e-commerce background scene. "
        f"Theme related to {category}. "
        f"Style: {style}. "
        f"Color tone: {color_hint}. "

        f"Do not generate any product, bottle, cosmetics, shoes, package, person, text, or logo. "
        f"Only background environment. "

        f"Leave a clean empty central area for later product placement. "
        f"Professional commercial photography background, realistic lighting, high quality."
    )

    return prompt

def build_sd_prompt(
        category,
        style,
        color_hint
):

    prompt = f"""
A professional e-commerce background photography scene.

Create ONLY the environment background.

Scene style:
{style}

Color palette:
{color_hint}


Requirements:

- empty scene
- no main objects
- large clean central area
- suitable for product placement
- commercial studio photography
- realistic lighting
- realistic shadows
- premium advertising background
- minimal composition


The image will be used as a blank product advertisement background.

Do NOT create:
- products
- objects
- devices
- bottles
- shoes
- clothing
- people
- packages
- text
- logos
- brand marks


Only create an empty background environment.
"""

    return prompt

def build_cache_key(
        category,
        style,
        color_hint
):
    """
    根据商品类别、风格、颜色生成唯一缓存标识
    """

    key = (
        category.strip().lower()
        + "_"
        +
        style.strip().lower()
        + "_"
        +
        color_hint.strip().lower()
    )

    return key

def generate_background(
        prompt,
        output_dir: Path
):
    """
    主背景生成：固定调用豆包 Seedream
    输出保存到 generated 目录
    """
    print("========== generate_background 被调用 ==========")
    return generate_seedream(
        prompt,
        output_dir
    )


def generate_seedream(
        prompt,
        output_dir: Path
):
    """
    调用豆包 Seedream 文生图
    """

    from dotenv import load_dotenv
    import requests

    load_dotenv()


    api_key = os.getenv("ARK_API_KEY")
    base_url = os.getenv("ARK_BASE_URL")
    model = os.getenv("ARK_MODEL")


    print("模型:", model)


    url = base_url + "/images/generations"


    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }


    payload = {

        "model": model,

        "prompt": prompt,

        "size": "1024x1024",

        "n": 1

    }


    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=120
    )


    print(response.text)


    response.raise_for_status()


    result = response.json()


    image_url = result["data"][0]["url"]


    image_response = requests.get(
    image_url,
    timeout=120
)

    image_response.raise_for_status()


    image = image_response.content


    filename = (
        uuid.uuid4().hex
        +
        "_background.jpg"
    )


    output_path = output_dir / filename


    with open(
        output_path,
        "wb"
    ) as f:
        f.write(image)


    return output_path

def generate_stable_diffusion(
        prompt,
        output_dir: Path
):
    """
    调用 Stability AI Stable Diffusion API
    """

    load_dotenv()

    api_key = os.getenv("STABILITY_API_KEY")

    model = os.getenv(
        "STABILITY_MODEL",
        "sd3.5-medium"
    )

    print("调用 Stability AI")
    print("模型:", model)

    # 不同模型对应不同接口
    if model in ["sd3.5-flash", "sd3.5-medium", "sd3.5-large"]:

        url = (
            "https://api.stability.ai/"
            "v2beta/stable-image/generate/sd3"
        )

    elif model == "core":

        url = (
            "https://api.stability.ai/"
            "v2beta/stable-image/generate/core"
        )

    else:
        raise ValueError(f"不支持的 Stability 模型: {model}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "image/*"
    }

    files = {
        "prompt": (None, prompt),
        "output_format": (None, "png"),
        "model": (None, model)
    }

    response = requests.post(
        url,
        headers=headers,
        files=files,
        timeout=120
    )

    print("Stability状态:", response.status_code)

    if response.status_code != 200:
        print(response.text)

    response.raise_for_status()

    image_data = response.content

    filename = (
        uuid.uuid4().hex
        +
        "_sd_background.png"
    )

    output_path = output_dir / filename

    with open(output_path, "wb") as f:
        f.write(image_data)

    return output_path
    

def super_resolution(
        image_path: Path,
        output_dir: Path
):
    """
    模拟超分增强

    后续替换：
    Real-ESRGAN
    """


    img = Image.open(image_path)


    result = img.resize(
        (
            img.width * 2,
            img.height * 2
        )
    )


    output = (
        output_dir /
        image_path.name.replace(
            ".png",
            "_2x.png"
        )
    )


    result.save(output)


    return output

