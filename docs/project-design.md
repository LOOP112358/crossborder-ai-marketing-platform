# 跨境 AI 营销平台项目设计文档

## 1. 项目概述

本项目是一个面向跨境电商场景的 AI 营销素材生产平台，核心目标是把“智能选品、营销文案、商品抠图、Seedream 背景生成、海报合成、作品管理、作品广场、智能客服、运营看板”串成一条可演示、可联调、可扩展的工作流。

系统采用前后端分离架构：

- 前端：Vue 3 + Vite + Element Plus + Pinia
- 后端：FastAPI + SQLAlchemy + SQLite
- AI 能力：DeepSeek / OpenAI 兼容文案接口、火山方舟豆包 Seedream 图像生成、rembg 抠图、FAISS/RAG 客服检索
- 静态资源：统一挂载 `/static`，用于访问抠图、背景图、海报图和 ABO 商品图片

项目入口以 `shared/` 为统一外壳，各成员模块保留在 `module1` 到 `module5` 中，便于小组分工开发和最终集成。

## 2. 设计目标

1. 提供完整电商营销素材生产链路。
2. 支持 ABO 商品库智能选品，并保持商品、图片、文案、海报上下文一致。
3. 支持作品沉淀、收藏、发布和广场浏览，形成闭环。
4. 统一后端 API 返回格式，降低前端接入成本。
5. 统一登录认证，业务接口通过 JWT 保护。
6. 保留模块独立性，方便小组成员并行开发。
7. 使用本地 SQLite 和静态文件目录，降低部署和演示门槛。

## 3. 总体架构

```text
Browser
  |
  | Vue 3 / Element Plus / Pinia
  v
Vite Frontend
  |
  | Axios /api + JWT
  v
FastAPI Backend
  |
  | include_router
  v
Auth / Catalog / Writing / Matte / Background / Poster / Works / Gallery / Chat / Dashboard
  |
  | SQLAlchemy ORM
  v
SQLite + static files
  |
  | external APIs / local data
  v
DeepSeek/OpenAI compatible API, Volcengine Ark Seedream, ABO local dataset
```

统一后端入口为 [shared/backend/app/main.py](C:/Users/lishu/crossborder-ai-marketing-platform/shared/backend/app/main.py)，启动脚本 [run.py](C:/Users/lishu/crossborder-ai-marketing-platform/run.py) 会把各模块的 `backend` 目录加入 `sys.path`，再注册模块路由。

## 4. 前端设计

前端统一项目位于 [shared/frontend](C:/Users/lishu/crossborder-ai-marketing-platform/shared/frontend)，主要职责包括：

- 登录注册和路由守卫。
- 智能选品、文案生成、海报工作流、作品管理、作品广场、客服看板等页面。
- 通过 Pinia 保存跨步骤状态。
- 通过 Axios 统一处理 API 响应和错误。

主要页面：

| 页面 | 路由 | 说明 |
| --- | --- | --- |
| 首页 | `/home` | 平台入口 |
| 智能选品中心 | `/catalog` | 检索 ABO 商品库，选择商品进入文案或海报流程 |
| 文案生成 | `/writing` | 多平台营销文案 |
| 文案到海报工作流 | `/writing-poster` | 先文案后海报的工作流 |
| AI 海报工作流 | `/poster-workflow` | 抠图、背景、底图、文案叠加 |
| 我的作品 | `/my-works` | 管理海报、文案和收藏 |
| 作品广场 | `/gallery` | 浏览公开作品并收藏 |
| 智能客服 | `/chat` | RAG 问答 |
| 运营看板 | `/dashboard` | 统计、趋势、建议、导出 |

跨模块状态集中在 [shared/frontend/src/store/useAppStore.js](C:/Users/lishu/crossborder-ai-marketing-platform/shared/frontend/src/store/useAppStore.js)，保存：

- `selectedProduct`：当前选中的 ABO 商品。
- `selectedProductId`：当前商品 ID。
- `mattedUrl` / `mattedProductId`：抠图结果及绑定商品 ID。
- `seedreamBgUrl` / `preferredBgUrl`：Seedream 背景图。
- `posterConfig`：海报标题、卖点、CTA、价格等文案配置。

## 5. 后端设计与接口规范

后端采用 FastAPI 分模块路由。业务接口统一使用 **JSON 信封**（与前端 `request.js` 拦截器一致）：

### 5.1 统一响应体

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 业务状态码。**成功固定为 `200`**；非 200 表示业务失败 |
| `message` | string | 人类可读说明（成功提示 / 失败原因） |
| `data` | object / array / null | 业务数据；无数据时可为 `null` |

