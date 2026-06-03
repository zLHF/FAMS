# 固定资产管理系统 (FAMS)

Fixed Asset Management System — 基于 Vue 3 + Flask 的企业多租户固定资产全生命周期管理平台，支持算力网络分布式管理平台 SSO 集成。

## 功能概览

- **工作台** — 资产统计概览、待处理事项、快捷入口
- **固定资产台账** — 资产的新增、修改、查询、详情查看
- **资产流转** — 派发、借用、归还、退库、变更领用人，完整操作记录
- **资产参数设置** — 分类、品牌、单位、存放地点等字典管理
- **三层权限管理** — 系统管理员 / 租户管理员 / 资产管理员，RBAC 权限模型
- **多租户管理** — 租户 CRUD、成员管理、租户间数据隔离
- **SSO 单点登录** — 对接算力网络分布式管理平台，自动开通租户和用户
- **应用心跳** — 定时向平台上报应用存活状态（签名认证）
- **操作日志** — 全部关键操作留痕可追溯
- **移动端适配** — 响应式布局，手机端侧边栏抽屉

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + Vite + Element Plus + Pinia + Vue Router + Axios |
| 后端 | Flask + SQLAlchemy + Flask-Migrate + Flask-Bcrypt + PyJWT |
| 数据库 | SQLite（开发）/ 可迁移至 PostgreSQL/MySQL |
| 认证 | JWT Token + HMAC-SHA256 签名认证 |

## 三层权限体系

| 角色 | Code | 归属 | 权限范围 |
|------|------|------|---------|
| 系统管理员 | `system_admin` | 全局角色（`tenant_id=NULL`） | 不属于任何租户，可自由切换到所有租户，管理所有租户和用户 |
| 租户管理员 | `tenant_admin` | 租户内角色 | 管理本租户的用户、角色、资产配置 |
| 资产管理员 | `asset_manager` | 租户内角色 | 资产日常操作（台账、流转），无用户管理权限 |

系统管理员登录后右上角显示租户下拉框，可切换到任意租户进行管理。

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

种子数据创建以下账号：

| 账号 | 密码 | 角色 | 说明 |
|------|------|------|------|
| `admin` | `123456` | 系统管理员 | 可管理所有租户 |
| `zhangsan` | `123456` | 租户管理员 | 默认租户管理员 |
| `lisi` | `123456` | 资产管理员 | 默认租户普通用户 |
| `wangwu` | `123456` | 资产管理员 | 默认租户普通用户 |

### 2. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

浏览器打开 http://localhost:5173（端口冲突时自动切换）

## 环境变量

### 基础配置

| 变量 | 必填 | 说明 | 默认值（仅开发） |
|------|------|------|--------|
| `FLASK_ENV` | 否 | `development` / `production` | `development` |
| `SECRET_KEY` | 生产必填 | Flask 会话密钥 | 开发用默认值 |
| `JWT_SECRET` | 生产必填 | JWT 签名密钥，至少 32 字符 | 开发用默认值 |
| `DATABASE_URL` | 否 | 数据库连接串 | SQLite |
| `CORS_ORIGINS` | 否 | 允许的前端源，逗号分隔 | `http://localhost:5173` |
| `JWT_EXPIRATION_HOURS` | 否 | Token 有效时长 | 24 |
| `LOGIN_MAX_ATTEMPTS` | 否 | 登录失败锁定阈值 | 5 |
| `LOGIN_LOCKOUT_MINUTES` | 否 | 锁定时长（分钟） | 15 |

### 算力网络平台 SSO 配置

| 变量 | 说明 |
|------|------|
| `PLATFORM_APP_ID` | 应用 ID（AppID），在平台应用详情中获取 |
| `PLATFORM_APP_SECRET` | 应用密钥（AppSecret），在平台应用详情中获取 |
| `PLATFORM_BASE_URL` | 平台代理地址，如 `http://10.136.0.8:8083/cpn` |
| `PLATFORM_APP_CODE` | 应用编码，用于拼接平台接口 URL |
| `SSO_ENABLED` | SSO 功能开关，`true` / `false`（默认 `false`） |
| `HEARTBEAT_ENABLED` | 心跳上报开关，`true` / `false`（默认 `false`） |
| `HEARTBEAT_INTERVAL` | 心跳间隔秒数（默认 `300`，即 5 分钟） |

生产环境配置示例：

```bash
# 基础安全配置
export FLASK_ENV=production
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
export JWT_SECRET=$(python -c 'import secrets; print(secrets.token_hex(32))')
export CORS_ORIGINS=https://your-domain.example

# SSO 配置（对接算力网络平台时填写）
export PLATFORM_APP_ID=your-app-id
export PLATFORM_APP_SECRET=your-app-secret
export PLATFORM_BASE_URL=http://10.136.0.8:8083/cpn
export PLATFORM_APP_CODE=applicationCode
export SSO_ENABLED=true
export HEARTBEAT_ENABLED=true
```

## SSO 对接说明

FAMS 对接算力网络分布式管理平台实现了 4 个接口：

