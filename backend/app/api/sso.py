"""SSO 蓝图 — 处理算力网络平台的单点登录回调。

流程：
1. 前端从 URL 拿到 code 参数，调用 POST /api/sso/callback
2. 后端调用平台 appAuthCheck (接口2) 用 code 换取平台 token
3. 后端调用平台 getUserInfoByToken (接口3) 获取用户信息
4. 匹配/创建本地用户和租户，生成本地 JWT token
5. 返回与 /api/auth/login 格式一致的响应
"""

import logging
import secrets

from flask import Blueprint, request, jsonify

from ..config import Config
from ..extensions import db, bcrypt
from ..models.user import User
from ..models.tenant import Tenant
from ..models.tenant_membership import TenantMembership
from ..models.role import Role
from ..models.operation_log import OperationLog
from ..services import platform_client
from ..utils.auth import generate_token
from ..utils.tenant import ensure_default_tenant, ensure_membership

logger = logging.getLogger(__name__)

sso_bp = Blueprint("sso", __name__, url_prefix="/api/sso")


def _tenant_dict(membership):
    return {
        "id": membership.tenant.id,
        "name": membership.tenant.name,
        "code": membership.tenant.code,
        "role": membership.role.code if membership.role else "",
        "is_default": membership.is_default,
    }


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
    """构造与 /api/auth/login 格式一致的登录响应。"""
    role_code = membership.role.code if membership and membership.role else ""
    token = generate_token(user.id, role_code, membership.tenant_id, membership.id)
    return {
        "token": token,
        "user": _user_payload(user, membership),
        "tenant": _tenant_dict(membership),
        "tenants": [_tenant_dict(m) for m in memberships] if memberships is not None else None,
    }


@sso_bp.route("/callback", methods=["POST"])
def sso_callback():
    """SSO 登录回调接口。

    接收前端传来的 code，调用平台接口完成身份验证，自动登录。
    """
    if not Config.SSO_ENABLED:
        return jsonify({"error": "SSO 功能未启用"}), 403

    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()

    if not code:
        return jsonify({"error": "缺少 code 参数"}), 400

    try:
        # 1. 调用平台身份校验（接口2）
        platform_token = platform_client.auth_check(code)
        logger.info("平台身份校验通过，获取到平台 token")

        # 2. 调用平台用户信息（接口3）
        platform_user_info = platform_client.get_user_info(platform_token)
        logger.info("获取平台用户信息成功: %s", platform_user_info)

        plat_user = platform_user_info.get("user", {})
        plat_tenant = platform_user_info.get("tenant", {})

        login_name = plat_user.get("loginLoginname", "")
        user_cn = plat_user.get("loginUname", "")
        tenant_id_str = plat_tenant.get("tenantID", "")
        tenant_account = plat_tenant.get("tenantAccount", "")
        tenant_password = plat_tenant.get("tenantPassword", "")

        if not login_name:
            return jsonify({"error": "平台用户信息不完整：缺少登录账号"}), 400

        # 3. 匹配/创建本地用户
        user = User.query.filter(User.plt_account == login_name).first()

        if not user:
            local_username = f"plt_{login_name}"
            if User.query.filter_by(username=local_username).first():
                local_username = f"plt_{login_name}_{secrets.token_hex(2)}"

            user = User(
                username=local_username,
                password_hash=bcrypt.generate_password_hash(secrets.token_hex(16)).decode("utf-8"),
                name=user_cn or login_name,
                plt_account=login_name,
                plt_user_cn=user_cn,
                sso_user=True,
                status="active",
            )
            db.session.add(user)
            db.session.flush()
            logger.info("SSO 自动创建用户: id=%s plt_account=%s", user.id, login_name)
        else:
            # 更新用户名（如果平台有变化）
            if user_cn and user.name != user_cn:
                user.name = user_cn
                user.plt_user_cn = user_cn

        # 4. 匹配/创建租户
        membership = None
        if tenant_id_str:
            # 尝试通过平台租户 ID 匹配本地租户
            # 先尝试用 tenant_id_str 匹配本地租户的 code 或 id
            tenant = Tenant.query.filter(
                db.or_(
                    Tenant.code == f"plt_{tenant_id_str}",
                    Tenant.code == tenant_id_str,
                )
            ).first()

            if not tenant:
                # 创建新租户
                tenant = Tenant(
                    name=plat_user.get("loginAccountName", tenant_account or f"租户_{tenant_id_str}"),
                    code=f"plt_{tenant_id_str}",
                    status="active",
                )
                db.session.add(tenant)
                db.session.flush()
                logger.info("SSO 自动创建租户: id=%s code=%s", tenant.id, tenant.code)

                # 为新租户创建默认角色
                _ensure_tenant_roles(tenant)

            # 确保用户属于该租户
            membership = TenantMembership.query.filter_by(
                tenant_id=tenant.id, user_id=user.id
            ).first()

            if not membership:
                admin_role = Role.query.filter_by(tenant_id=tenant.id, code="tenant_admin").first()
                asset_role = Role.query.filter_by(tenant_id=tenant.id, code="asset_manager").first()
                default_role = admin_role or asset_role

                membership = TenantMembership(
                    tenant_id=tenant.id,
                    user_id=user.id,
                    role_id=default_role.id if default_role else None,
                    status="active",
                    is_default=True,
                )
                db.session.add(membership)
                db.session.flush()
                logger.info("SSO 创建成员关系: tenant=%s user=%s", tenant.id, user.id)

        if not membership:
            # 没有租户信息，使用默认租户
            tenant = ensure_default_tenant()
            membership = ensure_membership(user, tenant=tenant)
            db.session.flush()

        # 更新用户的全局角色
        if membership.role and not user.role_id:
            user.role_id = membership.role.id

        # 5. 获取用户全部成员关系，生成登录响应
        all_memberships = TenantMembership.query.filter(
            TenantMembership.user_id == user.id,
            TenantMembership.status == "active",
        ).join(Tenant).filter(Tenant.status == "active").all()

        result = _issue_login_response(user, membership, all_memberships)

        # 6. 记录操作日志
        log = OperationLog(
            tenant_id=membership.tenant_id,
            user_id=user.id,
            action="sso_login",
            target_type="user",
            target_id=user.id,
            detail=f"SSO 登录（平台账号: {login_name}）",
        )
        db.session.add(log)
        db.session.commit()

        logger.info("SSO 登录成功: user=%s tenant=%s", user.id, membership.tenant_id)
        return jsonify(result)

    except platform_client.PlatformError as e:
        logger.warning("SSO 平台接口调用失败: %s", e)
        return jsonify({"error": f"平台认证失败: {e.msg}"}), 401
    except Exception:
        db.session.rollback()
        logger.exception("SSO 回调处理异常")
        return jsonify({"error": "SSO 登录处理失败，请稍后重试"}), 500


def _ensure_tenant_roles(tenant):
    """为新创建的租户生成默认角色。"""
    existing_codes = {r.code for r in Role.query.filter_by(tenant_id=tenant.id).all()}

    if "tenant_admin" not in existing_codes:
        db.session.add(Role(
            tenant_id=tenant.id, name="租户管理员", code="tenant_admin",
            description="租户管理员", status="active",
        ))
    if "asset_manager" not in existing_codes:
        db.session.add(Role(
            tenant_id=tenant.id, name="资产管理员", code="asset_manager",
            description="负责资产日常管理", status="active",
        ))
    db.session.flush()
