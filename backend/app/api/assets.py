from flask import Blueprint, request, jsonify
from datetime import date
from ..extensions import db
from ..models.asset import Asset
from ..models.flow_record import FlowRecord
from ..models.operation_log import OperationLog
from ..models.user import User
from ..utils.decorators import login_required, role_required
from ..utils.tenant import is_tenant_member

assets_bp = Blueprint("assets", __name__, url_prefix="/api/assets")


def _current_tenant_id():
    t = getattr(request, "current_tenant", None)
    return t.id if t else None


def _asset_dict(a, detail=False):
    d = {
        "id": a.id,
        "code": a.code,
        "name": a.name,
        "category": a.category,
        "brand": a.brand,
        "model": a.model,
        "serial_number": a.serial_number,
        "unit": a.unit,
        "purchase_date": str(a.purchase_date) if a.purchase_date else None,
        "location": a.location,
        "status": a.status,
        "owner_id": a.owner_id,
        "owner_name": a.owner.name if a.owner else None,
        "borrower_id": a.borrower_id,
        "borrower_name": a.borrower.name if a.borrower else None,
        "notes": a.notes,
        "updated_at": str(a.updated_at) if a.updated_at else None,
    }
    if detail:
        d["created_at"] = str(a.created_at) if a.created_at else None
    return d


def _log(user_id, action, target_type, target_id, detail):
    db.session.add(
        OperationLog(tenant_id=_current_tenant_id(), user_id=user_id, action=action, target_type=target_type, target_id=target_id, detail=detail)
    )


def _get_asset_or_404(id):
    return Asset.query.filter_by(id=id, tenant_id=_current_tenant_id()).first_or_404()


def _get_member_user(user_id):
    user = db.session.get(User, user_id)
    if not user or not is_tenant_member(user.id, _current_tenant_id()):
        return None
    return user


@assets_bp.route("", methods=["GET"])
@login_required
def list_assets():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    code = request.args.get("code", "")
    name = request.args.get("name", "")
    category = request.args.get("category", "")
    status = request.args.get("status", "")

    tid = _current_tenant_id()
    if tid is None:
        return jsonify({"items": [], "total": 0, "page": page, "per_page": per_page})
    query = Asset.query.filter_by(tenant_id=tid)
    if code:
        query = query.filter(Asset.code.contains(code))
    if name:
        query = query.filter(Asset.name.contains(name))
    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)

    pag = query.order_by(Asset.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "items": [_asset_dict(a) for a in pag.items],
            "total": pag.total,
            "page": pag.page,
            "per_page": pag.per_page,
        }
    )


@assets_bp.route("/<int:id>", methods=["GET"])
@login_required
def get_asset(id):
    asset = _get_asset_or_404(id)
    return jsonify(_asset_dict(asset, detail=True))


@assets_bp.route("", methods=["POST"])
@role_required("admin", "tenant_admin")
def create_asset():
    data = request.get_json()
    if not data or not data.get("code") or not data.get("name"):
        return jsonify({"error": "资产编码和名称为必填"}), 400
    if Asset.query.filter_by(tenant_id=_current_tenant_id(), code=data["code"]).first():
        return jsonify({"error": "资产编码已存在"}), 400
    a = Asset(
        tenant_id=_current_tenant_id(),
        code=data["code"],
        name=data["name"],
        category=data.get("category") or None,
        brand=data.get("brand") or None,
        model=data.get("model") or None,
        serial_number=data.get("serial_number") or None,
        unit=data.get("unit") or None,
        purchase_date=data.get("purchase_date") or None,
        location=data.get("location") or None,
        status=data.get("status", "idle") if data.get("status") in VALID_STATUSES else "idle",
        notes=data.get("notes") or None,
    )
    db.session.add(a)
    db.session.flush()
    _log(request.current_user.id, "create", "asset", a.id, f"新增资产 {a.code}")
    db.session.commit()
    return jsonify(_asset_dict(a)), 201


@assets_bp.route("/<int:id>", methods=["PUT"])
@role_required("admin", "tenant_admin")
def update_asset(id):
    a = _get_asset_or_404(id)
    data = request.get_json()
    for field in [
        "name", "category", "brand", "model", "serial_number",
        "unit", "purchase_date", "location", "status", "notes",
    ]:
        if field in data:
            setattr(a, field, data[field] or None)
    _log(request.current_user.id, "update", "asset", a.id, f"修改资产 {a.code}")
    db.session.commit()
    return jsonify(_asset_dict(a))


# ========== 流转操作 ==========

STATUS_LABELS = {"idle": "闲置", "distributed": "已派发", "borrowing": "借用中", "returned": "已退库"}
VALID_STATUSES = set(STATUS_LABELS.keys())


def _record(asset, flow_type, operator_id, detail):
    db.session.add(FlowRecord(tenant_id=_current_tenant_id(), asset_id=asset.id, flow_type=flow_type, operator_id=operator_id, detail=detail))
    db.session.add(
        OperationLog(tenant_id=_current_tenant_id(), user_id=operator_id, action=flow_type, target_type="asset", target_id=asset.id, detail=str(detail))
    )


