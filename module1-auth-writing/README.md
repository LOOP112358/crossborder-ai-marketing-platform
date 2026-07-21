# 模块1：用户认证 + 文案生成 + 项目整合

**负责：成员1**

## 功能清单

### 基础功能
- ✅ 用户注册/登录（JWT 认证）
- ✅ 文案生成（输入商品→AI生成标题+正文+标签）
- ✅ 文案历史记录（分页查询）
- ✅ 首页导航（总览所有模块入口）
- ✅ 项目脚手架搭建（FastAPI + Vue3 + 路由 + 状态管理）

### 进阶功能
- ✅ 5种语言扩展（中/英/日/韩/西）
- ✅ 6种文案风格（专业商务/活泼种草/极简高级/情感共鸣/幽默风趣/奢华高端）
- ✅ Prompt 工程优化（Few-shot 示例库 + 风格特征描述）
- ✅ 批量生成（一次输入，多平台输出）
- ✅ vue-i18n 全站国际化（UI 5语言切换）

## 目录
```
backend/app/modules/
  auth/          # JWT注册/登录
  writing/       # 文案生成 + LLM客户端
frontend/views/
  Login.vue      # 登录页
  Register.vue   # 注册页
  Home.vue       # 首页导航
  writing/       # 文案生成页（6风格选择器 + 历史记录）
```

## API
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/register | 注册 |
| POST | /api/auth/login | 登录 |
| GET | /api/auth/me | 用户信息 |
| POST | /api/writing/generate | 生成文案 |
| GET | /api/writing/history | 历史记录 |

## 数据库
- `users` — 用户表
- `history_writing` — 文案生成历史
