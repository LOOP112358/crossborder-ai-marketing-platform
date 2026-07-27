# 模块3：背景生成（Seedream + Stable Diffusion）

**负责：成员3**

模块主要包含背景生成服务、Stable Diffusion 增强生成、背景缓存管理、历史记录保存，以及与其他模块的数据接口联调。

## 一、主要功能

### 1. 智能背景生成

用户输入商品类别、背景风格以及颜色倾向后，系统自动构造适用于图像生成模型的 Prompt，并调用文生图模型生成商业化背景。

当前支持 **Seedream** 和 **Stable Diffusion** 双模型：

| 模型 | 用途 | 返回字段 |
|------|------|----------|
| 豆包 Seedream | 主要背景生成 | `bg_url` |
| Stable Diffusion | 额外背景方案 | `enhanced_url` |

为避免生成结果出现商品主体，Prompt 中加入了禁止生成商品、人物、文字、Logo 等约束，同时要求保留中心区域用于后续商品放置。

### 2. 背景缓存机制

系统根据 `category`、`style`、`color_hint` 生成唯一缓存标识。

当用户再次请求相同参数时，优先查询缓存；若已有对应结果，则直接返回已有图片地址，避免重复调用 API，降低生成成本。

### 3. 历史记录保存

使用 SQLite 保存背景生成记录，包括商品类别、风格、颜色、Prompt、原始背景 URL、增强背景 URL 以及生成时间，方便后续查询和扩展。

---

## 二、接口说明

统一平台响应格式：`{ "code": 200, "message": "...", "data": { ... } }`  
统一平台接口需登录（JWT：`Authorization: Bearer <token>`）。

### 1. 商品联动生成

`POST /api/background/generate_from_product`

用于连接成员2 商品抠图与智能识别模块。

输入示例：

```json
{
  "category": "香水",
  "category_en": "cosmetics",
  "attributes": {
    "style": "简约高级",
    "color": "pink and gold"
  }
}
```

返回主要字段：

- `bg_url`：基础背景图片地址（Seedream）
- `enhanced_url`：增强/备选背景图片地址（Stable Diffusion）

### 2. 独立背景生成

`POST /api/background/generate`（`multipart/form-data`）

| 字段 | 说明 | 示例 |
|------|------|------|
| `category` | 商品类别 | 运动鞋 |
| `style` | 背景风格 | 户外运动 / outdoor |
| `color_hint` | 颜色倾向 | 绿色 |

### 3. 其他接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/background/styles` | 风格列表 |
| GET | `/api/background/history` | 当前用户历史 |
| GET | `/api/background/history/{id}` | 单条历史 |

---

## 三、前端 / 联调方式

### 方式 A：统一平台（推荐）

```bash
# 项目根目录
python run.py

# 另开终端
cd shared/frontend
npm run dev
```

- 前端：http://127.0.0.1:5173 → AI 海报工作流 → 背景步骤  
- API 文档：http://127.0.0.1:8000/docs  

### 方式 B：Swagger 直接测接口

1. 先登录拿 token（`POST /api/auth/login`）  
2. 在 Swagger 右上角 Authorize 填入 `Bearer <token>`  
3. 选择 `POST /api/background/generate` 或 `generate_from_product`  
4. Try it out → Execute  
5. 查看返回中的 `bg_url` / `enhanced_url`  

### 方式 C：成员3 独立服务（原始目录）

```bash
cd module3-background
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```

访问：http://127.0.0.1:8003/docs  
（独立版默认无 JWT，端口建议避开 8000，避免与统一入口冲突）

---

## 四、模块协作

### 与成员2（抠图 / 识别）

成员2 输出：

- `category`
- `category_en`
- `attributes`（含 style / color 等）

模块3 读取后调用 `generate_from_product` 自动生成背景。

### 与成员4（海报合成）

模块3 输出：

- `bg_url`：基础背景  
- `enhanced_url`：增强/备选背景  

成员4 将抠图商品与背景融合，生成最终营销海报。前端通过 Pinia `useAppStore` 传递 `enhanced_url`（或用户选中的背景）。

---

## 五、环境变量

在项目根目录 `.env` 配置（未配置时走 Mock 占位图，便于联调）：

```env
# 豆包 Seedream（火山方舟）
ARK_API_KEY=
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL=doubao-seedream-4-0-250828

# Stable Diffusion（Stability AI）
STABILITY_API_KEY=
STABILITY_MODEL=sd3.5-medium
```

静态资源目录：`static/background/generated/`、`static/background/enhanced/`

---

## 六、目录结构

```
module3-background/
├── app/                    # 成员原始独立实现（双模型 + 缓存）
│   ├── main.py
│   ├── services.py
│   └── database.py
├── backend/app/modules/background/
│   └── router.py           # 接入统一平台的适配层（JWT + 历史表）
├── frontend/views/background/
│   └── BackgroundPage.vue  # 统一前端页面
└── requirements.txt
```
