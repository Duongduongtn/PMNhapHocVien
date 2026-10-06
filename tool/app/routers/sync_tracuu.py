"""Tra cứu CDB đích — đọc HV trên CSDL ĐÍCH (GPLX_CDB_CSDT) cho Feature TCB.

TCB-01 (task 63): chỉ ĐỌC — tra khóa (mọi khóa kể cả BC1), lưới HV theo khóa,
chi tiết + ảnh. Mọi truy vấn qua `sqlserver_conn_dich(db_đích)` — KHÔNG đụng
`GPLX_CSDT` (DB Nạp). Song song router Nạp `hoso.py`/`khoahoc.py` nhưng trỏ đích.

Mount kèm `require_session` ở main.py (collector không có session cục bộ → 403),
đúng như mọi router /local/* nghiệp vụ.

Mốc khóa (TDD §11B.7, chốt /reviewtdd 04/10):
- `bc1` khóa (EXISTS BaoCaoI theo MaKH) — chỉ để HIỂN THỊ cờ cảnh báo ở lưới.
- `dkkh` = khóa đã kết xuất đăng ký khóa học lên Sở (gói DANG_KY_KHOA_HOC trong
  TRANS_CLI_HangDoiGui chứa MaKH) — xem `sync_helpers.dkkh_exists_sql`. KHÔNG dùng
  SoQD_KhaiGiang (mọi khóa đều có số QĐ nội bộ nên không phân biệt được).
(Mốc CHẶN sửa nhân thân = dkkh áp ở TCB-03; xóa/đổi khóa = BC1 áp ở TCB-04, task 65/66.)
"""
from __future__ import annotations

import base64
import re
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, field_validator

from app import sync_helpers
from app import dvhc  # danh mục Tỉnh/Xã/Sở — TCB-03 đọc từ DB đích (CHANGES #37)
from app.db import sqlserver_conn_dich, ConfigChuaDay
from app.image import jp2_sang_png, thumb_jp2, validate_jp2
from app.nap import tach_ho_ten, validate_do_dai, sinh_so_ho_so
from app.routers.sync import _db_dich, _loi_db  # dùng chung: chọn DB đích + gói lỗi
# TCB-03: tái dùng khung sửa nhân thân của Nạp (QLY-01 lát 2) — đổi mốc chặn (BC1 → DKKH),
# chạy trên conn_dich. **Tái dùng `_EXEC_UPDATE`** (chuỗi SQL 24 tham số) nhưng model +
# hàm dựng tham số RIÊNG cho CDB (`HoSoSuaCDB`/`dung_tham_so_update_cdb` bên dưới, CHANGES #37):
# TCB-03 mở rộng thêm địa chỉ 2 cấp + ngày/nơi cấp CCCD, Nạp QLY-01 giữ 5 trường (user chốt).
from app.routers.hoso import (
    ngay_sinh_hien,
    ngay_sinh_luu,
    gioi_tinh_hien,
    gioi_tinh_ma,
    _COT_NGUOILX,
    _EXEC_UPDATE,
)
from app.session import Phien, require_session

router = APIRouter(prefix="/local/sync/tra-cuu", tags=["sync-tracuu"])


def thay_anh_ghi_de(duong_dan: str, jp2_bytes: bytes) -> str:
    """TCB-02 — ghi đè ĐÚNG file .jp2 cũ (giữ nguyên tên + đường dẫn).

    Trước khi đè, **sao lưu `<stem>_BACKUP.jp2` CÙNG thư mục** — CHỈ nếu chưa có (chạy lần 2 không
    đè mất bản gốc). Ghi atomic (temp → replace) để crash giữa chừng không để lại .jp2 cụt.
    Ảnh là file VẬT LÝ dùng chung 2 DB (Nạp + đích) → thao tác này đổi ảnh ở cả hai.

    File không còn → FileNotFoundError. File bị phần mềm CDB khóa → PermissionError (caller → 409).
    """
    p = Path(duong_dan)
    if not p.exists():
        raise FileNotFoundError(duong_dan)
    backup = p.with_name(f"{p.stem}_BACKUP{p.suffix}")
    if not backup.exists():
        shutil.copy2(p, backup)  # giữ bản gốc đầu tiên (copy2 giữ cả metadata)
    tmp = p.with_name(f"{p.name}.tmp")
    tmp.write_bytes(jp2_bytes)
    try:
        tmp.replace(p)  # nguyên tử; app CDB còn khóa file → PermissionError
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return str(p)


class NapAnhCDBIn(BaseModel):
    jp2_b64: str