| 接口 | 文档章节 | 类型 | 路由/模块 |
|------|---------|------|----------|
| 应用用户开通 | 2.4.2.1 | 平台→FAMS | `POST /open-api/app/tenants` |
| 身份校验 (appAuthCheck) | 2.4.2.2 | FAMS→平台 | `services/platform_client.py` |
| 用户信息 (getUserInfoByToken) | 2.4.2.3 | FAMS→平台 | `services/platform_client.py` |
| 应用心跳 (签名认证) | 2.4.2.4 | FAMS→平台 | `utils/heartbeat.py`，5 分钟一次 |

**SSO 登录流程**：用户在平台点击 FAMS 应用 → URL 携带 `code` 参数 → 前端检测 `code` 跳转 SSO 回调页 → 后端调用平台接口换取用户信息 → 自动创建/匹配本地用户并登录。

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── api/                # API 蓝图
│   │   │   ├── auth.py         # 登录/登出/租户切换
│   │   │   ├── sso.py          # SSO 回调处理
│   │   │   ├── open_api.py     # 平台开通接口
│   │   │   ├── tenants.py      # 租户管理
│   │   │   ├── users.py        # 用户管理
│   │   │   ├── roles.py        # 角色管理
│   │   │   └── ...             # assets, dashboard, logs 等
│   │   ├── models/             # SQLAlchemy 数据模型
│   │   ├── services/           # 外部服务客户端
│   │   │   └── platform_client.py  # 算力网络平台 HTTP 客户端
│   │   ├── utils/              # 工具函数
│   │   │   ├── decorators.py   # 权限装饰器（login_required, role_required）
│   │   │   ├── signature.py    # HMAC-SHA256 签名工具
│   │   │   ├── heartbeat.py    # 心跳定时任务
│   │   │   ├── auth.py         # JWT 生成/解析
│   │   │   └── tenant.py       # 租户工具函数
│   │   └── config.py           # 应用配置
│   ├── migrations/             # 数据库迁移脚本
│   ├── run.py                  # 应用入口
│   └── seed.py                 # 种子数据（仅开发环境）
├── frontend/
│   ├── src/
│   │   ├── api/                # Axios API 封装
│   │   ├── views/              # 页面组件（含 SSOCallback.vue）
│   │   ├── components/         # 通用组件（Sidebar, Topbar, AppLayout）
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── router/             # Vue Router 路由配置
│   │   └── styles/             # 全局样式
│   └── vite.config.js          # Vite 配置（含 API 代理）
├── CLAUDE.md                   # Claude Code 开发指引
└── 固定资产管理系统PRD.md        # 产品需求文档
```

## API 概览

| 模块 | 路径前缀 | 说明 |
|------|---------|------|
| 认证 | `/api/auth` | 登录、登出、租户列表、切换租户、当前用户 |
| SSO | `/api/sso` | SSO 登录回调 |
| 租户 | `/api/tenants` | 租户 CRUD、成员列表（仅系统管理员） |
| 用户 | `/api/users` | 用户管理（系统管理员 + 租户管理员） |
| 角色 | `/api/roles` | 角色管理 + 权限分配（系统管理员 + 租户管理员） |
| 权限 | `/api/permissions` | 权限树（只读） |
| 资产 | `/api/assets` | CRUD + 派发/借用/归还/退库/变更 |
| 资产参数 | `/api/asset-params` | 字典管理 |
| 工作台 | `/api/dashboard` | 统计数据 |
| 日志 | `/api/operation-logs` | 操作日志 |
| 开通接口 | `/open-api/app/tenants` | 平台调用，自动开通租户和用户 |

## 生产部署

### 方式一：Gunicorn + Nginx

```bash
# 1. 构建前端
cd frontend && npm run build

# 2. 安装生产依赖
cd backend
pip install gunicorn

# 3. 配置环境变量（见上方「环境变量」章节）
export FLASK_ENV=production
export SECRET_KEY=...
export JWT_SECRET=...

# 4. 启动后端（4 worker 进程）
gunicorn -w 4 -b 127.0.0.1:5001 "app:create_app()"
```

### Nginx 配置参考

```nginx
server {
    listen 80;
    server_name your-domain.example;

    # 前端静态文件
    root /path/to/FAMS/frontend/dist;
    index index.html;

    # 前端路由（history 模式）
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Open API 反向代理（供算力网络平台调用）
    location /open-api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

> **注意**：平台使用 HTTP 协议，iframe 打开 HTTPS 会受限，因此应用默认地址和开通地址需使用 HTTP。

### 方式二：Docker（可选）

```dockerfile
# Dockerfile 示例（后端）
FROM python:3.12-slim
WORKDIR /app
COPY backend/ .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
EXPOSE 5001
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "app:create_app()"]
```

## 运行测试

```bash
cd backend
source venv/bin/activate
pytest
```

## 安全措施

- JWT Token 含 `jti`（唯一 ID），登出时加入黑名单
- 登录失败计数，超过阈值临时锁定账号
- 三层 RBAC 权限控制，`role_required` 装饰器统一校验
- 多租户数据隔离，系统管理员无租户时安全降级
- SSO/Open API 接口通过 `appKey + appSecret` 双重验证
- 心跳接口使用 HMAC-SHA256 签名认证
- CORS 白名单，仅允许配置的源
- 密码 Bcrypt 哈希，不明文存储
- 生产环境强制通过环境变量配置密钥
- 分页查询 `per_page` 上限 100

## License

MIT
