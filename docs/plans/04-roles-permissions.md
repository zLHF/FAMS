# 04 — 角色权限管理模块

> **依赖:** 03-users
> **目标:** 角色 CRUD + 权限树 + 角色分配权限 + 前端菜单按权限显示。

---

## Task 1: 后端角色 CRUD API

**Files:**
- Create: `backend/app/api/roles.py`
- Modify: `backend/app/api/__init__.py`

**Step 1: 创建 roles.py**

```python
from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.role import Role
from ..models.permission import Permission
from ..models.user import User
from ..models.operation_log import OperationLog
from ..utils.decorators import login_required

roles_bp = Blueprint("roles", __name__, url_prefix="/api/roles")

@roles_bp.route("", methods=["GET"])
@login_required
def list_roles():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    name = request.args.get("name", "")
    status = request.args.get("status", "")
    query = Role.query
    if name:
        query = query.filter(Role.name.contains(name))
    if status:
        query = query.filter_by(status=status)
    pag = query.order_by(Role.id).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [{"id": r.id, "name": r.name, "code": r.code, "description": r.description, "status": r.status} for r in pag.items],
        "total": pag.total, "page": pag.page, "per_page": pag.per_page,
    })

@roles_bp.route("", methods=["POST"])
@login_required
def create_role():
    data = request.get_json()
    if not data or not data.get("name") or not data.get("code"):
        return jsonify({"error": "缺少必填字段"}), 400
    if Role.query.filter_by(name=data["name"]).first():
        return jsonify({"error": "角色名称已存在"}), 400
    role = Role(name=data["name"], code=data["code"], description=data.get("description"), status=data.get("status", "active"))
    db.session.add(role)
    db.session.commit()
    return jsonify({"id": role.id, "name": role.name}), 201

@roles_bp.route("/<int:id>", methods=["PUT"])
@login_required
def update_role(id):
    role = Role.query.get_or_404(id)
    data = request.get_json()
    if data.get("name"): role.name = data["name"]
    if data.get("description") is not None: role.description = data["description"]
    if data.get("status"): role.status = data["status"]
    db.session.commit()
    return jsonify({"id": role.id, "name": role.name})

@roles_bp.route("/<int:id>", methods=["DELETE"])
@login_required
def delete_role(id):
    role = Role.query.get_or_404(id)
    if User.query.filter_by(role_id=id).count() > 0:
        return jsonify({"error": "该角色已绑定用户，无法删除"}), 400
    db.session.delete(role)
    db.session.commit()
    return jsonify({"message": "删除成功"})

@roles_bp.route("/<int:id>/permissions", methods=["PUT"])
@login_required
def assign_permissions(id):
    role = Role.query.get_or_404(id)
    data = request.get_json()
    perm_ids = data.get("permission_ids", [])
    from ..models.role import role_permissions
    db.session.execute(role_permissions.delete().where(role_permissions.c.role_id == id))
    for pid in perm_ids:
        db.session.execute(role_permissions.insert().values(role_id=id, permission_id=pid))
    db.session.commit()
    return jsonify({"message": "权限分配成功"})
```

**Step 2: 注册蓝图**

在 `backend/app/api/__init__.py` 追加：

```python
from .roles import roles_bp
app.register_blueprint(roles_bp)
```

**Step 3: Commit**

```bash
git add backend/
git commit -m "feat: add role CRUD API and permission assignment endpoint"
```

---

## Task 2: 后端权限树 API

**Files:**
- Create: `backend/app/api/permissions.py`
- Modify: `backend/app/api/__init__.py`

**Step 1: 创建 permissions.py**