成功示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 12,
    "title": "夏季种草文案"
  }
}
```

业务失败示例（HTTP 仍可为 200，由 `code` 区分；或配合 4xx）：

```json
{
  "code": 4001,
  "message": "用户名已存在",
  "data": null
}
```

> 说明：早期方案曾写 `code: 0` 表示成功；**本仓库最终约定与实现均为 `code: 200`**，前端以 `res.code !== 200` 判失败并 `return res.data`。

### 5.2 HTTP 状态与鉴权

| 场景 | 约定 |
|------|------|
| 正常业务成功 | HTTP 200 + `code: 200` |
| 未登录 / Token 无效 | HTTP 401，body 常为 FastAPI `{ "detail": "..." }`；前端清 Token 并跳转登录 |
| 参数校验失败 | HTTP 422，`detail` 为校验数组 |
| 资源不存在 / 无权限 | HTTP 404 / 403 + `detail` 或统一信封 |
| 鉴权头 | `Authorization: Bearer <access_token>` |
| 字段命名 | JSON 使用 `snake_case`（如 `page_size`、`poster_url`） |
| 分页 | 请求 `page` / `page_size`；响应 `data: { items, total, page, page_size }` |

### 5.3 路径与静态资源

- API 前缀：`/api/<模块>/...`（如 `/api/writing/generate`、`/api/poster/compose`、`/api/video/generate`）
- 静态资源：写入 `./static/<模块名>/`，对外 URL `/static/<模块名>/...`，由 FastAPI `StaticFiles` 挂载
- 文件下载等特殊接口可直接返回二进制流，不强制套信封

### 5.4 公共能力位置

- [shared/backend/app/core/config.py](C:/Users/lishu/crossborder-ai-marketing-platform/shared/backend/app/core/config.py)：环境变量配置
- [shared/backend/app/core/database.py](C:/Users/lishu/crossborder-ai-marketing-platform/shared/backend/app/core/database.py)：SQLAlchemy 初始化
- [shared/backend/app/core/security.py](C:/Users/lishu/crossborder-ai-marketing-platform/shared/backend/app/core/security.py)：密码哈希和 JWT
- [shared/backend/app/models](C:/Users/lishu/crossborder-ai-marketing-platform/shared/backend/app/models)：统一数据模型

## 6. 功能模块设计

### 6.1 认证模块

位置：

- 后端：[module1-auth-writing/backend/app/modules/auth](C:/Users/lishu/crossborder-ai-marketing-platform/module1-auth-writing/backend/app/modules/auth)
- 前端：[module1-auth-writing/frontend/views](C:/Users/lishu/crossborder-ai-marketing-platform/module1-auth-writing/frontend/views)

核心能力：

- 用户注册。
- 用户登录。
- 获取当前用户信息。
- 通过 JWT 保护后续业务接口。

主要接口：

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

### 6.2 智能选品模块

位置：

- 后端接口复用文案模块中的 ABO 商品接口：[module1-auth-writing/backend/app/modules/writing/router.py](C:/Users/lishu/crossborder-ai-marketing-platform/module1-auth-writing/backend/app/modules/writing/router.py)
- 前端页面：[module1-auth-writing/frontend/views/catalog/CatalogPage.vue](C:/Users/lishu/crossborder-ai-marketing-platform/module1-auth-writing/frontend/views/catalog/CatalogPage.vue)
- 商品数据模型：[shared/backend/app/models/chat.py](C:/Users/lishu/crossborder-ai-marketing-platform/shared/backend/app/models/chat.py) 中的 `AboProduct`

核心能力：

- 检索本地 ABO 商品知识库。
- 按商品名、品牌、品类等维度搜索。
- 获取商品分类和商品总量。
- 查看商品详情、相似商品和商品图片。
- 选中商品后写入 `useAppStore.selectedProduct`，作为文案生成、抠图、背景生成、海报合成的统一上下文。

主要接口：

- `GET /api/writing/products/categories`
- `GET /api/writing/products/search`
- `GET /api/writing/products/{product_id}`
- `GET /api/writing/products/{product_id}/similar`
- `GET /api/writing/products/{product_id}/poster-copy`

设计说明：

- 智能选品是平台的上游入口，不直接生成素材，而是为后续模块提供稳定的商品上下文。
- 商品图片通过 `/static/abo-images/` 挂载，数据库中只保存相对图片路径。
- 选品结果会被后续工作流复用，避免“图片是 A 商品、文案是 B 商品”的串货问题。

### 6.3 文案生成模块

位置：

- 后端：[module1-auth-writing/backend/app/modules/writing](C:/Users/lishu/crossborder-ai-marketing-platform/module1-auth-writing/backend/app/modules/writing)
- 前端：[module1-auth-writing/frontend/views/writing](C:/Users/lishu/crossborder-ai-marketing-platform/module1-auth-writing/frontend/views/writing)

核心能力：

- 基于商品名称、卖点、平台、语言、风格生成营销文案。
- 支持库内商品一键带入。
- 支持生成海报短文案。
- 保存文案历史。

主要接口：

- `POST /api/writing/generate`
- `GET /api/writing/history`
- `DELETE /api/writing/history/{history_id}`
- `GET /api/writing/campaigns`
- `POST /api/writing/campaigns/recommend`

### 6.4 商品抠图模块

位置：

- 后端：[module2-matte/backend/app/modules/matte](C:/Users/lishu/crossborder-ai-marketing-platform/module2-matte/backend/app/modules/matte)
- 前端：[module2-matte/frontend/views/matte](C:/Users/lishu/crossborder-ai-marketing-platform/module2-matte/frontend/views/matte)

核心能力：

- 支持本地上传图片或传入图片 URL。
- 生成透明背景商品图，保存到 `/static/matte/`。
- 识别商品类别、英文类别、置信度和属性。
- 保存抠图历史。

主要接口：

- `GET /api/matte/health`
- `POST /api/matte/process`
- `POST /api/matte/process-url`
- `GET /api/matte/history`
- `GET /api/matte/download/{record_id}`

### 6.5 背景生成模块

位置：

- 后端路由：[module3-background/backend/app/modules/background/router.py](C:/Users/lishu/crossborder-ai-marketing-platform/module3-background/backend/app/modules/background/router.py)
- 图像服务：[module3-background/app/services.py](C:/Users/lishu/crossborder-ai-marketing-platform/module3-background/app/services.py)
- 前端页面：[module3-background/frontend/views/background/BackgroundPage.vue](C:/Users/lishu/crossborder-ai-marketing-platform/module3-background/frontend/views/background/BackgroundPage.vue)

当前设计为全程使用火山方舟豆包 Seedream，不再提供 Stable Diffusion 选项。

核心能力：

- 根据品类、风格、色调、场景、光照、氛围、机位、补充说明构造背景 Prompt。
- Prompt 强约束“只生成空背景”，避免模型生成商品、人物、文字、Logo 或包装。
- 优先使用 `ARK_MODEL`，失败时可使用 `ARK_MODEL_FALLBACK`。
- 生成图保存到 `/static/background/generated/`。
- 为兼容旧字段，接口仍返回 `enhanced_url`，但当前与 `bg_url` 指向同一张 Seedream 图片。

主要接口：

- `GET /api/background/options`
- `GET /api/background/styles`
- `POST /api/background/generate`
- `GET /api/background/history`

### 6.6 海报合成模块

位置：

- 后端：[module4-poster/backend/app/modules/poster](C:/Users/lishu/crossborder-ai-marketing-platform/module4-poster/backend/app/modules/poster)
- 合成引擎：[module4-poster/poster_module/poster_service.py](C:/Users/lishu/crossborder-ai-marketing-platform/module4-poster/poster_module/poster_service.py)
- 前端：[module4-poster/frontend/views/poster/PosterPage.vue](C:/Users/lishu/crossborder-ai-marketing-platform/module4-poster/frontend/views/poster/PosterPage.vue)

核心能力：

- 管理海报模板。
- 将抠图商品和 Seedream 背景合成无字底图。
- 支持文案叠加、字体、颜色、描边、阴影、CTA 按钮等样式控制。
- 支持 Seedream 融合精修。
- 保存海报历史。

主要接口：

- `POST /api/poster/upload/image`
- `GET /api/poster/templates`
- `POST /api/poster/compose`
- `GET /api/poster/history`
- `DELETE /api/poster/history/{pid}`
- `GET /api/poster/download/{pid}`

### 6.7 我的作品模块

位置：

- 前端页面：[shared/frontend/src/views/MyWorksPage.vue](C:/Users/lishu/crossborder-ai-marketing-platform/shared/frontend/src/views/MyWorksPage.vue)
- 后端接口：海报模块和文案模块历史接口

核心能力：

- 查看当前用户的海报历史。
- 查看文案历史。
- 查看我的收藏。
- 删除海报历史。
- 下载海报。
- 收藏或取消收藏海报。
- 发布或取消发布海报到作品广场。

主要接口：

- `GET /api/poster/history`
- `DELETE /api/poster/history/{pid}`
- `GET /api/poster/download/{pid}`
- `POST /api/poster/favorite/{pid}`
- `GET /api/poster/favorites`
- `POST /api/poster/{pid}/publish`
- `POST /api/poster/{pid}/unpublish`
- `GET /api/writing/history`

设计说明：

- “我的作品”是用户侧资产管理中心。
- `history_poster.is_public` 控制作品是否进入广场。
- `favorites` 表记录用户收藏关系。
- 同一页面聚合“我的海报、我的文案、我的收藏”，方便演示完整闭环。

### 6.8 作品广场模块

位置：

- 前端页面：[shared/frontend/src/views/GalleryPage.vue](C:/Users/lishu/crossborder-ai-marketing-platform/shared/frontend/src/views/GalleryPage.vue)
- 后端接口：[module4-poster/backend/app/modules/poster/router.py](C:/Users/lishu/crossborder-ai-marketing-platform/module4-poster/backend/app/modules/poster/router.py)

核心能力：

- 展示所有已发布的公开海报。
- 支持分页浏览。
- 支持预览海报。
- 支持收藏或取消收藏。
- 标记当前用户是否已收藏、是否为本人作品。

主要接口：

- `GET /api/poster/gallery`
- `POST /api/poster/favorite/{pid}`

设计说明：

- 作品广场只展示 `history_poster.is_public = true` 的海报。
- 海报发布入口在“我的作品”中，广场负责展示和互动。
- 收藏数据与 `favorites` 表关联，支持用户回到“我的作品”查看收藏。

### 6.9 智能客服与运营看板模块

位置：

- 后端：[module5-chat/backend/app/modules](C:/Users/lishu/crossborder-ai-marketing-platform/module5-chat/backend/app/modules)
- 前端：[module5-chat/frontend/views/chat](C:/Users/lishu/crossborder-ai-marketing-platform/module5-chat/frontend/views/chat)

核心能力：

- 导入 ABO 商品知识库。
- 通过 FAISS 和 RAG 支持商品问答。
- 支持会话、消息、文件上传和反馈。
- 提供运营统计、趋势、建议和导出。

主要接口：

- `POST /api/chat/sessions`
- `GET /api/chat/sessions`
- `DELETE /api/chat/sessions/{session_id}`
- `GET /api/chat/messages/{session_id}`
- `POST /api/chat/upload`
- `POST /api/chat/message`
- `POST /api/chat/feedback`
- `GET /api/dashboard/stats`
- `GET /api/dashboard/trend`
- `GET /api/dashboard/advice`
- `GET /api/dashboard/export/excel`
- `GET /api/dashboard/export/pdf`

## 7. 核心业务流程

### 7.1 智能选品到海报生产流程

```text
1. 智能选品
   从 ABO 商品库检索商品，选定商品后写入 selectedProduct。

