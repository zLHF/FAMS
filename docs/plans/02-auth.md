# 02 — 登录认证模块

> **依赖:** 01-scaffolding
> **目标:** JWT 登录/登出，前端登录页 + 路由守卫 + Axios 拦截器。

---

## Task 1: 后端 JWT 工具函数

**Files:**
- Create: `backend/app/utils/auth.py`

**Step 1: 创建 JWT 工具**

```python
import jwt
from datetime import datetime, timedelta, timezone
from ..config import Config

def generate_token(user_id, role_code=""):
    payload = {
        "user_id": user_id,
        "role_code": role_code,
        "exp": datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")

def decode_token(token):
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
```

**Step 2: Commit**

```bash
git add backend/app/utils/auth.py
git commit -m "feat: add JWT token generate/decode utilities"
```

---

## Task 2: 后端登录/登出 API

**Files:**
- Create: `backend/app/api/auth.py`
- Modify: `backend/app/api/__init__.py`

**Step 1: 创建 auth.py**

```python
from flask import Blueprint, request, jsonify
from ..extensions import db, bcrypt
from ..models.user import User
from ..models.operation_log import OperationLog
from ..utils.auth import generate_token, decode_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = (data or {}).get("username", "").strip()
    password = (data or {}).get("password", "")

    if not username or not password:
        return jsonify({"error": "账号和密码不能为空"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "账号或密码错误"}), 401

    if user.status == "disabled":
        return jsonify({"error": "该账号已停用"}), 403

    role_code = user.role.code if user.role else ""
    token = generate_token(user.id, role_code)

    # 记录登录日志
    log = OperationLog(user_id=user.id, action="login", target_type="user", target_id=user.id, detail="用户登录")
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "role": role_code,
            "department": user.department,
        }
    })

@auth_bp.route("/logout", methods=["POST"])
def logout():
    # JWT 无状态，前端清除即可；可选记录日志
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    payload = decode_token(token) if token else None
    if payload:
        log = OperationLog(user_id=payload["user_id"], action="logout", target_type="user", target_id=payload["user_id"], detail="用户登出")
        db.session.add(log)
        db.session.commit()
    return jsonify({"message": "已登出"})

@auth_bp.route("/me", methods=["GET"])
def me():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    payload = decode_token(token)
    if not payload:
        return jsonify({"error": "未登录或登录已过期"}), 401

    user = User.query.get(payload["user_id"])
    if not user or user.status == "disabled":
        return jsonify({"error": "用户不存在或已停用"}), 401

    role_code = user.role.code if user.role else ""
    return jsonify({
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "role": role_code,
        "department": user.department,
    })
```

**Step 2: 注册蓝图到 api/__init__.py**

```python
def register_blueprints(app):
    from .auth import auth_bp
    app.register_blueprint(auth_bp)
```

**Step 3: 写测试 tests/conftest.py**

```python
import pytest
from app import create_app
from app.extensions import db as _db

@pytest.fixture(scope="function")
def app():
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.config["TESTING"] = True
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db(app):
    return _db
```

**Step 4: 写测试 tests/test_auth.py**

```python
import json
from app.extensions import db, bcrypt
from app.models.user import User
from app.models.role import Role

def setup_admin(db):
    role = Role(name="系统管理员", code="admin", status="active")
    db.session.add(role)
    db.session.flush()
    user = User(
        username="admin",
        password_hash=bcrypt.generate_password_hash("123456").decode("utf-8"),
        name="管理员",
        role_id=role.id,
        status="active",
    )
    db.session.add(user)
    db.session.commit()
    return user

def test_login_success(client, db, app):
    with app.app_context():
        setup_admin(db)
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "123456"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "token" in data
    assert data["user"]["username"] == "admin"

def test_login_wrong_password(client, db, app):
    with app.app_context():
        setup_admin(db)
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401

def test_login_missing_fields(client):
    resp = client.post("/api/auth/login", json={"username": ""})
    assert resp.status_code == 400

def test_me_with_valid_token(client, db, app):
    with app.app_context():
        user = setup_admin(db)
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "123456"})
    token = resp.get_json()["token"]
    resp2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    assert resp2.get_json()["username"] == "admin"
```

**Step 5: 运行测试**

```bash
cd /Users/liuhanfei/Projects/FAMS/固定资产管理系统/backend
source venv/bin/activate
python -m pytest tests/test_auth.py -v
```

Expected: 4 tests PASSED

**Step 6: Commit**

```bash
git add backend/
git commit -m "feat: add login/logout/me API with JWT auth and tests"
```

---

## Task 3: 前端 — API 封装 + Axios 拦截器

**Files:**
- Create: `frontend/src/api/index.js`
- Create: `frontend/src/api/auth.js`
- Create: `frontend/src/stores/auth.js`

**Step 1: 创建 api/index.js**

```javascript
import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const http = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('fams_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.error || '请求失败'
    if (err.response?.status === 401) {
      localStorage.removeItem('fams_token')
      localStorage.removeItem('fams_user')
      router.push('/login')
    }
    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

export default http
```

**Step 2: 创建 api/auth.js**

