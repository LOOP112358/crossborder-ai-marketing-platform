"""手动导入 ABO 知识库（项目根目录执行）

  python scripts/import_abo_kb.py
  python scripts/import_abo_kb.py --limit 8000
  python scripts/import_abo_kb.py --limit 3000 --skip-images --skip-index
  python scripts/import_abo_kb.py --backfill-images
  python scripts/import_abo_kb.py --import-with-images --limit 0
  python scripts/import_abo_kb.py --rebuild-only

说明：
  --backfill-images     给已有商品补 main_image_id / image_path（要求 jpg 在盘上）
  --import-with-images  只导入磁盘上确有 jpg 的商品；--limit 0 = 不设上限
  --skip-images         导入时不解析图片（省内存，随后再 backfill）
  --skip-index          导入时不重建 FAISS（省内存，随后再 rebuild-only）
"""
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv
    load_dotenv(Path(ROOT) / ".env", override=False)
except ImportError:
    pass

MODULES = [
    "shared",
    "module1-auth-writing",
    "module2-matte",
    "module3-background",
    "module4-poster",
    "module5-chat",
]
for mod in MODULES:
    mod_path = os.path.join(ROOT, mod, "backend")
    if os.path.isdir(mod_path):
        sys.path.insert(0, mod_path)

os.chdir(ROOT)

from app.modules.chat.services.import_abo import main  # noqa: E402

if __name__ == "__main__":
    main()
