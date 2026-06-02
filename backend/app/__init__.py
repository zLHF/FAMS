from flask import Flask
from flask_cors import CORS
from .config import Config
from .extensions import db, migrate, bcrypt


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, supports_credentials=True)
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    # 导入模型以确保 migrate / create_all 能发现
    from . import models  # noqa: F401

    from .api import register_blueprints
    register_blueprints(app)

    return app
