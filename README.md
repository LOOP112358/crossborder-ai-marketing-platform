# 越境智绘 · 跨境 AI 营销平台

一站式 AI 电商营销工具：**选品 → 抠图 → 场景背景 → 海报合成**，并配套多平台文案生成、智能客服与运营看板。  
5 人小组协作；统一入口在 `shared/`，各成员功能在 `module1`–`module5`。

---

## 功能一览

| 模块 | 能力 |
|------|------|
| **认证 / 文案** | 注册登录（JWT）；DeepSeek 多平台多语言营销文案；ABO 商品库检索与海报短文案 |
| **商品抠图** | 库内主图 / 本地上传抠图；品类识别；与海报文案绑定同一商品，避免图文串货 |
| **背景生成** | 豆包 **Seedream** 文生图（默认）；可选 Stability SD；场景 / 光照 / 氛围等可调 |
| **海报合成** | 多模板（含图文融合模板）；自动排版换行；Seedream / SD 融合精修；艺术字与 CTA |
| **客服 / 看板** | ABO + FAISS RAG 双语客服；运营统计与 ECharts 看板 |

**推荐工作流（海报）**

```
商品库选品 → 抠图（图文绑定）→ 背景生成（Seedream）→ 海报合成（融合模板 + 短文案）
```

前端入口：`/poster-workflow`（分步向导）或侧栏各功能页。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Element Plus + Pinia + vue-i18n + ECharts |
| 后端 | FastAPI + SQLAlchemy + SQLite + JWT |
| AI | DeepSeek（文案/客服）；火山方舟 Seedream（背景/海报精修）；可选 Stability SD；Rembg（可选精细抠图） |
| 数据 | ABO 商品列表 + 缩略图；FAISS 全局知识库 |

---

## 仓库结构

```
├── shared/                      # 统一外壳
│   ├── backend/app/             # FastAPI 入口、配置、公共模型、挂载各模块路由
│   └── frontend/                # Vue 布局、路由、i18n、API、Pinia
├── module1-auth-writing/        # 认证 + 文案 + ABO 海报文案工具
├── module2-matte/               # 抠图
├── module3-background/          # 背景（Seedream / SD）
├── module4-poster/              # 海报（poster_module 引擎 + 模板）
├── module5-chat/                # 客服 + 运营看板
├── static/                      # matte / background / poster 等静态资源
├── scripts/                     # 如 import_abo_kb.py
├── data/                        # SQLite 等本地数据
├── docs/                        # 合并说明等文档
├── .env.example                 # 环境变量模板（勿提交真实 Key）
├── requirements.txt
└── run.py                       # 后端启动入口
```

各模块内可能仍保留成员原始 `app/` 或 `poster_module/`，供独立调试；**日常开发请走 `python run.py` + `shared/frontend`。**

---

## 环境要求

- Python **3.10+**
- Node.js **18+** / npm **9+**
- Windows / macOS / Linux（当前团队以 Windows 开发为主）

可选本地数据：

- ABO listings / images 目录（见 `.env.example` 中 `ABO_*`）
- 火山方舟 ARK Key（Seedream）
- DeepSeek / OpenAI 兼容 Key（文案、客服）
- Stability Key（可选；额度不足时设 `BG_USE_SD=0`）

---

