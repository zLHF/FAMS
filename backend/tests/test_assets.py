from app.extensions import db, bcrypt
from app.models.user import User
from app.models.role import Role
from app.models.tenant import Tenant
from app.models.tenant_membership import TenantMembership
from app.models.asset import Asset


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


def test_create_and_get(client, db, app):
    with app.app_context():
        setup_admin(db)
    t = get_token(client)
    r = client.post("/api/assets", json={"code": "T001", "name": "测试资产", "unit": "台", "location": "库房"}, headers=h(t))
    assert r.status_code == 201
    aid = r.get_json()["id"]
    r2 = client.get(f"/api/assets/{aid}", headers=h(t))
    assert r2.get_json()["code"] == "T001"


def test_duplicate_code(client, db, app):
    with app.app_context():
        setup_admin(db)
    t = get_token(client)
    client.post("/api/assets", json={"code": "T001", "name": "资产1"}, headers=h(t))
    r = client.post("/api/assets", json={"code": "T001", "name": "资产2"}, headers=h(t))
    assert r.status_code == 400


def test_list_with_filter(client, db, app):
    with app.app_context():
        setup_admin(db)
        db.session.add(Asset(tenant_id=1, code="A001", name="电脑", status="idle"))
        db.session.add(Asset(tenant_id=1, code="A002", name="桌子", status="distributed"))
        db.session.commit()
    t = get_token(client)
    r = client.get("/api/assets?status=idle", headers=h(t))
    assert r.get_json()["total"] == 1


def test_distribute_flow(client, db, app):
    with app.app_context():
        uid, _ = setup_admin(db)
        db.session.add(Asset(tenant_id=1, code="F001", name="流转测试", status="idle"))
        db.session.commit()
    t = get_token(client)
    a = client.get("/api/assets?code=F001", headers=h(t)).get_json()["items"][0]
    r = client.post(f"/api/assets/{a['id']}/distribute", json={"owner_id": uid, "location": "研发部"}, headers=h(t))
    assert r.status_code == 200
    assert r.get_json()["status"] == "distributed"
    r = client.post(f"/api/assets/{a['id']}/revert", json={"location": "库房", "condition": "完好"}, headers=h(t))
    assert r.status_code == 200
    assert r.get_json()["status"] == "returned"
    r = client.post(f"/api/assets/{a['id']}/revert", json={"location": "库房"}, headers=h(t))
    assert r.status_code == 400


def test_borrow_return_flow(client, db, app):
    with app.app_context():
        uid, _ = setup_admin(db)
        db.session.add(Asset(tenant_id=1, code="B001", name="借用测试", status="idle"))
        db.session.commit()
    t = get_token(client)
    a = client.get("/api/assets?code=B001", headers=h(t)).get_json()["items"][0]
    r = client.post(f"/api/assets/{a['id']}/borrow", json={"borrower_id": uid, "expected_return_date": "2026-12-31"}, headers=h(t))
    assert r.status_code == 200
    assert r.get_json()["status"] == "borrowing"
    r = client.post(f"/api/assets/{a['id']}/return", json={"location": "库房", "condition": "完好"}, headers=h(t))
    assert r.status_code == 200
    assert r.get_json()["status"] == "returned"


def test_owner_change_flow(client, db, app):
    with app.app_context():
        uid, rid = setup_admin(db)
        user2 = User(username="u2", password_hash=bcrypt.generate_password_hash("123456").decode(), name="用户2", role_id=rid, status="active")
        db.session.add(user2)
        db.session.flush()
        db.session.add(TenantMembership(tenant_id=1, user_id=user2.id, role_id=rid, status="active", is_default=True))
        db.session.add(Asset(tenant_id=1, code="C001", name="变更测试", status="distributed", owner_id=uid))
        db.session.commit()
        uid2 = user2.id
    t = get_token(client)
    a = client.get("/api/assets?code=C001", headers=h(t)).get_json()["items"][0]
    r = client.post(f"/api/assets/{a['id']}/owner-change", json={"new_owner_id": uid2, "location": "市场部"}, headers=h(t))
    assert r.status_code == 200


def test_assets_are_scoped_by_tenant(client, db, app):
    with app.app_context():
        uid, role_id = setup_admin(db)
        tenant2 = Tenant(name="第二租户", code="tenant2", status="active")
        db.session.add(tenant2)
        db.session.flush()
        role2 = Role(tenant_id=tenant2.id, name="管理员", code="admin", status="active")
        db.session.add(role2)
        db.session.flush()
        db.session.add(TenantMembership(tenant_id=tenant2.id, user_id=uid, role_id=role2.id, status="active", is_default=False))
        db.session.add(Asset(tenant_id=1, code="SAME", name="默认租户资产", status="idle"))
        db.session.add(Asset(tenant_id=tenant2.id, code="SAME", name="第二租户资产", status="idle"))
        db.session.commit()

    token = get_token(client)
    resp = client.get("/api/assets?code=SAME", headers=h(token))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "默认租户资产"

    switched = client.post("/api/auth/switch-tenant", json={"tenant_id": 2}, headers=h(token))
    assert switched.status_code == 200
    token2 = switched.get_json()["token"]
    resp = client.get("/api/assets?code=SAME", headers=h(token2))
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "第二租户资产"
