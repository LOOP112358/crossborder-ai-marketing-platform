from pathlib import Path

from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


from .services import (
    build_prompt,
    generate_background,
    super_resolution
    
)
print("加载的是我的services.py")

from .database import BackgroundRepository



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
    title="背景生成与超分增强 API",
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



def ok(data=None,message="success"):

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



@app.post("/api/background/generate")
async def generate(

    category:str=Form(...),

    style:str=Form("default"),

    color_hint:str=Form("")

):


    # 1. 自动生成prompt

    prompt = build_prompt(
        category,
        style,
        color_hint
    )


    # 2. 生成背景

    bg_path = generate_background(
        prompt,
        GENERATED_DIR
    )


    # 3. 超分

    enhanced_path = super_resolution(
        bg_path,
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


    record = repo.create({

        "product_category":category,

        "style":style,

        "color_hint":color_hint,

        "prompt_used":prompt,

        "bg_url":bg_url,

        "enhanced_url":enhanced_url

    })


    return ok(
        record,
        "背景生成完成"
    )