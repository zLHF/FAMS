# 06 — 固定资产台账模块

> **依赖:** 05-asset-params
> **目标:** 资产 CRUD + 列表查询 + 详情查看。

---

## Task 1: 后端资产 CRUD API

**Files:**
- Create: `backend/app/api/assets.py`
- Modify: `backend/app/api/__init__.py`

**Step 1: 创建 assets.py**

```python
from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.asset import Asset
from ..models.operation_log import OperationLog
from ..utils.decorators import login_required

assets_bp = Blueprint("assets", __name__, url_prefix="/api/assets")

@assets_bp.route("", methods=["GET"])
@login_required
def list_assets():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    code = request.args.get("code", "")
    name = request.args.get("name", "")
    category = request.args.get("category", "")
    status = request.args.get("status", "")
    owner_name = request.args.get("owner_name", "")

    query = Asset.query
    if code: query = query.filter(Asset.code.contains(code))
    if name: query = query.filter(Asset.name.contains(name))
    if category: query = query.filter_by(category=category)
    if status: query = query.filter_by(status=status)
    if owner_name:
        from ..models.user import User
        query = query.join(User, Asset.owner_id == User.id, isouter=True).filter(User.name.contains(owner_name))

    pag = query.order_by(Asset.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [_asset_dict(a) for a in pag.items],
        "total": pag.total, "page": pag.page, "per_page": pag.per_page,
    })

@assets_bp.route("/<int:id>", methods=["GET"])
@login_required
def get_asset(id):
    asset = Asset.query.get_or_404(id)
    return jsonify(_asset_dict(asset, detail=True))

@assets_bp.route("", methods=["POST"])
@login_required
def create_asset():
    data = request.get_json()
    if not data or not data.get("code") or not data.get("name"):
        return jsonify({"error": "资产编码和名称为必填"}), 400
    if Asset.query.filter_by(code=data["code"]).first():
        return jsonify({"error": "资产编码已存在"}), 400
    a = Asset(
        code=data["code"], name=data["name"], category=data.get("category"),
        brand=data.get("brand"), model=data.get("model"), serial_number=data.get("serial_number"),
        unit=data.get("unit"), purchase_date=data.get("purchase_date"), location=data.get("location"),
        status=data.get("status", "idle"), notes=data.get("notes"),
    )
    db.session.add(a)
    _log(request.current_user.id, "create", "asset", a.id, f"新增资产 {a.code}")
    db.session.commit()
    return jsonify(_asset_dict(a)), 201

@assets_bp.route("/<int:id>", methods=["PUT"])
@login_required
def update_asset(id):
    a = Asset.query.get_or_404(id)
    data = request.get_json()
    for field in ["name", "category", "brand", "model", "serial_number", "unit", "purchase_date", "location", "status", "notes"]:
        if field in data: setattr(a, field, data[field])
    _log(request.current_user.id, "update", "asset", a.id, f"修改资产 {a.code}")
    db.session.commit()
    return jsonify(_asset_dict(a))

def _asset_dict(a, detail=False):
    d = {
        "id": a.id, "code": a.code, "name": a.name, "category": a.category,
        "brand": a.brand, "model": a.model, "serial_number": a.serial_number,
        "unit": a.unit, "purchase_date": str(a.purchase_date) if a.purchase_date else None,
        "location": a.location, "status": a.status,
        "owner_name": a.owner.name if a.owner else None,
        "borrower_name": a.borrower.name if a.borrower else None,
        "notes": a.notes, "updated_at": str(a.updated_at) if a.updated_at else None,
    }
    if detail:
        d["owner_id"] = a.owner_id
        d["borrower_id"] = a.borrower_id
        d["created_at"] = str(a.created_at) if a.created_at else None
    return d

def _log(user_id, action, target_type, target_id, detail):
    db.session.add(OperationLog(user_id=user_id, action=action, target_type=target_type, target_id=target_id, detail=detail))
```

**Step 2: 注册蓝图**

```python
from .assets import assets_bp
app.register_blueprint(assets_bp)
```

**Step 3: 写测试 tests/test_assets.py**

