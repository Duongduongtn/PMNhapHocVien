"""Đăng nhập / đăng xuất / thông tin user (TDD §4.2, §5.1)."""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.security import create_access_token, decode_token, hash_password, verify_password
from app.db import get_db
from app.models.user import TokenBlocklist, User

router = APIRouter(prefix="/api/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=True)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    ho_ten: str | None
    vai_tro: str


class MeOut(BaseModel):
    id: UUID
    username: str
    ho_ten: str | None
    vai_tro: str
    is_active: bool


class DoiMatKhauIn(BaseModel):
    mat_khau_hien_tai: str
    mat_khau_moi: str

    @field_validator("mat_khau_moi")
    @classmethod
    def _du_dai(cls, v: str) -> str:
        if not v or len(v) < 4:
            raise ValueError("Mật khẩu mới phải từ 4 ký tự")
        return v


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(User.username == body.username))
    # Thông báo chung cho sai tài khoản/mật khẩu — không tiết lộ username có tồn tại.
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sai tài khoản hoặc mật khẩu")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Tài khoản đã bị khóa")

    token, _jti, _exp = create_access_token(sub=user.id, username=user.username, vai_tro=user.vai_tro)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    return TokenOut(access_token=token, username=user.username, ho_ten=user.ho_ten, vai_tro=user.vai_tro)


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user)) -> MeOut:
    return MeOut(id=user.id, username=user.username, ho_ten=user.ho_ten, vai_tro=user.vai_tro, is_active=user.is_active)


@router.post("/doi-mat-khau", status_code=status.HTTP_204_NO_CONTENT)
def doi_mat_khau(body: DoiMatKhauIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    """Tự đổi mật khẩu của CHÍNH MÌNH (HTG-06). Kiểm mật khẩu hiện tại trước; băm bcrypt.
    Chỉ đổi theo `sub` trong token — không nhận user_id bên ngoài (không đổi hộ người khác)."""
    if not verify_password(body.mat_khau_hien_tai, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Mật khẩu hiện tại không đúng")
    user.password_hash = hash_password(body.mat_khau_moi)
    db.commit()


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    cred: HTTPAuthorizationCredentials = Depends(_bearer),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Thu hồi phiên: ghi jti vào blocklist tới khi token hết hạn (TDD §5.1)."""
    payload = decode_token(cred.credentials)
    jti = UUID(payload["jti"])
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    if db.get(TokenBlocklist, jti) is None:
        db.add(TokenBlocklist(jti=jti, exp=exp))
        db.commit()
