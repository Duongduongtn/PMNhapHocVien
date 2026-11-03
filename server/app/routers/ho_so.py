"""Hồ sơ thu thập — endpoint collector (TDD §4.3, §5.3, §7).

Collector gửi hồ sơ (idempotent theo uuid client sinh), xem/sửa hồ sơ của MÌNH khi
còn pending, upload ảnh thô. Quyền sở hữu kiểm ở server (created_by = user hiện tại) —
chặn IDOR (OG-001): không dựa vào sự khó đoán của uuid.
"""
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.auth.deps import require_role
from app.db import get_db
from app.models.ho_so import GIOI_TINH, AuditLog, HoSoThuThap
from app.models.user import User
from app.storage import AnhKhongHopLe, luu_anh, validate_anh

router = APIRouter(prefix="/api/ho-so", tags=["ho-so"])


GPLX_HANG = frozenset({"A01", "A02", "A1", "A1m", "A2", "A3", "B1", "B11", "B2", "C", "C1", "D", "D1",
                       "E", "FB2", "FC", "FD", "FE"})
GPLX_TOI_DA = 8


class GplxBang(BaseModel):
    """1 bằng GPLX đã có (THU-07, TDD §10.6). `hang` là mã DM_HangGPLX, ngày yyyymmdd, ô trống = chuỗi rỗng."""
    # hide_input_in_errors: lỗi 422 không chép lại số GPLX (dữ liệu cá nhân)
    model_config = ConfigDict(hide_input_in_errors=True)
    nhom: Literal["cu", "moi"]
    hang: str
    so: str = Field(min_length=1, max_length=20, pattern=r"^[^|]+$")
    ngay_tt: str = Field(min_length=8)   # bắt buộc như form cũ FPT.GPLX.CSDT
    ngay_cap: str = Field(min_length=8)  # bắt buộc như form cũ
    ngay_hh: str = ""
    don_vi: str = Field("", pattern=r"^(\d{2})?$")

    @field_validator("hang")
    @classmethod
    def _hang(cls, v: str) -> str:
        if v not in GPLX_HANG:
            raise ValueError("hạng GPLX không hợp lệ")
        return v

    @field_validator("ngay_tt", "ngay_cap", "ngay_hh")
    @classmethod
    def _ngay(cls, v: str) -> str:
        if v:
            try:
                datetime.strptime(v, "%Y%m%d")
            except ValueError:
                raise ValueError("ngày phải là yyyymmdd hợp lệ") from None
        return v

    @model_validator(mode="after")
    def _thu_tu_ngay(self) -> "GplxBang":
        if self.ngay_cap < self.ngay_tt:
            raise ValueError("ngày cấp phải sau ngày trúng tuyển")
        if self.ngay_cap > datetime.now().strftime("%Y%m%d"):
            raise ValueError("ngày cấp không được sau hôm nay")
        if self.ngay_hh and self.ngay_hh <= self.ngay_cap:
            raise ValueError("ngày hết hạn phải sau ngày cấp")
        return self


def _kiem_gplx(ds: list[GplxBang] | None) -> list[GplxBang] | None:
    """Trần số bằng + độ dài sau khi nối "|" (cột varchar(100) ở DB Nạp) — báo ngay lúc gửi, không đợi tới lúc nạp."""
    if not ds:
        return ds
    if len(ds) > GPLX_TOI_DA:
        raise ValueError(f"tối đa {GPLX_TOI_DA} bằng")
    for f in ("so", "hang", "ngay_tt", "ngay_cap", "ngay_hh", "don_vi"):
        if len("|".join(getattr(b, f) for b in ds)) > 100:
            raise ValueError("quá nhiều bằng, vượt giới hạn 100 ký tự")
    return ds


class HoSoIn(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)
    uuid: UUID  # client sinh — idempotency key
    so_cccd: str | None = None
    so_cmnd_cu: str | None = None
    ho_ten: str | None = None
    ngay_sinh: str | None = None   # yyyymmdd
    gioi_tinh: str | None = None
    noi_tt_raw: str | None = None
    ngay_cap_cccd: date | None = None
    noi_cap_cccd: str | None = None
    gplx_da_co: list[GplxBang] | None = None

    _gplx = field_validator("gplx_da_co")(_kiem_gplx)

    @field_validator("gioi_tinh")
    @classmethod
    def _gt(cls, v: str | None) -> str | None:
        if v is not None and v not in GIOI_TINH:
            raise ValueError(f"gioi_tinh phải là một trong {GIOI_TINH}")
        return v


class HoSoSua(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)
    so_cccd: str | None = None
    so_cmnd_cu: str | None = None
    ho_ten: str | None = None
    ngay_sinh: str | None = None
    gioi_tinh: str | None = None
    noi_tt_raw: str | None = None
    ngay_cap_cccd: date | None = None
    noi_cap_cccd: str | None = None
    gplx_da_co: list[GplxBang] | None = None  # chỉ gửi khi người dùng có sửa; exclude_unset giữ nguyên nếu không gửi

    _gplx = field_validator("gplx_da_co")(_kiem_gplx)

    @field_validator("gioi_tinh")
    @classmethod
    def _gt(cls, v: str | None) -> str | None:
        if v is not None and v not in GIOI_TINH:
            raise ValueError(f"gioi_tinh phải là một trong {GIOI_TINH}")
        return v


