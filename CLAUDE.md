# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FAMS（固定资产管理系统）— 企业级多租户固定资产管理平台，支持算力网络分布式管理平台 SSO 集成。

## Commands

```bash
# 后端 (在 backend/ 目录下)
source venv/bin/activate
python run.py                    # 启动开发服务器 (port 5001)
python seed.py                   # 重新初始化种子数据 (会清空数据库)
flask db migrate -m "描述"       # 生成数据库迁移
flask db upgrade                 # 执行迁移
pytest                           # 运行测试

# 前端 (在 frontend/ 目录下)
npm run dev                      # 启动开发服务器 (port 5173)
npm run build                    # 生产构建
```

## Architecture

### Three-Layer RBAC

| Role | Code | Scope | Description |
|------|------|-------|-------------|
| 系统管理员 | `system_admin` | 全局 | 不属于任何租户，可切换到所有租户管理，由 `User.role_id` 关联全局角色 (`tenant_id=NULL`) |
| 租户管理员 | `tenant_admin` | 租户内 | 管理本租户用户和配置，由 `TenantMembership.role_id` 关联租户角色 |
| 资产管理员 | `asset_manager` | 租户内 | 资产日常操作，无用户管理权限 |

**关键机制**：系统管理员通过 `decorators._is_system_admin(user)` 判断，`role_required` 装饰器对系统管理员始终放行。系统管理员切换租户时自动创建临时 `TenantMembership`。

### Backend (Flask)

- **App Factory**: `app/__init__.py:create_app()` — 注册所有蓝图、启动心跳任务
- **Blueprints**: `app/api/` — 每个模块一个蓝图，通过 `register_blueprints(app)` 统一注册
- **Models**: `app/models/` — SQLAlchemy models，所有业务模型都有 `tenant_id` 实现租户隔离
- **Auth Flow**: JWT token 包含 `user_id, role_code, tenant_id, membership_id`；`decorators._load_auth_context()` 加载请求上下文到 `request.current_user/tenant/membership/role`
- **Tenant Isolation**: 所有依赖租户的 API 通过 `_current_tenant_id()` 过滤数据；系统管理员无租户时返回空数据

### Frontend (Vue 3)

- **HTTP Client**: `src/api/index.js` — axios 实例，`baseURL='/api'`，自动附加 Bearer token
- **Auth Store**: `src/stores/auth.js` — Pinia store，管理 token/user/tenant 状态，持久化到 localStorage
- **Router Guards**: `src/router/index.js` — 检查 token 和 SSO code 参数
- **Sidebar Menu**: `src/components/Sidebar.vue` — 根据 `system_admin/tenant_admin` 角色显示管理菜单

### SSO Integration (算力网络平台)

通过环境变量配置（`PLATFORM_APP_ID`, `PLATFORM_APP_SECRET`, `PLATFORM_BASE_URL`, `PLATFORM_APP_CODE`），由 `SSO_ENABLED` 和 `HEARTBEAT_ENABLED` 开关控制。

- **Open API** (`/open-api/app/tenants`) — 平台调用，自动开通租户和用户
- **SSO Callback** (`/api/sso/callback`) — 前端回调，调用平台 `appAuthCheck` + `getUserInfoByToken` 完成自动登录
- **Heartbeat** (`utils/heartbeat.py`) — APScheduler 定时任务，5 分钟一次
- **Signature** (`utils/signature.py`) — HMAC-SHA256 签名，拼接格式 `x-body={md5}&x-random={random}&x-time={timestamp}`

## Key Patterns

- **响应格式**: 后端 API 返回 `{"error": "..."}` (错误) 或 `{"items": [], "total": N}` (列表)，SSO/Open API 返回 `{"code": 20000, "msg": "...", "data": {...}}` (平台格式)
- **权限装饰器**: `@login_required` → `@role_required("system_admin", "tenant_admin")`，系统管理员始终放行
- **租户安全降级**: `_current_tenant_id()` 返回 None 时，列表 API 返回空数据不崩溃
- **用户创建**: SSO/Open API 创建用户时用户名加 `plt_` 前缀，标记 `sso_user=True`
