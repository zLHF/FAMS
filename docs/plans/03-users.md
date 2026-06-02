# 03 — 用户管理模块

> **依赖:** 02-auth
> **目标:** 用户 CRUD API + 前端用户管理页面（参照原型 users.html）。

---

## Task 1: 后端权限装饰器

**Files:**
- Create: `backend/app/utils/decorators.py`

**Step 1: 创建登录验证装饰器**

```python
from functools import wraps
from flask import request, jsonify
from ..utils.auth import decode_token
from ..models.user import User

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "未登录"}), 401
        token = auth_header[7:]
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "登录已过期"}), 401
        user = User.query.get(payload["user_id"])
        if not user or user.status == "disabled":
            return jsonify({"error": "用户不可用"}), 401
        request.current_user = user
        return f(*args, **kwargs)
    return decorated
```

**Step 2: Commit**

```bash
git add backend/app/utils/decorators.py
git commit -m "feat: add login_required decorator"
```

---

## Task 2: 后端用户 CRUD API

**Files:**
- Create: `backend/app/api/users.py`
- Modify: `backend/app/api/__init__.py`

**Step 1: 创建 users.py**

```python
from flask import Blueprint, request, jsonify
from ..extensions import db, bcrypt
from ..models.user import User
from ..models.operation_log import OperationLog
from ..utils.decorators import login_required

users_bp = Blueprint("users", __name__, url_prefix="/api/users")

@users_bp.route("", methods=["GET"])
@login_required
def list_users():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    name = request.args.get("name", "")
    role_id = request.args.get("role_id", type=int)
    status = request.args.get("status", "")

    query = User.query
    if name:
        query = query.filter(User.name.contains(name) | User.username.contains(name))
    if role_id:
        query = query.filter_by(role_id=role_id)
    if status:
        query = query.filter_by(status=status)

    pag = query.order_by(User.id).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [_user_dict(u) for u in pag.items],
        "total": pag.total,
        "page": pag.page,
        "per_page": pag.per_page,
    })

@users_bp.route("", methods=["POST"])
@login_required
def create_user():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("name") or not data.get("role_id"):
        return jsonify({"error": "缺少必填字段"}), 400
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "用户账号已存在"}), 400

    user = User(
        username=data["username"],
        password_hash=bcrypt.generate_password_hash(data.get("password", "123456")).decode("utf-8"),
        name=data["name"],
        phone=data.get("phone"),
        department=data.get("department"),
        role_id=data["role_id"],
        status=data.get("status", "active"),
    )
    db.session.add(user)
    _log(request.current_user.id, "create", "user", user.id, f"新增用户 {user.username}")
    db.session.commit()
    return jsonify(_user_dict(user)), 201

@users_bp.route("/<int:id>", methods=["PUT"])
@login_required
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json()
    if data.get("name"): user.name = data["name"]
    if data.get("phone") is not None: user.phone = data["phone"]
    if data.get("department") is not None: user.department = data["department"]
    if data.get("role_id"): user.role_id = data["role_id"]
    if data.get("status"): user.status = data["status"]
    if data.get("password"):
        user.password_hash = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    _log(request.current_user.id, "update", "user", user.id, f"修改用户 {user.username}")
    db.session.commit()
    return jsonify(_user_dict(user))

@users_bp.route("/<int:id>", methods=["DELETE"])
@login_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.username == "admin":
        return jsonify({"error": "不能删除管理员账号"}), 400
    _log(request.current_user.id, "delete", "user", user.id, f"删除用户 {user.username}")
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "删除成功"})

def _user_dict(u):
    return {
        "id": u.id, "username": u.username, "name": u.name,
        "phone": u.phone, "department": u.department,
        "role_id": u.role_id, "role_name": u.role.name if u.role else None,
        "status": u.status,
    }

def _log(user_id, action, target_type, target_id, detail):
    db.session.add(OperationLog(user_id=user_id, action=action, target_type=target_type, target_id=target_id, detail=detail))
```

**Step 2: 注册蓝图**

在 `backend/app/api/__init__.py` 追加：

```python
from .users import users_bp
app.register_blueprint(users_bp)
```

**Step 3: 写测试 tests/test_users.py**

```python
from app.extensions import db, bcrypt
from app.models.user import User
from app.models.role import Role

def setup_data(db):
    role = Role(name="管理员", code="admin", status="active")
    db.session.add(role)
    db.session.flush()
    user = User(username="admin", password_hash=bcrypt.generate_password_hash("123456").decode(), name="管理员", role_id=role.id, status="active")
    db.session.add(user)
    db.session.commit()
    return user, role

def get_token(client, username="admin", password="123456"):
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    return resp.get_json()["token"]

def headers(token):
    return {"Authorization": f"Bearer {token}"}

def test_list_users(client, db, app):
    with app.app_context():
        user, _ = setup_data(db)
    token = get_token(client)
    resp = client.get("/api/users", headers=headers(token))
    assert resp.status_code == 200
    assert resp.get_json()["total"] >= 1

def test_create_user(client, db, app):
    with app.app_context():
        user, role = setup_data(db)
    token = get_token(client)
    resp = client.post("/api/users", json={
        "username": "newuser", "name": "新用户", "password": "123456", "role_id": role.id
    }, headers=headers(token))
    assert resp.status_code == 201
    assert resp.get_json()["username"] == "newuser"

def test_create_duplicate_user(client, db, app):
    with app.app_context():
        setup_data(db)
    token = get_token(client)
    resp = client.post("/api/users", json={"username": "admin", "name": "重复", "role_id": 1}, headers=headers(token))
    assert resp.status_code == 400

def test_update_user(client, db, app):
    with app.app_context():
        user, role = setup_data(db)
    token = get_token(client)
    resp = client.put(f"/api/users/{user.id}", json={"name": "改名"}, headers=headers(token))
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "改名"
```

