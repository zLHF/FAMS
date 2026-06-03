"""Simple in-memory token blocklist. For production, use Redis or a database table."""
import time

# {jti: expiry_timestamp}
_revoked = {}


def revoke_token(jti: str, exp: int):
    """Add a token's jti to the blocklist."""
    _revoked[jti] = exp


def is_token_revoked(jti: str) -> bool:
    """Check if a token's jti has been revoked."""
    # Lazy cleanup: remove expired entries on check
    now = time.time()
    expired = [k for k, v in _revoked.items() if v <= now]
    for k in expired:
        _revoked.pop(k, None)
    return jti in _revoked


def revoke_all_user_tokens(user_id: int, get_active_jtis=None):
    """Revoke all active tokens for a user. Requires app context to query."""
    # In a production app, store user_tokens in Redis/DB
    # For now, this is a placeholder that can be extended
    pass