@router.post("/nap-anh")
def nap_anh_dich(body: NapAnhCDBIn, ma_dk: str = Query(..., min_length=1),
                 target_key: str | None = None, phien: Phien = Depends(require_session)):
    """TCB-02 — thay ảnh HV ở CDB đích (GHI). Ghi đè đúng file .jp2 cũ (giữ `DuongDanAnh`), sao lưu
    `_BACKUP` cùng thư mục trước khi đè, cập nhật `ChatLuongAnh`/`NgayThuNhanAnh` ở bản ghi CDB.

    Ảnh dùng chung 2 DB → đổi cả ở Nạp. Cho phép kể cả khi DKKH/BC1 (cảnh báo do UI lo). KHÔNG đụng
    `TT_XuLy`/`DuongDanAnh`. File bị phần mềm CDB khóa → 409; file cũ đã mất → 404; ghi lỗi → không
    cập nhật DB (ghi file TRƯỚC, UPDATE SAU)."""
    db = _db_dich(target_key)
    nguoi = (phien.ho_ten or phien.username or "tool")[:60]
    try:
        jp2_bytes = base64.b64decode(body.jp2_b64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Ảnh không hợp lệ.")
    if not jp2_bytes:
        raise HTTPException(status_code=400, detail="Thiếu dữ liệu ảnh.")
    try:
        validate_jp2(jp2_bytes)  # ≤8 MB + magic-byte .jp2 (§7.4) — chặn file quá cỡ / không phải ảnh
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        with sqlserver_conn_dich(db, autocommit=True) as conn:
            cur = conn.cursor(as_dict=True)
            cur.execute("SELECT DuongDanAnh FROM dbo.NguoiLX_HoSo WHERE MaDK=%s", (ma_dk,))
            r = cur.fetchone()
            if not r:
                raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ học viên ở CSDL đích.")
            duong_dan = (r["DuongDanAnh"] or "").strip()
            if not duong_dan:
                raise HTTPException(status_code=409,
                                    detail="Học viên chưa có ảnh ở CDB — chức năng này chỉ thay ảnh đã có.")
            thay_anh_ghi_de(duong_dan, jp2_bytes)  # backup + ghi đè file (dùng chung 2 DB)
            cur.execute(
                "UPDATE dbo.NguoiLX_HoSo SET ChatLuongAnh=1, NgayThuNhanAnh=%s, NguoiThuNhanAnh=%s "
                "WHERE MaDK=%s",
                (datetime.now(), nguoi, ma_dk),
            )
    except HTTPException:
        raise
    except PermissionError:
        raise HTTPException(status_code=409,
                            detail="File ảnh đang bị khóa (phần mềm CDB đang mở) — đóng rồi thử lại.")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File ảnh cũ không còn trên ổ — không ghi đè được.")
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không ghi được ảnh — kiểm kết nối rồi thử lại.")
    return {"ok": True, "ma_dk": ma_dk, "duong_dan_anh": duong_dan, "co_anh": True}

# ── SQL dùng chung (bám đúng hoso.py bên Nạp, nhưng chạy trên conn đích) ──

# Tên nơi cấp/thường trú/cư trú lấy bằng SCALAR SUBQUERY (TOP 1) — KHÔNG LEFT JOIN:
# MaDvhc trong DM_DVHC không duy nhất → join nhân dòng HV (BUG-11 bên Nạp).
_SQL_HV_THEO_KHOA = (
    "SELECT A.MaDK, A.HoVaTen, A.NgaySinh, A.GioiTinh, A.SoCMT, A.SO_CMND_CU, "
    "B.SoHoSo, A.NoiTT, A.NoiCT, A.NoiCapCMT, "
    "CONVERT(varchar(8), A.NgayCapCMT, 112) AS NgayCapCMT, "
    "(SELECT TOP 1 dv.TenNganGon FROM dbo.DM_DVHC dv WHERE dv.MaDvhc = A.NoiCapCMT AND LEN(dv.MaDvhc) = 2) AS NoiCapTen, "
    "(SELECT TOP 1 tt.TenDayDu FROM dbo.DM_DVHC tt WHERE tt.MaDvhc = A.NoiTT_MaDVHC) AS HKTT, "
    "(SELECT TOP 1 ct.TenDayDu FROM dbo.DM_DVHC ct WHERE ct.MaDvhc = A.NoiCT_MaDVHC) AS HKCT, "
    "B.DuongDanAnh, B.MaLoaiHs, B.TT_XuLy "
    "FROM dbo.NguoiLX A JOIN dbo.NguoiLX_HoSo B ON A.MaDK = B.MaDK "
    "WHERE B.MaKhoaHoc = %s AND B.TrangThai = 1 "
    "ORDER BY CAST(B.SoHoSo AS INT)"
)


def _row_hv(r: dict) -> dict:
    """Chuẩn hóa 1 dòng HV đích về shape HoSoRow (giống bên Nạp để tái dùng UI)."""
    return {
        "ma_dk": r["MaDK"],
        "ho_ten": r["HoVaTen"],
        "ngay_sinh": r["NgaySinh"],
        "gioi_tinh": r["GioiTinh"],
        "so_cccd": r["SoCMT"],
        "so_cmnd_cu": r["SO_CMND_CU"],
        "so_ho_so": r["SoHoSo"],
        "noi_tt": r["NoiTT"],
        "hktt": r["HKTT"],
        "noi_ct": r["NoiCT"],
        "hkct": r["HKCT"],
        "ngay_cap": r["NgayCapCMT"],
        "noi_cap_ma": r["NoiCapCMT"],
        "noi_cap_ten": r["NoiCapTen"],
        "co_anh": bool((r["DuongDanAnh"] or "").strip()),
        "duong_dan_anh": (r["DuongDanAnh"] or "").strip() or None,
        "ma_loai_hs": r["MaLoaiHs"],
        "tt_xuly": (r["TT_XuLy"] or "").strip() or None,
    }


def _khoa_flags_sql(alias: str) -> str:
    """Hai cờ hiển thị cho khóa đích: bc1 (cấp khóa) + dkkh (đã kết xuất DKKH).

    dkkh dùng ĐỊNH NGHĨA CHUNG `sync_helpers.dkkh_exists_sql` (gói DANG_KY_KHOA_HOC
    đã gửi Sở), KHÔNG phải SoQD_KhaiGiang — xem docs/DB-GPLX_CDB_CSDT.md."""
    return (
        f", CASE WHEN EXISTS (SELECT 1 FROM dbo.BaoCaoI b WHERE b.MaKH = {alias}.MaKH) "
        "THEN 1 ELSE 0 END AS bc1"
        f", {sync_helpers.dkkh_exists_sql(alias)} AS dkkh"
    )


@router.get("/khoa")
def tra_cuu_khoa_dich(q: str = "", target_key: str | None = None) -> list[dict]:
    """Tìm khóa ở CSDL ĐÍCH theo tên/mã — mọi khóa (kể cả đã BC1), kèm cờ bc1 + dkkh.

    Lọc theo đúng CSĐT của DB đích (QTHT_ThamSoHT.MA_CSDT) như màn Nạp lọc theo CSĐT nguồn."""
    db = _db_dich(target_key)
    like = f"%{q.strip()}%"
    sql = (
        "SELECT TOP 50 k.MaKH, k.TenKH, k.HangGPLX, k.HangDT"
        + _khoa_flags_sql("k")
        + " FROM dbo.KhoaHoc k WHERE k.MaCSDT = %s AND k.TrangThai = 1 "
        "AND (k.MaKH LIKE %s OR k.TenKH LIKE %s) ORDER BY k.NgayTao DESC"
    )
    try:
        with sqlserver_conn_dich(db) as conn:
            ma_csdt = sync_helpers.get_ma_csdt_tu_qtht(conn)
            if not ma_csdt:
                raise HTTPException(status_code=400, detail="CSDL đích thiếu MA_CSDT trong QTHT_ThamSoHT.")
            cur = conn.cursor(as_dict=True)
            cur.execute(sql, (ma_csdt, like, like))
            rows = cur.fetchall()
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)
    return [
        {
            "ma_kh": r["MaKH"],
            "ten_kh": r["TenKH"],
            "hang_gplx": r["HangGPLX"],
            "hang_dt": r["HangDT"],
            "bc1": bool(r["bc1"]),
            "dkkh": bool(r["dkkh"]),
        }
        for r in rows
    ]


