# 跨境 AI 营销平台

一站式 AI 电商营销工具：选品、抠图、Seedream 场景背景、海报合成、营销文案、客服和运营看板。

## 功能概览

| 模块 | 能力 |
| --- | --- |
| 认证 / 文案 | 注册登录、JWT、DeepSeek 多平台文案 |
| 商品抠图 | 库内主图或本地上传抠图，绑定商品避免图文串货 |
| 背景生成 | 全程使用火山方舟豆包 Seedream 生成商业场景背景 |
| 海报合成 | 多模板、自动排版、商品与背景融合、Seedream 精修 |
| 客服 / 看板 | ABO + FAISS RAG 客服和运营统计 |

推荐海报流程：

```text
商品库选品 -> 抠图 -> Seedream 背景生成 -> 海报合成
```

前端入口：`/poster-workflow`。

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 3 + Vite + Element Plus + Pinia + vue-i18n + ECharts |
| 后端 | FastAPI + SQLAlchemy + SQLite + JWT |
| AI | DeepSeek / OpenAI 兼容接口、火山方舟豆包 Seedream、rembg |
| 数据 | ABO 商品列表、缩略图、FAISS 知识库 |

## 快速启动

### 1. 配置环境变量

```bash
cp .env.example .env
```

常用变量：

| 变量 | 说明 |
| --- | --- |
| `BG_MOCK_MODE=0` | `1` 时背景强制占位图 |
| `ARK_API_KEY` / `ARK_BASE_URL` / `ARK_MODEL` | Seedream 背景和海报精修 |
| `LLM_*` 或 `OPENAI_*` | 文案与客服 |
| `ABO_LISTINGS_DIR` / `ABO_IMAGES_DIR` | 本地 ABO 知识库路径 |
| `MATTE_USE_REMBG=1` | 需要 AI 精细抠图时开启 |

### 2. 启动后端

```bash
pip install -r requirements.txt
python run.py
```

Swagger: `http://127.0.0.1:8000/docs`

### 3. 启动前端

```bash
cd shared/frontend
npm install
npm run dev
```

前端：`http://localhost:5173`

## 主要 API

| 模块 | 示例 |
| --- | --- |
| 认证 | `POST /api/auth/register`、`POST /api/auth/login` |
| 文案 | `POST /api/writing/generate` |
| 抠图 | `POST /api/matte/process`、`POST /api/matte/process-url` |
| 背景 | `POST /api/background/generate`、`GET /api/background/options` |
| 海报 | `GET /api/poster/templates`、`POST /api/poster/compose` |
| 客服 | `/api/chat/*`、`/api/dashboard/*` |

## 目录

```text
shared/                     统一前后端入口
module1-auth-writing/       认证 + 文案
module2-matte/              抠图
module3-background/         Seedream 背景生成
module4-poster/             海报合成
module5-chat/               客服 + 运营看板
static/                     静态资源
data/                       SQLite 等本地数据
```

## 说明

- 背景生成不再提供 Stable Diffusion 分支。
- `enhanced_url` 作为旧字段保留，但与 `bg_url` 指向同一张 Seedream 图片。
- 真实密钥只放本地 `.env`，不要提交。