```python
from app.extensions import db, bcrypt
from app.models.user import User
from app.models.role import Role
from app.models.asset import Asset

def setup_admin(db):
    role = Role(name="管理员", code="admin", status="active")
    db.session.add(role); db.session.flush()
    user = User(username="admin", password_hash=bcrypt.generate_password_hash("123456").decode(), name="管理员", role_id=role.id, status="active")
    db.session.add(user); db.session.commit()

def get_token(client):
    return client.post("/api/auth/login", json={"username":"admin","password":"123456"}).get_json()["token"]
def h(t): return {"Authorization": f"Bearer {t}"}

def test_create_and_get(client, db, app):
    with app.app_context(): setup_admin(db)
    t = get_token(client)
    r = client.post("/api/assets", json={"code":"A001","name":"联想笔记本","category":"电脑设备","unit":"台","location":"研发部"}, headers=h(t))
    assert r.status_code == 201
    aid = r.get_json()["id"]
    r2 = client.get(f"/api/assets/{aid}", headers=h(t))
    assert r2.get_json()["code"] == "A001"

def test_duplicate_code(client, db, app):
    with app.app_context(): setup_admin(db)
    t = get_token(client)
    client.post("/api/assets", json={"code":"A001","name":"资产1"}, headers=h(t))
    r = client.post("/api/assets", json={"code":"A001","name":"资产2"}, headers=h(t))
    assert r.status_code == 400

def test_list_with_filter(client, db, app):
    with app.app_context():
        setup_admin(db)
        db.session.add(Asset(code="A001", name="电脑", status="idle"))
        db.session.add(Asset(code="A002", name="桌子", status="distributed"))
        db.session.commit()
    t = get_token(client)
    r = client.get("/api/assets?status=idle", headers=h(t))
    assert r.get_json()["total"] == 1
```

**Step 4: 运行测试**

```bash
python -m pytest tests/test_assets.py -v
```

**Step 5: Commit**

```bash
git add backend/ && git commit -m "feat: add asset CRUD API with search, pagination, detail view"
```

---

## Task 2: 前端 — 资产台账页面

**Files:**
- Create: `frontend/src/api/assets.js`
- Create: `frontend/src/views/Assets.vue`

**Step 1: 创建 api/assets.js**

```javascript
import http from './index'
export function getAssets(params) { return http.get('/assets', { params }) }
export function getAsset(id) { return http.get(`/assets/${id}`) }
export function createAsset(data) { return http.post('/assets', data) }
export function updateAsset(id, data) { return http.put(`/assets/${id}`, data) }
```

**Step 2: 创建 views/Assets.vue（参照原型 assets.html）**

