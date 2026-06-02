from ..extensions import db


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    code = db.Column(db.String(64), unique=True, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("permissions.id"))
    sort_order = db.Column(db.Integer, default=0)

    children = db.relationship(
        "Permission", backref=db.backref("parent", remote_side=[id]), lazy="dynamic"
    )
