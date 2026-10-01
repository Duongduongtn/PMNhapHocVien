"""Hồ sơ thu thập — endpoint collector (TDD §4.3, §5.3, §7).

Collector gửi hồ sơ (idempotent theo uuid client sinh), xem/sửa hồ sơ của MÌNH khi
còn pending, upload ảnh thô. Quyền sở hữu kiểm ở server (created_by = user hiện tại) —
chặn IDOR (OG-001): không dựa vào sự khó đoán của uuid.
"""
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.deps import require_role
from app.db import get_db
from app.models.ho_so import GIOI_TINH, AuditLog, HoSoThuThap
from app.models.user import User
from app.storage import AnhKhongHopLe, luu_anh, validate_anh

router = APIRouter(prefix="/api/ho-so", tags=["ho-so"])


class HoSoIn(BaseModel):
    uuid: UUID  # client sinh — idempotency key
    so_cccd: str | None = None
    so_cmnd_cu: str | None = None
    ho_ten: str | None = None
    ngay_sinh: str | None = None   # yyyymmdd
    gioi_tinh: str | None = None
    noi_tt_raw: str | None = None
    ngay_cap_cccd: date | None = None
    noi_cap_cccd: str | None = None

    @field_validator("gioi_tinh")
    @classmethod
    def _gt(cls, v: str | None) -> str | None:
        if v is not None and v not in GIOI_TINH:
            raise ValueError(f"gioi_tinh phải là một trong {GIOI_TINH}")
        return v


class HoSoSua(BaseModel):
    so_cccd: str | None = None
    so_cmnd_cu: str | None = None
    ho_ten: str | None = None
    ngay_sinh: str | None = None
    gioi_tinh: str | None = None
    noi_tt_raw: str | None = None
    ngay_cap_cccd: date | None = None
    noi_cap_cccd: str | None = None

    @field_validator("gioi_tinh")
    @classmethod
    def _gt(cls, v: str | None) -> str | None:
        if v is not None and v not in GIOI_TINH:
            raise ValueError(f"gioi_tinh phải là một trong {GIOI_TINH}")
        return v


class HoSoOut(BaseModel):
    uuid: UUID
    trang_thai: str
    so_cccd: str | None
    so_cmnd_cu: str | None
    ho_ten: str | None
    ngay_sinh: str | None
    gioi_tinh: str | None
    noi_tt_raw: str | None
    noi_cap_cccd: str | None
    co_anh: bool
    ma_dk: str | None
    created_at: datetime

    @classmethod
    def tu_model(cls, hs: HoSoThuThap) -> "HoSoOut":
        return cls(
            uuid=hs.uuid,
            trang_thai=hs.trang_thai,
            so_cccd=hs.so_cccd,
            so_cmnd_cu=hs.so_cmnd_cu,
            ho_ten=hs.ho_ten,
            ngay_sinh=hs.ngay_sinh,
            gioi_tinh=hs.gioi_tinh,
            noi_tt_raw=hs.noi_tt_raw,
            noi_cap_cccd=hs.noi_cap_cccd,
            co_anh=hs.anh_tho_path is not None,
            ma_dk=hs.ma_dk,
            created_at=hs.created_at,
        )


class KiemTrungOut(BaseModel):
    """Kết quả soi hàng đợi CSDT xem CCCD đã có hồ sơ CHƯA NẠP chưa (THU-04, CHANGES #13).

    Chỉ cảnh báo mềm ở app web — không chặn. Chốt trùng thật ở bước nạp (NAP-06, đối
    chiếu DB SQL Server). App web không nối DB nên chỉ soi được hàng đợi (pending/importing).
    """
    trung: bool
    so_luong: int
    nguoi_gui: str | None = None   # tên người gửi bản gần nhất (collector cùng CSDT)
    luc: datetime | None = None
    trang_thai: str | None = None


def _cua_minh(uuid: UUID, user: User, db: Session) -> HoSoThuThap:
    """Lấy hồ sơ của chính user. Không tồn tại hoặc không phải của mình → 404
    (không tiết lộ hồ sơ tồn tại nhưng thuộc người khác — chống IDOR)."""
    hs = db.get(HoSoThuThap, uuid)
    if hs is None or hs.created_by != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ")
    return hs


@router.post("", response_model=HoSoOut, status_code=status.HTTP_201_CREATED)
def gui_ho_so(body: HoSoIn, response: Response, user: User = Depends(require_role("collector")), db: Session = Depends(get_db)):
    """Gửi hồ sơ mới → 201. Idempotent: gửi lại cùng uuid (mất mạng rồi thử lại)
    không nhân đôi, trả 200 (TDD §4.7)."""
    hs = db.get(HoSoThuThap, body.uuid)
    if hs is not None:
        if hs.created_by != user.id:
            raise HTTPException(status.HTTP_409_CONFLICT, "Mã hồ sơ đã được dùng")
        response.status_code = status.HTTP_200_OK
        return HoSoOut.tu_model(hs)  # đã gửi trước đó → trả lại, không tạo thêm

    hs = HoSoThuThap(
        uuid=body.uuid,
        so_cccd=body.so_cccd,
        so_cmnd_cu=body.so_cmnd_cu,
        ho_ten=body.ho_ten,
        ngay_sinh=body.ngay_sinh,
        gioi_tinh=body.gioi_tinh,
        noi_tt_raw=body.noi_tt_raw,
        ngay_cap_cccd=body.ngay_cap_cccd,
        noi_cap_cccd=body.noi_cap_cccd,
        created_by=user.id,
    )
    db.add(hs)
    db.add(AuditLog(actor_id=user.id, hanh_dong="gui", uuid_hs=hs.uuid))
    db.commit()
    db.refresh(hs)
    return HoSoOut.tu_model(hs)


