"""手动填充运营看板演示调用历史。

用法（在项目根目录）:
  python scripts/seed_dashboard.py
  python scripts/seed_dashboard.py --force   # 已有数据时再追加一批
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)

MODULES = [
    "shared",
    "module1-auth-writing",
    "module2-matte",
    "module3-background",
    "module4-poster",
    "module5-chat",
]
for mod in MODULES:
    mod_path = ROOT / mod / "backend"
    if mod_path.is_dir():
        sys.path.insert(0, str(mod_path))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env", override=False)
except ImportError:
    pass


def main() -> None:
    parser = argparse.ArgumentParser(description="填充看板演示调用历史")
    parser.add_argument("--force", action="store_true", help="已有历史时仍追加写入")
    args = parser.parse_args()

    from app.core.database import SessionLocal, init_db
    from app.modules.poster.services import init_templates
    from app.modules.chat.services.seed_data import seed_demo_history

    init_db()
    db = SessionLocal()
    try:
        init_templates(db)
        ok = seed_demo_history(db, force=args.force)
        if ok:
            print("完成：运营看板演示数据已写入。演示账号 demo / demo123")
        else:
            print("未写入（已有历史）。如需追加请加 --force")
    finally:
        db.close()


if __name__ == "__main__":
    main()
