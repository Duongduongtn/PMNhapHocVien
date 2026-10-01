"""Băm mật khẩu (bcrypt) + JWT (HS256, 8h) — TDD §5.1, §5.2."""
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import bcrypt
import jwt

from app.config import get_settings

ALGO = "HS256"
TOKEN_TTL_HOURS = 8


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(*, sub: UUID, username: str, vai_tro: str) -> tuple[str, UUID, datetime]:
    """Trả (token, jti, exp) — jti/exp để ghi blocklist khi logout."""
    now = datetime.now(timezone.utc)
    jti = uuid4()
    exp = now + timedelta(hours=TOKEN_TTL_HOURS)
    payload = {
        "sub": str(sub),
        "username": username,
        "vai_tro": vai_tro,
        "jti": str(jti),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    token = jwt.encode(payload, get_settings().jwt_secret, algorithm=ALGO)
    return token, jti, exp


def decode_token(token: str) -> dict:
    """Giải mã + verify chữ ký & hạn. Ném jwt.PyJWTError nếu sai/hết hạn."""
    return jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGO])
