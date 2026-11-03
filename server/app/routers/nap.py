"""Nạp — endpoint operator, kèm X-Tool-Key (TDD §4.4, §5.3, §7.2).

Tool kéo bản ghi pending về, KHÓA (pending→importing) bằng compare-and-set nguyên tử
trong 1 UPDATE để hai tool không nạp trùng một người, nạp xong đánh dấu imported
(kèm ma_dk) hoặc mở khóa khi lỗi.
"""
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import and_, or_, select, update
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
    ngay_cap_cccd: date | None
    noi_cap_cccd: str | None
    gplx_da_co: list[dict] | None = None
    co_anh: bool
    created_at: datetime


class DaNapIn(BaseModel):
    ma_dk: str


class TrangThaiOut(BaseModel):
    uuid: UUID
    trang_thai: str
    ma_dk: str | None
    locked_at: datetime | None


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
            ngay_cap_cccd=hs.ngay_cap_cccd,
            noi_cap_cccd=hs.noi_cap_cccd,
            gplx_da_co=hs.gplx_da_co,
            co_anh=hs.anh_tho_path is not None,
            created_at=hs.created_at,
        )
        for hs in rows
    ]


class DaXoaOut(BaseModel):
    uuids: list[UUID]
    moc: datetime  # created_at bản xóa mới nhất — lượt kéo sau truyền lại làm `since` (incremental)


@router.get("/da-xoa", response_model=DaXoaOut)
def da_xoa(since: datetime | None = None, _op: User = Depends(require_role("operator")), db: Session = Depends(get_db)):
    """DS uuid hồ sơ collector đã XÓA ở app web (soft-delete 'xoa', THU-05) kể từ mốc `since` —
    để tool bỏ dòng staging `pending` tương ứng khi "Kéo về" (NAP-01 task 44, TDD §11.7).

    CHỈ hành động 'xoa'; KHÔNG suy xóa từ việc uuid vắng mặt trong /keo (keo còn lọc lock + limit
    → vắng mặt ≠ đã xóa → sẽ bỏ nhầm hồ sơ chưa xóa). Trả kèm `moc` = created_at bản xóa mới nhất
    (rỗng → trả lại `since`/now) để lượt sau truyền làm `since`, chỉ lấy phần mới.

    Khai báo TRƯỚC các route /{uuid}/... vì đây là đường tĩnh (tránh bị path-param nuốt)."""
    stmt = select(AuditLog).where(AuditLog.hanh_dong == "xoa").order_by(AuditLog.created_at.asc())
    if since is not None:
        stmt = stmt.where(AuditLog.created_at > since)
    rows = db.scalars(stmt).all()
    uuids = [r.uuid_hs for r in rows if r.uuid_hs is not None]
    moc = rows[-1].created_at if rows else (since or _now())
    return DaXoaOut(uuids=uuids, moc=moc)


@router.get("/tra-uuid", status_code=status.HTTP_200_OK)
def tra_uuid(ma_dk: str, _op: User = Depends(require_role("operator")), db: Session = Depends(get_db)):
    """Tra uuid gốc theo ma_dk — fallback cho QLY-08 (gỡ HV về chờ nạp) khi staging nap_xong
    local của tool không còn (đổi máy/xóa SQLite). VPS lưu ma_dk khi da-nap (TDD §4.4, §11.7).
    Chỉ tìm bản đã nạp (imported). Không thấy → 404.

    Khai báo TRƯỚC các route /{uuid}/... vì đây là đường tĩnh (tránh bị path-param nuốt)."""
    ma = (ma_dk or "").strip()
    if ma:
        hs = db.scalars(
            select(HoSoThuThap)
            .where(HoSoThuThap.ma_dk == ma, HoSoThuThap.trang_thai == "imported")
            .limit(1)
        ).first()
        if hs is not None:
            return {"uuid": str(hs.uuid), "ma_dk": ma}
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ đã nạp theo mã đăng ký")


class GplxBoSungDong(BaseModel):
    uuid: UUID
    ma_dk: str | None
    gplx_da_co: list[dict]
    nguoi_gui: str | None
    updated_at: datetime


class GplxBoSungOut(BaseModel):
    items: list[GplxBoSungDong]
    co_tiep: bool
    cursor: str | None  # truyền lại ở lượt sau khi co_tiep


def _doc_cursor(cursor: str) -> tuple[datetime, UUID]:
    try:
        moc, ma = cursor.split("|", 1)
        return datetime.fromisoformat(moc), UUID(ma)
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "cursor không hợp lệ") from None