```javascript
import http from './index'

export function login(data) {
  return http.post('/auth/login', data)
}

export function logout() {
  return http.post('/auth/logout')
}

export function getMe() {
  return http.get('/auth/me')
}
```

**Step 3: 创建 stores/auth.js (Pinia)**

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi, logout as logoutApi, getMe } from '../api/auth'
import router from '../router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('fams_user') || 'null'))
  const token = ref(localStorage.getItem('fams_token') || '')

  async function login(username, password) {
    const res = await loginApi({ username, password })
    token.value = res.token
    user.value = res.user
    localStorage.setItem('fams_token', res.token)
    localStorage.setItem('fams_user', JSON.stringify(res.user))
    return res
  }

  async function logout() {
    try { await logoutApi() } catch {}
    token.value = ''
    user.value = null
    localStorage.removeItem('fams_token')
    localStorage.removeItem('fams_user')
    router.push('/login')
  }

  async function fetchUser() {
    try {
      const res = await getMe()
      user.value = res
      localStorage.setItem('fams_user', JSON.stringify(res))
    } catch {
      token.value = ''
      user.value = null
      localStorage.removeItem('fams_token')
      localStorage.removeItem('fams_user')
    }
  }

  return { user, token, login, logout, fetchUser }
})
```

**Step 4: Commit**

```bash
git add frontend/src/api frontend/src/stores
git commit -m "feat: add frontend auth API, Pinia store, axios interceptors"
```

---

## Task 4: 前端 — 登录页 + 路由守卫

**Files:**
- Create: `frontend/src/views/Login.vue`
- Modify: `frontend/src/router/index.js`

**Step 1: 创建 Login.vue（参照原型 index.html 的设计）**

```vue
<template>
  <div class="login-page">
    <div class="login-shell">
      <!-- 左侧视觉区 -->
      <div class="login-visual">
        <div class="brand-row">
          <div style="width:42px;height:42px;border-radius:8px;background:#21a67a;display:grid;place-items:center;color:#fff;font-weight:800;">资</div>
          <div><strong style="color:#fff">固定资产管理系统</strong><br><span>Fixed Asset Management</span></div>
        </div>
        <h1 style="color:#fff;font-size:34px;line-height:1.3;">企业固定资产<br>数字化管理平台</h1>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
          <div style="background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);border-radius:8px;padding:14px;">
            <b style="color:#fff;font-size:24px;">1286</b><br><span style="color:#bcccdc;font-size:12px;">资产总数</span>
          </div>
          <div style="background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);border-radius:8px;padding:14px;">
            <b style="color:#fff;font-size:24px;">86</b><br><span style="color:#bcccdc;font-size:12px;">闲置资产</span>
          </div>
          <div style="background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);border-radius:8px;padding:14px;">
            <b style="color:#fff;font-size:24px;">42</b><br><span style="color:#bcccdc;font-size:12px;">借用中</span>
          </div>
        </div>
      </div>
      <!-- 右侧登录表单 -->
      <div class="login-card">
        <h2>欢迎登录</h2>
        <p style="color:#7b8794">请输入账号和密码</p>
        <el-form :model="form" @submit.prevent="handleLogin" style="margin-top:20px;">
          <el-form-item>
            <el-input v-model="form.username" placeholder="请输入账号" size="large" prefix-icon="User" />
          </el-form-item>
          <el-form-item>
            <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large" prefix-icon="Lock" show-password />
          </el-form-item>
          <el-button type="primary" size="large" style="width:100%;background:#16805f;border-color:#16805f;" :loading="loading" native-type="submit">
            登录系统
          </el-button>
        </el-form>
        <p style="color:#7b8794;font-size:13px;margin-top:16px;">演示账号：admin / 123456</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const router = useRouter()
const loading = ref(false)
const form = ref({ username: 'admin', password: '123456' })