```python
from flask import Blueprint, jsonify
from ..models.permission import Permission
from ..models.role import role_permissions
from ..utils.decorators import login_required

perms_bp = Blueprint("permissions", __name__, url_prefix="/api/permissions")

@perms_bp.route("/tree", methods=["GET"])
@login_required
def permission_tree():
    perms = Permission.query.order_by(Permission.sort_order).all()
    return jsonify({"items": [_perm_dict(p) for p in perms]})

@perms_bp.route("/role/<int:role_id>", methods=["GET"])
@login_required
def role_permissions(role_id):
    rows = db.session.execute(
        role_permissions.select().where(role_permissions.c.role_id == role_id)
    ).fetchall()
    return jsonify({"permission_ids": [r.permission_id for r in rows]})

def _perm_dict(p):
    return {"id": p.id, "name": p.name, "code": p.code, "parent_id": p.parent_id, "sort_order": p.sort_order}
```

需在顶部加 `from ..extensions import db`

**Step 2: 注册蓝图 + Commit**

```python
from .permissions import perms_bp
app.register_blueprint(perms_bp)
```

```bash
git add backend/ && git commit -m "feat: add permission tree and role-permission query API"
```

---

## Task 3: 前端 — 角色管理页面

**Files:**
- Create: `frontend/src/views/Roles.vue`
- Complete: `frontend/src/api/roles.js`
- Modify: `frontend/src/router/index.js`

**Step 1: 完善 api/roles.js**

```javascript
import http from './index'

export function getRoles(params) { return http.get('/roles', { params }) }
export function createRole(data) { return http.post('/roles', data) }
export function updateRole(id, data) { return http.put(`/roles/${id}`, data) }
export function deleteRole(id) { return http.delete(`/roles/${id}`) }
export function assignPermissions(id, permission_ids) { return http.put(`/roles/${id}/permissions`, { permission_ids }) }
```

**Step 2: 创建 api/permissions.js**

```javascript
import http from './index'

export function getPermissionTree() { return http.get('/permissions/tree') }
export function getRolePermissions(roleId) { return http.get(`/permissions/role/${roleId}`) }
```

**Step 3: 创建 views/Roles.vue（参照原型 roles.html）**

```vue
<template>
  <div style="padding:24px;">
    <el-card style="margin-bottom:16px;">
      <div style="display:flex;gap:12px;align-items:flex-end;">
        <el-input v-model="filters.name" placeholder="角色名称" clearable style="width:200px;" />
        <el-select v-model="filters.status" placeholder="状态" clearable style="width:140px;">
          <el-option label="启用" value="active" /><el-option label="停用" value="disabled" />
        </el-select>
        <el-button @click="loadData">查询</el-button>
        <el-button type="primary" style="background:#16805f;border-color:#16805f;" @click="openDialog()">新增角色</el-button>
      </div>
    </el-card>
    <el-card>
      <el-table :data="tableData" stripe>
        <el-table-column prop="name" label="角色名称" />
        <el-table-column prop="code" label="角色编码" />
        <el-table-column prop="description" label="描述" />
        <el-table-column label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'">{{ row.status === 'active' ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">修改</el-button>
            <el-button link type="success" @click="openPermDialog(row)">分配权限</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/修改弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '修改角色' : '新增角色'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="角色名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="角色编码" required><el-input v-model="form.code" :disabled="!!editing" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" /></el-form-item>
        <el-form-item label="状态"><el-switch v-model="form.statusBool" active-text="启用" inactive-text="停用" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" style="background:#16805f;border-color:#16805f;" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 权限分配弹窗 -->
    <el-dialog v-model="permDialogVisible" title="分配权限" width="500px">
      <el-tree ref="treeRef" :data="permTree" :props="{ label: 'name', children: 'children' }" show-checkbox node-key="id" :default-checked-keys="checkedKeys" />
      <template #footer>
        <el-button @click="permDialogVisible = false">取消</el-button>
        <el-button type="primary" style="background:#16805f;border-color:#16805f;" @click="savePermissions">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getRoles, createRole, updateRole, deleteRole, assignPermissions } from '../api/roles'
import { getPermissionTree, getRolePermissions } from '../api/permissions'
import { ElMessage, ElMessageBox } from 'element-plus'

const filters = ref({ name: '', status: '' })
const tableData = ref([])
const dialogVisible = ref(false)
const editing = ref(null)
const form = ref({ name: '', code: '', description: '', statusBool: true })
const permDialogVisible = ref(false)
const permTree = ref([])
const checkedKeys = ref([])
const currentRole = ref(null)
const treeRef = ref(null)

async function loadData() {
  const res = await getRoles(filters.value)
  tableData.value = res.items
}

function openDialog(role = null) {
  editing.value = role
  form.value = role ? { ...role, statusBool: role.status === 'active' } : { name: '', code: '', description: '', statusBool: true }
  dialogVisible.value = true
}

async function handleSave() {
  const data = { ...form.value, status: form.value.statusBool ? 'active' : 'disabled' }
  if (editing.value) { await updateRole(editing.value.id, data) } else { await createRole(data) }
  ElMessage.success('保存成功')
  dialogVisible.value = false
  loadData()
}

async function handleDelete(role) {
  await ElMessageBox.confirm(`确认删除角色 "${role.name}"？`, '提示', { type: 'warning' })
  await deleteRole(role.id)
  ElMessage.success('删除成功')
  loadData()
}

async function openPermDialog(role) {
  currentRole.value = role
  const [treeRes, permRes] = await Promise.all([getPermissionTree(), getRolePermissions(role.id)])
  // 构建树
  const items = treeRes.items
  const map = {}
  items.forEach(i => { map[i.id] = { ...i, children: [] } })
  const roots = []
  items.forEach(i => {
    if (i.parent_id && map[i.parent_id]) { map[i.parent_id].children.push(map[i.id]) }
    else { roots.push(map[i.id]) }
  })
  permTree.value = roots
  // 只设置叶子节点的 checkedKeys
  const parentIds = new Set(items.filter(i => i.parent_id).map(i => i.parent_id))
  checkedKeys.value = permRes.permission_ids.filter(id => !parentIds.has(id) || !items.find(i => i.parent_id === id))
  permDialogVisible.value = true
}

async function savePermissions() {
  const checked = treeRef.value.getCheckedKeys(false)
  const halfChecked = treeRef.value.getHalfCheckedKeys()
  await assignPermissions(currentRole.value.id, [...checked, ...halfChecked])
  ElMessage.success('权限分配成功')
  permDialogVisible.value = false
}

onMounted(loadData)
</script>
```

