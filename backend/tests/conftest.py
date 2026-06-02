import pytest
from app import create_app
from app.extensions import db as _db
import uuid


@pytest.fixture(scope="function")
def app():
    app = create_app()
    # 每个测试用独立的内存数据库（唯一 URI 防止 SQLite 连接池共享）
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(uuid.uuid4())
    app.config["TESTING"] = True
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db
