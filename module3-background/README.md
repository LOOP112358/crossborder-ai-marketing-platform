# 模块3：背景生成（Seedream）

模块3负责为商品海报生成空场景商业背景。当前全程使用火山方舟豆包 Seedream 接口，不再提供 Stable Diffusion 选项。

## 功能

- 根据商品品类、风格、色调、场景、光照、氛围、机位等参数生成背景图。
- 生成结果保存到 `static/background/generated/`。
- 记录用户历史和缓存，相同参数优先返回缓存结果。
- 为兼容旧流程，接口仍返回 `enhanced_url`，但它与 `bg_url` 指向同一张 Seedream 图片（已跳过本地假超分以加速）。

## 主要接口

- `POST /api/background/generate`
- `POST /api/background/generate_from_product`
- `GET /api/background/options`
- `GET /api/background/styles`
- `GET /api/background/history`

`POST /api/background/generate` 使用 `multipart/form-data`，常用字段：

| 字段 | 说明 |
| --- | --- |
| `category` | 场景/商品品类 |
| `style` | 视觉风格 |
| `color_hint` | 色调 |
| `scene_preset` | 场景预设 |
| `lighting` | 光照 |
| `mood` | 氛围 |
| `camera` | 机位/构图 |
| `extra_note` | 补充说明 |

## 环境变量

```env
BG_MOCK_MODE=0
ARK_API_KEY=
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL=doubao-seedream-4-0-250828
```

`BG_MOCK_MODE=1` 时强制返回占位图，便于无 API Key 联调。