async function handleLogin() {
  if (!form.value.username || !form.value.password) {
    return ElMessage.warning('请输入账号和密码')
  }
  loading.value = true
  try {
    await auth.login(form.value.username, form.value.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e) {
    // 错误已由拦截器处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page { min-height:100vh; display:grid; place-items:center; background:linear-gradient(135deg,#102a43,#243b53 48%,#1f513f); padding:28px; }
.login-shell { width:min(980px,100%); display:grid; grid-template-columns:1.15fr .85fr; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 28px 80px rgba(0,0,0,.25); }
.login-visual { background:#17212f; color:#fff; padding:42px; display:flex; flex-direction:column; justify-content:space-between; min-height:520px; }
.login-card { padding:46px 38px; display:grid; align-content:center; gap:6px; }
.brand-row { display:flex; gap:12px; align-items:center; }
.brand-row span { color:#bcccdc; font-size:13px; }
@media(max-width:900px){ .login-shell{grid-template-columns:1fr;} .login-visual{min-height:auto;display:none;} }
</style>
```

**Step 2: 更新 router/index.js — 添加路由守卫**

```javascript
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { public: true } },
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  // 后续模块的路由在此追加
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const token = localStorage.getItem('fams_token')
  if (!to.meta?.public && !token) {
    return { path: '/login' }
  }
})

export default router
```

**Step 3: 创建 Dashboard.vue 占位**

```vue
<template>
  <div style="padding:24px;">
    <h1>工作台</h1>
    <p>仪表盘 — 后续模块实现</p>
    <el-button @click="auth.logout()">退出登录</el-button>
  </div>
</template>

<script setup>
import { useAuthStore } from '../stores/auth'
const auth = useAuthStore()
</script>
```

**Step 4: 验证 — 启动前后端，测试登录流程**

```bash
# 终端1: 后端
cd /Users/liuhanfei/Projects/FAMS/固定资产管理系统/backend
source venv/bin/activate
python run.py

# 终端2: 前端
cd /Users/liuhanfei/Projects/FAMS/固定资产管理系统/frontend
npm run dev
```

1. 访问 http://localhost:5173 → 自动跳转到 /login
2. 输入 admin / 123456（需先有种子数据，见 Task 5）
3. 登录成功 → 跳转到 / 显示"工作台"

**Step 5: Commit**

```bash
git add frontend/src/views frontend/src/router
git commit -m "feat: add Login page with route guard and Dashboard placeholder"
```

---

## Task 5: 种子数据脚本

**Files:**
- Create: `backend/seed.py`

**Step 1: 创建 seed.py**

```python
"""初始化种子数据：管理员角色 + 管理员账号 + 权限树 + 基础参数"""
from app import create_app
from app.extensions import db, bcrypt
from app.models.role import Role
from app.models.permission import Permission
from app.models.user import User
from app.models.asset_param import AssetParam

def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        # 权限树
        perms = [
            {"name": "工作台", "code": "dashboard"},
            {"name": "人员管理", "code": "personnel"},
            {"name": "用户管理", "code": "users", "parent": "personnel"},
            {"name": "角色管理", "code": "roles", "parent": "personnel"},
            {"name": "权限管理", "code": "permissions", "parent": "personnel"},
            {"name": "基础参数设置", "code": "asset_params"},
            {"name": "固定资产管理", "code": "assets"},
            {"name": "资产台账", "code": "asset_list", "parent": "assets"},
            {"name": "资产派发", "code": "asset_distribute", "parent": "assets"},
            {"name": "资产借用", "code": "asset_borrow", "parent": "assets"},
            {"name": "借用归还", "code": "asset_return", "parent": "assets"},
            {"name": "领用退库", "code": "asset_revert", "parent": "assets"},
            {"name": "变更领用人", "code": "asset_owner_change", "parent": "assets"},
        ]
        perm_map = {}
        for p in perms:
            parent = perm_map.get(p.get("parent"))
            obj = Permission(name=p["name"], code=p["code"], parent_id=parent.id if parent else None)
            db.session.add(obj)
            db.session.flush()
            perm_map[p["code"]] = obj

        # 角色
        admin_role = Role(name="系统管理员", code="admin", status="active")
        asset_role = Role(name="资产管理员", code="asset_manager", status="active")
        db.session.add_all([admin_role, asset_role])
        db.session.flush()

        # 管理员拥有全部权限
        for p in perm_map.values():
            db.session.execute(
                db.table("role_permissions").insert().values(role_id=admin_role.id, permission_id=p.id)
            )

        # 管理员账号
        user = User(
            username="admin",
            password_hash=bcrypt.generate_password_hash("123456").decode("utf-8"),
            name="管理员",
            role_id=admin_role.id,
            status="active",
        )
        db.session.add(user)

        # 基础参数
        params = [
            ("category", "电脑设备", "computer"), ("category", "办公家具", "furniture"),
            ("category", "网络设备", "network"), ("category", "办公电器", "appliance"),
            ("brand", "联想", "lenovo"), ("brand", "戴尔", "dell"),
            ("brand", "惠普", "hp"), ("brand", "苹果", "apple"),
            ("unit", "台", "tai"), ("unit", "个", "ge"), ("unit", "套", "tao"), ("unit", "张", "zhang"),
            ("location", "总部库房", "hq_warehouse"), ("location", "财务部", "finance"),
            ("location", "研发部", "rd"), ("location", "会议室", "meeting"),
        ]
        for idx, (t, n, c) in enumerate(params):
            db.session.add(AssetParam(type=t, name=n, code=c, sort_order=idx, status="active"))

        db.session.commit()
        print("✅ 种子数据初始化完成")

if __name__ == "__main__":
    seed()
```

**Step 2: 运行种子数据**

```bash
cd /Users/liuhanfei/Projects/FAMS/固定资产管理系统/backend
source venv/bin/activate
python seed.py
```

Expected: 输出 "✅ 种子数据初始化完成"

**Step 3: Commit**

```bash
git add backend/seed.py
git commit -m "feat: add seed data script with admin user, roles, permissions, params"
```

---

## ✅ 完成标准

- [ ] `POST /api/auth/login` 返回 JWT token
- [ ] `GET /api/auth/me` 用 token 返回用户信息
- [ ] 错误密码返回 401
- [ ] 前端登录页可正常登录跳转
- [ ] 未登录访问首页自动跳转 /login
- [ ] 4 个后端测试全部通过