@router.get("/ho-so")
def ds_ho_so_dich(makh: str = Query(..., min_length=1), target_key: str | None = None) -> list[dict]:
    """Lưới học viên của 1 khóa ĐÍCH. Tìm trong lưới = lọc client (bỏ dấu tên / CCCD).

    Bỏ lọc TT_XuLy (hiện cả HV chưa ảnh) như BUG-02 bên Nạp."""
    db = _db_dich(target_key)
    try:
        with sqlserver_conn_dich(db) as conn:
            cur = conn.cursor(as_dict=True)
            cur.execute(_SQL_HV_THEO_KHOA, (makh,))
            rows = cur.fetchall()
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)
    return [_row_hv(r) for r in rows]


@router.get("/khoa-cua-madk")
def khoa_cua_madk(ma_dk: str = Query(..., min_length=1), target_key: str | None = None) -> dict:
    """Khóa chứa 1 MaDK đích → mở đúng khóa + tô sáng HV khi bấm "Xem chi tiết HV"
    từ Bàn đồng bộ (SYNC-01). HV không có ở đích → 404."""
    db = _db_dich(target_key)
    sql = (
        "SELECT k.MaKH, k.TenKH, k.HangGPLX, k.HangDT"
        + _khoa_flags_sql("k")
        + " FROM dbo.NguoiLX_HoSo hs JOIN dbo.KhoaHoc k ON k.MaKH = hs.MaKhoaHoc "
        "WHERE hs.MaDK = %s AND hs.TrangThai = 1"
    )
    try:
        with sqlserver_conn_dich(db) as conn:
            cur = conn.cursor(as_dict=True)
            cur.execute(sql, (ma_dk,))
            r = cur.fetchone()
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy học viên ở CSDL đích.")
    return {
        "ma_kh": r["MaKH"],
        "ten_kh": r["TenKH"],
        "hang_gplx": r["HangGPLX"],
        "hang_dt": r["HangDT"],
        "bc1": bool(r["bc1"]),
        "dkkh": bool(r["dkkh"]),
    }


