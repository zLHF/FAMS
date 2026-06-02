# 固定资产管理系统 — 实施计划总览

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement each module plan task-by-task.

**Goal:** 构建企业内部固定资产管理系统，支持资产台账、领用派发、借用归还、退库和领用人变更全流程。

**Architecture:** 前后端分离架构。前端 Vue 3 SPA + Element Plus，后端 Flask RESTful API + SQLAlchemy ORM，SQLite 数据库，JWT 认证。前端基于现有 HTML 原型的 UI 设计重写。

**Tech Stack:**
- Frontend: Vue 3 + Vite + Element Plus + Vue Router + Pinia + Axios
- Backend: Python 3.10+ / Flask + Flask-SQLAlchemy + Flask-Migrate + PyJWT + Flask-CORS
- Database: SQLite (开发/小规模部署)
- Auth: JWT (access token)

---

## 项目目录结构

```
fams/
├── backend/
│   ├── app/
│   │   ├── __init__.py           # Flask app factory
│   │   ├── config.py             # 配置项
│   │   ├── extensions.py         # db, jwt 等扩展实例
│   │   ├── models/               # SQLAlchemy 模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── role.py
│   │   │   ├── permission.py
│   │   │   ├── asset_param.py
│   │   │   ├── asset.py
│   │   │   └── operation_log.py
│   │   ├── api/                  # Blueprint 路由
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── roles.py
│   │   │   ├── permissions.py
│   │   │   ├── asset_params.py
│   │   │   ├── assets.py
│   │   │   └── flows.py          # 派发/借用/归还/退库/变更
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── auth.py           # JWT 工具函数
│   │       └── decorators.py     # 权限装饰器
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_users.py
│   │   ├── test_roles.py
│   │   ├── test_permissions.py
│   │   ├── test_asset_params.py
│   │   ├── test_assets.py
│   │   └── test_flows.py
│   ├── migrations/               # Flask-Migrate 自动生成
│   ├── requirements.txt
│   ├── run.py                    # 入口 python run.py
│   └── seed.py                   # 种子数据
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/index.js
│   │   ├── stores/
│   │   │   └── auth.js           # Pinia 用户状态
│   │   ├── api/                  # 接口封装
│   │   │   ├── index.js          # Axios 实例 + 拦截器
│   │   │   ├── auth.js
│   │   │   ├── users.js
│   │   │   ├── roles.js
│   │   │   ├── permissions.js
│   │   │   ├── assetParams.js
│   │   │   └── assets.js
│   │   ├── views/                # 页面组件
│   │   │   ├── Login.vue
│   │   │   ├── Dashboard.vue
│   │   │   ├── Users.vue
│   │   │   ├── Roles.vue
│   │   │   ├── Permissions.vue
│   │   │   ├── AssetParams.vue
│   │   │   ├── Assets.vue
│   │   │   ├── AssetDistribute.vue
│   │   │   ├── AssetBorrow.vue
│   │   │   ├── AssetReturn.vue
│   │   │   ├── AssetRevert.vue
│   │   │   └── AssetOwnerChange.vue
│   │   ├── components/
│   │   │   ├── AppLayout.vue     # 侧边栏+顶栏布局
│   │   │   ├── Sidebar.vue
│   │   │   └── Topbar.vue
│   │   └── styles/
│   │       └── global.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── docs/
    └── plans/                    # 本目录 — 实施计划
```

---

## 数据库 ER 设计

### 核心表

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `users` | 用户 | id, username, password_hash, name, phone, department, role_id, status |
| `roles` | 角色 | id, name, code, description, status |
| `permissions` | 权限菜单树 | id, name, code, parent_id, sort_order |
| `role_permissions` | 角色-权限关联 | role_id, permission_id |
| `asset_params` | 资产参数 | id, type, name, code, sort_order, status |
| `assets` | 固定资产 | id, code, name, category, brand, model, serial_number, unit, purchase_date, location, status, owner_id, borrower_id, notes |
| `flow_records` | 流转记录 | id, asset_id, flow_type, operator_id, detail_json, created_at |
| `operation_logs` | 操作日志 | id, user_id, action, target_type, target_id, detail, created_at |

### 资产状态枚举

```
idle       = 闲置
distributed = 已派发
borrowing  = 借用中
returned   = 已退库
```

---

## 模块划分与执行顺序

| 序号 | 计划文件 | 模块 | 依赖 |
|------|---------|------|------|
| 01 | `01-scaffolding.md` | 前后端项目脚手架 + 数据库初始化 | 无 |
| 02 | `02-auth.md` | 登录/登出 + JWT 认证 | 01 |
| 03 | `03-users.md` | 用户管理 CRUD | 02 |
| 04 | `04-roles-permissions.md` | 角色管理 + 权限管理 + 菜单控制 | 03 |
| 05 | `05-asset-params.md` | 资产参数设置 | 02 |
| 06 | `06-assets.md` | 固定资产台账 CRUD | 05 |
| 07 | `07-asset-flows.md` | 资产流转（派发/借用/归还/退库/变更） | 06 |
| 08 | `08-dashboard.md` | 首页仪表盘 + 操作日志 | 07 |
| 09 | `09-polish.md` | 联调收尾 + 种子数据 + 最终验收 | 08 |

---

## 执行方式

每个模块计划文件包含：
1. 后端 Model → API → Test（TDD）
2. 前端 API 封装 → 页面组件 → 联调
3. 每步都是 2-5 分钟的原子任务
4. 每个模块完成后 git commit

开始执行时选择：
- **Subagent-Driven（本会话）** — 每个任务派发子代理，逐任务 review
- **Parallel Session（新会话）** — 新会话中使用 executing-plans 技能批量执行