```vue
<template>
  <div>
    <el-card style="margin-bottom:16px;">
      <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end;">
        <el-input v-model="filters.code" placeholder="资产编码" clearable style="width:160px;" />
        <el-input v-model="filters.name" placeholder="资产名称" clearable style="width:160px;" />
        <el-select v-model="filters.status" placeholder="状态" clearable style="width:140px;">
          <el-option label="闲置" value="idle" /><el-option label="已派发" value="distributed" />
          <el-option label="借用中" value="borrowing" /><el-option label="已退库" value="returned" />
        </el-select>
        <el-button @click="loadData">查询</el-button>
        <el-button type="primary" style="background:#16805f;border-color:#16805f;" @click="openDialog()">新增资产</el-button>
      </div>
    </el-card>
    <el-card>
      <el-table :data="tableData" stripe>
        <el-table-column prop="code" label="资产编码" />
        <el-table-column prop="name" label="资产名称" />
        <el-table-column prop="category" label="分类" />
        <el-table-column prop="brand" label="品牌" />
        <el-table-column prop="location" label="存放地点" />
        <el-table-column label="状态">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner_name" label="责任人" />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row)">详情</el-button>
            <el-button link type="primary" @click="openDialog(row)">修改</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="display:flex;justify-content:flex-end;margin-top:16px;">
        <el-pagination background layout="total, prev, pager, next" :total="total" :page-size="filters.per_page" v-model:current-page="filters.page" @current-change="loadData" />
      </div>
    </el-card>

    <!-- 新增/修改弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '修改资产' : '新增资产'" width="700px">
      <el-form :model="form" label-width="80px" :disabled="readonly">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 16px;">
          <el-form-item label="资产编码" required><el-input v-model="form.code" /></el-form-item>
          <el-form-item label="资产名称" required><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="资产分类"><el-select v-model="form.category" style="width:100%;"><el-option v-for="c in options.category||[]" :key="c.name" :label="c.name" :value="c.name" /></el-select></el-form-item>
          <el-form-item label="品牌"><el-select v-model="form.brand" clearable style="width:100%;"><el-option v-for="b in options.brand||[]" :key="b.name" :label="b.name" :value="b.name" /></el-select></el-form-item>
          <el-form-item label="型号"><el-input v-model="form.model" /></el-form-item>
          <el-form-item label="序列号"><el-input v-model="form.serial_number" /></el-form-item>
          <el-form-item label="计量单位"><el-select v-model="form.unit" style="width:100%;"><el-option v-for="u in options.unit||[]" :key="u.name" :label="u.name" :value="u.name" /></el-select></el-form-item>
          <el-form-item label="购置日期"><el-date-picker v-model="form.purchase_date" type="date" value-format="YYYY-MM-DD" style="width:100%;" /></el-form-item>
          <el-form-item label="存放地点"><el-select v-model="form.location" style="width:100%;"><el-option v-for="l in options.location||[]" :key="l.name" :label="l.name" :value="l.name" /></el-select></el-form-item>
          <el-form-item label="当前状态"><el-select v-model="form.status" style="width:100%;"><el-option label="闲置" value="idle" /><el-option label="已派发" value="distributed" /><el-option label="借用中" value="borrowing" /><el-option label="已退库" value="returned" /></el-select></el-form-item>
        </div>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer v-if="!readonly">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" style="background:#16805f;border-color:#16805f;" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAssets, getAsset, createAsset, updateAsset } from '../api/assets'
import { getParamOptions } from '../api/assetParams'
import { ElMessage } from 'element-plus'

const statusLabel = { idle: '闲置', distributed: '已派发', borrowing: '借用中', returned: '已退库' }
const statusType = { idle: 'success', distributed: 'warning', borrowing: 'info', returned: 'muted' }

const filters = ref({ code: '', name: '', status: '', page: 1, per_page: 10 })
const tableData = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const editing = ref(null)
const readonly = ref(false)
const options = ref({})
const form = ref({ code: '', name: '', category: '', brand: '', model: '', serial_number: '', unit: '', purchase_date: '', location: '', status: 'idle', notes: '' })

async function loadData() {
  const res = await getAssets(filters.value)
  tableData.value = res.items; total.value = res.total
}

async function loadOptions() {
  options.value = await getParamOptions()
}

function openDialog(row = null) {
  readonly.value = false
  editing.value = row
  form.value = row ? { ...row } : { code: '', name: '', category: '', brand: '', model: '', serial_number: '', unit: '', purchase_date: '', location: '', status: 'idle', notes: '' }
  dialogVisible.value = true
}

async function viewDetail(row) {
  const detail = await getAsset(row.id)
  form.value = detail; editing.value = detail; readonly.value = true; dialogVisible.value = true
}

async function handleSave() {
  if (editing.value?.id) { await updateAsset(editing.value.id, form.value) } else { await createAsset(form.value) }
  ElMessage.success('保存成功'); dialogVisible.value = false; loadData()
}

onMounted(() => { loadData(); loadOptions() })
</script>
```

**Step 3: Commit**

```bash
git add frontend/src/ && git commit -m "feat: add Assets page with CRUD, detail view, and param dropdowns"
```

---

## ✅ 完成标准

- [ ] 资产列表分页 + 按编码/名称/状态查询
- [ ] 新增资产，编码唯一校验
- [ ] 修改资产信息
- [ ] 查看资产详情
- [ ] 下拉选项来自参数配置
- [ ] 后端 3 个测试通过
