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
import base64
import re
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, field_validator

from app import nap, vps
from app.db import sqlserver_cursor, sqlserver_conn, ConfigChuaDay
from app.image import jp2_sang_png, thumb_jp2
from app.nap import tach_ho_ten, validate_do_dai, sinh_so_ho_so, di_chuyen_anh, ghi_anh_update, log_xoa_hv
from app.session import Phien, require_session
from app.vps import VpsLoi

router = APIRouter(prefix="/local/ho-so", tags=["ho-so"])

_NOITT_MAX = 50  # NguoiLX.NoiTT nvarchar(50) (chi tiết thường trú)
_TEN_TS_IMG = "IMG_PATH_CSDT"  # tham số đường dẫn ảnh trong QTHT_ThamSoHT (đọc động)


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
    """Lưới học viên theo khóa. Tìm trong lưới = lọc phía client trên kết quả này
    (bỏ dấu tên / CCCD) như NAP-01/THU-02.

    BUG-02 (03/10): KHÔNG dùng SP app cũ `usp_NguoiLX_Select_By_MaKH` — SP đó lọc cứng
    `TT_XuLy IN ('03','04')` (chỉ HV đã có ảnh) nên HV nạp KHÔNG ảnh (BR-011, TT_XuLy='01')
    bị ẩn khỏi Tra cứu DB → "Xem trong DB" (NAP-01) không thấy HV vừa nạp, và bộ lọc
    "Chưa ảnh" (QLY-05) không bao giờ hiện gì. Thay bằng SELECT riêng, bỏ lọc TT_XuLy.
    Không sửa SP cũ (dùng chung app cũ — sửa là vỡ báo cáo cũ). Giữ nguyên shape trả về."""
    sql = (
        "SELECT A.MaDK, A.HoVaTen, A.NgaySinh, A.GioiTinh, A.SoCMT, A.SO_CMND_CU, "
        "B.SoHoSo, A.NoiTT, A.NoiCT, A.NoiCapCMT, "
        "CONVERT(varchar(8), A.NgayCapCMT, 112) AS NgayCapCMT, "  # datetime → yyyymmdd
        "dv.TenDV AS NoiCapTen, tt.TenDayDu AS HKTT, ct.TenDayDu AS HKCT, "
        "B.DuongDanAnh, B.MaLoaiHs "
        "FROM dbo.NguoiLX A JOIN dbo.NguoiLX_HoSo B ON A.MaDK = B.MaDK "
        "LEFT JOIN dbo.DM_DonViGTVT dv ON dv.MaDVQL = A.NoiCapCMT AND dv.LoaiDV = 'SO' "  # nơi cấp = Sở GTVT
        "LEFT JOIN dbo.DM_DVHC tt ON tt.MaDvhc = A.NoiTT_MaDVHC "
        "LEFT JOIN dbo.DM_DVHC ct ON ct.MaDvhc = A.NoiCT_MaDVHC "
        "WHERE B.MaKhoaHoc = %s AND B.TrangThai = 1 "
        "ORDER BY CAST(B.SoHoSo AS INT)"
    )
    try:
        with sqlserver_cursor() as cur:
            cur.execute(sql, (makh,))
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
            "hktt": r["HKTT"],              # thường trú đầy đủ (xã/tỉnh từ DM_DVHC)
            "noi_ct": r["NoiCT"],          # chi tiết cư trú
            "hkct": r["HKCT"],              # cư trú đầy đủ
            "ngay_cap": r["NgayCapCMT"],   # ngày cấp CCCD (yyyymmdd | None)
            "noi_cap_ma": r["NoiCapCMT"],  # mã Sở GTVT (nơi cấp)
            "noi_cap_ten": r["NoiCapTen"], # tên Sở GTVT (tỉnh cấp CCCD)
            "co_anh": bool((r["DuongDanAnh"] or "").strip()),
            "duong_dan_anh": (r["DuongDanAnh"] or "").strip() or None,  # QLY-01 task 35: hiện ở modal chi tiết
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


