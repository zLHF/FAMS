from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models.permission import Permission
from ..models.role import Role, role_permissions
from ..utils.decorators import login_required

perms_bp = Blueprint("permissions", __name__, url_prefix="/api/permissions")


@perms_bp.route("/tree", methods=["GET"])
@login_required
def permission_tree():
    perms = Permission.query.order_by(Permission.sort_order).all()
    return jsonify(
        {
            "items": [
                {"id": p.id, "name": p.name, "code": p.code, "parent_id": p.parent_id, "sort_order": p.sort_order}
                for p in perms
            ]
        }
    )


@perms_bp.route("/role/<int:role_id>", methods=["GET"])
@login_required
def role_perms(role_id):
    Role.query.filter_by(id=role_id, tenant_id=request.current_tenant.id).first_or_404()
    rows = db.session.execute(role_permissions.select().where(role_permissions.c.role_id == role_id)).fetchall()
    return jsonify({"permission_ids": [r.permission_id for r in rows]})
