"""Băm mật khẩu (bcrypt) + JWT (HS256, 8h) + refresh token (DGT-04) — TDD §5.1, §5.2, §12."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import bcrypt
import jwt

from app.config import get_settings

ALGO = "HS256"
TOKEN_TTL_HOURS = 8

# Refresh token cho phiên tool vĩnh viễn (DGT-04, TDD §12):
# - lưu HASH (sha256 hex) ở DB, KHÔNG plaintext; trả plaintext đúng 1 lần cho tool.
# - xoay một-lần-dùng; không TTL lịch (phục vụ "vĩnh viễn") nhưng revoke được.
# - ÂN HẠN: refresh đã dùng mà gọi lại trong khoảng này → coi là retry mạng (máy CSDT
#   chập chờn), cấp token mới; gọi lại SAU khoảng này → replay thật → thu hồi cả chuỗi.
REFRESH_GRACE_SECONDS = 60


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


def hash_refresh_token(raw: str) -> str:
    """SHA-256 hex của refresh token — thứ DUY NHẤT lưu ở DB (không lưu plaintext)."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def tao_refresh_token() -> tuple[str, str]:
    """Sinh refresh token mới → (plaintext trả cho tool 1 lần, hash lưu DB)."""
    raw = secrets.token_urlsafe(48)
    return raw, hash_refresh_token(raw)
