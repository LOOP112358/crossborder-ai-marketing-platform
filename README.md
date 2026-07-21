# AI 跨境电商营销工具平台

一站式 AI 驱动的电商营销工具平台，5人小组协作项目。

## 项目结构

```
├── shared/                    # 共享基础设施（框架层）
│   ├── backend/               # FastAPI核心、配置、数据库、公共模型
│   └── frontend/              # Vue3 外壳、路由、布局、国际化、API客户端
│
├── module1-auth-writing/      # 成员1：用户认证 + 文案生成 + 项目整合
│   ├── backend/app/modules/   # auth/ + writing/
│   └── frontend/views/        # Login, Register, Home, WritingPage
│
├── module2-matte/             # 成员2：商品抠图 + 智能识别
│   ├── backend/app/modules/   # matte/
│   └── frontend/views/        # MattePage
│
├── module3-background/        # 成员3：背景生成 + 超分增强（待开发）
│   ├── backend/app/modules/   # background/
│   └── frontend/views/        # Placeholder
│
├── module4-poster/            # 成员4：海报合成 + 模板管理
│   ├── backend/app/modules/   # poster/
│   └── frontend/views/        # PosterPage
│
├── module5-chat/              # 成员5：智能客服 + 运营看板（待开发）
│   ├── backend/app/modules/   # chat/
│   └── frontend/views/        # Placeholder
│
├── static/                    # 图片共享存储
├── docs/                      # 项目文档
├── data/                      # SQLite 数据库文件
├── requirements.txt           # Python 依赖
├── run.py                     # 后端启动入口
└── README.md
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Element Plus + Vite + Pinia + vue-i18n |
| 后端 | FastAPI + SQLAlchemy + SQLite + JWT |
| AI能力 | LLM文案生成 / Rembg抠图 / Ollama商品识别 / Pillow海报合成 |

## 快速启动

```bash
# 1. 安装 Python 依赖
pip install -r requirements.txt

# 2. 启动后端 (http://127.0.0.1:8000)
python run.py

# 3. 安装前端依赖 & 启动 (http://localhost:5173)
cd shared/frontend
npm install
npm run dev
```

## 模块协作数据流

```
成员1(文案) → 生成标题/折扣文案
                     ↓
成员2(抠图) → matted_url + category → Pinia useAppStore
                     ↓
成员3(背景) → enhanced_bg_url → Pinia (待实现)
                     ↓
成员4(海报) ← 读取 matted_url + bg_url → 合成海报
```

## API 文档

后端启动后访问 http://127.0.0.1:8000/docs 查看 Swagger 文档。

## Git 分支规范

| 分支 | 负责 | 模块 |
|------|------|------|
| feature/module1 | 成员1 | 认证 + 文案 + 整合 |
| feature/module2 | 成员2 | 商品抠图 |
| feature/module3 | 成员3 | 背景生成 |
| feature/module4 | 成员4 | 海报合成 |
| feature/module5 | 成员5 | 智能客服 |
