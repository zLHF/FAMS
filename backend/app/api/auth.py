from flask import Blueprint, request, jsonify
from ..extensions import db, bcrypt
from ..models.user import User
from ..models.operation_log import OperationLog
from ..utils.auth import generate_token, decode_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "账号和密码不能为空"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "账号或密码错误"}), 401

    if user.status == "disabled":
        return jsonify({"error": "该账号已停用"}), 403

    role_code = user.role.code if user.role else ""
    token = generate_token(user.id, role_code)

    log = OperationLog(
        user_id=user.id,
        action="login",
        target_type="user",
        target_id=user.id,
        detail="用户登录",
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(
        {
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "name": user.name,
                "role": role_code,
                "department": user.department,
            },
        }
    )


@auth_bp.route("/logout", methods=["POST"])
def logout():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header[7:] if auth_header.startswith("Bearer ") else ""
    payload = decode_token(token) if token else None
    if payload:
        log = OperationLog(
            user_id=payload["user_id"],
            action="logout",
            target_type="user",
            target_id=payload["user_id"],
            detail="用户登出",
        )
        db.session.add(log)
        db.session.commit()
    return jsonify({"message": "已登出"})


@auth_bp.route("/me", methods=["GET"])
def me():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header[7:] if auth_header.startswith("Bearer ") else ""
    payload = decode_token(token)
    if not payload:
        return jsonify({"error": "未登录或登录已过期"}), 401

    user = db.session.get(User, payload["user_id"])
    if not user or user.status == "disabled":
        return jsonify({"error": "用户不存在或已停用"}), 401

    role_code = user.role.code if user.role else ""
    return jsonify(
        {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "role": role_code,
            "department": user.department,
        }
    )