# ── Phục vụ ảnh chân dung đích (.jp2 → PNG). Ảnh là file VẬT LÝ dùng chung với
#    DB Nạp (DuongDanAnh copy verbatim khi sync) — đọc theo DuongDanAnh ở bản ghi CDB. ──
def _file_anh_dich(db: str, ma_dk: str) -> Path:
    try:
        with sqlserver_conn_dich(db) as conn:
            cur = conn.cursor(as_dict=True)
            cur.execute("SELECT DuongDanAnh FROM dbo.NguoiLX_HoSo WHERE MaDK=%s", (ma_dk,))
            r = cur.fetchone()
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ học viên ở CSDL đích.")
    duong_dan = (r["DuongDanAnh"] or "").strip() or None
    if not duong_dan:
        raise HTTPException(status_code=404, detail="Học viên chưa có ảnh.")
    p = Path(duong_dan)
    if not p.exists():
        raise HTTPException(status_code=404,
                            detail="Không tìm thấy file ảnh trên ổ (DB có đường dẫn nhưng file đã mất).")
    return p


@router.get("/anh")
def xem_anh_dich(ma_dk: str = Query(..., min_length=1), target_key: str | None = None):
    """Ảnh chân dung đích (.jp2) → PNG. File mất → 404; file hỏng → 422."""
    p = _file_anh_dich(_db_dich(target_key), ma_dk)
    try:
        png = jp2_sang_png(p.read_bytes())
    except ValueError:
        raise HTTPException(status_code=422, detail="Ảnh hỏng, không đọc được — cần nạp lại ảnh.")
    return Response(content=png, media_type="image/png")


@router.get("/anh-thumb")
def xem_anh_thumb_dich(ma_dk: str = Query(..., min_length=1), target_key: str | None = None):
    """Thumbnail PNG (avatar lưới) ảnh đích. File mất → 404; hỏng → 422."""
    p = _file_anh_dich(_db_dich(target_key), ma_dk)
    try:
        png = thumb_jp2(str(p))
    except ValueError:
        raise HTTPException(status_code=422, detail="Ảnh hỏng, không đọc được.")
    return Response(content=png, media_type="image/png")


# ── TCB-03: sửa nhân thân HV ở CDB đích (chặn khi đã kết xuất DKKH) ──
# Mốc chặn = khóa đã kết xuất DKKH (gửi đăng ký khóa học lên Sở), định nghĩa chung
# ở sync_helpers.dkkh_exists_sql — KHÔNG dùng SoQD_KhaiGiang (sai, mọi khóa đều có).
_DKKH_SQL = sync_helpers.dkkh_exists_sql("kh") + " AS dkkh"


class HoSoSuaCDB(BaseModel):
    """Trường nhân thân sửa ở CDB đích (TCB-03, CHANGES #37). Model RIÊNG cho CDB — KHÔNG
    mở rộng `HoSoSua` dùng chung (Nạp QLY-01 giữ 5 trường, user chốt 05/10).

    5 trường bản đầu: ho_ten, ngay_sinh, gioi_tinh, so_cccd, noi_tt (chi tiết chữ tự do).
    4 trường mở rộng #37 — địa chỉ 2 cấp + ngày/nơi cấp CCCD. **Bỏ trống thì GIỮ giá trị cũ**
    (dung_tham_so_update_cdb fallback về cur_row) → không ghi đè rỗng, không mất dữ liệu.
    """
    ho_ten: str
    ngay_sinh: str = ""
    gioi_tinh: str = "U"
    so_cccd: str
    noi_tt: str = ""
    # Mở rộng #37 — rỗng = giữ giá trị cũ
    noi_tt_ma_dvhc: str = ""   # mã xã/phường (DM_DVHC)
    noi_tt_ma_dvql: str = ""   # mã tỉnh (MaDVQL)
    ngay_cap_cmt: str = ""     # ngày cấp CCCD — 'yyyymmdd' từ UI (rỗng = giữ cũ)
    noi_cap_cmt: str = ""      # nơi cấp CCCD — mã Sở GTVT (MaDVQL)

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

    @field_validator("ngay_cap_cmt")
    @classmethod
    def _ngay_cap_hop_le(cls, v: str) -> str:
        """Chuẩn hóa về 'yyyymmdd' (8 số) hoặc rỗng; chặn ngày cấp > hôm nay (PRD TCB-03)."""
        so = re.sub(r"\D", "", v or "")
        if not so:
            return ""
        if len(so) != 8:
            raise ValueError("Ngày cấp CCCD phải đủ ngày/tháng/năm (dd/mm/yyyy)")
        try:
            d = datetime.strptime(so, "%Y%m%d").date()
        except ValueError:
            raise ValueError("Ngày cấp CCCD không hợp lệ")
        if d > datetime.now().date():
            raise ValueError("Ngày cấp CCCD không được sau hôm nay")
        return so


def _hoac_cu(moi: str, cu):
    """#37 bỏ-trống-giữ-cũ: giá trị UI gửi lên không rỗng thì dùng, rỗng thì giữ cột cũ."""
    m = (moi or "").strip()
    return m if m else cu


