from ..extensions import db

role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True),
)


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256))
    status = db.Column(db.String(16), default="active")

    tenant = db.relationship("Tenant", backref="roles")
    users = db.relationship("User", backref="role", lazy="dynamic")
    permissions = db.relationship(
        "Permission", secondary="role_permissions", backref="roles", lazy="dynamic"
    )

    __table_args__ = (
        db.UniqueConstraint("tenant_id", "name", name="uq_role_tenant_name"),
        db.UniqueConstraint("tenant_id", "code", name="uq_role_tenant_code"),
    )
