from functools import wraps
from flask import request, jsonify
from ..extensions import db
from ..utils.auth import decode_token
from ..models.user import User
from ..models.tenant import Tenant
from ..models.tenant_membership import TenantMembership
from ..models.role import Role


def _is_system_admin(user):
    """判断用户是否为系统管理员（通过全局角色）。"""
    return user.role and user.role.code == "system_admin"


def _load_auth_context():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, (jsonify({"error": "未登录"}), 401)
    token = auth_header[7:]
    payload = decode_token(token)
    if not payload:
        return None, (jsonify({"error": "登录已过期"}), 401)

    from ..utils.token_blocklist import is_token_revoked
    jti = payload.get("jti")
    if jti and is_token_revoked(jti):
        return None, (jsonify({"error": "登录已过期"}), 401)

    user = db.session.get(User, payload["user_id"])
    if not user or user.status == "disabled":
        return None, (jsonify({"error": "用户不可用"}), 401)

    # 判断是否为系统管理员
    system_admin = _is_system_admin(user)

    tenant = None
    membership = None
    tenant_id = payload.get("tenant_id")
    membership_id = payload.get("membership_id")

    # 系统管理员未选择租户时，允许无 membership 访问
    if system_admin and not tenant_id:
        request.current_user = user
        request.current_tenant = None
        request.current_membership = None
        request.current_role = user.role
        request.is_system_admin = True
        return payload, None

    # 加载租户
    if tenant_id:
        tenant = db.session.get(Tenant, tenant_id)
        if not tenant or tenant.status == "disabled":
            return None, (jsonify({"error": "租户不可用"}), 403)
        membership_query = TenantMembership.query.filter_by(
            tenant_id=tenant.id, user_id=user.id, status="active"
        )
        if membership_id:
            membership_query = membership_query.filter_by(id=membership_id)
        membership = membership_query.first()

    # 系统管理员切换到某租户但没有 membership → 自动创建
    if not membership and system_admin and tenant:
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

    # 普通用户无租户时，尝试使用默认租户
    if not membership and not system_admin:
        membership = (
            TenantMembership.query.join(Tenant)
            .filter(
                TenantMembership.user_id == user.id,
                TenantMembership.status == "active",
                Tenant.status == "active",
            )
            .order_by(TenantMembership.is_default.desc(), TenantMembership.id)
            .first()
        )
        tenant = membership.tenant if membership else None

    if not membership and not system_admin:
        return None, (jsonify({"error": "用户不属于当前租户"}), 403)

    request.current_user = user
    request.current_tenant = tenant
    request.current_membership = membership
    request.current_role = membership.role if membership else user.role
    request.is_system_admin = system_admin
    return payload, None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        _, error = _load_auth_context()
        if error:
            return error
        return f(*args, **kwargs)

    return decorated


def role_required(*roles):
    """Decorator to require specific role codes in current tenant context.
    系统管理员（system_admin）始终放行。
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            _, error = _load_auth_context()
            if error:
                return error

            # 系统管理员始终放行
            if getattr(request, "is_system_admin", False):
                return f(*args, **kwargs)

            role = getattr(request, "current_role", None)
            role_code = role.code if role else ""
            if role_code not in roles:
                return jsonify({"error": "权限不足"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
