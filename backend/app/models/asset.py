from datetime import datetime, timezone
from ..extensions import db


class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True)
    code = db.Column(db.String(64), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(32))
    brand = db.Column(db.String(64))
    model = db.Column(db.String(64))
    serial_number = db.Column(db.String(64))
    unit = db.Column(db.String(16))
    purchase_date = db.Column(db.Date)
    location = db.Column(db.String(128))
    status = db.Column(db.String(16), default="idle")
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    borrower_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    tenant = db.relationship("Tenant", backref="assets")
    owner = db.relationship("User", foreign_keys=[owner_id], backref="owned_assets")
    borrower = db.relationship(
        "User", foreign_keys=[borrower_id], backref="borrowed_assets"
    )

    __table_args__ = (
        db.UniqueConstraint("tenant_id", "code", name="uq_asset_tenant_code"),
    )
