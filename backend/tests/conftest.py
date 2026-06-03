import pytest
from app import create_app
from app.config import Config
from app.extensions import db as _db
import uuid


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def app():
    class UniqueTestConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/%s.db" % uuid.uuid4()

    app = create_app(UniqueTestConfig)
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
