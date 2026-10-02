"""QLY-01 — Tra cứu & sửa hồ sơ đã có trong DB đích (chế độ "Tra cứu DB").

Lát 1 (đọc): lưới học viên theo khóa qua usp_NguoiLX_Select_By_MaKH.
Lát 2 (sửa — GHI PROD): CHỈ thông tin NHÂN THÂN (bảng NguoiLX) qua usp_NguoiLX_Update.
  Phạm vi chốt với chủ dự án 02/10: họ tên, ngày sinh, giới tính, số căn cước, địa chỉ
  thường trú (chi tiết). KHÔNG đụng bảng NguoiLX_HoSo (SP đó ghi đè 65 cột gồm kết quả
  thi/báo cáo → rủi ro xóa trắng). Ảnh để QLY-05, đổi khóa QLY-02, xóa QLY-03.

An toàn: usp_NguoiLX_Update ghi đè TOÀN BỘ 22 cột, mà SP không nhận "sửa từng trường".
  Nên trước khi ghi, đọc lại full bản ghi NguoiLX hiện tại rồi chỉ chồng các trường user
  sửa — giữ nguyên quốc tịch, nơi cấp CCCD, ghi chú, mã DVHC, người/ngày tạo...
Chặn sửa khi khóa đã lập BC1 (BR-012). Mọi SQL parameterized (TDD §12).
"""
from __future__ import annotations
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator

from app.db import sqlserver_cursor, sqlserver_conn, ConfigChuaDay
from app.nap import tach_ho_ten, validate_do_dai
from app.session import Phien, require_session

router = APIRouter(prefix="/local/ho-so", tags=["ho-so"])

_NOITT_MAX = 50  # NguoiLX.NoiTT nvarchar(50) (chi tiết thường trú)


# ---- Hàm thuần (unit-test được, không chạm DB) ------------------------------
def gioi_tinh_ma(raw: str | None) -> str:
    """Nhãn/UI → mã cột char(1): Nam→'M', Nữ→'F', còn lại→'U' (khớp CASE của SP Get_Sua_HS)."""
    v = (raw or "").strip().upper()
    if v in ("M", "F", "U"):
        return v
    if v in ("NAM",):
        return "M"
    if v in ("NỮ", "NU"):
        return "F"
    return "U"


def gioi_tinh_hien(ma: str | None) -> str:
    """Mã cột → nhãn tiếng Việt cho UI."""
    return {"M": "Nam", "F": "Nữ"}.get((ma or "").strip().upper(), "Không xác định")


def ngay_sinh_luu(raw: str | None) -> str:
    """Ô ngày sinh (dd/mm/yyyy khi gõ, hoặc chỉ yyyy) → lưu 'yyyymmdd' (hoặc 'yyyy').

    NgaySinh là varchar(8) lưu yyyymmdd (hoặc yyyy khi chỉ biết năm) — khớp nạp mới + SP
    Get_Sua_HS (LEN 4/6/8). 8 số nhập tay là ddmmyyyy → đảo về yyyymmdd. Rỗng → ''."""
    so = re.sub(r"\D", "", raw or "")
    if len(so) == 8:
        return f"{so[4:]}{so[2:4]}{so[:2]}"  # ddmmyyyy → yyyymmdd
    if len(so) in (4, 6):
        return so
    return so


def ngay_sinh_hien(stored: str | None) -> str:
    """'yyyymmdd' → 'dd/mm/yyyy'; 'yyyymm' → 'mm/yyyy'; 'yyyy' → 'yyyy' (cho ô nhập)."""
    so = re.sub(r"\D", "", stored or "")
    if len(so) == 8:
        return f"{so[6:8]}/{so[4:6]}/{so[0:4]}"
    if len(so) == 6:
        return f"{so[4:6]}/{so[0:4]}"
    if len(so) == 4:
        return so
    return stored or ""


# Thứ tự 24 tham số đúng khai báo usp_NguoiLX_Update (ghi đè toàn bộ cột NguoiLX).
_COT_NGUOILX = (
    "MaDK", "DonViNhanHSo", "HoDemNLX", "TenNLX", "HoVaTen", "MaQuocTich", "NgaySinh",
    "NoiTT", "NoiTT_MaDVHC", "NoiTT_MaDVQL", "NoiCT", "NoiCT_MaDVHC", "NoiCT_MaDVQL",
    "SoCMT", "NgayCapCMT", "NoiCapCMT", "GhiChu", "TrangThai", "NguoiTao", "NguoiSua",
    "NgayTao", "NgaySua", "GioiTinh", "HoVaTenIn",
)

