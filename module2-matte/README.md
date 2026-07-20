# 成员2：商品抠图 + 智能识别

这是可独立运行、也可合并进小组总项目的 FastAPI 模块，接口统一返回
`{code, message, data}`，生成图片统一保存到 `static/matte/`。

## 已实现

- 单图上传与格式/大小校验（JPG、PNG、WEBP，最大 10 MB）
- Rembg 商品主体抠图，输出透明 PNG
- 边缘平滑与轻微羽化
- Ollama 多模态商品识别（可选）
- 无 Ollama 时的轻量属性识别兜底（主色、明暗风格）
- SQLite 历史记录，字段与小组 `history_matte` 约定一致
- 抠图历史、结果下载、健康检查接口
- Vue3 单文件组件，可直接交给组长并入 UniApp/Vue3 项目
- 独立演示页面，后端启动后访问 `/`

## 快速启动

```bash
cd member2-matte-recognition
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

浏览器打开 <http://127.0.0.1:8000>，接口文档位于
<http://127.0.0.1:8000/docs>。

首次安装 `rembg` 会下载模型，需联网。若只想先演示页面和接口，可设置：

```powershell
$env:MATTE_MOCK_MODE="1"
uvicorn app.main:app --reload --port 8000
```

Mock 模式会把近白色背景透明化，仅用于联调，不代表最终抠图效果。

## 可选：启用 Ollama 智能识别

安装并启动 Ollama，准备支持视觉的模型，例如：

```bash
ollama pull qwen2.5vl:3b
```

然后配置：

```powershell
$env:OLLAMA_BASE_URL="http://127.0.0.1:11434"
$env:OLLAMA_VISION_MODEL="qwen2.5vl:3b"
```

未配置时，系统返回 `category=商品/product`，同时仍会识别主色和视觉风格。

## 接口

| 方法 | 路径 | 作用 |
|---|---|---|
| POST | `/api/matte/process` | 抠图 + 识别；表单字段 `file`、`user_id`、`edge_smoothing` |
| GET | `/api/matte/history?user_id=1` | 查询历史记录 |
| GET | `/api/matte/download/{id}` | 下载透明 PNG |
| GET | `/api/matte/health` | 检查服务状态 |

`POST /api/matte/process` 成功响应中的 `matted_url`、`category` 应写入 Pinia
全局状态，供成员3的背景生成模块读取。示例：

```js
workflowStore.setMatteResult({
  mattedUrl: result.matted_url,
  category: result.category,
  attributes: result.attributes
})
```

## 目录

```text
app/
  main.py          FastAPI入口与路由
  database.py      SQLite初始化与历史记录
  services.py      抠图、边缘优化、颜色及Ollama识别
frontend/
  MatteWorkspace.vue  可合并的Vue3组件
static/matte/      原图与透明图共享目录
tests/             API自动测试
```

## 答辩演示顺序

1. 上传 ABO 数据集商品图或一张高清白底商品图。
2. 展示原图，点击“开始智能抠图”。
3. 展示棋盘格透明背景结果及中英文类别、置信度、颜色/风格属性。
4. 下载透明 PNG。
5. 打开历史记录，说明数据已存入 SQLite。
6. 展示响应里的 `matted_url` 和 `category`，说明它们会传给成员3。

