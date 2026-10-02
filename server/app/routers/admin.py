"""Quản trị — chỉ admin.

- HTG-04: hiện `TOOL_API_KEY` để admin cấu hình tool mà không phải SSH vào máy chủ.
  Đánh đổi bảo mật đã chốt ở PRD HTG-04: chỉ admin thấy, KHÔNG ghi log giá trị key.
- HTG-03: lọc & xóa thủ công bản ghi PII trong hàng đợi VPS (TDD §4.5, BR-016).
  Xóa tay là hard-delete (bản ghi + ảnh thô), KHÔNG khôi phục được.
"""
from datetime import datetime, time, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.deps import require_role
from app.config import get_settings
from app.db import get_db
from app.jobs.pii import xoa_mot_ho_so
from app.models.ho_so import TRANG_THAI, HoSoThuThap
from app.models.user import User

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Ngày gửi do collector nhập theo giờ VN; created_at lưu UTC. Lọc theo khoảng ngày
# phải quy đổi biên ngày VN (+07:00) sang UTC, nếu không sẽ lệch 1 ngày ở rìa.
_VN = timezone(timedelta(hours=7))


class ToolKeyOut(BaseModel):
    tool_key: str


@router.get("/tool-key", response_model=ToolKeyOut)
def xem_tool_key(_admin: User = Depends(require_role("admin"))) -> ToolKeyOut:
    """Trả X-Tool-Key (khóa kết nối tool) cho admin. Không log giá trị."""
    return ToolKeyOut(tool_key=get_settings().tool_api_key)


# ── HTG-03: Bộ lọc & xóa PII thủ công ────────────────────────────────────────

class HoSoAdminOut(BaseModel):
    uuid: UUID
    ho_ten: str | None
    so_cccd: str | None
    noi_tt_raw: str | None
    trang_thai: str
    co_anh: bool
    created_at: datetime


class HoSoAdminListOut(BaseModel):
    items: list[HoSoAdminOut]
    total: int


def _ra(hs: HoSoThuThap) -> HoSoAdminOut:
    return HoSoAdminOut(
        uuid=hs.uuid,
        ho_ten=hs.ho_ten,
        so_cccd=hs.so_cccd,
        noi_tt_raw=hs.noi_tt_raw,
        trang_thai=hs.trang_thai,
        co_anh=hs.anh_tho_path is not None,
        created_at=hs.created_at,
    )


@router.get("/ho-so", response_model=HoSoAdminListOut)
def loc_ho_so(
    trang_thai: str | None = Query(None, description="pending/importing/imported/deleted; bỏ trống = tất cả"),
    tu_ngay: str | None = Query(None, description="Ngày gửi từ (dd/mm/yyyy ISO yyyy-mm-dd), theo giờ VN"),
    den_ngay: str | None = Query(None, description="Ngày gửi đến (bao gồm cả ngày này), theo giờ VN"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> HoSoAdminListOut:
    """Lọc bản ghi hàng đợi theo trạng thái + khoảng ngày gửi, phân trang (HTG-03)."""
    conds = []
    if trang_thai is not None:
        if trang_thai not in TRANG_THAI:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"trang_thai phải là một trong {TRANG_THAI}")
        conds.append(HoSoThuThap.trang_thai == trang_thai)
    if tu_ngay is not None:
        moc = datetime.combine(_parse_ngay(tu_ngay), time.min, _VN).astimezone(timezone.utc)
        conds.append(HoSoThuThap.created_at >= moc)
    if den_ngay is not None:
        # Bao gồm cả ngày "đến": chặn dưới mốc 00:00 của ngày kế tiếp (giờ VN), quy về UTC.
        moc = (datetime.combine(_parse_ngay(den_ngay), time.min, _VN) + timedelta(days=1)).astimezone(timezone.utc)
        conds.append(HoSoThuThap.created_at < moc)

    total = db.scalar(select(func.count()).select_from(HoSoThuThap).where(*conds)) or 0
    rows = db.scalars(
        select(HoSoThuThap).where(*conds).order_by(HoSoThuThap.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return HoSoAdminListOut(items=[_ra(hs) for hs in rows], total=total)


@router.delete("/ho-so/{uuid}", status_code=status.HTTP_200_OK)
def xoa_ho_so(uuid: UUID, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    """Xóa thủ công 1 bản ghi PII (bản ghi + ảnh thô). Hard-delete, không khôi phục (BR-016).

    Admin xóa có chủ đích nên cho phép mọi trạng thái (khác job tự động bỏ qua importing).
    """
    hs = db.get(HoSoThuThap, uuid)
    if hs is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ")
    xoa_mot_ho_so(db, hs, hanh_dong="xoa_pii_tay", actor_id=admin.id)
    db.commit()
    return {"uuid": str(uuid), "da_xoa": True}


def _parse_ngay(s: str):
    """Nhận yyyy-mm-dd (ISO, chuẩn máy đọc) → date. Sai định dạng → 422."""
    from datetime import date

    try:
        return date.fromisoformat(s)
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Ngày phải đúng định dạng yyyy-mm-dd")
