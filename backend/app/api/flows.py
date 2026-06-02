from flask import Blueprint, request, jsonify
from datetime import date
from ..extensions import db
from ..models.asset import Asset
from ..models.flow_record import FlowRecord
from ..models.operation_log import OperationLog
from ..models.user import User
from ..utils.decorators import login_required

flows_bp = Blueprint("flows", __name__, url_prefix="/api/assets")

STATUS_LABELS = {"idle": "闲置", "distributed": "已派发", "borrowing": "借用中", "returned": "已退库"}


def _record(asset, flow_type, operator_id, detail):
    db.session.add(FlowRecord(asset_id=asset.id, flow_type=flow_type, operator_id=operator_id, detail=detail))
    db.session.add(
        OperationLog(
            user_id=operator_id, action=flow_type, target_type="asset", target_id=asset.id, detail=str(detail)
        )
    )


@flows_bp.route("/<int:id>/distribute", methods=["POST"])
@login_required
def distribute(id):
    a = Asset.query.filter_by(id=id).first_or_404()
    if a.status not in ("idle", "returned"):
        return jsonify({"error": f"当前状态「{STATUS_LABELS.get(a.status, a.status)}」不允许派发"}), 400
    data = request.get_json()
    if not data.get("owner_id"):
        return jsonify({"error": "请选择领用人"}), 400
    owner = db.session.get(User, data["owner_id"])
    if not owner:
        return jsonify({"error": "领用人不存在"}), 400
    a.status = "distributed"
    a.owner_id = owner.id
    if data.get("location"):
        a.location = data["location"]
    _record(
        a, "distribute", request.current_user.id,
        {"owner_name": owner.name, "department": owner.department, "distribute_date": data.get("distribute_date", str(date.today())), "location": a.location, "notes": data.get("notes", "")}
    )
    db.session.commit()
    return jsonify({"message": "派发成功", "status": a.status})


@flows_bp.route("/<int:id>/borrow", methods=["POST"])
@login_required
def borrow(id):
    a = Asset.query.filter_by(id=id).first_or_404()
    if a.status not in ("idle", "returned"):
        return jsonify({"error": f"当前状态「{STATUS_LABELS.get(a.status, a.status)}」不允许借用"}), 400
    data = request.get_json()
    if not data.get("borrower_id") or not data.get("expected_return_date"):
        return jsonify({"error": "借用人和预计归还日期为必填"}), 400
    borrower = db.session.get(User, data["borrower_id"])
    if not borrower:
        return jsonify({"error": "借用人不存在"}), 400
    a.status = "borrowing"
    a.borrower_id = borrower.id
    _record(
        a, "borrow", request.current_user.id,
        {"borrower_name": borrower.name, "department": borrower.department, "borrow_date": data.get("borrow_date", str(date.today())), "expected_return_date": data["expected_return_date"], "reason": data.get("reason", "")}
    )
    db.session.commit()
    return jsonify({"message": "借用成功", "status": a.status})


@flows_bp.route("/<int:id>/return", methods=["POST"])
@login_required
def return_(id):
    a = Asset.query.filter_by(id=id).first_or_404()
    if a.status != "borrowing":
        return jsonify({"error": "只有借用中的资产可以归还"}), 400
    data = request.get_json()
    if data.get("location"):
        a.location = data["location"]
    _record(
        a, "return", request.current_user.id,
        {"return_date": data.get("return_date", str(date.today())), "location": a.location, "condition": data.get("condition", "完好"), "notes": data.get("notes", "")}
    )
    a.status = "returned"
    a.borrower_id = None
    db.session.commit()
    return jsonify({"message": "归还成功", "status": a.status})


@flows_bp.route("/<int:id>/revert", methods=["POST"])
@login_required
def revert(id):
    a = Asset.query.filter_by(id=id).first_or_404()
    if a.status != "distributed":
        return jsonify({"error": "只有已派发的资产可以退库"}), 400
    data = request.get_json()
    old_owner = a.owner.name if a.owner else ""
    if data.get("location"):
        a.location = data["location"]
    _record(
        a, "revert", request.current_user.id,
        {"owner_name": old_owner, "revert_date": data.get("revert_date", str(date.today())), "location": a.location, "condition": data.get("condition", "完好"), "notes": data.get("notes", "")}
    )
    a.status = "returned"
    a.owner_id = None
    db.session.commit()
    return jsonify({"message": "退库成功", "status": a.status})


@flows_bp.route("/<int:id>/owner-change", methods=["POST"])
@login_required
def owner_change(id):
    a = Asset.query.filter_by(id=id).first_or_404()
    if a.status != "distributed":
        return jsonify({"error": "只有已派发的资产可以变更领用人"}), 400
    data = request.get_json()
    if not data.get("new_owner_id"):
        return jsonify({"error": "请选择新领用人"}), 400
    old_owner = a.owner.name if a.owner else ""
    new_owner = db.session.get(User, data["new_owner_id"])
    if not new_owner:
        return jsonify({"error": "新领用人不存在"}), 400
    if data.get("location"):
        a.location = data["location"]
    _record(
        a, "owner_change", request.current_user.id,
        {"old_owner": old_owner, "new_owner": new_owner.name, "change_date": data.get("change_date", str(date.today())), "location": a.location, "reason": data.get("reason", "")}
    )
    a.owner_id = new_owner.id
    db.session.commit()
    return jsonify({"message": "变更成功"})


@flows_bp.route("/<int:id>/records", methods=["GET"])
@login_required
def flow_records(id):
    Asset.query.filter_by(id=id).first_or_404()
    records = FlowRecord.query.filter_by(asset_id=id).order_by(FlowRecord.id.desc()).all()
    return jsonify(
        {
            "items": [
                {"id": r.id, "flow_type": r.flow_type, "operator_name": r.operator.name if r.operator else "", "detail": r.detail, "created_at": str(r.created_at)}
                for r in records
            ]
        }
    )
