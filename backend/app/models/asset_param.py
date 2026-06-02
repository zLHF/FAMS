from ..extensions import db


class AssetParam(db.Model):
    __tablename__ = "asset_params"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(32), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(64), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    status = db.Column(db.String(16), default="active")

    __table_args__ = (
        db.UniqueConstraint("type", "name", name="uq_asset_param_type_name"),
    )
