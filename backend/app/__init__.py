from flask import Flask
from flask_cors import CORS
from .config import Config
from .extensions import db, migrate, bcrypt


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if hasattr(config_class, "validate_production"):
        errors = config_class.validate_production()
        if errors:
            raise RuntimeError("Production config validation failed: " + "; ".join(errors))

    CORS(app, origins=app.config["CORS_ORIGINS"].split(","), supports_credentials=True)
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    # 导入模型以确保 migrate / create_all 能发现
    from . import models  # noqa: F401

    from .api import register_blueprints
    register_blueprints(app)

    # 启动心跳定时任务（仅非测试环境）
    if not app.config.get("TESTING"):
        from .utils.heartbeat import start_heartbeat_scheduler, stop_heartbeat_scheduler
        start_heartbeat_scheduler(app)

        import atexit
        atexit.register(stop_heartbeat_scheduler)

    return app