class DoiKhoaIn(BaseModel):
    """Input đổi khóa (QLY-02): khóa đích (cùng hạng, chưa BC1)."""
    ma_kh_dich: str

    @field_validator("ma_kh_dich")
    @classmethod
    def _khong_rong(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Chưa chọn khóa đích")
        return v.strip()


@router.post("/doi-khoa")
def doi_khoa(body: DoiKhoaIn, ma_dk: str = Query(..., min_length=1),
            phien: Phien = Depends(require_session)):
    """QLY-02 — đổi khóa CÙNG HẠNG cho HV đã nạp (GHI PROD).

    UPDATE nhắm 3 cột (MaKhoaHoc / SoHoSo / DuongDanAnh) WHERE MaDK — KHÔNG dùng
    usp_NguoiLX_HoSo_Update (ghi đè 65 cột, rủi ro xóa kết quả thi; CHANGES #18). Chặn (BR-013):
    khác hạng · khóa cũ hoặc khóa đích đã BC1 · HV đã có GPLX (có dòng NguoiLX_GPLX). SoHoSo sinh
    lại trong applock khóa đích (không trùng). File .jp2 di chuyển sang folder khóa mới (giữ tên MaDK).
    """
    ma_kh_moi = body.ma_kh_dich.strip()
    so_ho_so = None
    try:
        with sqlserver_conn(autocommit=True) as conn:
            cur = conn.cursor(as_dict=True)
            # 1) Hồ sơ hiện tại
            cur.execute("SELECT MaKhoaHoc, SoHoSo, DuongDanAnh FROM NguoiLX_HoSo WHERE MaDK=%s", (ma_dk,))
            hs = cur.fetchone()
            if not hs:
                raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ học viên.")
            ma_kh_cu = hs["MaKhoaHoc"]
            if ma_kh_cu == ma_kh_moi:
                raise HTTPException(status_code=400, detail="Học viên đã ở khóa này rồi.")

            # 2) Hai khóa + cờ BC1 + hạng
            cur.execute(
                "SELECT MaKH, HangGPLX, "
                "CASE WHEN EXISTS (SELECT 1 FROM BaoCaoI b WHERE b.MaKH = k.MaKH) THEN 1 ELSE 0 END AS bc1 "
                "FROM KhoaHoc k WHERE MaKH IN (%s, %s)",
                (ma_kh_cu, ma_kh_moi),
            )
            khoas = {r["MaKH"]: r for r in cur.fetchall()}
            cu, moi = khoas.get(ma_kh_cu), khoas.get(ma_kh_moi)
            if not moi:
                raise HTTPException(status_code=400, detail="Khóa đích không tồn tại.")
            if not cu:
                raise HTTPException(status_code=400, detail="Không đọc được khóa hiện tại của học viên.")
            if (cu["HangGPLX"] or "") != (moi["HangGPLX"] or ""):
                raise HTTPException(status_code=400, detail="Khác hạng — không đổi trực tiếp, phải xóa rồi tạo lại.")
            if cu["bc1"]:
                raise HTTPException(status_code=409, detail="Khóa hiện tại đã lập Báo cáo 1 — không đổi được.")
            if moi["bc1"]:
                raise HTTPException(status_code=409, detail="Khóa đích đã lập Báo cáo 1 — không nhận thêm được.")

            # 3) HV đã có GPLX → chặn (FK NguoiLX_GPLX NO_ACTION, BR-013)
            cur.execute("SELECT COUNT(*) AS n FROM NguoiLX_GPLX WHERE MaDK=%s", (ma_dk,))
            if cur.fetchone()["n"] > 0:
                raise HTTPException(status_code=409, detail="Học viên đã có GPLX — không đổi khóa được.")

            # 4) Đường dẫn ảnh (đọc động)
            cur.execute("SELECT GiaTriTS FROM QTHT_ThamSoHT WHERE TenTS=%s", (_TEN_TS_IMG,))
            r = cur.fetchone()
            img_path = (r and r["GiaTriTS"]) or ""
            if (hs["DuongDanAnh"] or "").strip() and not img_path:
                raise HTTPException(status_code=502, detail="Chưa cấu hình IMG_PATH_CSDT trên DB đích.")

            # 5) applock khóa đích → SoHoSo mới → di chuyển ảnh → UPDATE 3 cột
            cur.execute("EXEC sp_getapplock @Resource=%s, @LockMode='Exclusive', @LockTimeout=15000", (ma_kh_moi,))
            try:
                # SoHoSo = số nhỏ nhất chưa dùng (lấp khe, không MAX+1 — BUG-09, như nạp mới)
                cur.execute("SELECT CAST(SoHoSo AS INT) AS n FROM NguoiLX_HoSo WHERE MaKhoaHoc=%s", (ma_kh_moi,))
                so_ho_so = sinh_so_ho_so({r["n"] for r in cur.fetchall() if r["n"] is not None})
                duong_dan_moi = di_chuyen_anh(hs["DuongDanAnh"], ma_kh_moi, ma_dk, img_path)
                try:
                    cur.execute(
                        "UPDATE NguoiLX_HoSo SET MaKhoaHoc=%s, SoHoSo=%s, DuongDanAnh=%s WHERE MaDK=%s",
                        (ma_kh_moi, so_ho_so, duong_dan_moi, ma_dk),
                    )
                except Exception:
                    # UPDATE lỗi sau khi đã di chuyển ảnh → chuyển file NGƯỢC về khóa cũ để
                    # DB và filesystem nhất quán (DB chưa đổi). Lỗi hoàn tác thì nuốt, báo lỗi gốc.
                    if duong_dan_moi and (hs["DuongDanAnh"] or "").strip():
                        try:
                            di_chuyen_anh(duong_dan_moi, ma_kh_cu, ma_dk, img_path)
                        except Exception:
                            pass
                    raise
            finally:
                try:
                    cur.execute("EXEC sp_releaseapplock @Resource=%s", (ma_kh_moi,))
                except Exception:
                    pass
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError:
        raise HTTPException(status_code=409, detail="File ảnh đang bị khóa (app cũ đang mở) — đóng app cũ rồi thử lại.")
    except Exception:
        raise HTTPException(status_code=502, detail="Không đổi được khóa trên SQL Server — kiểm kết nối rồi thử lại.")

    return {"ok": True, "ma_dk": ma_dk, "ma_kh": ma_kh_moi, "so_ho_so": so_ho_so}


def _loi_vps(e: VpsLoi) -> HTTPException:
    """VpsLoi → HTTPException: giữ mã VPS cho các mã client cần phân biệt, còn lại gộp 502."""
    st = e.status if e.status in (401, 403, 404, 409) else 502
    return HTTPException(status_code=st, detail=str(e))


def _xoa_hv_csdt(ma_dk: str, nguoi: str) -> dict:
    """Gỡ HV khỏi CSDT (GHI PROD) — dùng chung QLY-03 'Xóa hẳn' và QLY-08 'Gỡ về chờ nạp'.

    `usp_NguoiLX_Delete` DELETE `NguoiLX` → cascade `NguoiLX_HoSo` + `NguoiLXHS_GiayTo`.
    Chặn BC1 (409, mất liên kết Báo cáo 1/2) và HV đã có GPLX (409, FK NO_ACTION, pre-check +
    verify vì SP không raiserror). File `.jp2` KHÔNG xóa cứng → **xóa mềm** sang folder `_DELETED`
    (giữ tên MaDK) + ghi log. Trả {ma_dk, ma_kh, anh_loi?}. Lỗi nghiệp vụ → HTTPException.
    """
    try:
        with sqlserver_conn(autocommit=True) as conn:
            cur = conn.cursor(as_dict=True)
            # 1) Hồ sơ hiện tại (lấy khóa + ảnh + cờ BC1 trước khi xóa)
            cur.execute(
                "SELECT hs.MaKhoaHoc, hs.DuongDanAnh, "
                "CASE WHEN EXISTS (SELECT 1 FROM BaoCaoI b WHERE b.MaKH = hs.MaKhoaHoc) THEN 1 ELSE 0 END AS bc1 "
                "FROM NguoiLX_HoSo hs WHERE hs.MaDK=%s",
                (ma_dk,),
            )
            hs = cur.fetchone()
            if not hs:
                raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ học viên.")
            ma_kh = hs["MaKhoaHoc"]
            duong_dan_cu = hs["DuongDanAnh"]

            # 1b) Khóa đã lập BC1 → CHẶN xóa ở backend (CHANGES #22, TDD §11.3). Xóa HV đã vào
            # Báo cáo làm mất liên kết NguoiLX_HoSo.MaBC1/MaBC2 → HV biến mất khỏi Báo cáo 1/2.
            # UI đã ẩn nút khi khóa BC1, nhưng phải chặn ở backend (không chỉ dựa vào UI).
            if hs["bc1"]:
                raise HTTPException(
                    status_code=409,
                    detail="Khóa đã lập Báo cáo 1 — không xóa học viên được (sẽ mất khỏi Báo cáo 1/2).",
                )

            # 2) HV đã có GPLX → chặn (FK NO_ACTION, BR-014). Pre-check cho thông báo rõ.
            cur.execute("SELECT COUNT(*) AS n FROM NguoiLX_GPLX WHERE MaDK=%s", (ma_dk,))
            if cur.fetchone()["n"] > 0:
                raise HTTPException(status_code=409, detail="Học viên đã có GPLX — không xóa được.")

            # 3) Đường dẫn ảnh (đọc động) — cần trước khi xóa để xóa mềm file
            cur.execute("SELECT GiaTriTS FROM QTHT_ThamSoHT WHERE TenTS=%s", (_TEN_TS_IMG,))
            r = cur.fetchone()
            img_path = (r and r["GiaTriTS"]) or ""

            # 4) Xóa DB (cascade). SP không raiserror → verify bản ghi đã mất.
            cur.execute("EXEC dbo.usp_NguoiLX_Delete @MaDK=%s", (ma_dk,))
            cur.execute("SELECT COUNT(*) AS n FROM NguoiLX WHERE MaDK=%s", (ma_dk,))
            if cur.fetchone()["n"] > 0:
                raise HTTPException(status_code=409, detail="Không xóa được — học viên có ràng buộc (vd đã có GPLX).")

            # 5) Xóa mềm ảnh: chuyển .jp2 sang folder _DELETED + log (DB đã xóa → lỗi file chỉ cảnh báo)
            duong_dan_moi = None
            anh_loi = None
            if (duong_dan_cu or "").strip():
                if img_path:
                    try:
                        duong_dan_moi = di_chuyen_anh(duong_dan_cu, "_DELETED", ma_dk, img_path)
                    except Exception as e:  # noqa: BLE001 — DB đã xóa, file lỗi không hoàn tác được
                        anh_loi = str(e)
                else:
                    # Thiếu cấu hình đường dẫn ảnh → không chuyển được, báo rõ (không im lặng)
                    anh_loi = "Chưa cấu hình IMG_PATH_CSDT — ảnh chưa chuyển sang _DELETED (còn ở thư mục cũ)."
            log_xoa_hv(ma_dk, ma_kh, duong_dan_cu, duong_dan_moi, nguoi)
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không xóa được học viên trên SQL Server — kiểm kết nối rồi thử lại.")

    out = {"ma_dk": ma_dk, "ma_kh": ma_kh}
    if anh_loi:
        out["anh_loi"] = anh_loi  # đã xóa DB nhưng chuyển ảnh _DELETED lỗi (file còn ở folder cũ)
    return out


@router.post("/xoa")
def xoa_ho_so(ma_dk: str = Query(..., min_length=1), phien: Phien = Depends(require_session)):
    """QLY-03 — xóa hẳn học viên nhập nhầm (GHI PROD). Gỡ khỏi CSDT + xóa mềm ảnh (không trả về
    hàng chờ — muốn nạp lại phải nhập lại ở app). Khác QLY-08 'Gỡ về chờ nạp'."""
    nguoi = (phien.ho_ten or phien.username or "tool")[:60]
    kq = _xoa_hv_csdt(ma_dk, nguoi)
    out = {"ok": True, "ma_dk": ma_dk}
    if "anh_loi" in kq:
        out["anh_loi"] = kq["anh_loi"]
    return out


def _dong_bo_tra_ve(vps_token: str | None, uuid: str) -> dict:
    """QLY-08 bước 4+5 — gọi VPS trả bản ghi gốc về chờ nạp + đưa dòng staging local về 'cho'.
    Dùng chung cho 'Gỡ về chờ nạp' và nút 'Thử lại đồng bộ'. VpsLoi để caller xử lý riêng
    (bước này KHÔNG đụng CSDT — an toàn chạy lại khi lần trước lỗi mạng)."""
    vps.tra_ve_cho_nap(vps_token, uuid)
    trong_hang_doi = nap.keo_ve_ve_cho(uuid)
    return {"uuid": uuid, "ve_cho_nap": True, "trong_hang_doi": trong_hang_doi}


@router.post("/go-ve-cho-nap")
def go_ve_cho_nap(ma_dk: str = Query(..., min_length=1), phien: Phien = Depends(require_session)):
    """QLY-08 — gỡ HV đã nạp (nhầm khóa) về chờ nạp (GHI PROD). Khác 'Xóa hẳn' (QLY-03): sau khi
    gỡ khỏi CSDT thì trả bản ghi gốc VPS về 'pending' để nạp lại đúng khóa, không nhập lại ở app.

    Thứ tự xóa-CSDT-TRƯỚC-rồi-VPS (TDD §11.7): tra uuid gốc TRƯỚC (không có → DỪNG, chưa xóa gì);
    gỡ CSDT (điểm KHÔNG hoàn tác); rồi gọi VPS. VPS lỗi SAU khi đã xóa CSDT → trả ok=True kèm
    `dong_bo_loi` để UI hiện banner + 'Thử lại đồng bộ' RIÊNG bước VPS (KHÔNG tạo lại HV ở CSDT).
    """
    token = phien.vps_token
    if not token:
        raise HTTPException(status_code=409, detail="Phiên chưa có quyền máy chủ — đăng nhập lại.")
    nguoi = (phien.ho_ten or phien.username or "tool")[:60]

    # Bước 2 (TRƯỚC khi xóa): tra uuid gốc — staging local ưu tiên, fallback VPS. Không tìm được
    # → DỪNG, KHÔNG xóa CSDT: xóa mà không trả về được = mất HV, buộc nhập lại ở app (chỉ Xóa hẳn).
    uuid = nap.lay_uuid_theo_ma_dk(ma_dk)
    if not uuid:
        try:
            uuid = vps.tra_uuid(token, ma_dk)
        except VpsLoi as e:
            raise _loi_vps(e)
    if not uuid:
        raise HTTPException(
            status_code=409,
            detail="Không tìm được hồ sơ gốc trên máy chủ để trả về chờ nạp (có thể đã dọn dữ liệu "
                   "quá hạn). Muốn bỏ hẳn học viên thì dùng 'Xóa hẳn'.",
        )

    # Bước 1+3: chặn BC1/GPLX → usp_NguoiLX_Delete + ảnh _DELETED (dùng chung QLY-03). Lỗi nghiệp
    # vụ raise ra TRƯỚC khi đụng gì → an toàn. Qua đây là CSDT đã xóa (điểm KHÔNG hoàn tác).
    kq_xoa = _xoa_hv_csdt(ma_dk, nguoi)

    # Bước 4+5: trả về chờ nạp trên VPS + staging 'cho'. Lỗi SAU khi đã xóa CSDT → báo rõ cho
    # operator, cho 'Thử lại đồng bộ' (idempotent). Không raise để UI không hiểu nhầm là chưa xóa.
    try:
        kq = _dong_bo_tra_ve(token, uuid)
    except VpsLoi as e:
        return {
            "ok": True, "ma_dk": ma_dk, "uuid": uuid, "da_xoa_csdt": True,
            "dong_bo_loi": str(e),
            "co_the_thu_lai": e.status not in (404, 409),  # 404/409 = VPS không còn bản gốc → thử lại vô ích
            **({"anh_loi": kq_xoa["anh_loi"]} if "anh_loi" in kq_xoa else {}),
        }
    out = {"ok": True, "ma_dk": ma_dk, **kq}
    if "anh_loi" in kq_xoa:
        out["anh_loi"] = kq_xoa["anh_loi"]
    return out


@router.post("/dong-bo-tra-ve")
def dong_bo_tra_ve(uuid: str = Query(..., min_length=1), phien: Phien = Depends(require_session)):
    """QLY-08 'Thử lại đồng bộ' — chạy lại RIÊNG bước gọi VPS trả về chờ nạp (KHÔNG xóa lại CSDT).
    Dùng khi 'Gỡ về chờ nạp' đã xóa CSDT nhưng bước đồng bộ VPS lỗi mạng. Idempotent (VPS trả 200
    khi bản ghi đã pending)."""
    token = phien.vps_token
    if not token:
        raise HTTPException(status_code=409, detail="Phiên chưa có quyền máy chủ — đăng nhập lại.")
    try:
        kq = _dong_bo_tra_ve(token, uuid)
    except VpsLoi as e:
        raise _loi_vps(e)
    return {"ok": True, **kq}


class NapAnhIn(BaseModel):
    jp2_b64: str  # ảnh .jp2 đã xử lý (crop 3:4 + nền trắng) từ /local/anh/xu-ly

    @field_validator("jp2_b64")
    @classmethod
    def _khong_rong(cls, v: str) -> str:
        if not (v or "").strip():
            raise ValueError("Thiếu dữ liệu ảnh.")
        return v


@router.post("/nap-anh")
def nap_anh(body: NapAnhIn, ma_dk: str = Query(..., min_length=1),
            phien: Phien = Depends(require_session)):
    """QLY-05 — nạp/thay ảnh cho HV đã có (GHI PROD).

    Dùng lại cơ chế ghi ảnh hướng A (§10.3): ghi `.jp2` tại <IMG_PATH_CSDT>\\<MaKhoaHoc>\\<MaDK>.jp2
    (ghi đè nếu đã có — thay ảnh) + UPDATE 5 cột ảnh `NguoiLX_HoSo` nâng `TT_XuLy='03'` WHERE MaDK.
    KHÔNG gọi SP tạo, KHÔNG tạo bản ghi mới. Ảnh đã được /local/anh/xu-ly xử lý sẵn (NAP-04);
    cảnh báo ghi đè ảnh cũ do UI lo (Done khi). Ca lỗi: file bị app cũ khóa → 409 báo đóng app cũ.
    """
    nguoi = (phien.ho_ten or phien.username or "tool")[:60]
    try:
        jp2_bytes = base64.b64decode(body.jp2_b64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Ảnh không hợp lệ.")
    if not jp2_bytes:
        raise HTTPException(status_code=400, detail="Thiếu dữ liệu ảnh.")

    try:
        with sqlserver_conn(autocommit=True) as conn:
            cur = conn.cursor(as_dict=True)
            # 1) Hồ sơ hiện tại → khóa (folder ảnh theo MaKhoaHoc)
            cur.execute("SELECT MaKhoaHoc FROM NguoiLX_HoSo WHERE MaDK=%s", (ma_dk,))
            hs = cur.fetchone()
            if not hs:
                raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ học viên.")
            ma_kh = hs["MaKhoaHoc"]

            # 2) Đường dẫn ảnh gốc (đọc động từ DB đích)
            cur.execute("SELECT GiaTriTS FROM QTHT_ThamSoHT WHERE TenTS=%s", (_TEN_TS_IMG,))
            r = cur.fetchone()
            img_path = (r and r["GiaTriTS"]) or ""
            if not img_path:
                raise HTTPException(status_code=502, detail="Chưa cấu hình IMG_PATH_CSDT trên DB đích.")

            # 3) Ghi .jp2 (ghi đè nếu có) + UPDATE 5 cột ảnh (hướng A). now = giờ máy DB.
            # EC (§11.5/§10.3): UPDATE lỗi sau khi đã ghi file → thử lại 1 lần theo MaDK
            # (ghi_anh_update ghi đè lại cùng file + UPDATE lại, không tạo HV mới). File bị khóa
            # (PermissionError) KHÔNG thử lại — retry cũng vô ích khi app cũ còn giữ file.
            try:
                duong_dan = ghi_anh_update(cur, ma_dk, ma_kh, jp2_bytes, img_path, datetime.now(), nguoi)
            except PermissionError:
                raise
            except Exception:
                duong_dan = ghi_anh_update(cur, ma_dk, ma_kh, jp2_bytes, img_path, datetime.now(), nguoi)
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError:
        raise HTTPException(status_code=409, detail="File ảnh đang bị khóa (app cũ đang mở) — đóng app cũ rồi thử lại.")
    except Exception:
        raise HTTPException(status_code=502, detail="Không ghi được ảnh trên SQL Server — kiểm kết nối rồi thử lại.")

    return {"ok": True, "ma_dk": ma_dk, "duong_dan_anh": duong_dan, "co_anh": True}


@router.get("/day-du")
def ho_so_day_du(ma_dk: str = Query(..., min_length=1), phien: Phien = Depends(require_session)):
    """QLY-06 — đọc ĐỦ dữ liệu cá nhân HV để điền sẵn khi mở hồ sơ khóa khác (nạp mới khóa đích).

    Trả các trường cần cho NapIn (SP gộp): họ tên, ngày sinh (yyyymmdd đã lưu), giới tính,
    số căn cước + ngày/nơi cấp, mã DVHC thường trú. Chỉ đọc NguoiLX, KHÔNG ghi.
    """
    sql = (
        "SELECT HoVaTen, NgaySinh, GioiTinh, SoCMT, NgayCapCMT, NoiCapCMT, "
        "NoiTT, NoiTT_MaDVHC, NoiTT_MaDVQL FROM NguoiLX WHERE MaDK=%s"
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
    ngay_cap = r["NgayCapCMT"]
    return {
        "ho_ten": r["HoVaTen"],
        "ngay_sinh": (r["NgaySinh"] or "").strip(),  # yyyymmdd (hoặc yyyy) như đã lưu
        "gioi_tinh": gt if gt in ("M", "F", "U") else "U",
        "so_cmt": r["SoCMT"],
        "ngay_cap_cmt": ngay_cap.strftime("%Y%m%d") if hasattr(ngay_cap, "strftime") else (ngay_cap or None),
        "noi_cap_cmt": r["NoiCapCMT"],
        "noi_tt": r["NoiTT"],
        "noi_tt_ma_dvhc": r["NoiTT_MaDVHC"],
        "noi_tt_ma_dvql": r["NoiTT_MaDVQL"],
    }


# ---- QLY-01 (task 34): phục vụ ảnh chân dung đã lưu cho màn Tra cứu DB (§11.1) ----
def _doc_duong_dan_anh(ma_dk: str) -> str | None:
    """Đọc DuongDanAnh của HV. Không có HV → 404. Trả None nếu HV chưa có ảnh."""
    with sqlserver_cursor() as cur:
        cur.execute("SELECT DuongDanAnh FROM NguoiLX_HoSo WHERE MaDK=%s", (ma_dk,))
        r = cur.fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ học viên.")
    return (r["DuongDanAnh"] or "").strip() or None


def _lay_file_anh(ma_dk: str) -> Path:
    """Chung cho 2 endpoint ảnh: tra đường dẫn → kiểm tồn tại. Chưa ảnh/mất file → 404."""
    try:
        duong_dan = _doc_duong_dan_anh(ma_dk)
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không truy vấn được SQL Server — kiểm kết nối.")
    if not duong_dan:
        raise HTTPException(status_code=404, detail="Học viên chưa có ảnh.")
    p = Path(duong_dan)
    if not p.exists():
        raise HTTPException(status_code=404,
                            detail="Không tìm thấy file ảnh trên ổ (DB có đường dẫn nhưng file đã mất).")
    return p


@router.get("/anh")
def xem_anh(ma_dk: str = Query(..., min_length=1), phien: Phien = Depends(require_session)):
    """Ảnh chân dung đã lưu (.jp2) → PNG để trình duyệt xem. File mất → 404; file hỏng → 422."""
    p = _lay_file_anh(ma_dk)
    try:
        png = jp2_sang_png(p.read_bytes())
    except ValueError:
        raise HTTPException(status_code=422, detail="Ảnh hỏng, không đọc được — cần nạp lại ảnh.")
    return Response(content=png, media_type="image/png")


@router.get("/anh-thumb")
def xem_anh_thumb(ma_dk: str = Query(..., min_length=1), phien: Phien = Depends(require_session)):
    """Thumbnail PNG (avatar lưới), cache in-memory theo mtime. File mất → 404; hỏng → 422."""
    p = _lay_file_anh(ma_dk)
    try:
        png = thumb_jp2(str(p))
    except ValueError:
        raise HTTPException(status_code=422, detail="Ảnh hỏng, không đọc được.")
    return Response(content=png, media_type="image/png")
