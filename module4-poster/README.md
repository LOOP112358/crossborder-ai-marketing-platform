# 成员4：海报合成模块

本模块是“跨境电商 AI 营销素材生成与管理平台”中的海报合成模块，主要负责将商品图、背景图、模板和文案信息合成为最终营销海报。

本模块属于后置合成模块，不负责商品主体抠图，也不负责 AI 背景生成。正式联调时，商品抠图结果由成员2模块提供，背景图由成员3模块提供。本模块接收 matted_url、bg_url、模板编号和文案内容，最终生成 poster_url。

模块功能

目前已完成以下功能：

1. 商品图上传
2. 背景图上传
3. 模板列表查询
4. 海报自动合成
5. 生成结果预览
6. 海报历史记录保存
7. MySQL 数据库存储
8. 海报下载
9. 下载次数统计
10. 收藏和取消收藏
11. 收藏列表查询
12. 简单前端测试页面

技术路线

后端使用 FastAPI 搭建接口服务，使用 SQLAlchemy 和 PyMySQL 连接 MySQL 数据库，使用 Pillow 完成图片合成和文字绘制。

前端目前使用 HTML、CSS、JavaScript 实现简单测试页面，用于验证图片上传、模板选择、海报生成、历史记录、下载和收藏等完整流程。

主要技术包括：

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- PyMySQL
- MySQL
- Pillow
- python-dotenv
- python-multipart
- HTML / CSS / JavaScript

目录结构

module4-poster/
├─ poster_module/
│  ├─ __init__.py
│  ├─ compose_test.py
│  ├─ create_demo_assets.py
│  ├─ database.py
│  ├─ db_models.py
│  ├─ init_db.py
│  ├─ poster_api.py
│  ├─ poster_service.py
│  ├─ templates_data.py
│  └─ static/
│     ├─ demo/
│     │  ├─ product.png
│     │  └─ background.png
│     └─ frontend/
│        └─ index.html
├─ requirements.txt
├─ .env.example
├─ .gitignore
└─ README.md

核心接口

| 接口 | 方法 | 说明 |
|---|---|---|
| / | GET | 模块启动测试 |
| /api/templates | GET | 获取模板列表 |
| /api/upload/image | POST | 上传商品图或背景图 |
| /api/poster/compose | POST | 合成海报 |
| /api/poster/history | GET | 查询海报生成历史 |
| /api/poster/download/{poster_id} | GET | 下载生成的海报 |
| /api/poster/favorite/{poster_id} | POST | 收藏或取消收藏 |
| /api/poster/favorites | GET | 查询收藏列表 |

海报合成接口

接口地址：

POST /api/poster/compose

请求示例：

{
  "user_id": 1,
  "matted_url": "/static/uploads/product_xxx.png",
  "bg_url": "/static/uploads/bg_xxx.png",
  "template_id": 1,
  "title": "Portable Blender",
  "discount": "30% OFF",
  "price": "$19.99",
  "ratio": "1:1"
}

返回示例：

{
  "message": "海报合成成功",
  "poster_url": "/static/posters/poster_xxx.png",
  "record": {
    "id": 1,
    "user_id": 1,
    "template_id": 1,
    "poster_url": "/static/posters/poster_xxx.png",
    "title": "Portable Blender",
    "discount": "30% OFF",
    "price": "$19.99",
    "downloads": 0
  }
}

字段说明

matted_url：商品抠图结果路径，正式联调时由成员2模块提供。

bg_url：背景图路径，正式联调时由成员3模块提供。

template_id：模板编号。

title：海报标题。

discount：折扣信息，可为空。

price：价格信息，可为空。

poster_url：最终生成的海报路径。

数据库说明

本模块使用 MySQL 保存数据，目前主要包含三张表。

1. templates

用于保存海报模板信息，包括模板名称、模板预览图、模板配置和使用次数。

2. history_poster

用于保存海报生成历史，包括商品图路径、背景图路径、模板编号、生成海报路径、标题、折扣、价格、下载次数和创建时间。

3. favorites

用于保存用户收藏的海报记录，支持收藏和取消收藏功能。

环境配置

本项目不会上传真实 .env 文件，只提供 .env.example 示例。运行前需要复制一份 .env.example，重命名为 .env，并填写自己的配置。

.env 示例：

DOUBAO_API_KEY=your_api_key
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL=doubao-seed-evolving

MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=ai_marketing

注意：真实 .env 文件中包含 API Key 和数据库密码，不能上传到 GitHub。

运行方式

进入模块目录：

cd module4-poster

安装依赖：

pip install -r requirements.txt

初始化数据库模板数据：

python -m poster_module.init_db

启动后端服务：

uvicorn poster_module.poster_api:app --reload --port 8001

打开接口文档：

http://127.0.0.1:8001/docs

打开前端测试页面：

http://127.0.0.1:8001/static/frontend/index.html

与其他成员的联调方式

本模块不负责商品抠图和背景生成，正式联调时需要读取其他模块的输出结果。

成员2商品抠图模块主要提供：

{
  "matted_url": "/static/matte/xxx.png",
  "category": "水杯",
  "category_en": "Cup",
  "attributes": {
    "color": "blue",
    "style": "simple"
  }
}

本模块主要使用其中的 matted_url 字段。

成员3背景生成模块需要提供：

{
  "bg_url": "/static/backgrounds/xxx.png"
}

本模块最终输出：

{
  "poster_url": "/static/posters/poster_xxx.png"
}

整体流程

成员2输出商品抠图结果 matted_url。

成员3输出背景图 bg_url。

用户选择模板并填写标题、折扣、价格等文案信息。

成员4根据 matted_url、bg_url、模板配置和文案内容合成最终海报 poster_url。

当前完成情况

当前模块已经完成前后端基础闭环，可以通过前端页面完成以下流程：

1. 上传商品图
2. 上传背景图
3. 选择模板
4. 填写标题、折扣、价格
5. 生成海报
6. 预览海报
7. 下载海报
8. 收藏海报
9. 查看历史记录
10. 查看收藏列表

后续计划

后续可以继续完善以下内容：

1. 增加多尺寸海报输出，例如 1:1、9:16、16:9
2. 优化模板样式和页面展示效果
3. 增加模板管理后台
4. 与成员2商品抠图模块正式联调
5. 与成员3背景生成模块正式联调
6. 接入文案生成模块，实现标题、折扣文案的自动生成