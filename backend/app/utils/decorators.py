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
        user = db.session.get(User, payload["user_id"])
        if not user or user.status == "disabled":
            return jsonify({"error": "用户不可用"}), 401
        request.current_user = user
        return f(*args, **kwargs)

    return decorated
