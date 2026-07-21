# AI 电商营销工具平台

一站式 AI 驱动的电商营销工具平台，助力产品推广全流程。

## 项目简介

本平台涵盖电商营销的5大核心场景：
1. **文案生成**（成员1）— AI 大模型生成多平台、多语言营销文案
2. **商品抠图**（成员2）— AI 自动去背景 + 商品类别识别
3. **背景生成**（成员3）— Stable Diffusion 生成场景背景 + 超分增强
4. **海报合成**（成员4）— 模板化海报合成，一键生成营销素材
5. **智能客服**（成员5）— RAG 文档问答 + 运营数据看板

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 (Composition API) + Element Plus + Vite |
| 后端 | FastAPI (Python) |
| 数据库 | SQLite |
| 认证 | JWT |
| 图像处理 | Rembg, Real-ESRGAN, Stable Diffusion API |

## 项目结构

```
├── frontend/          # Vue 3 前端项目
├── backend/           # FastAPI 后端项目
│   └── app/
│       ├── core/      # 核心配置、安全、数据库
│       ├── models/    # SQLAlchemy 数据模型
│       └── modules/   # 各功能模块
├── static/            # 静态资源（图片存储）
└── docs/              # 项目文档
```

## 快速启动

### 环境要求
- Python 3.10+
- Node.js 18+
- npm 9+

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python run.py
```

启动后访问 http://127.0.0.1:8000/docs 查看 Swagger API 文档。

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

启动后访问 http://localhost:5173。

### 默认账号

首次使用需自行注册账号。

## API 接口概览

### 认证模块（成员1）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/register | 用户注册 |
| POST | /api/auth/login | 用户登录 |
| GET | /api/auth/me | 获取当前用户信息 |

### 文案生成（成员1）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/writing/generate | 生成文案（支持多平台/多语言/多风格） |
| GET | /api/writing/history | 获取历史记录（分页） |

### 商品抠图（成员2）— 待开发
### 背景生成（成员3）— 待开发
### 海报合成（成员4）— 待开发
### 智能客服（成员5）— 待开发

## Git 分支管理

| 分支 | 负责人 | 模块 |
|------|--------|------|
| main | 组长 | 主分支 |
| feature/module1 | 成员1 | 文案生成 + 认证 + 整合 |
| feature/module2 | 成员2 | 商品抠图 |
| feature/module3 | 成员3 | 背景生成 |
| feature/module4 | 成员4 | 海报合成 |
| feature/module5 | 成员5 | 智能客服 |

## 协作规范

- 统一 API 返回格式：`{code: 200, message: "ok", data: {...}}`
- 图片存储路径：`./static/{模块名}/`，前端通过 `/static/` 路径访问
- 数据库：每人一个 SQLite 文件（`backend/data/module{1-5}.db`），最终合并
- 前端组件放在 `src/views/{模块名}/` 目录
- 后端模块放在 `app/modules/{模块名}/` 目录，通过 `router.py` 导出路由
