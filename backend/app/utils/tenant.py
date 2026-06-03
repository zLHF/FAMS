from flask import request
from ..extensions import db
from ..models.tenant import Tenant
from ..models.tenant_membership import TenantMembership

DEFAULT_TENANT_CODE = "default"
DEFAULT_TENANT_NAME = "默认租户"


def ensure_default_tenant():
    tenant = Tenant.query.filter_by(code=DEFAULT_TENANT_CODE).first()
    if tenant:
        return tenant
    tenant = Tenant(name=DEFAULT_TENANT_NAME, code=DEFAULT_TENANT_CODE, status="active")
    db.session.add(tenant)
    db.session.flush()
    return tenant


def ensure_membership(user, tenant=None, role=None, is_default=True):
    tenant = tenant or ensure_default_tenant()
    role = role or user.role
    if not role:
        return None
    if role.tenant_id is None:
        role.tenant_id = tenant.id
    membership = TenantMembership.query.filter_by(tenant_id=tenant.id, user_id=user.id).first()
    if membership:
        return membership
    membership = TenantMembership(
        tenant_id=tenant.id,
        user_id=user.id,
        role_id=role.id,
        department=user.department,
        status=user.status or "active",
        is_default=is_default,
    )
    db.session.add(membership)
    db.session.flush()
    return membership


def current_tenant_id():
    tenant = getattr(request, "current_tenant", None)
    return tenant.id if tenant else None


def scoped_query(model):
    tenant_id = current_tenant_id()
    return model.query.filter_by(tenant_id=tenant_id)


def get_scoped_or_404(model, id):
    return scoped_query(model).filter_by(id=id).first_or_404()


def is_tenant_member(user_id, tenant_id):
    return TenantMembership.query.filter_by(
        user_id=user_id, tenant_id=tenant_id, status="active"
    ).first()
