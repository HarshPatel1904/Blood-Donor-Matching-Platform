import datetime
from typing import Dict, Any, Optional
import jwt
from app.config import Config


def generate_jwt_token(user_id: str, email: str, role: str, expires_in_hours: int = 24) -> str:
    """
    Generates a signed HS256 JWT token containing user identification claims.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": now,
        "exp": now + datetime.timedelta(hours=expires_in_hours)
    }
    token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")
    # PyJWT 2.x returns a str; ensure it is decoded string
    return token if isinstance(token, str) else token.decode("utf-8")


def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and verifies a JWT token. Returns payload dict if valid, None if expired or invalid.
    """
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None