from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.asset_param import AssetParam
from ..models.asset import Asset
from ..models.operation_log import OperationLog
from ..utils.decorators import login_required

params_bp = Blueprint("asset_params", __name__, url_prefix="/api/asset-params")


def _log(user_id, action, target_type, target_id, detail):
    db.session.add(
        OperationLog(user_id=user_id, action=action, target_type=target_type, target_id=target_id, detail=detail)
    )


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
    return jsonify(
        {
            "items": [
                {"id": p.id, "type": p.type, "name": p.name, "code": p.code, "sort_order": p.sort_order, "status": p.status}
                for p in pag.items
            ],
            "total": pag.total,
            "page": pag.page,
            "per_page": pag.per_page,
        }
    )


@params_bp.route("", methods=["POST"])
@login_required
def create_param():
    data = request.get_json()
    if not data or not data.get("type") or not data.get("name"):
        return jsonify({"error": "缺少必填字段"}), 400
    if AssetParam.query.filter_by(type=data["type"], name=data["name"]).first():
        return jsonify({"error": "该类型下参数名称已存在"}), 400
    p = AssetParam(
        type=data["type"],
        name=data["name"],
        code=data.get("code", ""),
        sort_order=data.get("sort_order", 0),
        status=data.get("status", "active"),
    )
    db.session.add(p)
    _log(request.current_user.id, "create", "asset_param", p.id, f"新增参数 {p.type}:{p.name}")
    db.session.commit()
    return jsonify({"id": p.id}), 201


@params_bp.route("/<int:id>", methods=["PUT"])
@login_required
def update_param(id):
    p = AssetParam.query.filter_by(id=id).first_or_404()
    data = request.get_json()
    if data.get("name"):
        p.name = data["name"]
    if data.get("code") is not None:
        p.code = data["code"]
    if data.get("sort_order") is not None:
        p.sort_order = data["sort_order"]
    if data.get("status"):
        p.status = data["status"]
    _log(request.current_user.id, "update", "asset_param", p.id, f"修改参数 {p.name}")
    db.session.commit()
    return jsonify({"id": p.id})


@params_bp.route("/<int:id>", methods=["DELETE"])
@login_required
def delete_param(id):
    p = AssetParam.query.filter_by(id=id).first_or_404()
    ref = Asset.query.filter(
        (Asset.category == p.name) | (Asset.brand == p.name) | (Asset.unit == p.name) | (Asset.location == p.name)
    ).first()
    if ref:
        return jsonify({"error": f'参数 "{p.name}" 已被资产引用，无法删除'}), 400
    _log(request.current_user.id, "delete", "asset_param", p.id, f"删除参数 {p.name}")
    db.session.delete(p)
    db.session.commit()
    return jsonify({"message": "删除成功"})


@params_bp.route("/options", methods=["GET"])
@login_required
def param_options():
    params = AssetParam.query.filter_by(status="active").order_by(AssetParam.sort_order).all()
    result = {}
    for p in params:
        result.setdefault(p.type, []).append({"id": p.id, "name": p.name, "code": p.code})
    return jsonify(result)
