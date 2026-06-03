from datetime import datetime, timezone
from ..extensions import db


class TenantMembership(db.Model):
    __tablename__ = "tenant_memberships"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    department = db.Column(db.String(64))
    status = db.Column(db.String(16), default="active", nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    tenant = db.relationship("Tenant", backref="memberships")
    user = db.relationship("User", backref="tenant_memberships")
    role = db.relationship("Role", backref="tenant_memberships")

    __table_args__ = (
        db.UniqueConstraint("tenant_id", "user_id", name="uq_tenant_membership_user"),
    )
