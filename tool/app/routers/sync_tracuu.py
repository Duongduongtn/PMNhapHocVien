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

import base64
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel

from app import sync_helpers
from app.db import sqlserver_conn_dich, ConfigChuaDay
from app.image import jp2_sang_png, thumb_jp2
from app.nap import tach_ho_ten, validate_do_dai
from app.routers.sync import _db_dich, _loi_db  # dùng chung: chọn DB đích + gói lỗi
# TCB-03: tái dùng Y HỆT cơ chế sửa nhân thân của Nạp (QLY-01 lát 2) — chỉ đổi mốc chặn
# (BC1 → DKKH) và chạy trên conn_dich. KHÔNG chép lại SQL 24 tham số để tránh lệch.
from app.routers.hoso import (
    HoSoSua,
    dung_tham_so_update,
    ngay_sinh_hien,
    gioi_tinh_hien,
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


# ── TCB-03: sửa nhân thân HV ở CDB đích (chặn khi đã kết xuất DKKH) ──
_DKKH_SQL = "CASE WHEN kh.SoQD_KhaiGiang IS NOT NULL AND LTRIM(RTRIM(kh.SoQD_KhaiGiang)) <> '' THEN 1 ELSE 0 END AS dkkh"


@router.get("/chi-tiet-sua")
def chi_tiet_sua_dich(ma_dk: str = Query(..., min_length=1), target_key: str | None = None) -> dict:
    """Nhân thân 1 HV đích để mở form sửa (TCB-03) + cờ `dkkh` (đã kết xuất DKKH → chặn sửa)."""
    db = _db_dich(target_key)
    sql = (
        "SELECT nl.MaDK, nl.HoVaTen, nl.NgaySinh, nl.GioiTinh, nl.SoCMT, nl.NoiTT, "
        "tt.TenDayDu AS HKTT, hs.MaKhoaHoc, " + _DKKH_SQL + " "
        "FROM dbo.NguoiLX nl "
        "JOIN dbo.NguoiLX_HoSo hs ON hs.MaDK = nl.MaDK "
        "JOIN dbo.KhoaHoc kh ON kh.MaKH = hs.MaKhoaHoc "
        "LEFT JOIN dbo.DM_DVHC tt ON tt.MaDvhc = nl.NoiTT_MaDVHC "
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
    }


@router.post("/sua")
def sua_ho_so_dich(body: HoSoSua, ma_dk: str = Query(..., min_length=1),
                   target_key: str | None = None, phien: Phien = Depends(require_session)):
    """TCB-03 — sửa nhân thân HV ở CDB đích (GHI) qua `usp_NguoiLX_Update`, giữ nguyên cột không sửa.

    CHẶN khi khóa đã kết xuất DKKH (`KhoaHoc.SoQD_KhaiGiang` có giá trị). KHÔNG đụng cột kết
    quả/BC1/BC2. Đọc + ghi trong 1 kết nối để bản ghi nền không đổi giữa đọc và ghi. Tái dùng
    nguyên bộ dựng-tham-số của Nạp (QLY-01 lát 2) — chỉ đổi mốc chặn BC1 → DKKH, chạy conn_dich."""
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
            cur.execute(_EXEC_UPDATE, dung_tham_so_update(row, body, nguoi))
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không sửa được hồ sơ trên CSDL đích — kiểm kết nối rồi thử lại.")
    return {"ok": True, "ma_dk": ma_dk, "canh_bao": canh_bao}