@router.get("/cua-toi", response_model=list[HoSoOut])
def ho_so_cua_toi(user: User = Depends(require_role("collector")), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(HoSoThuThap)
        .where(HoSoThuThap.created_by == user.id, HoSoThuThap.trang_thai != "deleted")
        .order_by(HoSoThuThap.created_at.desc())
    ).all()
    return [HoSoOut.tu_model(hs) for hs in rows]


@router.get("/kiem-trung", response_model=KiemTrungOut)
def kiem_trung_cccd(
    cccd: str,
    uuid: UUID | None = None,
    user: User = Depends(require_role("collector")),
    db: Session = Depends(get_db),
):
    """Cảnh báo mềm: CCCD này đã có hồ sơ CHƯA NẠP (pending/importing) trong hàng đợi chưa
    (THU-04, CHANGES #13). Mọi nhân viên cùng CSDT, không chỉ của mình. `uuid` (tùy chọn) loại
    trừ chính hồ sơ đang gửi khi gửi lại. Không có CCCD hợp lệ → coi như không trùng."""
    so = (cccd or "").strip()
    # Từ chối sớm input không hợp lệ (CCCD = 12 chữ số) — không để chuỗi lạ/dài chạm DB.
    if not so or len(so) > 12 or not so.isdigit():
        return KiemTrungOut(trung=False, so_luong=0)
    conds = [
        HoSoThuThap.so_cccd == so,
        HoSoThuThap.trang_thai.in_(["pending", "importing"]),
    ]
    if uuid is not None:
        conds.append(HoSoThuThap.uuid != uuid)
    so_luong = db.scalar(select(func.count()).select_from(HoSoThuThap).where(*conds)) or 0
    if so_luong == 0:
        return KiemTrungOut(trung=False, so_luong=0)
    moi_nhat = db.scalars(
        select(HoSoThuThap).where(*conds).order_by(HoSoThuThap.created_at.desc()).limit(1)
    ).first()
    nguoi = db.get(User, moi_nhat.created_by) if moi_nhat else None
    ten = (nguoi.ho_ten or nguoi.username) if nguoi else None
    return KiemTrungOut(
        trung=True,
        so_luong=so_luong,
        nguoi_gui=ten,
        luc=moi_nhat.created_at if moi_nhat else None,
        trang_thai=moi_nhat.trang_thai if moi_nhat else None,
    )


@router.put("/{uuid}", response_model=HoSoOut)
def sua_ho_so(uuid: UUID, body: HoSoSua, user: User = Depends(require_role("collector")), db: Session = Depends(get_db)):
    """Sửa khi còn pending. Đã vào nạp (importing/imported) → không cho sửa."""
    hs = _cua_minh(uuid, user, db)
    if hs.trang_thai != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, "Hồ sơ đã được xử lý, không sửa được")
    for truong, gia_tri in body.model_dump(exclude_unset=True).items():
        setattr(hs, truong, gia_tri)
    db.commit()
    db.refresh(hs)
    return HoSoOut.tu_model(hs)


@router.post("/{uuid}/anh", response_model=HoSoOut)
async def upload_anh(uuid: UUID, file: UploadFile, user: User = Depends(require_role("collector")), db: Session = Depends(get_db)):
    """Upload ảnh thô (JPEG/PNG). Chỉ khi hồ sơ còn pending và là của mình."""
    hs = _cua_minh(uuid, user, db)
    if hs.trang_thai != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, "Hồ sơ đã được xử lý, không đổi ảnh được")
    data = await file.read()
    try:
        ext = validate_anh(data)
    except AnhKhongHopLe as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    hs.anh_tho_path = luu_anh(hs.uuid, data, ext)
    db.commit()
    db.refresh(hs)
    return HoSoOut.tu_model(hs)


@router.get("/{uuid}/anh")
def tai_anh(uuid: UUID, user: User = Depends(require_role("collector")), db: Session = Depends(get_db)):
    """Tải lại ảnh thô CỦA MÌNH để hiện thumbnail list/chi tiết (THU-02, CHANGES #12).

    Kiểm quyền sở hữu (`created_by`) như `_cua_minh` — chống IDOR (OG-001):
    không tải được ảnh của hồ sơ người khác dù biết uuid."""
    hs = _cua_minh(uuid, user, db)
    if not hs.anh_tho_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Hồ sơ chưa có ảnh")
    duong_dan = Path(hs.anh_tho_path)
    if not duong_dan.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tệp ảnh không còn trên máy chủ")
    return FileResponse(duong_dan)
