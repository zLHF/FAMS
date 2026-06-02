from ..extensions import db

role_permissions = db.Table(
    "role_permissions",
    db.Column("role_id", db.Integer, db.ForeignKey("roles.id"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permissions.id"), primary_key=True),
)


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    code = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    status = db.Column(db.String(16), default="active")

    users = db.relationship("User", backref="role", lazy="dynamic")
    permissions = db.relationship(
        "Permission", secondary="role_permissions", backref="roles", lazy="dynamic"
    )
