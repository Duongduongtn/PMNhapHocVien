"""Model users + token_blocklist (TDD §3.2, §5.1).

id và thời gian có default phía Python (uuid4, now) — ngoài DEFAULT của init.sql —
để test dựng bảng trên SQLite in-memory không cần PostgreSQL.
"""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

VAI_TRO = ("collector", "operator", "admin")


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("vai_tro IN ('collector','operator','admin')", name="ck_users_vai_tro"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    ho_ten: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vai_tro: Mapped[str] = mapped_column(String(20), default="collector")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TokenBlocklist(Base):
    __tablename__ = "token_blocklist"

    jti: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    exp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
