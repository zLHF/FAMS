def register_blueprints(app):
    from .auth import auth_bp
    from .users import users_bp
    from .roles import roles_bp
    from .permissions import perms_bp
    from .asset_params import params_bp
    from .assets import assets_bp
    from .dashboard import dashboard_bp
    from .logs import logs_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(roles_bp)
    app.register_blueprint(perms_bp)
    app.register_blueprint(params_bp)
    app.register_blueprint(assets_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(logs_bp)
