from flask import Blueprint, request, jsonify
from ..extensions import db, bcrypt
from ..models.user import User
from ..models.role import Role
from ..models.operation_log import OperationLog
from ..models.tenant_membership import TenantMembership
from ..utils.decorators import login_required, role_required

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


def _user_dict(u, membership=None):
    role = membership.role if membership else u.role
    return {
        "id": u.id,
        "username": u.username,
        "name": u.name,
        "phone": u.phone,
        "department": membership.department if membership else u.department,
        "role_id": membership.role_id if membership else u.role_id,
        "role_name": role.name if role else None,
        "status": membership.status if membership else u.status,
        "tenant_id": membership.tenant_id if membership else None,
    }


def _log(tenant_id, user_id, action, target_type, target_id, detail):
    db.session.add(
        OperationLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
        )
    )


def _current_tenant_id():
    return request.current_tenant.id


def _role_in_current_tenant(role_id):
    return Role.query.filter_by(id=role_id, tenant_id=_current_tenant_id()).first()


@users_bp.route("", methods=["GET"])
@login_required
def list_users():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    name = request.args.get("name", "")
    role_id = request.args.get("role_id", type=int)
    status = request.args.get("status", "")

    query = TenantMembership.query.join(User).filter(TenantMembership.tenant_id == _current_tenant_id())
    if name:
        query = query.filter(User.name.contains(name) | User.username.contains(name))
    if role_id:
        query = query.filter(TenantMembership.role_id == role_id)
    if status:
        query = query.filter(TenantMembership.status == status)

    pag = query.order_by(TenantMembership.id).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "items": [_user_dict(m.user, m) for m in pag.items],
            "total": pag.total,
            "page": pag.page,
            "per_page": pag.per_page,
        }
    )


@users_bp.route("", methods=["POST"])
@role_required("admin", "tenant_admin")
def create_user():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("name") or not data.get("role_id"):
        return jsonify({"error": "缺少必填字段"}), 400
    role = _role_in_current_tenant(data["role_id"])
    if not role:
        return jsonify({"error": "角色不存在"}), 400

    user = User.query.filter_by(username=data["username"]).first()
    if user:
        if TenantMembership.query.filter_by(tenant_id=_current_tenant_id(), user_id=user.id).first():
            return jsonify({"error": "用户账号已存在"}), 400
    else:
        password = data.get("password")
        if not password or len(password) < 6:
            return jsonify({"error": "密码长度不能少于6位"}), 400
        user = User(
            username=data["username"],
            password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
            name=data["name"],
            phone=data.get("phone"),
            department=data.get("department"),
            role_id=role.id,
            status="active",
        )
        db.session.add(user)
        db.session.flush()

    membership = TenantMembership(
        tenant_id=_current_tenant_id(),
        user_id=user.id,
        role_id=role.id,
        department=data.get("department"),
        status=data.get("status", "active"),
        is_default=False,
    )
    db.session.add(membership)
    db.session.flush()
    _log(_current_tenant_id(), request.current_user.id, "create", "user", user.id, f"新增用户 {user.username}")
    db.session.commit()
    return jsonify(_user_dict(user, membership)), 201


@users_bp.route("/<int:id>", methods=["PUT"])
@role_required("admin", "tenant_admin")
def update_user(id):
    membership = TenantMembership.query.filter_by(tenant_id=_current_tenant_id(), user_id=id).first_or_404()
    user = membership.user
    data = request.get_json()
    if data.get("name"):
        user.name = data["name"]
    if data.get("phone") is not None:
        user.phone = data["phone"]
    if data.get("department") is not None:
        membership.department = data["department"]
        if user.role_id == membership.role_id:
            user.department = data["department"]
    if data.get("role_id"):
        role = _role_in_current_tenant(data["role_id"])
        if not role:
            return jsonify({"error": "角色不存在"}), 400
        membership.role_id = role.id
        if user.role_id is None or user.role_id == request.current_membership.role_id:
            user.role_id = role.id
    if data.get("status"):
        membership.status = data["status"]
    if data.get("password"):
        if len(data["password"]) < 6:
            return jsonify({"error": "密码长度不能少于6位"}), 400
        user.password_hash = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    _log(_current_tenant_id(), request.current_user.id, "update", "user", user.id, f"修改用户 {user.username}")
    db.session.commit()
    return jsonify(_user_dict(user, membership))


@users_bp.route("/<int:id>", methods=["DELETE"])
@role_required("admin", "tenant_admin")
def delete_user(id):
    membership = TenantMembership.query.filter_by(tenant_id=_current_tenant_id(), user_id=id).first_or_404()
    user = membership.user
    if user.id == request.current_user.id:
        return jsonify({"error": "不能删除当前登录账号"}), 400
    if user.username == "admin":
        return jsonify({"error": "不能删除管理员账号"}), 400
    _log(_current_tenant_id(), request.current_user.id, "delete", "user", user.id, f"移出租户用户 {user.username}")
    db.session.delete(membership)
    db.session.commit()
    return jsonify({"message": "删除成功"})
