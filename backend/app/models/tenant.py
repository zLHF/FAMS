from datetime import datetime, timezone
from ..extensions import db


class Tenant(db.Model):
    __tablename__ = "tenants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    status = db.Column(db.String(16), default="active", nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # SSO 相关字段
    plt_enterprise_name = db.Column(db.String(256), nullable=True)
