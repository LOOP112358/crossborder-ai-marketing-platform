import os
from pathlib import Path

# module5-chat/backend/app/modules/chat/services/config.py
# parents: services → chat → modules → app → backend → module5-chat → repo
MODULE5_ROOT = Path(__file__).resolve().parents[5]
REPO_ROOT = MODULE5_ROOT.parent

DATA_DIR = MODULE5_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
FAISS_DIR = DATA_DIR / "faiss"
DB_PATH = DATA_DIR / "chat_kb.db"

# 本地 ABO 知识库（默认指向你 Downloads 中的解压目录，可用环境变量覆盖）
ABO_LISTINGS_DIR = Path(
    os.getenv("ABO_LISTINGS_DIR", r"C:\Users\lishu\Downloads\abo-listings")
)
ABO_IMAGES_DIR = Path(
    os.getenv("ABO_IMAGES_DIR", r"C:\Users\lishu\Downloads\abo-images-small")
)
ABO_METADATA_DIR = ABO_LISTINGS_DIR / "listings" / "metadata"
ABO_IMAGES_SMALL_DIR = ABO_IMAGES_DIR / "images" / "small"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
FAISS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

# LLM 配置（支持 OpenAI 兼容接口）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "") or os.getenv("LLM_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "deepseek-chat")

# RAG 配置
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 5
# 首次导入默认 3000 条，避免启动过久；全量可设 ABO_IMPORT_LIMIT=200000
ABO_IMPORT_LIMIT = int(os.getenv("ABO_IMPORT_LIMIT", "3000"))

DEFAULT_USER_ID = 1

# 兼容旧变量名
ABO_DIR = ABO_LISTINGS_DIR
BASE_DIR = MODULE5_ROOT
