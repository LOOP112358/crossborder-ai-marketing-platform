"""FastAPI 应用入口 — 自动发现并注册所有模块路由"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.database import init_db

# ─── 模块路由注册 ─────────────────────────────────────
# 每个模块独立放在 module{1-5}-*/backend/app/modules/ 下
# run.py 启动时会自动将所有模块目录加入 sys.path

# 模块1：认证 + 文案生成
from app.modules.auth.router import router as auth_router
from app.modules.writing.router import router as writing_router

# 模块2：商品抠图 + 智能识别
from app.modules.matte.router import router as matte_router

# 模块3：背景生成 + 超分（待开发）
# from app.modules.background.router import router as background_router

# 模块4：海报合成 + 模板管理
from app.modules.poster.router import router as poster_router

# 模块5：智能客服 + 运营看板
from app.modules.chat.router import router as chat_router
from app.modules.dashboard.router import router as dashboard_router


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件 (shared/backend/app/main.py → 向上4级到项目根)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
static_dir = os.path.join(ROOT, "static")
os.makedirs(os.path.join(static_dir, "matte"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "background"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "poster"), exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 路由注册
app.include_router(auth_router)
app.include_router(writing_router)
app.include_router(matte_router)
app.include_router(poster_router)
app.include_router(chat_router)
app.include_router(dashboard_router)


@app.on_event("startup")
def on_startup():
    init_db()
    from app.core.database import SessionLocal
    from app.modules.poster.services import init_templates
    db = SessionLocal()
    try:
        init_templates(db)
    finally:
        db.close()


@app.get("/api/health")
def health_check():
    return {"code": 200, "message": "ok", "data": {"version": settings.APP_VERSION}}