2. 商品抠图
   使用商品图片生成透明背景图，写入 mattedUrl，并绑定商品 ID。

3. 背景生成
   根据商品上下文和用户选择的风格参数调用 Seedream，生成空场景背景。

4. 生成无字底图
   海报模块把透明商品图贴入背景，输出无文字底图。

5. 添加文案
   叠加标题、卖点、价格、CTA 等元素，生成最终海报。

6. 我的作品
   保存历史，可下载、收藏、删除或发布。

7. 作品广场
   已发布作品进入广场，其他用户可浏览和收藏。
```

### 7.2 文案到海报流程

```text
商品信息 -> 文案生成/商品短文案 -> posterConfig -> 海报合成 -> 我的作品 -> 作品广场
```

### 7.3 作品发布与收藏流程

```text
海报生成 -> history_poster
  -> 用户发布 -> is_public=true, published_at=当前时间 -> 作品广场展示
  -> 用户收藏 -> favorites 写入 user_id + poster_id
  -> 我的作品/我的收藏聚合展示
```

### 7.4 客服问答流程

```text
用户问题 -> 会话上下文 -> ABO 商品检索/FAISS/RAG -> LLM 生成答复 -> 保存消息和反馈
```

## 8. 数据模型设计

当前主要数据表：

| 表 | 模型 | 说明 |
| --- | --- | --- |
| `users` | `User` | 用户账号、密码哈希、创建时间 |
| `abo_products` | `AboProduct` | ABO 商品知识库，支撑智能选品和客服检索 |
| `history_writing` | `WritingHistory` | 文案生成历史 |
| `history_matte` | `MatteHistory` | 抠图历史、分类识别结果 |
| `history_background` | `BackgroundHistory` | Seedream 背景生成历史 |
| `background_cache` | `BackgroundCache` | 背景缓存，减少重复生成 |
| `templates` | `Template` | 海报模板配置 |
| `history_poster` | `PosterHistory` | 海报生成历史、发布状态、下载量 |
| `favorites` | `Favorite` | 用户收藏的公开或自有海报 |
| `chat_sessions` | `ChatSession` | 客服会话 |
| `chat_messages` | `ChatMessage` | 客服消息 |
| `chat_feedback` | `ChatFeedback` | 消息反馈 |
| `system_daily_stats` | `SystemDailyStat` | 运营日报 |
| `module_errors` | `ModuleError` | 模块错误记录 |

关键关系：

```text
users 1 -> N history_writing
users 1 -> N history_matte
users 1 -> N history_background
users 1 -> N history_poster
users 1 -> N favorites