@assets_bp.route("/<int:id>/distribute", methods=["POST"])
@login_required
def distribute(id):
    a = _get_asset_or_404(id)
    if a.status not in ("idle", "returned"):
        return jsonify({"error": f"当前状态「{STATUS_LABELS.get(a.status, a.status)}」不允许派发"}), 400
    data = request.get_json()
    if not data.get("owner_id"):
        return jsonify({"error": "请选择领用人"}), 400
    owner = _get_member_user(data["owner_id"])
    if not owner:
        return jsonify({"error": "领用人不存在"}), 400
    a.status = "distributed"
    a.owner_id = owner.id
    if data.get("location"):
        a.location = data["location"]
    _record(a, "distribute", request.current_user.id, {
        "owner_name": owner.name, "department": owner.department,
        "distribute_date": data.get("distribute_date", str(date.today())),
        "location": a.location, "notes": data.get("notes", ""),
    })
    db.session.commit()
    return jsonify({"message": "派发成功", "status": a.status})


@assets_bp.route("/<int:id>/borrow", methods=["POST"])
@login_required
def borrow(id):
    a = _get_asset_or_404(id)
    if a.status not in ("idle", "returned"):
        return jsonify({"error": f"当前状态「{STATUS_LABELS.get(a.status, a.status)}」不允许借用"}), 400
    data = request.get_json()
    if not data.get("borrower_id") or not data.get("expected_return_date"):
        return jsonify({"error": "借用人和预计归还日期为必填"}), 400
    borrower = _get_member_user(data["borrower_id"])
    if not borrower:
        return jsonify({"error": "借用人不存在"}), 400
    a.status = "borrowing"
    a.borrower_id = borrower.id
    _record(a, "borrow", request.current_user.id, {
        "borrower_name": borrower.name, "department": borrower.department,
        "borrow_date": data.get("borrow_date", str(date.today())),
        "expected_return_date": data["expected_return_date"], "reason": data.get("reason", ""),
    })
    db.session.commit()
    return jsonify({"message": "借用成功", "status": a.status})


@assets_bp.route("/<int:id>/return", methods=["POST"])
@login_required
def return_(id):
    a = _get_asset_or_404(id)
    if a.status != "borrowing":
        return jsonify({"error": "只有借用中的资产可以归还"}), 400
    data = request.get_json()
    if data.get("location"):
        a.location = data["location"]
    _record(a, "return", request.current_user.id, {
        "return_date": data.get("return_date", str(date.today())),
        "location": a.location, "condition": data.get("condition", "完好"), "notes": data.get("notes", ""),
    })
    a.status = "returned"
    a.borrower_id = None
    db.session.commit()
    return jsonify({"message": "归还成功", "status": a.status})


@assets_bp.route("/<int:id>/revert", methods=["POST"])
@login_required
def revert(id):
    a = _get_asset_or_404(id)
    if a.status != "distributed":
        return jsonify({"error": "只有已派发的资产可以退库"}), 400
    data = request.get_json()
    old_owner = a.owner.name if a.owner else ""
    if data.get("location"):
        a.location = data["location"]
    _record(a, "revert", request.current_user.id, {
        "owner_name": old_owner, "revert_date": data.get("revert_date", str(date.today())),
        "location": a.location, "condition": data.get("condition", "完好"), "notes": data.get("notes", ""),
    })
    a.status = "returned"
    a.owner_id = None
    db.session.commit()
    return jsonify({"message": "退库成功", "status": a.status})


@assets_bp.route("/<int:id>/owner-change", methods=["POST"])
@login_required
def owner_change(id):
    a = _get_asset_or_404(id)
    if a.status != "distributed":
        return jsonify({"error": "只有已派发的资产可以变更领用人"}), 400
    data = request.get_json()
    if not data.get("new_owner_id"):
        return jsonify({"error": "请选择新领用人"}), 400
    old_owner = a.owner.name if a.owner else ""
    new_owner = _get_member_user(data["new_owner_id"])
    if not new_owner:
        return jsonify({"error": "新领用人不存在"}), 400
    if data.get("location"):
        a.location = data["location"]
    _record(a, "owner_change", request.current_user.id, {
        "old_owner": old_owner, "new_owner": new_owner.name,
        "change_date": data.get("change_date", str(date.today())),
        "location": a.location, "reason": data.get("reason", ""),
    })
    a.owner_id = new_owner.id
    db.session.commit()
    return jsonify({"message": "变更成功"})


@assets_bp.route("/<int:id>/records", methods=["GET"])
@login_required
def flow_records(id):
    _get_asset_or_404(id)
    records = FlowRecord.query.filter_by(asset_id=id, tenant_id=_current_tenant_id()).order_by(FlowRecord.id.desc()).all()
    return jsonify({
        "items": [{
            "id": r.id, "flow_type": r.flow_type,
            "operator_name": r.operator.name if r.operator else "",
            "detail": r.detail, "created_at": str(r.created_at),
        } for r in records]
    })