class GplxBoSungIn(BaseModel):
    """Bổ sung sau khi đã nạp: phải có ít nhất 1 bằng; muốn xóa GPLX trong DB thì làm ở tool (TDD §10.7)."""
    model_config = ConfigDict(hide_input_in_errors=True)
    gplx_da_co: list[GplxBang] = Field(min_length=1)

    _gplx = field_validator("gplx_da_co")(_kiem_gplx)


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
    gplx_da_co: list[dict] | None = None
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
            gplx_da_co=hs.gplx_da_co,
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
        gplx_da_co=[b.model_dump() for b in body.gplx_da_co] if body.gplx_da_co else None,
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
        setattr(hs, truong, (gia_tri or None) if truong == "gplx_da_co" else gia_tri)
    db.commit()
    db.refresh(hs)
    return HoSoOut.tu_model(hs)


@router.put("/{uuid}/gplx", response_model=HoSoOut)
def bo_sung_gplx(uuid: UUID, body: GplxBoSungIn, user: User = Depends(require_role("collector")), db: Session = Depends(get_db)):
    """Bổ sung GPLX đã có cho hồ sơ ĐÃ NẠP của mình (THU-07, TDD §10.7): chỉ ghi `gplx_da_co` + `updated_at`, người nạp
    duyệt mới vào DB. UPDATE nguyên tử để không đua với gỡ về chờ nạp; `pending` dùng PUT /{uuid}. Dòng audit
    `bo_sung_gplx` là dấu hiệu tool phân biệt bổ sung thật với GPLX có từ trước khi nạp; không ghi giá trị vào audit."""
    rowcount = db.execute(
        update(HoSoThuThap)
        .where(HoSoThuThap.uuid == uuid, HoSoThuThap.created_by == user.id, HoSoThuThap.trang_thai == "imported")
        .values(gplx_da_co=[b.model_dump() for b in body.gplx_da_co], updated_at=datetime.now(timezone.utc))
    ).rowcount
    if rowcount == 0:
        db.rollback()
        _cua_minh(uuid, user, db)  # không phải của mình → 404
        raise HTTPException(status.HTTP_409_CONFLICT, "Chỉ bổ sung được cho hồ sơ đã nạp")
    db.add(AuditLog(actor_id=user.id, hanh_dong="bo_sung_gplx", uuid_hs=uuid))
    db.commit()
    return HoSoOut.tu_model(_cua_minh(uuid, user, db))


@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
def xoa_ho_so(uuid: UUID, user: User = Depends(require_role("collector")), db: Session = Depends(get_db)):
    """Xóa hồ sơ đã gửi — SOFT-DELETE (trang_thai→'deleted'), CHỈ khi còn 'pending' (THU-05, §4.3).

    Collector chỉ xóa hồ sơ CỦA MÌNH (created_by) — chống IDOR như `_cua_minh`: không phải
    của mình → 404 (không lộ hồ sơ tồn tại; thống nhất với PUT/GET ảnh). Admin xóa bất kỳ.
    Hồ sơ đã/đang nạp (importing/imported) hoặc đã xóa → 409.

    Chuyển trạng thái bằng CAS nguyên tử (WHERE trang_thai='pending') để không đua với tool
    `lock` (pending→importing) chạy đồng thời (§7.5). Ghi audit_log hành động 'xoa' — mốc
    `created_at` để endpoint /api/nap/da-xoa đọc danh sách đã xóa (NAP-01, task 44)."""
    hs = db.get(HoSoThuThap, uuid)
    la_admin = user.vai_tro == "admin"
    if hs is None or (not la_admin and hs.created_by != user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy hồ sơ")
    if hs.trang_thai != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, "Hồ sơ đã được nạp hoặc đã xóa, không xóa được")
    rowcount = db.execute(
        update(HoSoThuThap)
        .where(HoSoThuThap.uuid == uuid, HoSoThuThap.trang_thai == "pending")
        .values(trang_thai="deleted", gplx_da_co=None, updated_at=datetime.now(timezone.utc))
    ).rowcount
    if rowcount == 0:  # tool vừa lock sang importing giữa lúc đọc và ghi
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Hồ sơ vừa được nạp, không xóa được")
    db.add(AuditLog(actor_id=user.id, hanh_dong="xoa", uuid_hs=uuid))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{uuid}/anh", response_model=HoSoOut)
async def upload_anh(uuid: UUID, file: UploadFile, user: User = Depends(require_role("collector")), db: Session = Depends(get_db)):
    """Upload ảnh thô (JPEG/PNG) cho hồ sơ của MÌNH (TDD §6.3, CHANGES #44).

    Allowlist trạng thái: CHỈ 'pending' HOẶC 'imported' (bổ sung ảnh cho HV đã nạp
    thiếu ảnh — collector chụp bù → tool kéo về ở Tra cứu DB/QLY-05). Mọi trạng thái
    khác → 409: 'importing' (tool đang nạp, tránh đua ảnh) và 'deleted' (đã xóa mềm,
    không ghi ảnh làm sống lại). Dùng allowlist chứ KHÔNG viết `== "importing"` —
    blocklist sẽ lọt 'deleted'. Endpoint chỉ ghi `anh_tho_path`, không đổi `trang_thai`.
    Ghi ảnh cho 'imported' làm UPDATE → `updated_at` tự bump (onupdate) → job PII
    gia hạn 30 ngày để operator kịp kéo (§9.3)."""
    hs = _cua_minh(uuid, user, db)
    if hs.trang_thai not in ("pending", "imported"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Hồ sơ đang nạp hoặc đã xóa, không đổi ảnh được")
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
