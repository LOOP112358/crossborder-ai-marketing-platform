from pathlib import Path

from fastapi import FastAPI, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


from .services import (
    build_prompt,
    build_sd_prompt,
    build_cache_key,
    generate_background,
    generate_stable_diffusion
)

from .database import BackgroundRepository


print("加载的是最新的main.py")



ROOT = Path(__file__).resolve().parents[1]


STATIC = ROOT / "static"



GENERATED_DIR = (
    STATIC /
    "background" /
    "generated"
)



ENHANCED_DIR = (
    STATIC /
    "background" /
    "enhanced"
)



GENERATED_DIR.mkdir(
    parents=True,
    exist_ok=True
)


ENHANCED_DIR.mkdir(
    parents=True,
    exist_ok=True
)




repo = BackgroundRepository(
    ROOT / "data" / "background.db"
)




app = FastAPI(
    title="背景双模型生成 API",
    version="1.0.0"
)




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)




app.mount(
    "/static",
    StaticFiles(directory=STATIC),
    name="static"
)




def ok(
        data=None,
        message="success"
):

    return {

        "code":0,

        "message":message,

        "data":data

    }





@app.get("/")
def home():

    return {

        "message":
        "background module running"

    }

#==============================
#=========成员4接口==========
@app.get("/api/background/history")
def history():

    data = repo.list()

    return ok(
        data,
        "获取背景历史"
    )
#=============================


# ==================================================
# 成员2调用接口
# 商品识别结果 -> 背景生成
# ==================================================

@app.post("/api/background/generate_from_product")
async def generate_from_product(
        data: dict = Body(...)
):


    # 成员2返回的商品类别

    category = data.get(
        "category",
        "unknown"
    )



    attributes = data.get(
        "attributes",
        {}
    )



    # 兼容中英文属性字段

    style = (

        attributes.get("style")

        or

        attributes.get("风格")

        or

        "modern commercial"

    )



    color_hint = (

        attributes.get("color")

        or

        attributes.get("颜色")

        or

        ""

    )



    print("===== 成员2传入 =====")
    print(data)

    print("category:",category)
    print("style:",style)
    print("color:",color_hint)
    print("========== 成员2调用背景生成 ==========")



    return await generate(
        category,
        style,
        color_hint
    )









# ==================================================
# 普通背景生成接口
# 前端调用
# ==================================================

@app.post("/api/background/generate")
async def generate(

    category: str = Form(...),

    style: str = Form("default"),

    color_hint: str = Form("")

):


    # =========================
    # 1. 创建缓存key
    # =========================


    cache_key = build_cache_key(
        category,
        style,
        color_hint
    )



    print(
        "当前缓存key:",
        cache_key
    )





    # =========================
    # 2. 查询缓存
    # =========================


    cache = repo.get_cache(
        cache_key
    )



    if cache:


        print(
            "========== 命中缓存 =========="
        )


        return ok(
            cache,
            "返回缓存背景"
        )



    print(
        "========== 未命中缓存，开始生成 =========="
    )





    # =========================
    # 3. 豆包 Prompt
    # =========================


    prompt = build_prompt(

        category,

        style,

        color_hint

    )





    # =========================
    # 4. SD Prompt
    # =========================


    sd_prompt = build_sd_prompt(

        category,

        style,

        color_hint

    )



    print(
        "========== 豆包Prompt =========="
    )

    print(prompt)



    print(
        "========== SD Prompt =========="
    )

    print(sd_prompt)






    # =========================
    # 5. 豆包生成
    # =========================


    bg_path = generate_background(

        prompt,

        GENERATED_DIR

    )







    # =========================
    # 6. SD生成
    # =========================


    enhanced_path = generate_stable_diffusion(

        sd_prompt,

        ENHANCED_DIR

    )







    bg_url = (

        "/static/background/generated/"

        +

        bg_path.name

    )



    enhanced_url = (

        "/static/background/enhanced/"

        +

        enhanced_path.name

    )







    # =========================
    # 7. 保存历史
    # =========================


    record = repo.create({

        "product_category":

            category,


        "style":

            style,


        "color_hint":

            color_hint,


        "prompt_used":

            (
                "Seedream Prompt:\n"

                +

                prompt

                +

                "\n\nSD Prompt:\n"

                +

                sd_prompt
            ),


        "bg_url":

            bg_url,


        "enhanced_url":

            enhanced_url

    })







    # =========================
    # 8. 保存缓存
    # =========================


    repo.save_cache({

        "cache_key":

            cache_key,


        "category":

            category,


        "style":

            style,


        "color_hint":

            color_hint,


        "bg_url":

            bg_url,


        "sd_url":

            enhanced_url

    })






    return ok(

        record,

        "背景生成完成"

    )









# ==================================================
# 成员4调用接口
# 根据历史id获取背景
# ==================================================

@app.get("/api/background/history/{id}")
def get_history(id:int):


    result = repo.get_by_id(
        id
    )


    if result is None:


        return ok(

            None,

            "not found"

        )



    return ok(

        result,

        "success"

    )