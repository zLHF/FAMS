# 05 — 资产参数设置模块

> **依赖:** 02-auth
> **目标:** 资产参数（分类、品牌、单位、地点）CRUD，被引用参数不可删除。

---

## Task 1: 后端资产参数 API

**Files:**
- Create: `backend/app/api/asset_params.py`
- Modify: `backend/app/api/__init__.py`

**Step 1: 创建 asset_params.py**

```python
from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.asset_param import AssetParam
from ..models.asset import Asset
from ..models.operation_log import OperationLog
from ..utils.decorators import login_required

params_bp = Blueprint("asset_params", __name__, url_prefix="/api/asset-params")

@params_bp.route("", methods=["GET"])
@login_required
def list_params():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    type_ = request.args.get("type", "")
    name = request.args.get("name", "")

    query = AssetParam.query
    if type_:
        query = query.filter_by(type=type_)
    if name:
        query = query.filter(AssetParam.name.contains(name))

    pag = query.order_by(AssetParam.type, AssetParam.sort_order).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [{"id": p.id, "type": p.type, "name": p.name, "code": p.code, "sort_order": p.sort_order, "status": p.status} for p in pag.items],
        "total": pag.total, "page": pag.page, "per_page": pag.per_page,
    })

@params_bp.route("", methods=["POST"])
@login_required
def create_param():
    data = request.get_json()
    if not data or not data.get("type") or not data.get("name"):
        return jsonify({"error": "缺少必填字段"}), 400
    if AssetParam.query.filter_by(type=data["type"], name=data["name"]).first():
        return jsonify({"error": "该类型下参数名称已存在"}), 400
    p = AssetParam(type=data["type"], name=data["name"], code=data.get("code", ""), sort_order=data.get("sort_order", 0), status=data.get("status", "active"))
    db.session.add(p)
    _log(request.current_user.id, "create", "asset_param", p.id, f"新增参数 {p.type}:{p.name}")
    db.session.commit()
    return jsonify({"id": p.id}), 201

@params_bp.route("/<int:id>", methods=["PUT"])
@login_required
def update_param(id):
    p = AssetParam.query.get_or_404(id)
    data = request.get_json()
    if data.get("name"): p.name = data["name"]
    if data.get("code") is not None: p.code = data["code"]
    if data.get("sort_order") is not None: p.sort_order = data["sort_order"]
    if data.get("status"): p.status = data["status"]
    _log(request.current_user.id, "update", "asset_param", p.id, f"修改参数 {p.name}")
    db.session.commit()
    return jsonify({"id": p.id})

@params_bp.route("/<int:id>", methods=["DELETE"])
@login_required
def delete_param(id):
    p = AssetParam.query.get_or_404(id)
    # 检查是否被资产引用
    ref = Asset.query.filter(
        (Asset.category == p.name) | (Asset.brand == p.name) |
        (Asset.unit == p.name) | (Asset.location == p.name)
    ).first()
    if ref:
        return jsonify({"error": f"参数 "{p.name}" 已被资产引用，无法删除"}), 400
    _log(request.current_user.id, "delete", "asset_param", p.id, f"删除参数 {p.name}")
    db.session.delete(p)
    db.session.commit()
    return jsonify({"message": "删除成功"})

@params_bp.route("/options", methods=["GET"])
@login_required
def param_options():
    """返回按 type 分组的参数选项，供其他页面下拉使用"""
    params = AssetParam.query.filter_by(status="active").order_by(AssetParam.sort_order).all()
    result = {}
    for p in params:
        result.setdefault(p.type, []).append({"id": p.id, "name": p.name, "code": p.code})
    return jsonify(result)

def _log(user_id, action, target_type, target_id, detail):
    db.session.add(OperationLog(user_id=user_id, action=action, target_type=target_type, target_id=target_id, detail=detail))
```

**Step 2: 注册蓝图**

```python
from .asset_params import params_bp
app.register_blueprint(params_bp)
```

**Step 3: 写测试 tests/test_asset_params.py**

```python
from app.extensions import db, bcrypt
from app.models.user import User
from app.models.role import Role
from app.models.asset_param import AssetParam

def setup_admin(db):
    role = Role(name="管理员", code="admin", status="active")
    db.session.add(role); db.session.flush()
    user = User(username="admin", password_hash=bcrypt.generate_password_hash("123456").decode(), name="管理员", role_id=role.id, status="active")
    db.session.add(user); db.session.commit()

def get_token(client):
    return client.post("/api/auth/login", json={"username": "admin", "password": "123456"}).get_json()["token"]

def h(token): return {"Authorization": f"Bearer {token}"}

def test_create_and_list(client, db, app):
    with app.app_context(): setup_admin(db)
    token = get_token(client)
    resp = client.post("/api/asset-params", json={"type": "category", "name": "电脑设备", "code": "computer"}, headers=h(token))
    assert resp.status_code == 201
    resp2 = client.get("/api/asset-params", headers=h(token))
    assert resp2.get_json()["total"] >= 1

def test_duplicate_name(client, db, app):
    with app.app_context(): setup_admin(db)
    token = get_token(client)
    client.post("/api/asset-params", json={"type": "category", "name": "电脑", "code": "pc"}, headers=h(token))
    resp = client.post("/api/asset-params", json={"type": "category", "name": "电脑", "code": "pc2"}, headers=h(token))
    assert resp.status_code == 400

def test_delete_referenced(client, db, app):
    with app.app_context():
        setup_admin(db)
        p = AssetParam(type="category", name="电脑", code="pc", status="active")
        db.session.add(p); db.session.flush()
        from app.models.asset import Asset
        a = Asset(code="A001", name="测试", category="电脑", status="idle")
        db.session.add(a); db.session.commit()
    token = get_token(client)
    resp = client.delete(f"/api/asset-params/{p.id}", headers=h(token))
    assert resp.status_code == 400
```