_EXEC_UPDATE = (
    "EXEC dbo.usp_NguoiLX_Update @MaDK=%s,@DonViNhanHSo=%s,@HoDemNLX=%s,@TenNLX=%s,"
    "@HoVaTen=%s,@MaQuocTich=%s,@NgaySinh=%s,@NoiTT=%s,@NoiTT_MaDVHC=%s,@NoiTT_MaDVQL=%s,"
    "@NoiCT=%s,@NoiCT_MaDVHC=%s,@NoiCT_MaDVQL=%s,@SoCMT=%s,@NgayCapCMT=%s,@NoiCapCMT=%s,"
    "@GhiChu=%s,@TrangThai=%s,@NguoiTao=%s,@NguoiSua=%s,@NgayTao=%s,@NgaySua=%s,"
    "@GioiTinh=%s,@HoVaTenIn=%s"
)


class HoSoSua(BaseModel):
    """Trường nhân thân cho sửa (QLY-01 lát 2). Chỉ 5 trường — còn lại giữ nguyên từ DB."""
    ho_ten: str
    ngay_sinh: str = ""
    gioi_tinh: str = "U"
    so_cccd: str
    noi_tt: str = ""

    @field_validator("ho_ten", "so_cccd")
    @classmethod
    def _khong_rong(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Không được để trống")
        return v.strip()

    @field_validator("so_cccd")
    @classmethod
    def _cccd_so(cls, v: str) -> str:
        if not v.isdigit() or len(v) > 20:
            raise ValueError("Số căn cước phải là chữ số, tối đa 20 ký tự")
        return v

    @field_validator("noi_tt")
    @classmethod
    def _noitt_do_dai(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) > _NOITT_MAX:
            raise ValueError(f"Địa chỉ thường trú tối đa {_NOITT_MAX} ký tự")
        return v

    @field_validator("ngay_sinh")
    @classmethod
    def _ngay_sinh_hop_le(cls, v: str) -> str:
        so = re.sub(r"\D", "", v or "")
        if so and len(so) not in (4, 6, 8):
            raise ValueError("Ngày sinh phải là năm (yyyy) hoặc ngày/tháng/năm (dd/mm/yyyy)")
        return v


def dung_tham_so_update(cur_row: dict, body: HoSoSua, nguoi: str) -> tuple:
    """Dựng 24 tham số usp_NguoiLX_Update: chồng 5 trường user sửa lên bản ghi hiện tại,
    giữ nguyên mọi cột khác. SP tự getdate() cho NgaySua (giá trị truyền bị bỏ qua)."""
    ten = tach_ho_ten(body.ho_ten)  # IN HOA giữ dấu → HoVaTen/Ho/Ten/HoVaTenIn
    return (
        cur_row["MaDK"],
        cur_row["DonViNhanHSo"],
        ten["HoDemNLX"],
        ten["TenNLX"],
        ten["HoVaTen"],
        cur_row["MaQuocTich"],
        ngay_sinh_luu(body.ngay_sinh),
        body.noi_tt.strip(),
        cur_row["NoiTT_MaDVHC"],
        cur_row["NoiTT_MaDVQL"],
        cur_row["NoiCT"],
        cur_row["NoiCT_MaDVHC"],
        cur_row["NoiCT_MaDVQL"],
        body.so_cccd.strip(),
        cur_row["NgayCapCMT"],
        cur_row["NoiCapCMT"],
        cur_row["GhiChu"],
        cur_row["TrangThai"],
        cur_row["NguoiTao"],
        nguoi,                       # NguoiSua ← người đang đăng nhập
        cur_row["NgayTao"],
        cur_row["NgaySua"],          # SP ghi đè bằng getdate()
        gioi_tinh_ma(body.gioi_tinh),
        ten["HoVaTenIn"],
    )


@router.get("")
def ds_ho_so(makh: str = Query(..., min_length=1)):
    """Lưới học viên theo khóa (usp_NguoiLX_Select_By_MaKH). Tìm trong lưới = lọc phía
    client trên kết quả này (bỏ dấu tên / CCCD) như NAP-01/THU-02."""
    try:
        with sqlserver_cursor() as cur:
            cur.execute("EXEC dbo.usp_NguoiLX_Select_By_MaKH @MaKH=%s", (makh,))
            rows = cur.fetchall()
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không truy vấn được SQL Server — kiểm kết nối.")

    return [
        {
            "ma_dk": r["MaDK"],
            "ho_ten": r["HoVaTen"],
            "ngay_sinh": r["NgaySinh"],
            "gioi_tinh": r["GioiTinh"],
            "so_cccd": r["SoCMT"],
            "so_cmnd_cu": r["SO_CMND_CU"],
            "so_ho_so": r["SoHoSo"],
            "noi_tt": r["NoiTT"],
            "co_anh": bool((r["DuongDanAnh"] or "").strip()),
            "ma_loai_hs": r["MaLoaiHs"],
        }
        for r in rows
    ]


@router.get("/chi-tiet")
def chi_tiet(ma_dk: str = Query(..., min_length=1)):
    """Nhân thân 1 HV để mở form sửa (đọc thẳng NguoiLX) + tên xã HKTT + cờ khóa đã BC1.

    bc1=True → UI chỉ cho xem (BR-012). ngay_sinh/giới tính trả về dạng để hiển thị trên ô."""
    sql = (
        "SELECT nl.MaDK, nl.HoVaTen, nl.NgaySinh, nl.GioiTinh, nl.SoCMT, nl.NoiTT, "
        "tt.TenDayDu AS HKTT, hs.MaKhoaHoc, "
        "CASE WHEN EXISTS (SELECT 1 FROM BaoCaoI b WHERE b.MaKH = hs.MaKhoaHoc) THEN 1 ELSE 0 END AS bc1 "
        "FROM NguoiLX nl "
        "JOIN NguoiLX_HoSo hs ON hs.MaDK = nl.MaDK "
        "LEFT JOIN DM_DVHC tt ON tt.MaDvhc = nl.NoiTT_MaDVHC "
        "WHERE nl.MaDK = %s"
    )
    try:
        with sqlserver_cursor() as cur:
            cur.execute(sql, (ma_dk,))
            r = cur.fetchone()
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không truy vấn được SQL Server — kiểm kết nối.")

    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ học viên.")
    gt = (r["GioiTinh"] or "").strip().upper()
    return {
        "ma_dk": r["MaDK"],
        "ho_ten": r["HoVaTen"],
        "ngay_sinh": ngay_sinh_hien(r["NgaySinh"]),
        "gioi_tinh": gt if gt in ("M", "F", "U") else "U",
        "gioi_tinh_ten": gioi_tinh_hien(gt),
        "so_cccd": r["SoCMT"],
        "noi_tt": r["NoiTT"],
        "hktt": r["HKTT"],
        "ma_kh": r["MaKhoaHoc"],
        "bc1": bool(r["bc1"]),
    }


@router.post("/sua")
def sua_ho_so(body: HoSoSua, ma_dk: str = Query(..., min_length=1),
             phien: Phien = Depends(require_session)):
    """Sửa nhân thân HV (GHI PROD) — usp_NguoiLX_Update, giữ nguyên cột không sửa.

    Chặn khi khóa đã BC1 (BR-012). Đọc + ghi trong 1 kết nối để bản ghi nền không đổi
    giữa đọc và ghi. SP tự BEGIN/COMMIT TRANSACTION + rollback nếu lỗi."""
    nguoi = (phien.ho_ten or phien.username or "tool")[:30]
    try:
        with sqlserver_conn(autocommit=True) as conn:
            cur = conn.cursor(as_dict=True)
            # 1) Khóa của HV + cờ BC1 (BR-012)
            cur.execute(
                "SELECT hs.MaKhoaHoc, "
                "CASE WHEN EXISTS (SELECT 1 FROM BaoCaoI b WHERE b.MaKH = hs.MaKhoaHoc) THEN 1 ELSE 0 END AS bc1 "
                "FROM NguoiLX_HoSo hs WHERE hs.MaDK = %s",
                (ma_dk,),
            )
            meta = cur.fetchone()
            if not meta:
                raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ học viên.")
            if meta["bc1"]:
                raise HTTPException(
                    status_code=409,
                    detail="Khóa đã lập Báo cáo 1 — chỉ xem, không sửa được. Cần sửa thì dùng app cũ.",
                )
            # 2) Đọc full bản ghi NguoiLX hiện tại (để giữ nguyên cột không sửa)
            cur.execute(
                f"SELECT {', '.join(_COT_NGUOILX)} FROM NguoiLX WHERE MaDK = %s", (ma_dk,)
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Không tìm thấy nhân thân học viên.")
            # 3) Validate độ dài cột (SP không tự cắt) rồi ghi
            ten = tach_ho_ten(body.ho_ten)
            loi = validate_do_dai(ten, body.so_cccd)
            if loi:
                raise HTTPException(status_code=400, detail="Dữ liệu vượt độ dài cột: " + "; ".join(loi))
            cur.execute(_EXEC_UPDATE, dung_tham_so_update(row, body, nguoi))
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không sửa được hồ sơ trên SQL Server — kiểm kết nối rồi thử lại.")

    return {"ok": True, "ma_dk": ma_dk}
