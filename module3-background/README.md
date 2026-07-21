# 模块3：背景生成 + 超分增强

**负责：成员3 | 待开发**

## 计划功能
- 根据商品类别自动构建 Prompt
- Stable Diffusion API 生成场景背景
- Real-ESRGAN 超分增强（2x/4x）
- 背景风格库（户外/简约/科技感/奢华等）
- 多图生成供用户选择
- CLIP 背景-商品匹配度评分

## API（计划）
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/background/generate | 生成背景+超分 |
| GET | /api/background/styles | 获取风格列表 |
| GET | /api/background/history | 历史记录 |

## 协作接口
- **输入**：从成员2读取 `category`（商品类别）
- **输出**：`enhanced_bg_url` 写入全局状态，供成员4读取
