from datetime import datetime, timezone
from ..extensions import db


class FlowRecord(db.Model):
    __tablename__ = "flow_records"

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.id"), nullable=False)
    flow_type = db.Column(db.String(32), nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    detail = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    asset = db.relationship("Asset", backref="flow_records")
    operator = db.relationship("User")
