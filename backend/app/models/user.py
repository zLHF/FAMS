from ..extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(64))
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    status = db.Column(db.String(16), default="active")

    # SSO 相关字段
    plt_account = db.Column(db.String(128), unique=True, nullable=True, index=True)
    plt_user_cn = db.Column(db.String(128), nullable=True)
    sso_user = db.Column(db.Boolean, default=False, nullable=False)