def dung_tham_so_update_cdb(cur_row: dict, body: HoSoSuaCDB, nguoi: str) -> tuple:
    """Dựng 24 tham số cho `_EXEC_UPDATE` (usp_NguoiLX_Update) ở CDB — chồng các trường
    user sửa lên bản ghi hiện tại, giữ nguyên cột không sửa. KHÁC bản Nạp `dung_tham_so_update`
    ở chỗ 4 trường mở rộng #37 do body điều khiển (bỏ trống → giữ cur_row). SP tự getdate() NgaySua."""
    ten = tach_ho_ten(body.ho_ten)  # IN HOA giữ dấu → HoVaTen/Ho/Ten/HoVaTenIn
    return (
        cur_row["MaDK"],
        cur_row["DonViNhanHSo"],
        ten["HoDemNLX"],
        ten["TenNLX"],
        ten["HoVaTen"],
        cur_row["MaQuocTich"],
        ngay_sinh_luu(body.ngay_sinh),
        body.noi_tt.strip(),                                 # chi tiết thường trú (chữ)
        _hoac_cu(body.noi_tt_ma_dvhc, cur_row["NoiTT_MaDVHC"]),   # #37 xã (bỏ trống = giữ)
        _hoac_cu(body.noi_tt_ma_dvql, cur_row["NoiTT_MaDVQL"]),   # #37 tỉnh
        cur_row["NoiCT"],
        cur_row["NoiCT_MaDVHC"],
        cur_row["NoiCT_MaDVQL"],
        body.so_cccd.strip(),
        _hoac_cu(body.ngay_cap_cmt, cur_row["NgayCapCMT"]),  # #37 ngày cấp CCCD
        _hoac_cu(body.noi_cap_cmt, cur_row["NoiCapCMT"]),    # #37 nơi cấp CCCD (Sở)
        cur_row["GhiChu"],
        cur_row["TrangThai"],
        cur_row["NguoiTao"],
        nguoi,                                               # NguoiSua ← người đăng nhập
        cur_row["NgayTao"],
        cur_row["NgaySua"],                                  # SP ghi đè bằng getdate()
        gioi_tinh_ma(body.gioi_tinh),
        ten["HoVaTenIn"],
    )


# ── Danh mục Tỉnh/Xã/Sở ĐỌC TỪ DB ĐÍCH (CHANGES #37) ──
# Bộ chọn địa chỉ 2 cấp + nơi cấp CCCD trong form sửa TCB-03 phải đọc danh mục ở CDB đích
# (theo target_key), KHÔNG dùng endpoint /local/dvhc/* (trỏ DB Nạp) — nếu không Xã/Sở hiện sai.
# Dùng chung hàm `app.dvhc.ds_*` với tham số `db` = tên CSDL đích.
@router.get("/dvhc/tinh")
def dvhc_tinh_dich(target_key: str | None = None) -> list[dict]:
    try:
        return dvhc.ds_tinh(_db_dich(target_key))
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)


@router.get("/dvhc/xa")
def dvhc_xa_dich(tinh: str = Query(..., min_length=1, max_length=10),
                 target_key: str | None = None) -> list[dict]:
    try:
        return dvhc.ds_xa(tinh, _db_dich(target_key))
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)


@router.get("/dvhc/so-gtvt")
def dvhc_so_gtvt_dich(target_key: str | None = None) -> list[dict]:
    try:
        return dvhc.ds_so_gtvt(_db_dich(target_key))
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)


@router.get("/chi-tiet-sua")
def chi_tiet_sua_dich(ma_dk: str = Query(..., min_length=1), target_key: str | None = None) -> dict:
    """Nhân thân 1 HV đích để mở form sửa (TCB-03) + cờ `dkkh` (đã kết xuất DKKH → chặn sửa)."""
    db = _db_dich(target_key)
    sql = (
        "SELECT nl.MaDK, nl.HoVaTen, nl.NgaySinh, nl.GioiTinh, nl.SoCMT, nl.NoiTT, "
        "nl.NoiTT_MaDVHC, nl.NoiTT_MaDVQL, nl.NoiCapCMT, "
        "CONVERT(varchar(8), nl.NgayCapCMT, 112) AS NgayCapCMT, "  # ngày cấp → 'yyyymmdd'
        # SCALAR SUBQUERY (TOP 1) — KHÔNG LEFT JOIN: MaDvhc không unique → join nhân dòng (BUG-11).
        "(SELECT TOP 1 tt.TenDayDu FROM dbo.DM_DVHC tt WHERE tt.MaDvhc = nl.NoiTT_MaDVHC) AS HKTT, "
        "(SELECT TOP 1 dv.TenNganGon FROM dbo.DM_DVHC dv WHERE dv.MaDvhc = nl.NoiCapCMT AND LEN(dv.MaDvhc) = 2) AS NoiCapTen, "
        "hs.MaKhoaHoc, " + _DKKH_SQL + " "
        "FROM dbo.NguoiLX nl "
        "JOIN dbo.NguoiLX_HoSo hs ON hs.MaDK = nl.MaDK "
        "JOIN dbo.KhoaHoc kh ON kh.MaKH = hs.MaKhoaHoc "
        "WHERE nl.MaDK = %s"
    )
    try:
        with sqlserver_conn_dich(db) as conn:
            cur = conn.cursor(as_dict=True)
            cur.execute(sql, (ma_dk,))
            r = cur.fetchone()
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ học viên ở CSDL đích.")
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
        "dkkh": bool(r["dkkh"]),
        # #37 — mã hiện tại để form preselect (bỏ trống = giữ cũ khi lưu)
        "noi_tt_ma_dvhc": (r["NoiTT_MaDVHC"] or "").strip(),
        "noi_tt_ma_dvql": (r["NoiTT_MaDVQL"] or "").strip(),
        "ngay_cap_cmt": (r["NgayCapCMT"] or "") or "",   # 'yyyymmdd' | ''
        "noi_cap_cmt": (r["NoiCapCMT"] or "").strip(),
        "noi_cap_ten": (r["NoiCapTen"] or "").strip(),
    }


