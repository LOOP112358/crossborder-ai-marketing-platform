"""AI电商营销工具平台 — 开发服务器启动入口

用法:
  python run.py              # 默认不热重载（Windows 下 Ctrl+C 更干净）
  python run.py --reload     # 需要热重载时再开
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.abspath(__file__))
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

# 加载项目根目录 .env
try:
    from dotenv import load_dotenv

    load_dotenv(Path(ROOT) / ".env", override=False)
except ImportError:
    env_path = Path(ROOT) / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key, val = key.strip(), val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)

import uvicorn


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reload",
        action="store_true",
        help="开启热重载（Windows 上 Ctrl+C 可能关不干净，默认关闭）",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        timeout_graceful_shutdown=3,
    )


if __name__ == "__main__":
    main()
