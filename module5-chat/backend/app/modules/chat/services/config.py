"""模块5 配置 — 适配项目共享结构"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[5]  # module5-chat/backend/
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
FAISS_DIR = BASE_DIR / "data" / "faiss"
DB_PATH = BASE_DIR / "data" / "app.db"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
FAISS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# LLM 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "deepseek-chat")

# RAG 配置
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 5
