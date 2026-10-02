"""Model hàng đợi thu thập + audit log (TDD §3.2, §7).

ho_so_thu_thap: bản ghi collector gửi lên, chờ tool kéo về nạp DB đích.
Vòng đời trang_thai: pending → importing (khóa) → imported; unlock quay lại pending.

Như user.py: id và thời gian có default phía Python (uuid4, now) + dùng Uuid/JSON
generic để Base.metadata.create_all dựng được bảng trên SQLite in-memory khi test,
không cần PostgreSQL.
"""
from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db import Base

TRANG_THAI = ("pending", "importing", "imported", "deleted")
GIOI_TINH = ("M", "F", "U")


def _now() -> datetime:
    return datetime.now(timezone.utc)


class HoSoThuThap(Base):
    __tablename__ = "ho_so_thu_thap"
    __table_args__ = (
        CheckConstraint(
            "trang_thai IN ('pending','importing','imported','deleted')",
            name="ck_hstt_trang_thai",
        ),
        CheckConstraint("gioi_tinh IN ('M','F','U')", name="ck_hstt_gioi_tinh"),
    )

    uuid: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)  # idempotency key
    trang_thai: Mapped[str] = mapped_column(String(20), default="pending")
    # Dữ liệu cá nhân (từ QR/nhập tay) — PII
    so_cccd: Mapped[str | None] = mapped_column(String(12), nullable=True)
    so_cmnd_cu: Mapped[str | None] = mapped_column(String(9), nullable=True)
    ho_ten: Mapped[str | None] = mapped_column(String(70), nullable=True)
    ngay_sinh: Mapped[str | None] = mapped_column(String(8), nullable=True)  # yyyymmdd
    gioi_tinh: Mapped[str | None] = mapped_column(String(1), nullable=True)
    noi_tt_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    ngay_cap_cccd: Mapped[date | None] = mapped_column(Date, nullable=True)
    noi_cap_cccd: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Ảnh thô
    anh_tho_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Chống trùng & truy vết
    ma_dk: Mapped[str | None] = mapped_column(String(25), nullable=True)
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    imported_by: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    locked_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class AuditLog(Base):
    """Nhật ký hành động trên PII (TDD §3.5): chỉ ghi hành động + uuid hồ sơ,
    KHÔNG ghi nội dung CCCD vào chi_tiet."""

    __tablename__ = "audit_log"

    # BigInteger khớp BIGSERIAL của PostgreSQL; biến thể Integer để SQLite test tự tăng rowid.
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    actor_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    hanh_dong: Mapped[str] = mapped_column(String(30))  # 'gui','keo','nap','unlock','xoa_pii','xoa_pii_tay'
    uuid_hs: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    chi_tiet: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