**Step 4: 注册路由**

```javascript
{ path: '/roles', name: 'Roles', component: () => import('../views/Roles.vue') },
```

**Step 5: Commit**

```bash
git add frontend/src/ && git commit -m "feat: add Roles and Permissions management pages"
```

---

## Task 4: 前端 — 侧边栏按权限显示 + AppLayout

**Files:**
- Create: `frontend/src/components/AppLayout.vue`
- Create: `frontend/src/components/Sidebar.vue`
- Create: `frontend/src/components/Topbar.vue`
- Modify: `frontend/src/router/index.js`

**Step 1: 创建 Sidebar.vue（参照原型 sidebar）**

```vue
<template>
  <div class="sidebar">
    <div class="brand">
      <div class="brand-mark">资</div>
      <div><strong>固定资产管理</strong><span>Fixed Asset Management</span></div>
    </div>
    <nav class="nav">
      <router-link v-for="item in visibleMenus" :key="item.path" :to="item.path" :class="{ active: $route.path === item.path }">
        <span></span>{{ item.label }}
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

const allMenus = [
  { path: '/', label: '工作台', code: 'dashboard' },
  { path: '/users', label: '用户管理', code: 'users' },
  { path: '/roles', label: '角色管理', code: 'roles' },
  { path: '/permissions', label: '权限管理', code: 'permissions' },
  { path: '/asset-params', label: '资产参数设置', code: 'asset_params' },
  { path: '/assets', label: '固定资产台账', code: 'asset_list' },
  { path: '/asset-distribute', label: '资产派发', code: 'asset_distribute' },
  { path: '/asset-borrow', label: '资产借用', code: 'asset_borrow' },
  { path: '/asset-return', label: '借用归还', code: 'asset_return' },
  { path: '/asset-revert', label: '领用退库', code: 'asset_revert' },
  { path: '/asset-owner-change', label: '变更领用人', code: 'asset_owner_change' },
]

// admin 角色看全部，其他角色后续可对接权限接口
const visibleMenus = computed(() => {
  if (auth.user?.role === 'admin') return allMenus
  return allMenus // 后续可按权限过滤
})
</script>

<style scoped>
.sidebar { position:fixed; inset:0 auto 0 0; width:248px; background:#17212f; color:#d9e2ec; padding:20px 16px; overflow:auto; }
.brand { display:flex; gap:12px; align-items:center; padding:4px 4px 22px; }
.brand-mark { width:42px; height:42px; border-radius:8px; background:#21a67a; color:#fff; display:grid; place-items:center; font-weight:800; }
.brand strong { display:block; font-size:16px; color:#fff; }
.brand span { display:block; color:#9fb3c8; font-size:12px; margin-top:3px; }
.nav { display:grid; gap:6px; }
.nav a { display:flex; gap:10px; align-items:center; padding:11px 12px; border-radius:8px; color:#bcccdc; text-decoration:none; }
.nav a span { width:7px; height:7px; border-radius:50%; background:#7b8794; }
.nav a:hover, .nav a.active { background:#243447; color:#fff; }
.nav a.active span { background:#f5a623; }
</style>
```

