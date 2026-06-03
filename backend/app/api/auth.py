import time
from flask import Blueprint, request, jsonify
from ..extensions import db, bcrypt
from ..models.user import User
from ..models.operation_log import OperationLog
from ..utils.auth import generate_token, decode_token
from ..utils.token_blocklist import revoke_token
from ..config import Config

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# In-memory login attempt tracking: {username: {"count": N, "locked_until": timestamp}}
_login_attempts = {}


def _check_login_lock(username):
    """Check if account is temporarily locked. Returns (locked, remaining_seconds)."""
    attempt = _login_attempts.get(username)
    if not attempt:
        return False, 0
    if attempt.get("locked_until") and time.time() < attempt["locked_until"]:
        remaining = int(attempt["locked_until"] - time.time())
        return True, remaining
    # Lock expired, reset
    if attempt.get("locked_until"):
        _login_attempts.pop(username, None)
    return False, 0


def _record_failed_login(username):
    """Record a failed login attempt."""
    max_attempts = Config.LOGIN_MAX_ATTEMPTS
    lockout_seconds = Config.LOGIN_LOCKOUT_MINUTES * 60

    attempt = _login_attempts.get(username, {"count": 0, "locked_until": None})
    attempt["count"] += 1
    if attempt["count"] >= max_attempts:
        attempt["locked_until"] = time.time() + lockout_seconds
        attempt["count"] = 0
    _login_attempts[username] = attempt


def _clear_failed_login(username):
    """Clear failed login attempts on success."""
    _login_attempts.pop(username, None)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "账号和密码不能为空"}), 400

    # Check lockout
    locked, remaining = _check_login_lock(username)
    if locked:
        return jsonify({"error": f"登录尝试过多，请 {remaining} 秒后再试"}), 429

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        _record_failed_login(username)
        # Log failed attempt
        if user:
            log = OperationLog(
                user_id=user.id, action="login_failed",
                target_type="user", target_id=user.id,
                detail="登录失败：密码错误",
            )
            db.session.add(log)
            db.session.commit()
        return jsonify({"error": "账号或密码错误"}), 401

    if user.status == "disabled":
        return jsonify({"error": "该账号已停用"}), 403

    _clear_failed_login(username)
    role_code = user.role.code if user.role else ""
    token = generate_token(user.id, role_code)

    log = OperationLog(
        user_id=user.id, action="login",
        target_type="user", target_id=user.id,
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
        # Revoke the token
        jti = payload.get("jti")
        if jti:
            revoke_token(jti, payload.get("exp", 0))
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
