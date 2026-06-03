from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.role import Role, role_permissions
from ..models.user import User
from ..models.permission import Permission
from ..utils.decorators import login_required, role_required

roles_bp = Blueprint("roles", __name__, url_prefix="/api/roles")


@roles_bp.route("", methods=["GET"])
@login_required
def list_roles():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 100)
    name = request.args.get("name", "")
    status = request.args.get("status", "")
    query = Role.query
    if name:
        query = query.filter(Role.name.contains(name))
    if status:
        query = query.filter_by(status=status)
    pag = query.order_by(Role.id).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "items": [
                {"id": r.id, "name": r.name, "code": r.code, "description": r.description, "status": r.status}
                for r in pag.items
            ],
            "total": pag.total,
            "page": pag.page,
            "per_page": pag.per_page,
        }
    )


@roles_bp.route("", methods=["POST"])
@role_required("admin")
def create_role():
    data = request.get_json()
    if not data or not data.get("name") or not data.get("code"):
        return jsonify({"error": "缺少必填字段"}), 400
    if Role.query.filter_by(name=data["name"]).first():
        return jsonify({"error": "角色名称已存在"}), 400
    if Role.query.filter_by(code=data["code"]).first():
        return jsonify({"error": "角色编码已存在"}), 400
    role = Role(
        name=data["name"],
        code=data["code"],
        description=data.get("description"),
        status=data.get("status", "active"),
    )
    db.session.add(role)
    db.session.commit()
    return jsonify({"id": role.id, "name": role.name}), 201


@roles_bp.route("/<int:id>", methods=["PUT"])
@role_required("admin")
def update_role(id):
    role = Role.query.filter_by(id=id).first_or_404()
    data = request.get_json()
    if data.get("name"):
        role.name = data["name"]
    if data.get("description") is not None:
        role.description = data["description"]
    if data.get("status"):
        role.status = data["status"]
    db.session.commit()
    return jsonify({"id": role.id, "name": role.name})


@roles_bp.route("/<int:id>", methods=["DELETE"])
@role_required("admin")
def delete_role(id):
    role = Role.query.filter_by(id=id).first_or_404()
    if User.query.filter_by(role_id=id).count() > 0:
        return jsonify({"error": "该角色已绑定用户，无法删除"}), 400
    db.session.delete(role)
    db.session.commit()
    return jsonify({"message": "删除成功"})


@roles_bp.route("/<int:id>/permissions", methods=["PUT"])
@role_required("admin")
def assign_permissions(id):
    role = Role.query.filter_by(id=id).first_or_404()
    data = request.get_json()
    perm_ids = data.get("permission_ids", [])
    # Validate permission IDs exist
    if perm_ids:
        valid_count = Permission.query.filter(Permission.id.in_(perm_ids)).count()
        if valid_count != len(perm_ids):
            return jsonify({"error": "包含无效的权限ID"}), 400
    db.session.execute(role_permissions.delete().where(role_permissions.c.role_id == id))
    for pid in perm_ids:
        db.session.execute(role_permissions.insert().values(role_id=id, permission_id=pid))
    db.session.commit()
    return jsonify({"message": "权限分配成功"})
