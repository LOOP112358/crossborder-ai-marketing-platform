# 系统架构设计文档

## 1. 架构概述

本项目采用前后端分离架构，前端使用 Vue 3 + Element Plus，后端使用 FastAPI，数据存储在 SQLite 中。

```
┌─────────────────────────────────────────────────────────┐
│                     浏览器 (Vue 3)                       │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐         │
│  │ 文案 │ │ 抠图 │ │ 背景 │ │ 海报 │ │ 客服 │         │
│  │ 生成 │ │ 识别 │ │ 生成 │ │ 合成 │ │ 看板 │         │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘         │
│     └────────┴────────┴────────┴────────┘              │
│                       │ Axios + JWT                      │
└───────────────────────┼─────────────────────────────────┘
                        │ HTTP /api/*
┌───────────────────────┼─────────────────────────────────┐
│              FastAPI Server (8000)                       │
│  ┌────────────────────┼──────────────────────┐          │
│  │         CORS Middleware                    │          │
│  │  ┌──────────┐ ┌──────────────────┐        │          │
│  │  │  Auth    │ │  Static Files    │        │          │
│  │  │  JWT     │ │  /static/        │        │          │
│  │  └──────────┘ └──────────────────┘        │          │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐   │          │
│  │  │ Writing  │ │  Matte   │ │   BG     │   │          │
│  │  │ Module   │ │  Module  │ │  Module  │   │          │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘   │          │
│  │  ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐   │          │
│  │  │  Poster  │ │   Chat   │ │Dashboard │   │          │
│  │  │  Module  │ │  Module  │ │  Module  │   │          │
│  │  └──────────┘ └──────────┘ └──────────┘   │          │
│  │               SQLAlchemy ORM               │          │
│  └───────────────────┬────────────────────────┘          │
│              ┌───────┴───────┐                          │
│              │    SQLite     │                          │
│              │ module{1-5}.db│                          │
│              └───────────────┘                          │
└─────────────────────────────────────────────────────────┘
```

## 2. 技术选型理由

| 技术 | 理由 |
|------|------|
| Vue 3 | 渐进式框架，Composition API 逻辑复用友好，社区活跃 |
| Element Plus | 企业级 UI 组件库，大屏/表单/表格组件丰富 |
| FastAPI | 自动生成 API 文档（Swagger），异步支持，类型安全 |
| SQLite | 零配置，每成员独立 db 文件方便并行开发，最终可合并 |
| JWT | 无状态认证，前端存储 token，后端无需 session |
| Pinia | Vue 3 官方状态管理，模块化设计，支持 DevTools |

## 3. 数据流

### 文案生成流程
```
用户输入商品名+卖点 → 选择平台/语言/风格
  → POST /api/writing/generate
  → LLM Client (Mock/真实API)
  → 返回 title + body + tags
  → 保存到 history_writing 表
  → 前端展示结果 + 一键复制
```

### 跨模块协作流程（成员2-4）
```
成员2: 上传图片 → 抠图 → 识别category → 存入 useAppStore
                                            ↓
成员3: 读取 category → 选择风格 → 生成背景 → 超分 → 存入 useAppStore
                                            ↓
成员4: 读取 matted_url + enhanced_bg_url → 选模板 → 合成海报
```

共享状态通过 Pinia `useAppStore` 实现，图片通过 `/static/` 目录共享。

## 4. 数据库设计

### 核心表关系
```
users (1) ────┬── (N) history_writing
               ├── (N) history_matte
               ├── (N) history_background
               ├── (N) history_poster
               └── (N) chat_sessions

templates (1) ──── (N) history_poster
history_poster (1) ──── (N) favorites
chat_sessions (1) ──── (N) chat_messages
chat_messages (1) ──── (N) chat_feedback
```

详细 SQL 建表语句见各成员模块文档。

## 5. 安全设计

- **密码加密**：bcrypt 哈希，不存储明文
- **JWT 认证**：HS256 算法，24小时过期
- **路由守卫**：前端 router.beforeEach 检查 token，后端 Depends(get_current_user) 保护接口
- **CORS 配置**：开发环境允许 localhost:5173，生产环境应限制域名
- **SQL 注入防护**：使用 SQLAlchemy ORM，参数化查询

## 6. 部署建议

开发阶段：前后端分别启动，通过 Vite proxy 转发 API 请求。
生产部署：前端 `npm run build` 生成静态文件，后端用 uvicorn + nginx 反向代理。