@router.post("/sua")
def sua_ho_so_dich(body: HoSoSuaCDB, ma_dk: str = Query(..., min_length=1),
                   target_key: str | None = None, phien: Phien = Depends(require_session)):
    """TCB-03 — sửa nhân thân HV ở CDB đích (GHI) qua `usp_NguoiLX_Update`, giữ nguyên cột không sửa.

    CHẶN khi khóa đã kết xuất DKKH (gói DANG_KY_KHOA_HOC đã gửi Sở — `dkkh_exists_sql`). KHÔNG đụng cột kết
    quả/BC1/BC2. Đọc + ghi trong 1 kết nối để bản ghi nền không đổi giữa đọc và ghi. Dùng model +
    bộ dựng-tham-số RIÊNG cho CDB (`HoSoSuaCDB`/`dung_tham_so_update_cdb`, CHANGES #37: +địa chỉ 2 cấp
    + ngày/nơi cấp CCCD, bỏ trống = giữ cũ) nhưng tái dùng `_EXEC_UPDATE`; mốc chặn DKKH, chạy conn_dich."""
    nguoi = (phien.ho_ten or phien.username or "tool")[:30]
    db = _db_dich(target_key)
    canh_bao = ""
    try:
        with sqlserver_conn_dich(db, autocommit=True) as conn:
            cur = conn.cursor(as_dict=True)
            # 1) Khóa của HV + cờ DKKH (mốc chặn sửa nhân thân)
            cur.execute(
                "SELECT hs.MaKhoaHoc, " + _DKKH_SQL + " "
                "FROM dbo.NguoiLX_HoSo hs JOIN dbo.KhoaHoc kh ON kh.MaKH = hs.MaKhoaHoc "
                "WHERE hs.MaDK = %s",
                (ma_dk,),
            )
            meta = cur.fetchone()
            if not meta:
                raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ học viên ở CSDL đích.")
            if meta["dkkh"]:
                raise HTTPException(
                    status_code=409,
                    detail="Khóa đã kết xuất DKKH (đã đăng ký khai giảng với Sở) — không sửa nhân thân qua tool.",
                )
            # 2) EC: CCCD trùng HV khác trong cùng khóa → CẢNH BÁO mềm (vẫn lưu — PRD TCB-03).
            cur.execute(
                "SELECT COUNT(*) AS n FROM dbo.NguoiLX nl JOIN dbo.NguoiLX_HoSo hs ON hs.MaDK = nl.MaDK "
                "WHERE hs.MaKhoaHoc = %s AND hs.TrangThai = 1 AND nl.SoCMT = %s AND nl.MaDK <> %s",
                (meta["MaKhoaHoc"], body.so_cccd.strip(), ma_dk),
            )
            if int((cur.fetchone() or {}).get("n", 0)) > 0:
                canh_bao = "Số căn cước vừa nhập trùng với học viên khác trong khóa — đã lưu, nên kiểm lại."
            # 3) Đọc full bản ghi NguoiLX hiện tại (giữ nguyên cột không sửa)
            cur.execute(f"SELECT {', '.join(_COT_NGUOILX)} FROM dbo.NguoiLX WHERE MaDK = %s", (ma_dk,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Không tìm thấy nhân thân học viên ở CSDL đích.")
            # 4) Validate độ dài cột (SP không tự cắt) rồi ghi
            ten = tach_ho_ten(body.ho_ten)
            loi = validate_do_dai(ten, body.so_cccd)
            if loi:
                raise HTTPException(status_code=400, detail="Dữ liệu vượt độ dài cột: " + "; ".join(loi))
            cur.execute(_EXEC_UPDATE, dung_tham_so_update_cdb(row, body, nguoi))
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không sửa được hồ sơ trên CSDL đích — kiểm kết nối rồi thử lại.")
    return {"ok": True, "ma_dk": ma_dk, "canh_bao": canh_bao}


# ── TCB-04: xóa HV / đổi khóa ở CDB đích ──
# Mốc chặn (CHANGES #36, 05/10/2026 — user chốt): khóa đã kết xuất DKKH (đã gửi
# danh sách đăng ký lên Sở) → KHÔNG xóa + KHÔNG đổi khóa (cả khóa đi lẫn khóa đến),
# vì thay đổi danh sách HV sẽ lệch với bản đã nộp Sở. BC1 vẫn giữ làm lưới an toàn
# (DKKH luôn trước BC1 nên DKKH là mốc chặn sớm hơn, bao trùm BC1) + bắt lỗi FK.
def _da_bc1(cur, ma_dk: str) -> bool:
    """HV đã BC1 ở đích = NguoiLX_HoSo.MaBC1 có giá trị (đúng cái FK NO_ACTION chặn xóa).
    KHÔNG dùng TT_XuLy, KHÔNG dùng dòng BaoCaoI cấp khóa (chốt /reviewtdd 04/10)."""
    cur.execute("SELECT MaBC1 FROM dbo.NguoiLX_HoSo WHERE MaDK=%s", (ma_dk,))
    r = cur.fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ học viên ở CSDL đích.")
    return bool((r["MaBC1"] or "") if isinstance(r["MaBC1"], str) else r["MaBC1"])


def _da_dkkh(cur, ma_dk: str) -> bool:
    """Khóa của HV đã kết xuất DKKH (gửi đăng ký khóa học lên Sở) — định nghĩa chung
    `sync_helpers.dkkh_exists_sql`. Chặn xóa + đổi khóa (TCB-04)."""
    cur.execute(
        "SELECT " + sync_helpers.dkkh_exists_sql("kh") + " AS dkkh "
        "FROM dbo.NguoiLX_HoSo hs JOIN dbo.KhoaHoc kh ON kh.MaKH = hs.MaKhoaHoc "
        "WHERE hs.MaDK = %s",
        (ma_dk,),
    )
    r = cur.fetchone()
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ học viên ở CSDL đích.")
    return bool(r["dkkh"])


@router.get("/khoa-cung-hang")
def khoa_cung_hang_dich(ma_dk: str = Query(..., min_length=1), target_key: str | None = None) -> list[dict]:
    """TCB-04 — khóa ĐÍCH để đổi khóa: cùng HangGPLX với khóa hiện tại của HV, **chưa BC1
    và chưa kết xuất DKKH** (gửi Sở), khác chính nó, cùng CSĐT đích. Chỉ cùng hạng mới đổi
    trực tiếp (như QLY-02). Lọc sẵn khóa đã DKKH để khỏi chọn rồi bị chặn ở bước đổi."""
    db = _db_dich(target_key)
    sql = (
        "SELECT k.MaKH, k.TenKH, k.HangGPLX, k.HangDT FROM dbo.KhoaHoc k "
        "JOIN dbo.NguoiLX_HoSo hs0 ON hs0.MaDK = %s "
        "JOIN dbo.KhoaHoc kcur ON kcur.MaKH = hs0.MaKhoaHoc "
        "WHERE k.MaCSDT = kcur.MaCSDT AND k.TrangThai = 1 AND k.MaKH <> kcur.MaKH "
        "AND k.HangGPLX = kcur.HangGPLX "
        "AND NOT EXISTS (SELECT 1 FROM dbo.BaoCaoI b WHERE b.MaKH = k.MaKH) "
        "AND NOT " + sync_helpers.dkkh_exists_cond("k") + " "
        "ORDER BY k.NgayTao DESC"
    )
    try:
        with sqlserver_conn_dich(db) as conn:
            cur = conn.cursor(as_dict=True)
            cur.execute(sql, (ma_dk,))
            rows = cur.fetchall()
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)
    return [{"ma_kh": r["MaKH"], "ten_kh": r["TenKH"], "hang_gplx": r["HangGPLX"], "hang_dt": r["HangDT"]} for r in rows]


@router.post("/xoa")
def xoa_ho_so_dich(ma_dk: str = Query(..., min_length=1), target_key: str | None = None,
                   phien: Phien = Depends(require_session)):
    """TCB-04 — xóa HV ở CDB đích (GHI). Chặn nếu HV đã BC1 (MaBC1). `usp_NguoiLX_Delete` cascade
    NguoiLX → NguoiLX_HoSo → GiayTo. **KHÔNG động file .jp2** (dùng chung với DB Nạp — xóa file sẽ
    làm Nạp mất ảnh); chỉ xóa bản ghi ở CDB. SP không raiserror → verify bản ghi đã mất."""
    db = _db_dich(target_key)
    try:
        with sqlserver_conn_dich(db, autocommit=True) as conn:
            cur = conn.cursor(as_dict=True)
            if _da_dkkh(cur, ma_dk):
                raise HTTPException(status_code=409,
                                    detail="Khóa đã kết xuất DKKH (đã gửi danh sách đăng ký lên Sở) — không xóa học viên (sẽ lệch danh sách với Sở).")
            if _da_bc1(cur, ma_dk):
                raise HTTPException(status_code=409,
                                    detail="Học viên đã lập Báo cáo 1 — không xóa được (sẽ mất khỏi Báo cáo 1/2).")
            cur.execute("EXEC dbo.usp_NguoiLX_Delete @MaDK=%s", (ma_dk,))
            cur.execute("SELECT COUNT(*) AS n FROM dbo.NguoiLX WHERE MaDK=%s", (ma_dk,))
            if int(cur.fetchone()["n"]) > 0:
                raise HTTPException(status_code=409,
                                    detail="Không xóa được — học viên có ràng buộc (vd đã lập Báo cáo / có GPLX).")
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không xóa được học viên trên CSDL đích — kiểm kết nối rồi thử lại.")
    return {"ok": True, "ma_dk": ma_dk}


class DoiKhoaCDBIn(BaseModel):
    ma_kh_dich: str


@router.post("/doi-khoa")
def doi_khoa_dich(body: DoiKhoaCDBIn, ma_dk: str = Query(..., min_length=1),
                  target_key: str | None = None, phien: Phien = Depends(require_session)):
    """TCB-04 — đổi khóa HV ở CDB đích (GHI), CÙNG HẠNG, chưa BC1. Chặn nếu HV đã BC1 (MaBC1).

    UPDATE 2 cột MaKhoaHoc + SoHoSo (SoHoSo sinh mới trong khóa đích qua applock). **GIỮ NGUYÊN
    DuongDanAnh** — KHÔNG di chuyển file (ảnh dùng chung với DB Nạp; đổi đường dẫn sẽ làm Nạp mất
    ảnh). KHÔNG dùng usp_NguoiLX_HoSo_Update (ghi đè nhiều cột, rủi ro xóa kết quả) — UPDATE nhắm cột."""
    ma_kh_moi = (body.ma_kh_dich or "").strip()
    if not ma_kh_moi:
        raise HTTPException(status_code=400, detail="Chưa chọn khóa đích.")
    db = _db_dich(target_key)
    try:
        with sqlserver_conn_dich(db, autocommit=True) as conn:
            cur = conn.cursor(as_dict=True)
            # 1) Hồ sơ hiện tại + chặn HV đã BC1
            cur.execute("SELECT MaKhoaHoc, MaBC1 FROM dbo.NguoiLX_HoSo WHERE MaDK=%s", (ma_dk,))
            hs = cur.fetchone()
            if not hs:
                raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ học viên ở CSDL đích.")
            if bool((hs["MaBC1"] or "") if isinstance(hs["MaBC1"], str) else hs["MaBC1"]):
                raise HTTPException(status_code=409, detail="Học viên đã lập Báo cáo 1 — không đổi khóa được.")
            ma_kh_cu = hs["MaKhoaHoc"]
            if ma_kh_cu == ma_kh_moi:
                raise HTTPException(status_code=400, detail="Học viên đã ở khóa này rồi.")
            # 2) Hai khóa: cùng hạng + cả hai chưa DKKH (gửi Sở) + khóa đích chưa BC1
            cur.execute(
                "SELECT MaKH, HangGPLX, "
                "CASE WHEN EXISTS (SELECT 1 FROM dbo.BaoCaoI b WHERE b.MaKH = k.MaKH) THEN 1 ELSE 0 END AS bc1, "
                + sync_helpers.dkkh_exists_sql("k") + " AS dkkh "
                "FROM dbo.KhoaHoc k WHERE MaKH IN (%s, %s)",
                (ma_kh_cu, ma_kh_moi),
            )
            khoas = {r["MaKH"]: r for r in cur.fetchall()}
            cu, moi = khoas.get(ma_kh_cu), khoas.get(ma_kh_moi)
            if not moi:
                raise HTTPException(status_code=400, detail="Khóa đích không tồn tại.")
            if not cu:
                raise HTTPException(status_code=400, detail="Không đọc được khóa hiện tại của học viên.")
            if (cu["HangGPLX"] or "") != (moi["HangGPLX"] or ""):
                raise HTTPException(status_code=400, detail="Khác hạng — không đổi trực tiếp.")
            if cu["dkkh"]:
                raise HTTPException(status_code=409, detail="Khóa hiện tại đã kết xuất DKKH (đã gửi danh sách lên Sở) — không chuyển học viên ra khỏi khóa (sẽ lệch danh sách với Sở).")
            if moi["dkkh"]:
                raise HTTPException(status_code=409, detail="Khóa đích đã kết xuất DKKH (đã gửi danh sách lên Sở) — không nhận thêm học viên (sẽ lệch danh sách với Sở).")
            if moi["bc1"]:
                raise HTTPException(status_code=409, detail="Khóa đích đã lập Báo cáo 1 — không nhận thêm được.")
            # 3) applock khóa đích → SoHoSo mới (lấp khe) → UPDATE (giữ DuongDanAnh)
            cur.execute("EXEC sp_getapplock @Resource=%s, @LockMode='Exclusive', @LockTimeout=15000", (ma_kh_moi,))
            try:
                cur.execute("SELECT CAST(SoHoSo AS INT) AS n FROM dbo.NguoiLX_HoSo WHERE MaKhoaHoc=%s", (ma_kh_moi,))
                so_ho_so = sinh_so_ho_so({r["n"] for r in cur.fetchall() if r["n"] is not None})
                cur.execute(
                    "UPDATE dbo.NguoiLX_HoSo SET MaKhoaHoc=%s, SoHoSo=%s WHERE MaDK=%s",
                    (ma_kh_moi, so_ho_so, ma_dk),
                )
            finally:
                try:
                    cur.execute("EXEC sp_releaseapplock @Resource=%s", (ma_kh_moi,))
                except Exception:
                    pass
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không đổi khóa được trên CSDL đích — kiểm kết nối rồi thử lại.")
    return {"ok": True, "ma_dk": ma_dk, "ma_kh_moi": ma_kh_moi}
