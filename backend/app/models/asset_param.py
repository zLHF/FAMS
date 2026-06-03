from ..extensions import db


class AssetParam(db.Model):
    __tablename__ = "asset_params"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=True, index=True)
    type = db.Column(db.String(32), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(64), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    status = db.Column(db.String(16), default="active")

    tenant = db.relationship("Tenant", backref="asset_params")

    __table_args__ = (
        db.UniqueConstraint("tenant_id", "type", "name", name="uq_asset_param_tenant_type_name"),
    )
