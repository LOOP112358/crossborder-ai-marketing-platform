# 合并说明（简）

## 怎么合才不丢原始代码

1. **保留各组独立目录**  
   - `module2-matte/app/`、`module3-background/app/`：成员原始可独立运行版本（已恢复）  
   - `module4-poster/poster_module/`：成员4原始海报实现  
   - `module5-chat-dashboard/`：成员5 React + ECharts 原版（`feature/module5-chat-dashboard`）  
   - `module*-*/backend/app/modules/`：接入 `shared` 统一后端的适配层  
   - `module*-*/frontend/views/`：接入统一路由的 Vue 页面  

2. **统一入口只做壳**  
   - 后端：`shared/backend/app/main.py` 只负责挂路由  
   - 前端：`shared/frontend` 只负责布局、路由、鉴权与主题  

3. **禁止用占位页覆盖原始功能页**  
   - 路由应指向 `MattePage / BackgroundPage / PosterPage / ChatPage / DashboardPage`  
   - `Placeholder.vue` 仅作备用，不要作为默认入口  

## 当前状态（整合负责人自查）

- [x] `MainLayout` 已挂到路由
- [x] m2/m3 原始 `app/` 目录已恢复保留
- [x] m4 海报合成已桥接 `poster_module` 艺术字引擎
- [x] m5 看板已补 trend / WebSocket / 导出；客服已补语言切换
- [x] 前端 API 客户端：`background.js` / `chat.js` / `dashboard.js`
- [x] 保留原版 `module5-chat-dashboard/`（React + ECharts 参考实现）
- [x] 已合并 feature/module5 二轮优化：char_wb 检索、客服 Prompt、LIKE 备选搜索
- [x] Vue 看板已接 ECharts（饼图/折线/错误柱）、blob 导出鉴权、WS 重连、删除会话 API
- [ ] 工作区未提交迁移需 push 后，协作者才能拉到完整整合版
- [ ] 更换 TF-IDF analyzer 后，建议重建全局 FAISS：`python scripts/import_abo_kb.py`（或等价导入脚本）
