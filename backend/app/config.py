import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

ENV = os.environ.get("FLASK_ENV", "development")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "fams-dev-secret-key-do-not-use-in-prod")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(BASE_DIR, "fams.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET = os.environ.get("JWT_SECRET", "fams-jwt-secret-do-not-use-in-prod")
    JWT_EXPIRATION_HOURS = int(os.environ.get("JWT_EXPIRATION_HOURS", "24"))

    # CORS allowed origins (comma-separated)
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:5001")

    # Login rate limiting
    LOGIN_MAX_ATTEMPTS = int(os.environ.get("LOGIN_MAX_ATTEMPTS", "5"))
    LOGIN_LOCKOUT_MINUTES = int(os.environ.get("LOGIN_LOCKOUT_MINUTES", "15"))

    # Pagination limit
    MAX_PER_PAGE = 100

    @classmethod
    def validate_production(cls):
        """Validate config for production. Raises RuntimeError if unsafe."""
        errors = []
        if ENV == "production":
            if cls.SECRET_KEY.startswith("fams-dev") or cls.JWT_SECRET.startswith("fams-jwt"):
                errors.append("SECRET_KEY and JWT_SECRET must be set via environment variables in production")
            if len(cls.JWT_SECRET) < 32:
                errors.append("JWT_SECRET must be at least 32 characters")
        return errors
