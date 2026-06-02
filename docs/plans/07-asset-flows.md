# 07 — 资产流转模块（派发/借用/归还/退库/变更）

> **依赖:** 06-assets
> **目标:** 五种资产流转操作 + 状态机校验 + 流转记录。

---

## Task 1: 后端流转 API（统一蓝图）

**Files:**
- Create: `backend/app/api/flows.py`
- Modify: `backend/app/api/__init__.py`

**核心逻辑:** 每个流转操作校验资产当前状态，更新资产状态和责任人，写入 flow_records。

```python
from flask import Blueprint, request, jsonify
from datetime import date
from ..extensions import db
from ..models.asset import Asset
from ..models.flow_record import FlowRecord
from ..models.operation_log import OperationLog
from ..models.user import User
from ..utils.decorators import login_required

flows_bp = Blueprint("flows", __name__, url_prefix="/api/assets")

# --- 派发 ---
@flows_bp.route("/<int:id>/distribute", methods=["POST"])
@login_required
def distribute(id):
    a = Asset.query.get_or_404(id)
    if a.status not in ("idle", "returned"):
        return jsonify({"error": f"当前状态「{a.status}」不允许派发"}), 400
    data = request.get_json()
    if not data.get("owner_id"):
        return jsonify({"error": "请选择领用人"}), 400
    owner = User.query.get(data["owner_id"])
    a.status = "distributed"
    a.owner_id = owner.id
    if data.get("location"): a.location = data["location"]
    _record(a, "distribute", request.current_user.id, {**data, "owner_name": owner.name, "distribute_date": data.get("distribute_date", str(date.today()))})
    db.session.commit()
    return jsonify({"message": "派发成功", "status": a.status})

# --- 借用 ---
@flows_bp.route("/<int:id>/borrow", methods=["POST"])
@login_required
def borrow(id):
    a = Asset.query.get_or_404(id)
    if a.status not in ("idle", "returned"):
        return jsonify({"error": f"当前状态「{a.status}」不允许借用"}), 400
    data = request.get_json()
    if not data.get("borrower_id") or not data.get("expected_return_date"):
        return jsonify({"error": "借用人和预计归还日期为必填"}), 400
    borrower = User.query.get(data["borrower_id"])
    a.status = "borrowing"
    a.borrower_id = borrower.id
    _record(a, "borrow", request.current_user.id, {**data, "borrower_name": borrower.name, "borrow_date": data.get("borrow_date", str(date.today()))})
    db.session.commit()
    return jsonify({"message": "借用成功", "status": a.status})

# --- 归还 ---
@flows_bp.route("/<int:id>/return", methods=["POST"])
@login_required
def return_(id):
    a = Asset.query.get_or_404(id)
    if a.status != "borrowing":
        return jsonify({"error": "只有借用中的资产可以归还"}), 400
    data = request.get_json()
    a.status = "returned"
    a.borrower_id = None
    if data.get("location"): a.location = data["location"]
    _record(a, "return", request.current_user.id, {**data, "return_date": data.get("return_date", str(date.today()))})
    db.session.commit()
    return jsonify({"message": "归还成功", "status": a.status})

# --- 退库 ---
@flows_bp.route("/<int:id>/revert", methods=["POST"])
@login_required
def revert(id):
    a = Asset.query.get_or_404(id)
    if a.status != "distributed":
        return jsonify({"error": "只有已派发的资产可以退库"}), 400
    data = request.get_json()
    _record(a, "revert", request.current_user.id, {"owner_name": a.owner.name if a.owner else "", "revert_date": data.get("revert_date", str(date.today())), **data})
    a.status = "returned"
    a.owner_id = None
    if data.get("location"): a.location = data["location"]
    db.session.commit()
    return jsonify({"message": "退库成功", "status": a.status})

# --- 变更领用人 ---
@flows_bp.route("/<int:id>/owner-change", methods=["POST"])
@login_required
def owner_change(id):
    a = Asset.query.get_or_404(id)
    if a.status != "distributed":
        return jsonify({"error": "只有已派发的资产可以变更领用人"}), 400
    data = request.get_json()
    if not data.get("new_owner_id"):
        return jsonify({"error": "请选择新领用人"}), 400
    old_owner = a.owner.name if a.owner else ""
    new_owner = User.query.get(data["new_owner_id"])
    a.owner_id = new_owner.id
    if data.get("location"): a.location = data["location"]
    _record(a, "owner_change", request.current_user.id, {"old_owner": old_owner, "new_owner": new_owner.name, "change_date": data.get("change_date", str(date.today())), **data})
    db.session.commit()
    return jsonify({"message": "变更成功"})

# --- 流转记录查询 ---
@flows_bp.route("/<int:id>/records", methods=["GET"])
@login_required
def flow_records(id):
    Asset.query.get_or_404(id)
    records = FlowRecord.query.filter_by(asset_id=id).order_by(FlowRecord.id.desc()).all()
    return jsonify({"items": [{"id": r.id, "flow_type": r.flow_type, "operator_name": r.operator.name if r.operator else "", "detail": r.detail, "created_at": str(r.created_at)} for r in records]})

def _record(asset, flow_type, operator_id, detail):
    db.session.add(FlowRecord(asset_id=asset.id, flow_type=flow_type, operator_id=operator_id, detail=detail))
    db.session.add(OperationLog(user_id=operator_id, action=flow_type, target_type="asset", target_id=asset.id, detail=str(detail)))
```

注册蓝图 + 测试 + Commit: 同前模式。

---

## Task 2-5: 前端五个流转页面

每个页面结构相同：列表 + 搜索 + 操作弹窗。具体参照原型 HTML。

- `AssetDistribute.vue` — 筛选闲置/已退库资产，弹窗选领用人
- `AssetBorrow.vue` — 筛选闲置/已退库资产，弹窗选借用人+预计归还日期
- `AssetReturn.vue` — 筛选借用中资产，弹窗填归还信息
- `AssetRevert.vue` — 筛选已派发资产，弹窗填退库信息
- `AssetOwnerChange.vue` — 筛选已派发资产，弹窗选新领用人

每个页面约 120 行 Vue SFC，复用 assets.js 的 API + 新增 flows API。
