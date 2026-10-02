"""Quản lý tài khoản — chỉ admin (TDD §4.2, §5.3, §5.4).

Không mở self-register: admin đầu tiên tạo bằng scripts/seed_admin.py.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.deps import require_role
from app.auth.security import hash_password
from app.db import get_db
from app.models.user import VAI_TRO, User

router = APIRouter(prefix="/api/admin/users", tags=["admin"])


class UserCreate(BaseModel):
    username: str
    password: str
    ho_ten: str | None = None
    vai_tro: str

    @field_validator("vai_tro")
    @classmethod
    def _role(cls, v: str) -> str:
        if v not in VAI_TRO:
            raise ValueError(f"vai_tro phải là một trong {VAI_TRO}")
        return v


class UserUpdate(BaseModel):
    ho_ten: str | None = None
    vai_tro: str | None = None
    is_active: bool | None = None
    password: str | None = None

    @field_validator("vai_tro")
    @classmethod
    def _role(cls, v: str | None) -> str | None:
        if v is not None and v not in VAI_TRO:
            raise ValueError(f"vai_tro phải là một trong {VAI_TRO}")
        return v


class ResetMatKhau(BaseModel):
    password: str

    @field_validator("password")
    @classmethod
    def _khong_rong(cls, v: str) -> str:
        if not v or len(v) < 4:
            raise ValueError("Mật khẩu phải từ 4 ký tự")
        return v


class UserOut(BaseModel):
    id: UUID
    username: str
    ho_ten: str | None
    vai_tro: str
    is_active: bool


class UserListOut(BaseModel):
    items: list[UserOut]
    total: int


def _ra(user: User) -> UserOut:
    return UserOut(id=user.id, username=user.username, ho_ten=user.ho_ten,
                   vai_tro=user.vai_tro, is_active=user.is_active)


@router.get("", response_model=UserListOut)
def list_users(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> UserListOut:
    """DS tài khoản, phân trang (HTG-05). Mới tạo trước; total để UI đếm trang."""
    total = db.scalar(select(func.count()).select_from(User)) or 0
    rows = db.scalars(
        select(User).order_by(User.created_at.desc(), User.username).limit(limit).offset(offset)
    ).all()
    return UserListOut(items=[_ra(u) for u in rows], total=total)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, _admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> UserOut:
    if db.scalar(select(User).where(User.username == body.username)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Tên đăng nhập đã tồn tại")
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        ho_ten=body.ho_ten,
        vai_tro=body.vai_tro,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _ra(user)


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: UUID, body: UserUpdate, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> UserOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài khoản")
    # Chặn admin tự khóa chính mình → tránh tự nhốt ra ngoài (HTG-05).
    if body.is_active is False and user.id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không thể khóa tài khoản đang đăng nhập")
    if body.ho_ten is not None:
        user.ho_ten = body.ho_ten
    if body.vai_tro is not None:
        user.vai_tro = body.vai_tro
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.password is not None:
        user.password_hash = hash_password(body.password)
    db.commit()
    db.refresh(user)
    return _ra(user)


@router.post("/{user_id}/reset-mat-khau", response_model=UserOut)
def reset_mat_khau(user_id: UUID, body: ResetMatKhau, _admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> UserOut:
    """Admin đặt mật khẩu mới cho nhân viên (HTG-05). Mật khẩu băm bcrypt, không log."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài khoản")
    user.password_hash = hash_password(body.password)
    db.commit()
    db.refresh(user)
    return _ra(user)
