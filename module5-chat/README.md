# 模块5：智能客服 + 运营看板

**负责：成员5 | 来源：LOOP112358/crossborder-ai-marketing-platform**

## 功能清单

### 智能客服
- ✅ 多会话管理（创建/切换/删除）
- ✅ PDF/Word/TXT/Markdown 文档上传与解析
- ✅ FAISS 向量索引（TF-IDF + FAISS，轻量无需GPU）
- ✅ RAG 检索增强生成（文档库 QA + LLM 回复）
- ✅ 中英双语自动切换
- ✅ 对话历史上下文理解
- ✅ 点赞/点踩反馈

### 运营看板
- ✅ 数据大屏：总用户数 / 今日调用量 / 各功能占比 / 热门品类排行
- ✅ AI 运营建议（基于真实数据 + LLM 生成）
- ✅ 异常预警（模块错误率 > 10% 告警）
- ✅ 客服满意度统计（点赞率）
- ✅ 数据导出：Excel / PDF
- ✅ WebSocket 实时看板刷新

## 目录
```
backend/app/modules/
  chat/
    router.py                  # 客服 API（会话/消息/文档/反馈）
    schemas.py                 # 请求/响应模型
    services/
      config.py                # 模块配置
      document_parser.py       # 文档解析（PDF/DOCX/TXT/MD）
      rag_service.py           # FAISS 向量检索
      llm_service.py           # LLM 回复生成 + 运营建议
      stats_service.py         # 统计数据汇总
      export_service.py        # Excel/PDF 导出
      seed_data.py             # 种子数据
  dashboard/
    router.py                  # 看板 API（统计/趋势/建议/导出/WS）
frontend/views/chat/
  ChatPage.vue                 # 客服聊天界面
  DashboardPage.vue            # 运营看板大屏
```

## API
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/chat/sessions | 创建会话 |
| GET | /api/chat/sessions | 会话列表 |
| DELETE | /api/chat/sessions/{id} | 删除会话 |
| GET | /api/chat/messages/{id} | 获取消息 |
| POST | /api/chat/upload | 上传文档 |
| POST | /api/chat/message | 发送消息（RAG + LLM） |
| POST | /api/chat/feedback | 提交反馈 |
| GET | /api/dashboard/stats | 看板统计数据 |
| GET | /api/dashboard/trend | 趋势数据（7天） |
| GET | /api/dashboard/advice | AI 运营建议 |
| GET | /api/dashboard/export/excel | 导出 Excel |
| GET | /api/dashboard/export/pdf | 导出 PDF |
| WS | /api/dashboard/ws | WebSocket 实时推送 |

## 运行要求
```bash
pip install faiss-cpu scikit-learn pypdf python-docx openpyxl
```

### 启用 LLM（可选，默认使用本地模板回复）
```bash
# 设置环境变量（支持任何 OpenAI 兼容接口）
export OPENAI_API_KEY="your_key"
export OPENAI_BASE_URL="https://api.deepseek.com/v1"
export OPENAI_MODEL="deepseek-chat"
```

## 数据库
- `chat_sessions` — 客服会话
- `chat_messages` — 聊天消息
- `chat_feedback` — 用户反馈
- `system_daily_stats` — 每日统计数据
- `module_errors` — 模块错误日志
