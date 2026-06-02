from flask import Blueprint, request, jsonify
from ..extensions import db, bcrypt
from ..models.user import User
from ..models.operation_log import OperationLog
from ..utils.decorators import login_required

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


def _user_dict(u):
    return {
        "id": u.id,
        "username": u.username,
        "name": u.name,
        "phone": u.phone,
        "department": u.department,
        "role_id": u.role_id,
        "role_name": u.role.name if u.role else None,
        "status": u.status,
    }


def _log(user_id, action, target_type, target_id, detail):
    db.session.add(
        OperationLog(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
        )
    )


@users_bp.route("", methods=["GET"])
@login_required
def list_users():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    name = request.args.get("name", "")
    role_id = request.args.get("role_id", type=int)
    status = request.args.get("status", "")

    query = User.query
    if name:
        query = query.filter(User.name.contains(name) | User.username.contains(name))
    if role_id:
        query = query.filter_by(role_id=role_id)
    if status:
        query = query.filter_by(status=status)

    pag = query.order_by(User.id).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "items": [_user_dict(u) for u in pag.items],
            "total": pag.total,
            "page": pag.page,
            "per_page": pag.per_page,
        }
    )


@users_bp.route("", methods=["POST"])
@login_required
def create_user():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("name") or not data.get("role_id"):
        return jsonify({"error": "缺少必填字段"}), 400
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "用户账号已存在"}), 400

    user = User(
        username=data["username"],
        password_hash=bcrypt.generate_password_hash(data.get("password", "123456")).decode("utf-8"),
        name=data["name"],
        phone=data.get("phone"),
        department=data.get("department"),
        role_id=data["role_id"],
        status=data.get("status", "active"),
    )
    db.session.add(user)
    _log(request.current_user.id, "create", "user", user.id, f"新增用户 {user.username}")
    db.session.commit()
    return jsonify(_user_dict(user)), 201


@users_bp.route("/<int:id>", methods=["PUT"])
@login_required
def update_user(id):
    user = User.query.filter_by(id=id).first_or_404()
    data = request.get_json()
    if data.get("name"):
        user.name = data["name"]
    if data.get("phone") is not None:
        user.phone = data["phone"]
    if data.get("department") is not None:
        user.department = data["department"]
    if data.get("role_id"):
        user.role_id = data["role_id"]
    if data.get("status"):
        user.status = data["status"]
    if data.get("password"):
        user.password_hash = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    _log(request.current_user.id, "update", "user", user.id, f"修改用户 {user.username}")
    db.session.commit()
    return jsonify(_user_dict(user))


@users_bp.route("/<int:id>", methods=["DELETE"])
@login_required
def delete_user(id):
    user = User.query.filter_by(id=id).first_or_404()
    if user.username == "admin":
        return jsonify({"error": "不能删除管理员账号"}), 400
    _log(request.current_user.id, "delete", "user", user.id, f"删除用户 {user.username}")
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "删除成功"})
