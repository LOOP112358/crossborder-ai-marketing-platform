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
    """
    根据商品信息自动构造文生图Prompt
    """

    prompt = (
        f"A high quality commercial background "
        f"for {category}, "
        f"style is {style}, "
        f"color tone is {color_hint}, "
        f"professional e-commerce photography"
    )

    return prompt



def mock_generate_background(
        prompt,
        output_dir: Path
):
    """
    模拟背景生成

    用于开发测试阶段。
    后续替换为真实文生图模型。
    """


    filename = (
        uuid.uuid4().hex
        +
        "_background.png"
    )


    path = output_dir / filename


    # 创建测试图片
    img = Image.new(
        "RGB",
        (1024, 1024),
        (230, 230, 230)
    )


    draw = ImageDraw.Draw(img)


    draw.text(
        (100, 450),
        "Mock Background",
        fill=(0, 0, 0)
    )


    img.save(path)


    return path

def generate_background(
        prompt,
        output_dir: Path
):
    print("========== generate_background 被调用 ==========")

    return generate_by_api(
        prompt,
        output_dir
    )



def generate_by_api(
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