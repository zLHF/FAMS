import uuid
import jwt
from datetime import datetime, timedelta, timezone
from ..config import Config


def generate_token(user_id, role_code="", tenant_id=None, membership_id=None):
    payload = {
        "user_id": user_id,
        "role_code": role_code,
        "tenant_id": tenant_id,
        "membership_id": membership_id,
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc),
        "iss": "fams",
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


def decode_token(token):
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"], options={"require": ["exp", "iat", "jti"]})
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
