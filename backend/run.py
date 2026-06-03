import os
from app import create_app
from app.config import Config

app = create_app()

if __name__ == "__main__":
    errors = Config.validate_production()
    if errors:
        for e in errors:
            print(f"FATAL: {e}")
        raise RuntimeError("Production config validation failed")

    debug = os.environ.get("FLASK_ENV", "development") != "production"
    port = int(os.environ.get("PORT", "5001"))
    app.run(debug=debug, port=port)