templates 1 -> N history_poster
history_poster 1 -> N favorites
users 1 -> N chat_sessions
chat_sessions 1 -> N chat_messages
```

## 9. 静态资源设计

静态资源统一挂载为 `/static`：

| 目录 | 用途 |
| --- | --- |
| `static/matte/` | 抠图结果 |
| `static/background/generated/` | Seedream 背景图 |
| `static/poster/` | 海报成品、底图、精修图 |
| `/static/abo-images/` | 外部 ABO 图片目录挂载 |

数据库只保存静态 URL，不直接保存图片二进制。

## 10. 配置设计

环境变量模板位于 [.env.example](C:/Users/lishu/crossborder-ai-marketing-platform/.env.example)。

关键配置：

| 配置 | 说明 |
| --- | --- |
| `SECRET_KEY` | JWT 签名密钥 |
| `DATABASE_URL` | SQLite 数据库地址 |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` | OpenAI 兼容接口配置 |
| `LLM_API_KEY` / `LLM_API_URL` / `LLM_MODEL` | 文案模块兼容配置 |
| `ARK_API_KEY` / `ARK_BASE_URL` | 火山方舟 Seedream 配置 |
| `ARK_MODEL` | Seedream 主模型 |
| `ARK_MODEL_FALLBACK` | Seedream 备用模型 |
| `BG_MOCK_MODE` | 背景生成占位图开关 |
| `BG_IMAGE_SIZE` | 背景图片尺寸 |
| `BG_API_TIMEOUT` | 背景生成超时时间 |
| `ABO_LISTINGS_DIR` / `ABO_IMAGES_DIR` | 本地 ABO 数据目录 |

