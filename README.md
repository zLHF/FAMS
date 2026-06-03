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

# （仅开发环境）导入种子数据
python seed.py

# 启动开发服务器
python run.py
```

首次运行 `seed.py` 后，系统会创建管理员账号。密码会在终端输出。

### 2. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

浏览器打开 http://localhost:5173

## 环境变量

| 变量 | 必填 | 说明 | 默认值（仅开发） |
|------|------|------|--------|
| `FLASK_ENV` | 否 | `development` / `production` | `development` |
| `SECRET_KEY` | 生产必填 | Flask 会话密钥 | 开发用默认值 |
| `JWT_SECRET` | 生产必填 | JWT 签名密钥，至少 32 字符 | 开发用默认值 |
| `DATABASE_URL` | 否 | 数据库连接串 | SQLite |
| `PORT` | 否 | 后端端口 | 5001 |
| `CORS_ORIGINS` | 否 | 允许的前端源，逗号分隔 | `http://localhost:5173` |
| `JWT_EXPIRATION_HOURS` | 否 | Token 有效时长 | 24 |
| `LOGIN_MAX_ATTEMPTS` | 否 | 登录失败锁定阈值 | 5 |
| `LOGIN_LOCKOUT_MINUTES` | 否 | 锁定时长（分钟） | 15 |

生产环境示例：

```bash
export FLASK_ENV=production
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
export JWT_SECRET=$(python -c 'import secrets; print(secrets.token_hex(32))')
export CORS_ORIGINS=https://your-domain.example
```

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── api/            # API 蓝图（auth, assets, users, roles...）
│   │   ├── models/         # SQLAlchemy 数据模型
│   │   ├── utils/          # 工具函数（JWT, 装饰器, Token 黑名单）
│   │   └── config.py       # 应用配置
│   ├── migrations/         # 数据库迁移脚本
│   ├── tests/              # pytest 测试
│   ├── run.py              # 入口（生产环境 debug=False）
│   └── seed.py             # 种子数据（仅开发环境）
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
| 认证 | `/api/auth` | 登录、登出、获取当前用户 |
| 资产 | `/api/assets` | CRUD + 派发/借用/归还/退库/变更（管理操作需 admin 角色） |
| 用户 | `/api/users` | 用户管理（写操作需 admin 角色） |
| 角色 | `/api/roles` | 角色管理 + 权限分配（写操作需 admin 角色） |
| 权限 | `/api/permissions` | 权限树（只读） |
| 资产参数 | `/api/asset-params` | 字典管理（写操作需 admin 角色） |
| 工作台 | `/api/dashboard` | 统计数据 |
| 日志 | `/api/logs` | 操作日志 |

## 安全措施

- JWT Token 含 `jti`（唯一 ID），登出时加入黑名单
- 登录失败计数，超过阈值临时锁定账号
- 管理接口强制 `admin` 角色校验
- CORS 白名单，仅允许配置的源
- 密码 Bcrypt 哈希，不明文存储
- 生产环境强制通过环境变量配置密钥
- 分页查询 `per_page` 上限 100

## 构建部署

```bash
# 构建前端
cd frontend && npm run build

# 生产环境用 Gunicorn 启动后端
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 "app:create_app()"
```

前端构建产物在 `frontend/dist/`，可由 Nginx 提供静态文件服务并反向代理 API。

## 运行测试

```bash
cd backend
source venv/bin/activate
pytest
```

## License

MIT
