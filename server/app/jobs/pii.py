"""Job xóa PII quá hạn (TDD §7.3, BR-016, EC-040).

Ảnh thô + số CCCD trên VPS là dữ liệu cá nhân: giữ tối đa `pii_retention_days`
(mặc định 30) kể từ khi collector gửi (`created_at`). Quá hạn → xóa cả dòng DB
lẫn file ảnh thô. BỎ QUA bản đang `importing` (tool có thể đang nạp dở — EC-040).
Chỉ ghi audit `hanh_dong='xoa_pii'` + uuid, KHÔNG ghi nội dung CCCD (§3.5).

Tách khỏi scheduler để test được trực tiếp trên SQLite in-memory, không cần giờ thật.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.ho_so import AuditLog, HoSoThuThap

# Trạng thái được phép xóa khi quá hạn. 'importing' cố ý loại trừ (EC-040).
_XOA_DUOC = ("pending", "imported")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def xoa_mot_ho_so(
    db: Session,
    hs: HoSoThuThap,
    *,
    hanh_dong: str = "xoa_pii",
    actor_id: UUID | None = None,
) -> None:
    """Xóa 1 bản ghi hàng đợi: unlink ảnh thô + ghi audit + xóa dòng. KHÔNG commit.

    Dùng chung cho job tự xóa 30 ngày (`hanh_dong='xoa_pii'`, không actor) và xóa tay
    của admin (`hanh_dong='xoa_pii_tay'`, kèm actor_id) — HTG-03. Caller tự `db.commit()`.
    Chỉ ghi hành động + uuid vào audit, KHÔNG ghi nội dung CCCD (§3.5).
    """
    if hs.anh_tho_path:
        # Xóa file ảnh thô; thiếu file (đã xóa tay) không phải lỗi.
        Path(hs.anh_tho_path).unlink(missing_ok=True)
    db.add(AuditLog(actor_id=actor_id, hanh_dong=hanh_dong, uuid_hs=hs.uuid))
    db.delete(hs)


def xoa_pii_qua_han(db: Session, *, now: datetime | None = None, retention_days: int | None = None) -> int:
    """Xóa bản ghi pending/imported quá hạn + file ảnh. Trả số dòng đã xóa.

    `now`/`retention_days` cho phép test bơm thời gian; mặc định lấy giờ hệ thống + cấu hình.
    """
    now = now or _now()
    days = retention_days if retention_days is not None else get_settings().pii_retention_days
    moc = now - timedelta(days=days)

    rows = db.scalars(
        select(HoSoThuThap).where(
            HoSoThuThap.trang_thai.in_(_XOA_DUOC),
            HoSoThuThap.created_at < moc,
        )
    ).all()

    for hs in rows:
        xoa_mot_ho_so(db, hs)

    db.commit()
    return len(rows)