## 11. 安全设计

- 用户密码使用哈希存储，不保存明文密码。
- 业务接口通过 `Depends(get_current_user)` 校验 JWT。
- 前端路由守卫根据本地 token 控制页面访问。
- SQL 操作通过 SQLAlchemy ORM 完成，避免手写拼接 SQL。
- API Key 只放 `.env`，不进入版本库。
- 生产环境建议收紧 CORS，目前开发环境允许 `localhost` 和通配来源。

## 12. 部署与运行

开发环境：

```bash
pip install -r requirements.txt
python run.py
```

```bash
cd shared/frontend
npm install
npm run dev
```

生产环境建议：

- 前端执行 `npm run build` 生成静态资源。
- 后端使用 `uvicorn` 或进程管理器运行 FastAPI。
- 使用 Nginx 做反向代理和静态文件服务。
- SQLite 可满足课程演示和小规模使用；长期生产可迁移到 PostgreSQL。

## 13. 当前约束与后续优化

当前约束：

- SQLite 适合演示和轻量部署，高并发写入能力有限。
- 部分模块仍保留成员独立版本，统一入口以 `shared` 集成为准。
- AI 图像生成依赖外部接口额度、模型开通状态和网络稳定性。
- `enhanced_url` 是兼容字段，当前与 `bg_url` 相同。

后续优化方向：

- 建立 Alembic 数据库迁移。
- 增加后台任务队列处理长耗时图像生成。
- 增加生成任务状态查询，避免前端长时间等待单个 HTTP 请求。
- 增加对象存储支持，替代本地静态文件目录。
- 增加作品审核、公开作品举报和广场推荐排序。
- 增加更细的权限、作品可见性和多用户隔离策略。
- 为核心 API 增加自动化测试和端到端工作流测试。
