from app.extensions import db, bcrypt
from app.models.user import User
from app.models.role import Role
from app.models.tenant import Tenant
from app.models.tenant_membership import TenantMembership


def setup_admin(db):
    tenant = Tenant(name="默认租户", code="default", status="active")
    db.session.add(tenant)
    db.session.flush()
    role = Role(tenant_id=tenant.id, name="管理员", code="admin", status="active")
    db.session.add(role)
    db.session.flush()
    user = User(
        username="admin",
        password_hash=bcrypt.generate_password_hash("123456").decode("utf-8"),
        name="管理员", role_id=role.id, status="active",
    )
    db.session.add(user)
    db.session.flush()
    db.session.add(TenantMembership(tenant_id=tenant.id, user_id=user.id, role_id=role.id, status="active", is_default=True))
    db.session.commit()
    return user, role


def get_token(client, username="admin", password="123456"):
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    return resp.get_json()["token"]


def headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_login_success(client, db, app):
    with app.app_context():
        setup_admin(db)
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "123456"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "token" in data
    assert data["user"]["username"] == "admin"


def test_login_wrong_password(client, db, app):
    with app.app_context():
        setup_admin(db)
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


def test_login_missing_fields(client):
    resp = client.post("/api/auth/login", json={"username": ""})
    assert resp.status_code == 400


def test_me_with_valid_token(client, db, app):
    with app.app_context():
        setup_admin(db)
    token = get_token(client)
    resp = client.get("/api/auth/me", headers=headers(token))
    assert resp.status_code == 200
    assert resp.get_json()["username"] == "admin"


def test_me_without_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401
