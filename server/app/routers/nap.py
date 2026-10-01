"""Nạp — endpoint operator, kèm X-Tool-Key (TDD §4.4, §5.3, §7.2).

Tool kéo bản ghi pending về, KHÓA (pending→importing) bằng compare-and-set nguyên tử
trong 1 UPDATE để hai tool không nạp trùng một người, nạp xong đánh dấu imported
(kèm ma_dk) hoặc mở khóa khi lỗi.
"""
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth.deps import require_role, require_tool_key
from app.db import get_db
from app.models.ho_so import AuditLog, HoSoThuThap
from app.models.user import User

router = APIRouter(prefix="/api/nap", tags=["nap"], dependencies=[Depends(require_tool_key)])


def _now() -> datetime:
    return datetime.now(timezone.utc)


class KeoOut(BaseModel):
    uuid: UUID
    so_cccd: str | None
    so_cmnd_cu: str | None
    ho_ten: str | None
    ngay_sinh: str | None
    gioi_tinh: str | None
    noi_tt_raw: str | None
    noi_cap_cccd: str | None
    co_anh: bool
    created_at: datetime


class DaNapIn(BaseModel):
    ma_dk: str


@router.get("/keo", response_model=list[KeoOut])
def keo(
    limit: int = 200,
    cursor: datetime | None = None,
    _op: User = Depends(require_role("operator")),
    db: Session = Depends(get_db),
):
    """Kéo DS pending chưa bị khóa, cũ trước (FIFO). cursor = created_at bản cuối lượt trước."""
    limit = max(1, min(limit, 500))
    stmt = (
        select(HoSoThuThap)
        .where(HoSoThuThap.trang_thai == "pending", HoSoThuThap.locked_by.is_(None))
        .order_by(HoSoThuThap.created_at.asc())
        .limit(limit)
    )
    if cursor is not None:
        stmt = stmt.where(HoSoThuThap.created_at > cursor)
    rows = db.scalars(stmt).all()
    return [
        KeoOut(
            uuid=hs.uuid,
            so_cccd=hs.so_cccd,
            so_cmnd_cu=hs.so_cmnd_cu,
            ho_ten=hs.ho_ten,
            ngay_sinh=hs.ngay_sinh,
            gioi_tinh=hs.gioi_tinh,
            noi_tt_raw=hs.noi_tt_raw,
            noi_cap_cccd=hs.noi_cap_cccd,
            co_anh=hs.anh_tho_path is not None,
            created_at=hs.created_at,
        )
        for hs in rows
    ]


@router.post("/{uuid}/lock", status_code=status.HTTP_200_OK)
def lock(uuid: UUID, op: User = Depends(require_role("operator")), db: Session = Depends(get_db)):
    """Khóa bản ghi trước khi nạp (compare-and-set: chỉ thành công khi còn pending).
    Tool khác đã khóa/đã nạp → 409."""
    now = _now()
    res = db.execute(
        update(HoSoThuThap)
        .where(
            HoSoThuThap.uuid == uuid,
            HoSoThuThap.trang_thai == "pending",
            HoSoThuThap.locked_by.is_(None),
        )
        .values(trang_thai="importing", locked_by=op.id, locked_at=now, updated_at=now)
    )
    db.commit()
    if res.rowcount == 0:
        hs = db.get(HoSoThuThap, uuid)
        if hs is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ")
        raise HTTPException(status.HTTP_409_CONFLICT, "Hồ sơ đang được nạp hoặc đã nạp")
    return {"uuid": str(uuid), "trang_thai": "importing"}


@router.post("/{uuid}/da-nap", status_code=status.HTTP_200_OK)
def da_nap(uuid: UUID, body: DaNapIn, op: User = Depends(require_role("operator")), db: Session = Depends(get_db)):
    """Đánh dấu đã nạp vào DB đích (kèm ma_dk) + mở khóa. Chỉ từ importing."""
    now = _now()
    res = db.execute(
        update(HoSoThuThap)
        .where(HoSoThuThap.uuid == uuid, HoSoThuThap.trang_thai == "importing")
        .values(
            trang_thai="imported",
            ma_dk=body.ma_dk,
            imported_at=now,
            imported_by=op.id,
            locked_by=None,
            locked_at=None,
            updated_at=now,
        )
    )
    if res.rowcount == 0:
        db.rollback()
        hs = db.get(HoSoThuThap, uuid)
        if hs is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ")
        raise HTTPException(status.HTTP_409_CONFLICT, "Hồ sơ chưa ở trạng thái đang nạp")
    db.add(AuditLog(actor_id=op.id, hanh_dong="nap", uuid_hs=uuid, chi_tiet={"ma_dk": body.ma_dk}))
    db.commit()
    return {"uuid": str(uuid), "trang_thai": "imported", "ma_dk": body.ma_dk}


@router.post("/{uuid}/unlock", status_code=status.HTTP_200_OK)
def unlock(uuid: UUID, op: User = Depends(require_role("operator")), db: Session = Depends(get_db)):
    """Mở khóa khi nạp lỗi/mất DB → quay lại pending để nạp lại. Chỉ từ importing."""
    now = _now()
    res = db.execute(
        update(HoSoThuThap)
        .where(HoSoThuThap.uuid == uuid, HoSoThuThap.trang_thai == "importing")
        .values(trang_thai="pending", locked_by=None, locked_at=None, updated_at=now)
    )
    if res.rowcount == 0:
        db.rollback()
        hs = db.get(HoSoThuThap, uuid)
        if hs is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ")
        raise HTTPException(status.HTTP_409_CONFLICT, "Hồ sơ không ở trạng thái đang nạp")
    db.add(AuditLog(actor_id=op.id, hanh_dong="unlock", uuid_hs=uuid))
    db.commit()
    return {"uuid": str(uuid), "trang_thai": "pending"}
