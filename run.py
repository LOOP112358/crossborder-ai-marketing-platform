"""AI电商营销工具平台 — 开发服务器启动入口"""
import sys
import os

# 将 shared 和各模块加入 Python 路径，使跨目录 import 正常工作
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

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