**Step 4: 运行测试**

```bash
python -m pytest tests/test_users.py -v
```

Expected: 4 tests PASSED

**Step 5: Commit**

```bash
git add backend/
git commit -m "feat: add user CRUD API with pagination, search, and tests"
```

---

## Task 3: 前端 — 用户管理页面

**Files:**
- Create: `frontend/src/api/users.js`
- Create: `frontend/src/views/Users.vue`
- Modify: `frontend/src/router/index.js`

**Step 1: 创建 api/users.js**

```javascript
import http from './index'

export function getUsers(params) {
  return http.get('/users', { params })
}

export function createUser(data) {
  return http.post('/users', data)
}

export function updateUser(id, data) {
  return http.put(`/users/${id}`, data)
}

export function deleteUser(id) {
  return http.delete(`/users/${id}`)
}
```

**Step 2: 创建 api/roles.js（用户管理需要角色下拉）**

```javascript
import http from './index'

export function getRoles(params) {
  return http.get('/roles', { params })
}
```

**Step 3: 创建 views/Users.vue（参照原型 users.html）**

```vue
<template>
  <div style="padding:24px;">
    <!-- 搜索栏 -->
    <el-card style="margin-bottom:16px;">
      <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end;">
        <el-input v-model="filters.name" placeholder="用户姓名/账号" clearable style="width:200px;" />
        <el-select v-model="filters.status" placeholder="状态" clearable style="width:140px;">
          <el-option label="启用" value="active" />
          <el-option label="停用" value="disabled" />
        </el-select>
        <el-button @click="loadData">查询</el-button>
        <el-button type="primary" style="background:#16805f;border-color:#16805f;" @click="openDialog()">新增用户</el-button>
      </div>
    </el-card>

    <!-- 表格 -->
    <el-card>
      <el-table :data="tableData" stripe>
        <el-table-column prop="username" label="账号" />
        <el-table-column prop="name" label="姓名" />
        <el-table-column prop="department" label="部门" />
        <el-table-column prop="role_name" label="角色" />
        <el-table-column prop="phone" label="手机号" />
        <el-table-column label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'">{{ row.status === 'active' ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">修改</el-button>
            <el-button link :type="row.status === 'active' ? 'warning' : 'success'" @click="toggleStatus(row)">
              {{ row.status === 'active' ? '停用' : '启用' }}
            </el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="display:flex;justify-content:flex-end;margin-top:16px;">
        <el-pagination background layout="total, prev, pager, next" :total="total" :page-size="filters.per_page" v-model:current-page="filters.page" @current-change="loadData" />
      </div>
    </el-card>

    <!-- 新增/修改弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editingUser ? '修改用户' : '新增用户'" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户账号" required>
          <el-input v-model="form.username" :disabled="!!editingUser" />
        </el-form-item>
        <el-form-item label="用户姓名" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="所属部门">
          <el-input v-model="form.department" />
        </el-form-item>
        <el-form-item label="角色" required>
          <el-select v-model="form.role_id" placeholder="请选择角色" style="width:100%;">
            <el-option v-for="r in roleOptions" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!editingUser" label="密码">
          <el-input v-model="form.password" type="password" placeholder="默认 123456" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.statusBool" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" style="background:#16805f;border-color:#16805f;" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getUsers, createUser, updateUser, deleteUser } from '../api/users'
import { getRoles } from '../api/roles'
import { ElMessage, ElMessageBox } from 'element-plus'

const filters = ref({ name: '', status: '', page: 1, per_page: 10 })
const tableData = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const editingUser = ref(null)
const roleOptions = ref([])
const form = ref({ username: '', name: '', phone: '', department: '', role_id: '', password: '', statusBool: true })

async function loadData() {
  const res = await getUsers(filters.value)
  tableData.value = res.items
  total.value = res.total
}

async function loadRoles() {
  const res = await getRoles({ per_page: 100 })
  roleOptions.value = res.items
}

function openDialog(user = null) {
  editingUser.value = user
  if (user) {
    form.value = { ...user, statusBool: user.status === 'active', password: '' }
  } else {
    form.value = { username: '', name: '', phone: '', department: '', role_id: '', password: '', statusBool: true }
  }
  dialogVisible.value = true
}

async function handleSave() {
  const data = { ...form.value, status: form.value.statusBool ? 'active' : 'disabled' }
  delete data.statusBool
  if (editingUser.value) {
    await updateUser(editingUser.value.id, data)
    ElMessage.success('修改成功')
  } else {
    await createUser(data)
    ElMessage.success('新增成功')
  }
  dialogVisible.value = false
  loadData()
}

async function toggleStatus(user) {
  const newStatus = user.status === 'active' ? 'disabled' : 'active'
  await updateUser(user.id, { status: newStatus })
  ElMessage.success(newStatus === 'active' ? '已启用' : '已停用')
  loadData()
}

async function handleDelete(user) {
  await ElMessageBox.confirm(`确认删除用户 "${user.name}"？`, '删除确认', { type: 'warning' })
  await deleteUser(user.id)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(() => { loadData(); loadRoles() })
</script>
```

**Step 4: 注册路由 — 在 router/index.js routes 数组追加**

```javascript
{ path: '/users', name: 'Users', component: () => import('../views/Users.vue') },
```

**Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: add Users management page with CRUD dialog and pagination"
```

---

## ✅ 完成标准

- [ ] `GET /api/users` 分页 + 搜索返回用户列表
- [ ] `POST /api/users` 创建用户，重复账号报 400
- [ ] `PUT /api/users/:id` 修改用户信息
- [ ] `DELETE /api/users/:id` 删除用户
- [ ] 前端用户管理页面完整可用
- [ ] 后端 4 个测试通过
