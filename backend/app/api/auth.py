import time
from flask import Blueprint, request, jsonify
from ..extensions import db, bcrypt
from ..models.user import User
from ..models.operation_log import OperationLog
from ..models.tenant import Tenant
from ..models.tenant_membership import TenantMembership
from ..models.role import Role
from ..utils.auth import generate_token, decode_token
from ..utils.token_blocklist import revoke_token
from ..utils.tenant import ensure_default_tenant, ensure_membership
from ..utils.decorators import _is_system_admin
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


def _tenant_dict(membership):
    return {
        "id": membership.tenant.id,
        "name": membership.tenant.name,
        "code": membership.tenant.code,
        "role": membership.role.code if membership.role else "",
        "is_default": membership.is_default,
    }


def _active_memberships(user):
    return (
        TenantMembership.query.join(Tenant)
        .filter(
            TenantMembership.user_id == user.id,
            TenantMembership.status == "active",
            Tenant.status == "active",
        )
        .order_by(TenantMembership.is_default.desc(), TenantMembership.id)
        .all()
    )


def _ensure_user_membership(user):
    memberships = _active_memberships(user)
    if memberships:
        return memberships
    tenant = ensure_default_tenant()
    membership = ensure_membership(user, tenant=tenant, role=user.role)
    db.session.commit()
    return [membership] if membership else []


def _user_payload(user, membership):
    role_code = membership.role.code if membership and membership.role else user.role.code if user.role else ""
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "role": role_code,
        "department": membership.department if membership else user.department,
        "tenant": {
            "id": membership.tenant.id,
            "name": membership.tenant.name,
            "code": membership.tenant.code,
        } if membership else None,
    }


def _issue_login_response(user, membership, memberships=None):
    role_code = membership.role.code if membership and membership.role else ""
    token = generate_token(user.id, role_code, membership.tenant_id if membership else None, membership.id if membership else None)
    return {
        "token": token,
        "user": _user_payload(user, membership),
        "tenant": _tenant_dict(membership) if membership else None,
        "tenants": [_tenant_dict(m) for m in memberships] if memberships is not None else None,
    }


def _system_admin_login_response(user):
    """系统管理员登录响应 — 返回所有租户列表。"""
    all_tenants = Tenant.query.filter_by(status="active").order_by(Tenant.id).all()
    token = generate_token(user.id, "system_admin", None, None)
    return {
        "token": token,
        "user": _user_payload(user, None),
        "tenant": None,
        "tenants": [
            {"id": t.id, "name": t.name, "code": t.code, "role": "system_admin", "is_default": False}
            for t in all_tenants
        ],
    }


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    tenant_id = data.get("tenant_id")

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

    # 系统管理员走特殊登录逻辑
    if _is_system_admin(user):
        log = OperationLog(
            user_id=user.id, action="login",
            target_type="user", target_id=user.id,
            detail="系统管理员登录",
        )
        db.session.add(log)
        db.session.commit()
        return jsonify(_system_admin_login_response(user))

    # 普通用户走现有逻辑
    memberships = _ensure_user_membership(user)
    if not memberships:
        return jsonify({"error": "该账号未加入任何租户"}), 403

    membership = memberships[0]
    if tenant_id:
        membership = next((m for m in memberships if m.tenant_id == int(tenant_id)), None)
        if not membership:
            return jsonify({"error": "无权访问所选租户"}), 403

    log = OperationLog(
        tenant_id=membership.tenant_id,
        user_id=user.id, action="login",
        target_type="user", target_id=user.id,
        detail="用户登录",
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(_issue_login_response(user, membership, memberships))


@auth_bp.route("/tenants", methods=["GET"])
def tenants():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header[7:] if auth_header.startswith("Bearer ") else ""
    payload = decode_token(token)
    if not payload:
        return jsonify({"error": "未登录或登录已过期"}), 401

    user = db.session.get(User, payload["user_id"])
    if not user or user.status == "disabled":
        return jsonify({"error": "用户不存在或已停用"}), 401

    # 系统管理员返回所有租户
    if _is_system_admin(user):
        all_tenants = Tenant.query.filter_by(status="active").order_by(Tenant.id).all()
        return jsonify({"items": [
            {"id": t.id, "name": t.name, "code": t.code, "role": "system_admin", "is_default": False}
            for t in all_tenants
        ]})

    # 普通用户返回已加入的租户
    memberships = _ensure_user_membership(user)
    return jsonify({"items": [_tenant_dict(m) for m in memberships]})


@auth_bp.route("/switch-tenant", methods=["POST"])
def switch_tenant():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header[7:] if auth_header.startswith("Bearer ") else ""
    payload = decode_token(token)
    if not payload:
        return jsonify({"error": "未登录或登录已过期"}), 401
    data = request.get_json() or {}
    tenant_id = data.get("tenant_id")
    if not tenant_id:
        return jsonify({"error": "请选择租户"}), 400

    user = db.session.get(User, payload["user_id"])
    if not user or user.status == "disabled":
        return jsonify({"error": "用户不存在或已停用"}), 401

    tenant = db.session.get(Tenant, int(tenant_id))
    if not tenant or tenant.status == "disabled":
        return jsonify({"error": "租户不存在或已停用"}), 403

    # 系统管理员可切换到任意租户
    if _is_system_admin(user):
        all_tenants = Tenant.query.filter_by(status="active").order_by(Tenant.id).all()

        # 查找或创建 membership
        membership = TenantMembership.query.filter_by(
            tenant_id=tenant.id, user_id=user.id, status="active"
        ).first()

        if not membership:
            tenant_admin_role = Role.query.filter_by(
                tenant_id=tenant.id, code="tenant_admin"
            ).first()
            membership = TenantMembership(
                tenant_id=tenant.id,
                user_id=user.id,
                role_id=tenant_admin_role.id if tenant_admin_role else None,
                status="active",
                is_default=False,
            )
            db.session.add(membership)
            db.session.flush()

        role_code = membership.role.code if membership.role else "system_admin"
        new_token = generate_token(user.id, role_code, tenant.id, membership.id)
        return jsonify({
            "token": new_token,
            "user": _user_payload(user, membership),
            "tenant": _tenant_dict(membership),
            "tenants": [
                {"id": t.id, "name": t.name, "code": t.code, "role": "system_admin", "is_default": False}
                for t in all_tenants
            ],
        })

    # 普通用户只能切换到已加入的租户
    memberships = _ensure_user_membership(user)
    membership = next((m for m in memberships if m.tenant_id == int(tenant_id)), None)
    if not membership:
        return jsonify({"error": "无权访问所选租户"}), 403
    return jsonify(_issue_login_response(user, membership, memberships))


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
            tenant_id=payload.get("tenant_id"),
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

    # 系统管理员
    if _is_system_admin(user):
        result = _user_payload(user, None)
        all_tenants = Tenant.query.filter_by(status="active").order_by(Tenant.id).all()
        result["tenants"] = [
            {"id": t.id, "name": t.name, "code": t.code, "role": "system_admin", "is_default": False}
            for t in all_tenants
        ]
        result["tenant"] = None
        return jsonify(result)

    # 普通用户
    memberships = _ensure_user_membership(user)
    tenant_id = payload.get("tenant_id")
    membership = next((m for m in memberships if m.tenant_id == tenant_id), None) or memberships[0]
    result = _user_payload(user, membership)
    result["tenants"] = [_tenant_dict(m) for m in memberships]
    result["tenant"] = _tenant_dict(membership)
    return jsonify(result)
