"""Đăng nhập / đăng xuất / thông tin user (TDD §4.2, §5.1)."""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, field_validator
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth import security
from app.auth.deps import get_current_user
from app.auth.security import (
    create_access_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    tao_refresh_token,
    verify_password,
)
from app.db import get_db
from app.models.user import RefreshToken, TokenBlocklist, User

router = APIRouter(prefix="/api/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=True)


class LoginIn(BaseModel):
    username: str
    password: str
    # DGT-04: tool bật cờ này để được cấp refresh token (phiên vĩnh viễn);
    # app web KHÔNG gửi → không nhận refresh, giữ phiên thường.
    cap_refresh: bool = False


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    ho_ten: str | None
    vai_tro: str
    refresh_token: str | None = None   # chỉ có khi cap_refresh=True (DGT-04)


class RefreshIn(BaseModel):
    refresh_token: str


class RefreshOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str   # token MỚI (xoay một-lần-dùng)


class LogoutIn(BaseModel):
    refresh_token: str | None = None   # tool gửi để thu hồi phiên vĩnh viễn


def _thu_hoi_refresh_cua_user(db: Session, user_id) -> None:
    """Xóa TOÀN BỘ refresh token của một user (đổi mật khẩu / khóa TK / phát hiện replay)."""
    db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))


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
    refresh_plain: str | None = None
    if body.cap_refresh:   # DGT-04 — chỉ đăng nhập qua tool
        refresh_plain, refresh_hash = tao_refresh_token()
        db.add(RefreshToken(user_id=user.id, token_hash=refresh_hash))
    db.commit()
    return TokenOut(access_token=token, username=user.username, ho_ten=user.ho_ten,
                    vai_tro=user.vai_tro, refresh_token=refresh_plain)


@router.post("/refresh", response_model=RefreshOut)
def refresh(body: RefreshIn, db: Session = Depends(get_db)) -> RefreshOut:
    """DGT-04 — đổi refresh token lấy cặp (access + refresh) MỚI (xoay một-lần-dùng).

    Refresh không hợp lệ → 401. Tài khoản bị khóa → thu hồi cả chuỗi + 401.
    Dùng lại token đã xoay: trong ân hạn → coi là retry mạng (cấp mới); quá ân hạn →
    replay thật → thu hồi toàn bộ refresh token của user (buộc đăng nhập lại)."""
    h = hash_refresh_token(body.refresh_token.strip())
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == h))
    if row is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Phiên không hợp lệ — đăng nhập lại")

    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        _thu_hoi_refresh_cua_user(db, row.user_id)
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Tài khoản đã bị khóa — đăng nhập lại")

    now = datetime.now(timezone.utc)
    if row.revoked:
        used = row.last_used_at or row.created_at
        if used.tzinfo is None:
            used = used.replace(tzinfo=timezone.utc)
        if (now - used).total_seconds() > security.REFRESH_GRACE_SECONDS:
            # replay thật (token lộ) → thu hồi cả chuỗi
            _thu_hoi_refresh_cua_user(db, user.id)
            db.commit()
            raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                                "Phiên bị thu hồi do phát hiện dùng lại — đăng nhập lại")
        # trong ân hạn → retry mạng, cấp token mới, không thu hồi chuỗi
    else:
        row.revoked = True
        row.last_used_at = now

    access, _jti, _exp = create_access_token(sub=user.id, username=user.username, vai_tro=user.vai_tro)
    raw_new, hash_new = tao_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=hash_new, last_used_at=now))
    db.commit()
    return RefreshOut(access_token=access, refresh_token=raw_new)


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
    _thu_hoi_refresh_cua_user(db, user.id)   # DGT-04 — đổi mật khẩu đá mọi phiên vĩnh viễn
    db.commit()


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    body: LogoutIn | None = None,
    cred: HTTPAuthorizationCredentials = Depends(_bearer),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Thu hồi phiên: ghi jti vào blocklist tới khi token hết hạn (TDD §5.1).

    DGT-04 — tool gửi kèm `refresh_token` để xóa luôn refresh token của phiên
    (lối ra duy nhất của phiên vĩnh viễn). App web không gửi → chỉ blocklist access."""
    payload = decode_token(cred.credentials)
    jti = UUID(payload["jti"])
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    if db.get(TokenBlocklist, jti) is None:
        db.add(TokenBlocklist(jti=jti, exp=exp))
    if body and body.refresh_token:
        db.execute(delete(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(body.refresh_token.strip())))
    db.commit()
