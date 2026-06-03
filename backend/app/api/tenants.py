"""租户管理 API — 列表、新增、编辑、启用/停用。"""

from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.tenant import Tenant
from ..models.tenant_membership import TenantMembership
from ..models.role import Role
from ..utils.decorators import login_required, role_required

tenants_bp = Blueprint("tenants", __name__, url_prefix="/api/tenants")


@tenants_bp.route("", methods=["GET"])
@login_required
@role_required("system_admin")
def list_tenants():
    """获取租户列表（分页）。"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    per_page = min(per_page, 100)
    name = request.args.get("name", "").strip()
    status = request.args.get("status", "").strip()

    query = Tenant.query
    if name:
        query = query.filter(Tenant.name.ilike(f"%{name}%"))
    if status:
        query = query.filter(Tenant.status == status)

    query = query.order_by(Tenant.id.desc())
    pag = query.paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for t in pag.items:
        member_count = TenantMembership.query.filter_by(
            tenant_id=t.id, status="active"
        ).count()
        items.append({
            "id": t.id,
            "name": t.name,
            "code": t.code,
            "status": t.status,
            "plt_enterprise_name": t.plt_enterprise_name,
            "member_count": member_count,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })

    return jsonify({"items": items, "total": pag.total})


@tenants_bp.route("", methods=["POST"])
@login_required
@role_required("system_admin")
def create_tenant():
    """新增租户。"""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    code = (data.get("code") or "").strip()
    status = data.get("status", "active")

    if not name or not code:
        return jsonify({"error": "租户名称和编码不能为空"}), 400

    if Tenant.query.filter_by(code=code).first():
        return jsonify({"error": f"租户编码 '{code}' 已存在"}), 400

    tenant = Tenant(name=name, code=code, status=status)
    db.session.add(tenant)
    db.session.flush()

    # 创建默认角色
    tenant_admin_role = Role(tenant_id=tenant.id, name="租户管理员", code="tenant_admin",
                      description="租户管理员，拥有本租户全部权限", status="active")
    asset_role = Role(tenant_id=tenant.id, name="资产管理员", code="asset_manager",
                      description="负责资产日常管理", status="active")
    db.session.add_all([tenant_admin_role, asset_role])
    db.session.commit()

    return jsonify({"id": tenant.id, "name": tenant.name, "code": tenant.code, "status": tenant.status})


@tenants_bp.route("/<int:id>", methods=["PUT"])
@login_required
@role_required("system_admin")
def update_tenant(id):
    """编辑租户。"""
    tenant = db.session.get(Tenant, id)
    if not tenant:
        return jsonify({"error": "租户不存在"}), 404

    data = request.get_json(silent=True) or {}
    name = data.get("name")
    code = data.get("code")
    status = data.get("status")

    if name is not None:
        tenant.name = name.strip()
    if code is not None:
        code = code.strip()
        existing = Tenant.query.filter(Tenant.code == code, Tenant.id != id).first()
        if existing:
            return jsonify({"error": f"租户编码 '{code}' 已被其他租户使用"}), 400
        tenant.code = code
    if status is not None:
        tenant.status = status

    db.session.commit()
    return jsonify({"id": tenant.id, "name": tenant.name, "code": tenant.code, "status": tenant.status})


@tenants_bp.route("/<int:id>", methods=["DELETE"])
@login_required
@role_required("system_admin")
def delete_tenant(id):
    """删除租户（仅允许删除无活跃成员的租户）。"""
    tenant = db.session.get(Tenant, id)
    if not tenant:
        return jsonify({"error": "租户不存在"}), 404

    active_members = TenantMembership.query.filter_by(tenant_id=id, status="active").count()
    if active_members > 0:
        return jsonify({"error": f"该租户下还有 {active_members} 个活跃成员，无法删除"}), 400

    db.session.delete(tenant)
    db.session.commit()
    return jsonify({"message": "删除成功"})


@tenants_bp.route("/<int:id>/members", methods=["GET"])
@login_required
@role_required("system_admin")
def list_tenant_members(id):
    """获取租户成员列表。"""
    tenant = db.session.get(Tenant, id)
    if not tenant:
        return jsonify({"error": "租户不存在"}), 404

    memberships = TenantMembership.query.filter_by(tenant_id=id).all()
    items = []
    for m in memberships:
        items.append({
            "id": m.id,
            "user_id": m.user_id,
            "username": m.user.username if m.user else "",
            "name": m.user.name if m.user else "",
            "role": m.role.name if m.role else "",
            "role_code": m.role.code if m.role else "",
            "department": m.department,
            "status": m.status,
            "is_default": m.is_default,
        })
    return jsonify({"items": items})