**Step 2: 创建 Topbar.vue**

```vue
<template>
  <div class="topbar">
    <div>
      <h1>{{ title }}</h1>
      <p>{{ subtitle }}</p>
    </div>
    <div class="user-chip">{{ auth.user?.name || '未登录' }} <el-button link type="danger" @click="auth.logout()" style="margin-left:8px;">退出</el-button></div>
  </div>
</template>

<script setup>
import { useAuthStore } from '../stores/auth'
defineProps({ title: String, subtitle: String })
const auth = useAuthStore()
</script>

<style scoped>
.topbar { display:flex; align-items:center; justify-content:space-between; margin-bottom:22px; }
.topbar h1 { font-size:24px; margin:0 0 6px; }
.topbar p { margin:0; color:#66788a; }
.user-chip { background:#fff; border:1px solid #d9e2ec; border-radius:999px; padding:8px 14px; color:#334e68; }
</style>
```

**Step 3: 创建 AppLayout.vue**

```vue
<template>
  <Sidebar />
  <div class="main">
    <Topbar :title="title" :subtitle="subtitle" />
    <router-view />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './Sidebar.vue'
import Topbar from './Topbar.vue'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const auth = useAuthStore()

const titleMap = { '/': '工作台', '/users': '用户管理', '/roles': '角色管理', '/permissions': '权限管理', '/asset-params': '资产参数设置', '/assets': '固定资产台账', '/asset-distribute': '资产派发', '/asset-borrow': '资产借用', '/asset-return': '借用归还', '/asset-revert': '领用退库', '/asset-owner-change': '变更领用人' }
const title = computed(() => titleMap[route.path] || '固定资产管理系统')
const subtitle = computed(() => `欢迎，${auth.user?.name || ''}`)
</script>

<style scoped>
.main { margin-left:248px; min-height:100vh; padding:24px; background:#f4f6f8; }
</style>
```

**Step 4: 更新 router — 嵌套路由**

```javascript
const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('../components/AppLayout.vue'),
    children: [
      { path: '', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'users', name: 'Users', component: () => import('../views/Users.vue') },
      { path: 'roles', name: 'Roles', component: () => import('../views/Roles.vue') },
      { path: 'permissions', name: 'Permissions', component: () => import('../views/Permissions.vue') },
      { path: 'asset-params', name: 'AssetParams', component: () => import('../views/AssetParams.vue') },
      { path: 'assets', name: 'Assets', component: () => import('../views/Assets.vue') },
      { path: 'asset-distribute', name: 'AssetDistribute', component: () => import('../views/AssetDistribute.vue') },
      { path: 'asset-borrow', name: 'AssetBorrow', component: () => import('../views/AssetBorrow.vue') },
      { path: 'asset-return', name: 'AssetReturn', component: () => import('../views/AssetReturn.vue') },
      { path: 'asset-revert', name: 'AssetRevert', component: () => import('../views/AssetRevert.vue') },
      { path: 'asset-owner-change', name: 'AssetOwnerChange', component: () => import('../views/AssetOwnerChange.vue') },
    ],
  },
]
```

