"""Open API 蓝图 — 应用用户开通接口（2.4.2.1）。

由算力网络平台在应用订购后自动调用，用于创建/匹配本地租户和用户。
接口地址: POST /open-api/app/tenants
"""

import logging
import secrets
import uuid

from flask import Blueprint, request, jsonify

from ..config import Config
from ..extensions import db, bcrypt
from ..models.user import User
from ..models.tenant import Tenant
from ..models.tenant_membership import TenantMembership
from ..models.role import Role
from ..utils.auth import generate_token

logger = logging.getLogger(__name__)

open_api_bp = Blueprint("open_api", __name__, url_prefix="/open-api")


def _make_response(code, msg, data=None, trace_id=None):
    """构造符合平台规范的返回格式。"""
    return jsonify({
        "code": code,
        "msg": msg,
        "data": data,
        "traceId": trace_id or uuid.uuid4().hex[:16],
    })


@open_api_bp.route("/app/tenants", methods=["POST"])
def create_tenant():
    """应用用户开通接口。

    平台在用户订购应用后调用此接口，自动创建/匹配本地租户和用户。
    相同企业下相同账号重复开通不报错，直接返回已有信息。
    """
    data = request.get_json(silent=True) or {}
    trace_id = uuid.uuid4().hex[:16]

    # ---- 参数校验 ----
    required_fields = [
        "enterpriseName", "pltUserCn", "pltAccountLogin",
        "purchaseDuration", "purchaseUnit", "appKey", "appSecret", "code",
    ]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return _make_response(50000, f"调用失败：缺失 {', '.join(missing)} 参数", trace_id=trace_id)

    # ---- 验证 appKey + appSecret ----
    if data["appKey"] != Config.PLATFORM_APP_ID or data["appSecret"] != Config.PLATFORM_APP_SECRET:
        return _make_response(50000, "应用认证失败：appKey 或 appSecret 不匹配", trace_id=trace_id)

    enterprise_name = data["enterpriseName"]
    plt_user_cn = data["pltUserCn"]
    plt_account_login = data["pltAccountLogin"]
    plt_mobile = data.get("pltMobile", "")
    plt_email = data.get("pltEmail", "")

    try:
        # ---- 查找或创建租户 ----
        tenant = Tenant.query.filter(
            db.or_(
                Tenant.plt_enterprise_name == enterprise_name,
                Tenant.name == enterprise_name,
            )
        ).first()

        if not tenant:
            tenant_code = f"plt_{secrets.token_hex(4)}"
            tenant = Tenant(
                name=enterprise_name,
                code=tenant_code,
                plt_enterprise_name=enterprise_name,
                status="active",
            )
            db.session.add(tenant)
            db.session.flush()
            logger.info("创建新租户: id=%s name=%s code=%s", tenant.id, tenant.name, tenant.code)

            # 为新租户创建默认角色
            _ensure_tenant_roles(tenant)
        else:
            logger.info("匹配已有租户: id=%s name=%s", tenant.id, tenant.name)

        # ---- 查找或创建用户 ----
        user = User.query.filter(User.plt_account == plt_account_login).first()

        if not user:
            # 生成一个本地用户名，加 plt_ 前缀避免与本地用户冲突
            local_username = f"plt_{plt_account_login}"
            # 确保用户名唯一
            if User.query.filter_by(username=local_username).first():
                local_username = f"plt_{plt_account_login}_{secrets.token_hex(2)}"

            # 获取默认角色
            asset_manager_role = Role.query.filter_by(
                tenant_id=tenant.id, code="asset_manager"
            ).first()
            tenant_admin_role = Role.query.filter_by(
                tenant_id=tenant.id, code="tenant_admin"
            ).first()
            default_role = tenant_admin_role or asset_manager_role

            user = User(
                username=local_username,
                password_hash=bcrypt.generate_password_hash(secrets.token_hex(16)).decode("utf-8"),
                name=plt_user_cn or plt_account_login,
                phone=plt_mobile,
                plt_account=plt_account_login,
                plt_user_cn=plt_user_cn,
                sso_user=True,
                role_id=default_role.id if default_role else None,
                status="active",
            )
            db.session.add(user)
            db.session.flush()
            logger.info("创建新SSO用户: id=%s plt_account=%s", user.id, plt_account_login)
        else:
            logger.info("匹配已有用户: id=%s plt_account=%s", user.id, user.plt_account)

        # ---- 创建租户成员关系 ----
        membership = TenantMembership.query.filter_by(
            tenant_id=tenant.id, user_id=user.id
        ).first()

        if not membership:
            # 同一租户多个账号订购，默认给最高权限（tenant_admin）
            tenant_admin_role = Role.query.filter_by(tenant_id=tenant.id, code="tenant_admin").first()
            membership = TenantMembership(
                tenant_id=tenant.id,
                user_id=user.id,
                role_id=tenant_admin_role.id if tenant_admin_role else user.role_id,
                status="active",
                is_default=False,
            )
            db.session.add(membership)
            db.session.flush()
            logger.info("创建租户成员关系: tenant=%s user=%s", tenant.id, user.id)
        else:
            logger.info("已有租户成员关系: tenant=%s user=%s", tenant.id, user.id)

        # ---- 生成本地 JWT token ----
        role_code = ""
        if membership.role:
            role_code = membership.role.code
        elif user.role:
            role_code = user.role.code

        token = generate_token(user.id, role_code, tenant.id, membership.id)

        db.session.commit()

        return _make_response(20000, "成功", data={
            "account": user.username,
            "token": token,
            "tenantId": str(tenant.id),
            "tenantInfo": {
                "tenantId": str(tenant.id),
                "tenantName": tenant.name,
                "tenantCode": tenant.code,
            },
        }, trace_id=trace_id)

    except Exception:
        db.session.rollback()
        logger.exception("应用用户开通接口异常")
        return _make_response(50000, "服务内部异常", trace_id=trace_id)


def _ensure_tenant_roles(tenant):
    """为新创建的租户生成默认角色（admin + asset_manager）。"""
    existing_codes = {r.code for r in Role.query.filter_by(tenant_id=tenant.id).all()}

    if "tenant_admin" not in existing_codes:
        tenant_admin_role = Role(
            tenant_id=tenant.id,
            name="租户管理员",
            code="tenant_admin",
            description="租户管理员，拥有本租户全部权限",
            status="active",
        )
        db.session.add(tenant_admin_role)

    if "asset_manager" not in existing_codes:
        asset_role = Role(
            tenant_id=tenant.id,
            name="资产管理员",
            code="asset_manager",
            description="负责资产日常管理",
            status="active",
        )
        db.session.add(asset_role)

    db.session.flush()
