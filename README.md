# 固定资产管理系统 (FAMS)

Fixed Asset Management System — 基于 Vue 3 + Flask 的企业固定资产全生命周期管理平台。

## 功能概览

- **工作台** — 资产统计概览、待处理事项、快捷入口
- **固定资产台账** — 资产的新增、修改、查询、详情查看
- **资产流转** — 派发、借用、归还、退库、变更领用人，完整操作记录
- **资产参数设置** — 分类、品牌、单位、存放地点等字典管理
- **用户/角色/权限** — RBAC 权限模型，角色分配权限，权限树管理
- **操作日志** — 全部关键操作留痕可追溯
- **移动端适配** — 响应式布局，手机端侧边栏抽屉

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + Vite + Element Plus + Pinia + Vue Router |
| 后端 | Flask + SQLAlchemy + Flask-Migrate + Flask-Bcrypt + PyJWT |
| 数据库 | SQLite（开发）/ 可迁移至 PostgreSQL/MySQL |
| 认证 | JWT Token，路由守卫 |

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 20.19+

### 1. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
flask db upgrade

# （可选）导入种子数据
python seed.py

# 启动服务（默认端口 5001，避免 macOS AirPlay 占用 5000）
python -c "from app import create_app; app = create_app(); app.run(debug=True, port=5001)"
```

### 2. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

浏览器打开 http://localhost:5173

### 默认账号

| 账号 | 密码 | 角色 |
|------|------|------|
| admin | 123456 | 系统管理员 |

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── api/            # API 蓝图（auth, assets, users, roles...）
│   │   ├── models/         # SQLAlchemy 数据模型
│   │   ├── utils/          # 工具函数（JWT, 装饰器）
│   │   └── config.py       # 应用配置
│   ├── migrations/         # 数据库迁移脚本
│   ├── tests/              # pytest 测试
│   ├── run.py              # 入口
│   └── seed.py             # 种子数据
├── frontend/
│   ├── src/
│   │   ├── api/            # Axios API 封装
│   │   ├── components/     # 通用组件（Sidebar, Topbar, AppLayout）
│   │   ├── views/          # 页面组件
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── router/         # Vue Router 路由配置
│   │   └── styles/         # 全局样式
│   └── vite.config.js
├── docs/plans/             # 开发计划文档
└── 固定资产管理系统PRD.md    # 产品需求文档
```

## API 概览

| 模块 | 路径前缀 | 说明 |
|------|---------|------|
| 认证 | `/api/auth` | 登录、获取当前用户 |
| 资产 | `/api/assets` | CRUD + 派发/借用/归还/退库/变更 |
| 用户 | `/api/users` | 用户管理 |
| 角色 | `/api/roles` | 角色管理 + 权限分配 |
| 权限 | `/api/permissions` | 权限树 |
| 资产参数 | `/api/asset-params` | 字典管理 |
| 工作台 | `/api/dashboard` | 统计数据 |
| 日志 | `/api/logs` | 操作日志 |

所有 API 需携带 `Authorization: Bearer <token>` 头（登录接口除外）。

## 构建部署

```bash
# 构建前端
cd frontend && npm run build

# 产物在 frontend/dist/，可由 Nginx 或 Flask 静态文件服务
```

## 运行测试

```bash
cd backend
source venv/bin/activate
pytest
```

## License

MIT
