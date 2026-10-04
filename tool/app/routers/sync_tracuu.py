"""Tra cứu CDB đích — đọc HV trên CSDL ĐÍCH (GPLX_CDB_CSDT) cho Feature TCB.

TCB-01 (task 63): chỉ ĐỌC — tra khóa (mọi khóa kể cả BC1), lưới HV theo khóa,
chi tiết + ảnh. Mọi truy vấn qua `sqlserver_conn_dich(db_đích)` — KHÔNG đụng
`GPLX_CSDT` (DB Nạp). Song song router Nạp `hoso.py`/`khoahoc.py` nhưng trỏ đích.

Mount kèm `require_session` ở main.py (collector không có session cục bộ → 403),
đúng như mọi router /local/* nghiệp vụ.

Mốc khóa (TDD §11B.7, chốt /reviewtdd 04/10):
- `bc1` khóa (EXISTS BaoCaoI theo MaKH) — chỉ để HIỂN THỊ cờ cảnh báo ở lưới.
- `dkkh` = KhoaHoc.SoQD_KhaiGiang có giá trị — cờ đã kết xuất DKKH.
(Mốc CHẶN per-HV `MaBC1`/`SoQD_KhaiGiang` áp ở TCB-03/04, task 65/66.)
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Response

from app import sync_helpers
from app.db import sqlserver_conn_dich, ConfigChuaDay
from app.image import jp2_sang_png, thumb_jp2
from app.routers.sync import _db_dich, _loi_db  # dùng chung: chọn DB đích + gói lỗi

router = APIRouter(prefix="/local/sync/tra-cuu", tags=["sync-tracuu"])

# ── SQL dùng chung (bám đúng hoso.py bên Nạp, nhưng chạy trên conn đích) ──

# Tên nơi cấp/thường trú/cư trú lấy bằng SCALAR SUBQUERY (TOP 1) — KHÔNG LEFT JOIN:
# MaDvhc trong DM_DVHC không duy nhất → join nhân dòng HV (BUG-11 bên Nạp).
_SQL_HV_THEO_KHOA = (
    "SELECT A.MaDK, A.HoVaTen, A.NgaySinh, A.GioiTinh, A.SoCMT, A.SO_CMND_CU, "
    "B.SoHoSo, A.NoiTT, A.NoiCT, A.NoiCapCMT, "
    "CONVERT(varchar(8), A.NgayCapCMT, 112) AS NgayCapCMT, "
    "(SELECT TOP 1 dv.TenDV FROM dbo.DM_DonViGTVT dv WHERE dv.MaDVQL = A.NoiCapCMT AND dv.LoaiDV = 'SO') AS NoiCapTen, "
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
    """Hai cờ hiển thị cho khóa đích: bc1 (cấp khóa) + dkkh (đã kết xuất DKKH)."""
    return (
        f", CASE WHEN EXISTS (SELECT 1 FROM dbo.BaoCaoI b WHERE b.MaKH = {alias}.MaKH) "
        "THEN 1 ELSE 0 END AS bc1"
        f", CASE WHEN {alias}.SoQD_KhaiGiang IS NOT NULL AND LTRIM(RTRIM({alias}.SoQD_KhaiGiang)) <> '' "
        "THEN 1 ELSE 0 END AS dkkh"
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