**Step 5: Commit**

```bash
git add frontend/src/ && git commit -m "feat: add AppLayout with Sidebar, Topbar, and nested routing"
```

---

## Task 5: 前端 — 权限管理页面

**Files:**
- Create: `frontend/src/views/Permissions.vue`

**Step 1: 创建 Permissions.vue（参照原型 permissions.html 的左右布局）**

```vue
<template>
  <div>
    <div class="permission-layout">
      <!-- 左侧角色选择 -->
      <el-card>
        <template #header>选择角色</template>
        <div v-for="r in roles" :key="r.id">
          <div class="role-option" :class="{ active: selectedRole?.id === r.id }" @click="selectRole(r)">
            {{ r.name }}
          </div>
        </div>
      </el-card>
      <!-- 右侧权限树 -->
      <el-card>
        <template #header>权限配置 — {{ selectedRole?.name || '请选择角色' }}</template>
        <el-tree v-if="selectedRole" ref="treeRef" :data="permTree" :props="{ label: 'name', children: 'children' }" show-checkbox node-key="id" :default-checked-keys="checkedKeys" />
        <p v-else style="color:#999;">请先在左侧选择一个角色</p>
        <div v-if="selectedRole" style="margin-top:16px;text-align:right;">
          <el-button type="primary" style="background:#16805f;border-color:#16805f;" @click="savePermissions">保存权限</el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getRoles, assignPermissions } from '../api/roles'
import { getPermissionTree, getRolePermissions } from '../api/permissions'
import { ElMessage } from 'element-plus'

const roles = ref([])
const selectedRole = ref(null)
const permTree = ref([])
const checkedKeys = ref([])
const treeRef = ref(null)

async function loadRoles() {
  const res = await getRoles({ per_page: 100 })
  roles.value = res.items
}

async function selectRole(role) {
  selectedRole.value = role
  const [treeRes, permRes] = await Promise.all([getPermissionTree(), getRolePermissions(role.id)])
  const items = treeRes.items
  const map = {}
  items.forEach(i => { map[i.id] = { ...i, children: [] } })
  const roots = []
  items.forEach(i => { if (i.parent_id && map[i.parent_id]) map[i.parent_id].children.push(map[i.id]); else roots.push(map[i.id]) })
  permTree.value = roots
  const parentIds = new Set(items.filter(i => i.parent_id).map(i => i.parent_id))
  checkedKeys.value = permRes.permission_ids.filter(id => !parentIds.has(id))
}

async function savePermissions() {
  const checked = treeRef.value.getCheckedKeys(false)
  const half = treeRef.value.getHalfCheckedKeys()
  await assignPermissions(selectedRole.value.id, [...checked, ...half])
  ElMessage.success('保存成功')
}

onMounted(loadRoles)
</script>

<style scoped>
.permission-layout { display:grid; grid-template-columns:260px 1fr; gap:16px; }
.role-option { width:100%; text-align:left; border:1px solid #d9e2ec; background:#fff; border-radius:6px; padding:11px 12px; margin-bottom:10px; cursor:pointer; }
.role-option.active { background:#e3f8ef; border-color:#21a67a; color:#13795b; }
</style>
```

**Step 2: Commit**

```bash
git add frontend/src/views/Permissions.vue && git commit -m "feat: add Permissions page with role selector and tree"
```

---

## ✅ 完成标准

- [ ] 角色 CRUD 完整可用
- [ ] 权限树 API 返回树形结构
- [ ] 角色可分配权限并保存
- [ ] 前端侧边栏显示全部菜单
- [ ] 权限管理页面左右布局正常
- [ ] 已绑定用户的角色无法删除
