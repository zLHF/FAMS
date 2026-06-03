from functools import wraps
from flask import request, jsonify
from ..extensions import db
from ..utils.auth import decode_token
from ..models.user import User


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "未登录"}), 401
        token = auth_header[7:]
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "登录已过期"}), 401
        # Check token revocation
        from ..utils.token_blocklist import is_token_revoked
        jti = payload.get("jti")
        if jti and is_token_revoked(jti):
            return jsonify({"error": "登录已过期"}), 401
        user = db.session.get(User, payload["user_id"])
        if not user or user.status == "disabled":
            return jsonify({"error": "用户不可用"}), 401
        request.current_user = user
        return f(*args, **kwargs)

    return decorated


def role_required(*roles):
    """Decorator to require specific role codes. Usage: @role_required('admin', 'asset_manager')"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "未登录"}), 401
            token = auth_header[7:]
            payload = decode_token(token)
            if not payload:
                return jsonify({"error": "登录已过期"}), 401
            # Check token revocation
            from ..utils.token_blocklist import is_token_revoked
            jti = payload.get("jti")
            if jti and is_token_revoked(jti):
                return jsonify({"error": "登录已过期"}), 401
            user = db.session.get(User, payload["user_id"])
            if not user or user.status == "disabled":
                return jsonify({"error": "用户不可用"}), 401
            role_code = user.role.code if user.role else ""
            if role_code not in roles:
                return jsonify({"error": "权限不足"}), 403
            request.current_user = user
            return f(*args, **kwargs)
        return decorated
    return decorator