@router.get("/gplx-bo-sung", response_model=GplxBoSungOut)
def gplx_bo_sung(
    limit: int = 200,
    cursor: str | None = None,
    _op: User = Depends(require_role("operator")),
    db: Session = Depends(get_db),
):
    """Hồ sơ đã nạp được bổ sung GPLX ở app web sau lần nạp gần nhất (QLY-10, TDD §10.7); tool so với DB để cảnh báo.
    Sắp (updated_at, uuid) vì updated_at đổi mỗi lần bổ sung; cursor = "<updated_at>|<uuid>" dòng cuối lượt trước.
    Không ghi `gplx_da_co` vào log. Khai báo TRƯỚC các route /{uuid}/... vì đây là đường tĩnh."""
    limit = max(1, min(limit, 500))
    co_bo_sung = (
        select(AuditLog.id)
        .where(
            AuditLog.hanh_dong == "bo_sung_gplx",
            AuditLog.uuid_hs == HoSoThuThap.uuid,
            or_(HoSoThuThap.imported_at.is_(None), AuditLog.created_at >= HoSoThuThap.imported_at),
        )
        .exists()
    )
    stmt = (
        select(HoSoThuThap, User.ho_ten)
        .outerjoin(User, User.id == HoSoThuThap.created_by)
        .where(HoSoThuThap.trang_thai == "imported", co_bo_sung)
        .order_by(HoSoThuThap.updated_at.asc(), HoSoThuThap.uuid.asc())
        .limit(limit + 1)
    )
    if cursor:
        moc, ma = _doc_cursor(cursor)
        stmt = stmt.where(or_(HoSoThuThap.updated_at > moc, and_(HoSoThuThap.updated_at == moc, HoSoThuThap.uuid > ma)))
    dong = db.execute(stmt).all()
    co_tiep = len(dong) > limit
    dong = dong[:limit]
    cuoi = dong[-1][0] if dong else None
    return GplxBoSungOut(
        items=[
            GplxBoSungDong(uuid=hs.uuid, ma_dk=hs.ma_dk, gplx_da_co=hs.gplx_da_co, nguoi_gui=ten, updated_at=hs.updated_at)
            for hs, ten in dong
            if hs.gplx_da_co
        ],
        co_tiep=co_tiep,
        cursor=f"{cuoi.updated_at.isoformat()}|{cuoi.uuid}" if cuoi and co_tiep else None,
    )


@router.get("/{uuid}/anh")
def tai_anh(uuid: UUID, _op: User = Depends(require_role("operator")), db: Session = Depends(get_db)):
    """Tải ảnh thô của 1 hồ sơ về tool để hiển thị + xử lý thành .jp2 (NAP-01/NAP-04).

    Trả file ảnh gốc (JPEG/PNG). Không có hồ sơ hoặc chưa có ảnh → 404.
    File đã mất trên đĩa (đã xóa PII) → 404.
    """
    hs = db.get(HoSoThuThap, uuid)
    if hs is None or hs.trang_thai == "deleted":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ")
    if not hs.anh_tho_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Hồ sơ chưa có ảnh")
    duong_dan = Path(hs.anh_tho_path)
    if not duong_dan.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tệp ảnh không còn trên máy chủ")
    return FileResponse(duong_dan)


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


@router.get("/trang-thai", response_model=list[TrangThaiOut])
def trang_thai_nhieu(
    uuids: str,
    _op: User = Depends(require_role("operator")),
    db: Session = Depends(get_db),
):
    """QLY-09 (CHANGES #28) — tra trạng thái VPS của nhiều uuid một lượt (đối soát ca ② theo khóa).
    READ thuần (không nạp mới). `uuids` = danh sách UUID ngăn bằng dấu phẩy (≤500); uuid rác/không
    tồn tại → bỏ qua (không 400 cả lô, không trả dòng). Operator gọi được — ca ② cho cả operator."""
    ids: list[UUID] = []
    for s in uuids.split(","):
        s = s.strip()
        if not s:
            continue
        try:
            ids.append(UUID(s))
        except ValueError:
            continue
    if not ids:
        return []
    rows = db.execute(select(HoSoThuThap).where(HoSoThuThap.uuid.in_(ids[:500]))).scalars().all()
    return [
        {"uuid": r.uuid, "trang_thai": r.trang_thai, "ma_dk": r.ma_dk, "locked_at": r.locked_at}
        for r in rows
    ]


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


@router.post("/{uuid}/tra-ve-cho-nap", status_code=status.HTTP_200_OK)
def tra_ve_cho_nap(uuid: UUID, op: User = Depends(require_role("operator")), db: Session = Depends(get_db)):
    """Trả hồ sơ ĐÃ NẠP về chờ nạp (imported→pending, gỡ ma_dk) — QLY-08: tool gọi SAU khi đã gỡ
    HV khỏi CSDT, để nạp lại đúng khóa (TDD §4.4, §7.1, §7.5). Khác `unlock` (chỉ importing→pending
    khi nạp lỗi).

    CAS nguyên tử (WHERE trang_thai='imported'). Gọi lại khi đã `pending` → **idempotent**: trả 200,
    không lỗi (an toàn cho retry bước đồng bộ VPS ở QLY-08 khi lần trước đã thành công nhưng tool
    tưởng lỗi). Bản ghi `deleted`/`importing`/không còn → 409 (không còn bản gốc đã-nạp để trả về)."""
    now = _now()
    res = db.execute(
        update(HoSoThuThap)
        .where(HoSoThuThap.uuid == uuid, HoSoThuThap.trang_thai == "imported")
        .values(
            trang_thai="pending",
            ma_dk=None,
            imported_at=None,
            imported_by=None,
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
        if hs.trang_thai == "pending":
            return {"uuid": str(uuid), "trang_thai": "pending"}  # idempotent — đã về chờ nạp
        raise HTTPException(status.HTTP_409_CONFLICT, "Không còn bản gốc đã nạp để trả về (đã xóa hoặc chưa nạp xong)")
    db.add(AuditLog(actor_id=op.id, hanh_dong="tra_ve_cho_nap", uuid_hs=uuid))
    db.commit()
    return {"uuid": str(uuid), "trang_thai": "pending"}
