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
        username="admin", password_hash=bcrypt.generate_password_hash("123456").decode(),
        name="管理员", role_id=role.id, status="active",
    )
    db.session.add(user)
    db.session.flush()
    db.session.add(TenantMembership(tenant_id=tenant.id, user_id=user.id, role_id=role.id, status="active", is_default=True))
    db.session.commit()
    return user.id, role.id


def get_token(client):
    return client.post("/api/auth/login", json={"username": "admin", "password": "123456"}).get_json()["token"]


def h(token):
    return {"Authorization": f"Bearer {token}"}


def test_list_users(client, db, app):
    with app.app_context():
        setup_admin(db)
    token = get_token(client)
    resp = client.get("/api/users", headers=h(token))
    assert resp.status_code == 200
    assert resp.get_json()["total"] >= 1


def test_create_user(client, db, app):
    with app.app_context():
        _, role_id = setup_admin(db)
    token = get_token(client)
    resp = client.post("/api/users", json={
        "username": "newuser", "name": "新用户", "password": "123456", "role_id": role_id,
    }, headers=h(token))
    assert resp.status_code == 201
    assert resp.get_json()["username"] == "newuser"


def test_create_duplicate_user(client, db, app):
    with app.app_context():
        setup_admin(db)
    token = get_token(client)
    resp = client.post("/api/users", json={"username": "admin", "name": "重复", "role_id": 1}, headers=h(token))
    assert resp.status_code == 400


def test_update_user(client, db, app):
    with app.app_context():
        uid, _ = setup_admin(db)
    token = get_token(client)
    resp = client.put(f"/api/users/{uid}", json={"name": "改名"}, headers=h(token))
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "改名"


def test_delete_admin_protected(client, db, app):
    with app.app_context():
        uid, _ = setup_admin(db)
    token = get_token(client)
    resp = client.delete(f"/api/users/{uid}", headers=h(token))
    assert resp.status_code == 400
