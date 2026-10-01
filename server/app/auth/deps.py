"""Dependency xác thực + phân quyền (TDD §5.1, §5.3).

get_current_user: giải mã JWT → kiểm blocklist → đọc is_active + vai_tro TỪ DB
theo sub (không tin claim, để admin khóa/đổi vai trò có hiệu lực ngay).
require_role: gác theo vai trò; admin luôn qua (admin = tất cả, §5.3).
"""
from collections.abc import Callable
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_token
from app.db import get_db
from app.models.user import TokenBlocklist, User

_bearer = HTTPBearer(auto_error=True)


def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(cred.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token không hợp lệ hoặc đã hết hạn")

    sub = payload.get("sub")
    jti = payload.get("jti")
    if not sub or not jti:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token thiếu thông tin")

    if db.get(TokenBlocklist, UUID(jti)) is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Phiên đã đăng xuất")

    user = db.get(User, UUID(sub))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tài khoản không tồn tại hoặc đã bị khóa")
    return user


def require_role(*roles: str) -> Callable[..., User]:
    """Gác endpoint theo vai trò. Admin luôn được phép (admin = tất cả, §5.3)."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.vai_tro == "admin" or user.vai_tro in roles:
            return user
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Không đủ quyền thực hiện")

    return checker