**Step 4: 运行测试**

```bash
python -m pytest tests/test_asset_params.py -v
```

**Step 5: Commit**

```bash
git add backend/ && git commit -m "feat: add asset parameter CRUD API with reference check"
```

---

## Task 2: 前端 — 资产参数页面

**Files:**
- Create: `frontend/src/api/assetParams.js`
- Create: `frontend/src/views/AssetParams.vue`

**Step 1: 创建 api/assetParams.js**

```javascript
import http from './index'
export function getAssetParams(params) { return http.get('/asset-params', { params }) }
export function createAssetParam(data) { return http.post('/asset-params', data) }
export function updateAssetParam(id, data) { return http.put(`/asset-params/${id}`, data) }
export function deleteAssetParam(id) { return http.delete(`/asset-params/${id}`) }
export function getParamOptions() { return http.get('/asset-params/options') }
```

**Step 2: 创建 views/AssetParams.vue（参照原型 asset-params.html）**

```vue
<template>
  <div>
    <el-card style="margin-bottom:16px;">
      <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end;">
        <el-select v-model="filters.type" placeholder="参数类型" clearable style="width:160px;">
          <el-option label="资产分类" value="category" /><el-option label="品牌" value="brand" />
          <el-option label="计量单位" value="unit" /><el-option label="存放地点" value="location" />
        </el-select>
        <el-input v-model="filters.name" placeholder="参数名称" clearable style="width:200px;" />
        <el-button @click="loadData">查询</el-button>
        <el-button type="primary" style="background:#16805f;border-color:#16805f;" @click="openDialog()">新增参数</el-button>
      </div>
    </el-card>
    <el-card>
      <el-table :data="tableData" stripe>
        <el-table-column prop="type" label="参数类型">
          <template #default="{ row }">{{ typeMap[row.type] || row.type }}</template>
        </el-table-column>
        <el-table-column prop="name" label="参数名称" />
        <el-table-column prop="code" label="编码" />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'">{{ row.status === 'active' ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">修改</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="display:flex;justify-content:flex-end;margin-top:16px;">
        <el-pagination background layout="total, prev, pager, next" :total="total" :page-size="filters.per_page" v-model:current-page="filters.page" @current-change="loadData" />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '修改参数' : '新增参数'" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="参数类型" required>
          <el-select v-model="form.type" placeholder="请选择" style="width:100%;">
            <el-option label="资产分类" value="category" /><el-option label="品牌" value="brand" />
            <el-option label="计量单位" value="unit" /><el-option label="存放地点" value="location" />
          </el-select>
        </el-form-item>
        <el-form-item label="参数名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="编码"><el-input v-model="form.code" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort_order" :min="0" /></el-form-item>
        <el-form-item label="状态"><el-switch v-model="form.statusBool" active-text="启用" inactive-text="停用" /></el-form-item>
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
import { getAssetParams, createAssetParam, updateAssetParam, deleteAssetParam } from '../api/assetParams'
import { ElMessage, ElMessageBox } from 'element-plus'

const typeMap = { category: '资产分类', brand: '品牌', unit: '计量单位', location: '存放地点' }
const filters = ref({ type: '', name: '', page: 1, per_page: 20 })
const tableData = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const editing = ref(null)
const form = ref({ type: 'category', name: '', code: '', sort_order: 0, statusBool: true })

async function loadData() {
  const res = await getAssetParams(filters.value)
  tableData.value = res.items; total.value = res.total
}

function openDialog(row = null) {
  editing.value = row
  form.value = row ? { ...row, statusBool: row.status === 'active' } : { type: 'category', name: '', code: '', sort_order: 0, statusBool: true }
  dialogVisible.value = true
}

async function handleSave() {
  const data = { ...form.value, status: form.value.statusBool ? 'active' : 'disabled' }
  delete data.statusBool
  if (editing.value) { await updateAssetParam(editing.value.id, data) } else { await createAssetParam(data) }
  ElMessage.success('保存成功'); dialogVisible.value = false; loadData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除参数 "${row.name}"？`, '提示', { type: 'warning' })
  await deleteAssetParam(row.id)
  ElMessage.success('删除成功'); loadData()
}

onMounted(loadData)
</script>
```

**Step 3: Commit**

```bash
git add frontend/src/ && git commit -m "feat: add AssetParams page with CRUD and type filter"
```

---

## ✅ 完成标准

- [ ] 参数按类型查询、新增、修改、删除
- [ ] 同类型下名称不可重复
- [ ] 被资产引用的参数删除时返回 400 错误
- [ ] `/api/asset-params/options` 返回分组选项
- [ ] 前端参数管理页面完整可用
