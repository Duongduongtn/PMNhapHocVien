"""Quản lý tài khoản — chỉ admin (TDD §4.2, §5.3, §5.4).

Không mở self-register: admin đầu tiên tạo bằng scripts/seed_admin.py.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
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


class UserOut(BaseModel):
    id: UUID
    username: str
    ho_ten: str | None
    vai_tro: str
    is_active: bool


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
    return UserOut(id=user.id, username=user.username, ho_ten=user.ho_ten, vai_tro=user.vai_tro, is_active=user.is_active)


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: UUID, body: UserUpdate, _admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> UserOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài khoản")
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
    return UserOut(id=user.id, username=user.username, ho_ten=user.ho_ten, vai_tro=user.vai_tro, is_active=user.is_active)