## 快速启动

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env：至少配置 SECRET_KEY；需要真图/真文案时再填 ARK_*、LLM_* / OPENAI_*
```

常用开关：

| 变量 | 说明 |
|------|------|
| `BG_MOCK_MODE=0` | `1` 时背景强制占位图 |
| `BG_USE_SD=0` | 默认**不**调 Stability；`1` 时背景双模型并行 |
| `ARK_*` | Seedream 背景 / 海报精修 |
| `LLM_*` 或 `OPENAI_*` | DeepSeek 文案与客服 |
| `ABO_LISTINGS_DIR` / `ABO_IMAGES_DIR` | 本地 ABO 知识库路径 |
| `MATTE_USE_REMBG=1` | 需要 AI 精细抠图时再开（默认快速白底抠图） |

### 2. 后端

```bash
pip install -r requirements.txt
python run.py                 # http://127.0.0.1:8000
python run.py --reload        # 热重载（Windows 上 Ctrl+C 可能关不干净）
```

Swagger：http://127.0.0.1:8000/docs

### 3. 前端

```bash
cd shared/frontend
npm install
npm run dev                   # http://localhost:5173
```

首次使用请先**注册账号**再登录。

### 4. （可选）导入 ABO 知识库

```bash
python scripts/import_abo_kb.py
# 按需：--backfill-images 等，见脚本帮助
```

---

## 模块协作与状态（Pinia）

全局 store：`shared/frontend/src/store/useAppStore.js`

| 字段 | 含义 |
|------|------|
| `mattedUrl` / `mattedProductId` | 抠图结果及**绑定商品 ID**（防图文串货） |
| `selectedProduct` / `posterConfig` | 库内商品与海报短文案 |
| `seedreamBgUrl` / `preferredBgUrl` | 背景图（默认优先 Seedream） |

海报页会校验抠图商品与文案商品是否一致；不一致时提示并阻止合成。

---

## 海报使用建议

1. 第 1 步从商品库选品并完成抠图（图文绑定）。
2. 第 2 步生成背景：默认只开 Seedream；SD 额度不足时勿勾选「同时调用 SD」。
3. 第 3 步选 **「图文融合」** 类模板；点「使用库内商品文案」或「AI 精炼短文案」；开启 **Seedream 融合精修**（可选）。
4. 保持「自动排版」，避免固定坐标把长文裁成 `…`。

---

## 主要 API（摘要）

| 模块 | 示例 |
|------|------|
| 认证 | `POST /api/auth/register` `POST /api/auth/login` |
| 文案 | `POST /api/writing/generate`；`GET /api/writing/products/{id}/poster-copy?llm=0\|1` |
| 抠图 | `POST /api/matte/process` / `process-url` |
| 背景 | `POST /api/background/generate`（`use_sd=0\|1`）；`GET /api/background/options` |
| 海报 | `GET /api/poster/templates`；`POST /api/poster/compose` |
| 客服 | `/api/chat/*`；看板 `/api/dashboard/*` |

完整列表见 Swagger。

---

## 开发约定

- **统一后端**：新路由挂到 `shared/backend/app/main.py`；业务代码放对应 `module*/backend/...`。
- **统一前端**：页面放 `module*/frontend/views/`，在 `shared/frontend/src/router` 注册。
- **密钥**：只放本机 `.env`，不要提交；`.env.example` 仅保留空占位与注释。
- **合并说明**：见 [docs/MERGE.md](docs/MERGE.md)。

### Git 分支（参考）

| 分支 | 模块 |
|------|------|
| `feature/module1` | 认证 + 文案 + 整合 |
| `feature/module2` | 抠图 |
| `feature/module3` | 背景 |
| `feature/module4` | 海报 |
| `feature/module5` | 客服 / 看板 |

---

## 常见问题

**背景很慢 / 报 SD 额度不足**  
保持 `BG_USE_SD=0`，背景页不要勾选 SD；海报精修选 Seedream。

**海报图文对不上（图是 A、文案是 B）**  
回第 1 步重新选品并抠图，再到海报点「使用库内商品文案」。

**文案带 `…` 显示不全**  
重新点「使用库内商品文案」刷新；模板开自动排版。

**改代码后接口没变**  
`run.py` 默认无热重载，需重启后端；前端 Vite 一般会自动刷新。

**端口被占用**  
结束占用 8000 / 5173 的旧进程后再启动。

---

## 文档

- [docs/MERGE.md](docs/MERGE.md) — 合并与目录约定  
- 各模块目录下 `README.md` — 成员原始说明（可能偏旧，以本文为准）

---

## License

课程 / 小组项目用途；第三方 API（DeepSeek、火山方舟、Stability）请遵守各自服务条款与配额限制。
