# -*- coding: utf-8 -*-
"""Tiện ích thao tác CSDL đích (GPLX_CDB_CSDT) cho phân hệ Đồng bộ CDB.

Port từ công cụ đồng bộ GPLX v2.0 (`db_helpers.py`), đổi driver pyodbc → pymssql.
Nhận một pymssql connection (mở qua `app.db.sqlserver_conn_dich`) và chỉ TRUY VẤN;
không mở/đóng kết nối, không INSERT (việc ghi do `sync_service` qua stored procedure).

Format MaDK ở CSDL đích (verify DB 04/10/2026, xem docs/DB-GPLX_CDB_CSDT.md):

    MaCSDT-yyyyMMdd-nnnnnn   (21 ký tự cố định)
    75032-20260803-000005    (CSDT 75032, ngày 03/08, HV thứ 5)

- 1-5:   MaCSDT (đúng 5 ký tự theo giả định của CreateNewMaDK)
- 6:     '-'
- 7-14:  yyyyMMdd (ngày nhập HS)
- 15:    '-'
- 16-21: 6 số thứ tự trong ngày, zero-pad, bắt đầu 000001
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)

MADK_LEN = 21
MADK_SEQ_START = 16
MADK_SEQ_LEN = 6
MADK_SEQ_PATTERN = "[0-9][0-9][0-9][0-9][0-9][0-9]"

_ENRICH_CHUNK_SIZE = 500  # tránh giới hạn tham số của driver


# -------------------------------------------------------------------------
# Sinh MaDK (dùng khi backdate — SP CreateNewMaDK hardcode GETDATE)
# -------------------------------------------------------------------------

def sinh_madk_batch(conn, ma_csdt: str, ngay_hs: date, so_luong: int) -> list[str]:
    """Sinh N MaDK liên tiếp cho ngày nhập HS chỉ định (không INSERT).

    Query MAX(số thứ tự) 1 lần cho prefix MaCSDT-yyyyMMdd rồi cấp dải
    [MAX+1 .. MAX+N]. Caller phải INSERT thành công từng MaDK trước khi
    dùng MaDK kế tiếp (app một người dùng nên race rất hiếm — có
    `kiem_tra_madk_ton_tai` chặn thêm).
    """
    if so_luong < 1:
        raise ValueError(f"so_luong phải >= 1, nhận {so_luong}")
    if not ma_csdt or not ma_csdt.strip():
        raise ValueError("ma_csdt không được rỗng")
    ma_csdt = ma_csdt.strip()
    # CreateNewMaDK cắt chuỗi cứng (LEFT 14 = 5 MaCSDT + 1 '-' + 8 ngày),
    # giả định MaCSDT đúng 5 ký tự. Khác → sinh MaDK sai vị trí → trùng.
    if len(ma_csdt) != 5:
        raise ValueError(
            f"MaCSDT phải đúng 5 ký tự (hiện '{ma_csdt}' = {len(ma_csdt)}). "
            f"CSDL đích yêu cầu MaDK dạng MaCSDT-yyyyMMdd-nnnnnn 21 ký tự."
        )

    ngay_str = ngay_hs.strftime("%Y%m%d")
    prefix = f"{ma_csdt}-{ngay_str}"  # 14 ký tự

    sql = """
        SELECT ISNULL(MAX(TRY_CAST(SUBSTRING(MaDK, 16, 6) AS INT)), 0) AS maxseq
        FROM dbo.NguoiLX_HoSo
        WHERE LEFT(MaDK, %s) = %s
          AND LEN(MaDK) = %s
          AND SUBSTRING(MaDK, 16, 6) LIKE %s
    """
    cur = conn.cursor(as_dict=True)
    cur.execute(sql, (len(prefix), prefix, MADK_LEN, MADK_SEQ_PATTERN))
    row = cur.fetchone()
    base_no = int(row["maxseq"]) if row and row["maxseq"] is not None else 0

    ma_dk_list = [f"{prefix}-{str(base_no + i).zfill(MADK_SEQ_LEN)}" for i in range(1, so_luong + 1)]
    logger.info("sinh_madk_batch prefix=%s base=%d n=%d", prefix, base_no, so_luong)
    return ma_dk_list


def kiem_tra_madk_ton_tai(conn, ma_dk: str) -> bool:
    """True nếu MaDK đã có trong NguoiLX (guard chống trùng trước INSERT)."""
    cur = conn.cursor(as_dict=True)
    cur.execute("SELECT 1 AS x FROM dbo.NguoiLX WHERE MaDK = %s", (ma_dk,))
    return cur.fetchone() is not None


# -------------------------------------------------------------------------
# Đối chiếu HV đã có ở CSDL đích (theo SoCMT) — cho lưới + quyết định skip
# -------------------------------------------------------------------------

def enrich_from_db_dich(conn, so_cmt_list: list[str]) -> dict[str, dict]:
    """Tra danh sách SoCMT trong CSDL đích → MaDK + NgàyHS mới nhất + số hồ sơ.

    SoCMT không có ở đích sẽ KHÔNG xuất hiện trong dict (caller check .get()).
    """
    result: dict[str, dict] = {}
    unique = sorted({c.strip() for c in (so_cmt_list or []) if c and c.strip()})
    if not unique:
        return result

    cur = conn.cursor(as_dict=True)
    for i in range(0, len(unique), _ENRICH_CHUNK_SIZE):
        chunk = unique[i : i + _ENRICH_CHUNK_SIZE]
        placeholders = ",".join(["%s"] * len(chunk))
        # placeholder chỉ là '%s' → không có SQL injection.
        sql = f"""
            SELECT nlx.SoCMT, nlx.MaDK, agg.NgayHSMax, agg.SoHS
            FROM dbo.NguoiLX nlx
            OUTER APPLY (
                SELECT MAX(NgayNhanHSo) AS NgayHSMax, COUNT(*) AS SoHS
                FROM dbo.NguoiLX_HoSo hs WHERE hs.MaDK = nlx.MaDK
            ) agg
            WHERE nlx.SoCMT IN ({placeholders})
        """
        cur.execute(sql, tuple(chunk))
        for r in cur.fetchall():
            socmt = (r["SoCMT"] or "").strip()
            result[socmt] = {
                "ma_dk": r["MaDK"],
                "ngay_hs_latest": r["NgayHSMax"],
                "so_hs": int(r["SoHS"]) if r["SoHS"] is not None else 0,
            }
    logger.info("enrich_from_db_dich: %d SoCMT → %d có ở đích", len(unique), len(result))
    return result


# -------------------------------------------------------------------------
# Năm + khóa học (combo nguồn & đích) — bám đúng v2.0
# -------------------------------------------------------------------------

def load_years_from_khoa(conn) -> list[int]:
    """Năm có khóa active (DISTINCT YEAR(NgayKG)), giảm dần. Rỗng → [năm nay]."""
    cur = conn.cursor(as_dict=True)
    cur.execute(
        "SELECT DISTINCT YEAR(NgayKG) AS Nam FROM dbo.KhoaHoc "
        "WHERE TrangThai = 1 AND NgayKG IS NOT NULL ORDER BY Nam DESC"
    )
    years = [int(r["Nam"]) for r in cur.fetchall()]
    if not years:
        return [datetime.now().year]
    return years


# -------------------------------------------------------------------------
# "Đã kết xuất DKKH" — ĐỊNH NGHĨA DÙNG CHUNG (verify DB 05/10/2026)
# -------------------------------------------------------------------------
# Một khóa ĐÃ KẾT XUẤT DKKH (đã gửi đăng ký khóa học lên Sở/TW) ⇔ tồn tại gói
# trong TRANS_CLI_HangDoiGui, KieuDuLieu='DANG_KY_KHOA_HOC', mà tên file DuongDan
# chứa MaKH của khóa (neo giữa 2 dấu '_': 'DKKH_75032_75_<MaKH>_yyyyMMdd_HHmmss.zip').
# KHÔNG dùng KhoaHoc.SoQD_KhaiGiang: mọi khóa đều có số QĐ khai giảng nội bộ nên
# cờ đó luôn bật, không phân biệt đã/chưa gửi Sở. KhoaHoc.TT_Xuly thì luôn NULL.
# Dùng CHARINDEX (không wildcard) để tránh vướng %/%% của pymssql. Chi tiết:
# docs/DB-GPLX_CDB_CSDT.md mục "Đã kết xuất DKKH".
def dkkh_exists_cond(alias: str = "kh") -> str:
    """Điều kiện SQL (bool) khóa `alias.MaKH` đã kết xuất DKKH — dùng trong WHERE / NOT EXISTS.

    Bảng TRANS_CLI_HangDoiGui chỉ có ở CSDL ĐÍCH — chỉ dùng cho truy vấn đích."""
    return (
        "EXISTS (SELECT 1 FROM dbo.TRANS_CLI_HangDoiGui g "
        "WHERE g.KieuDuLieu = 'DANG_KY_KHOA_HOC' "
        f"AND CHARINDEX('_' + {alias}.MaKH + '_', g.DuongDan) > 0)"
    )


def dkkh_exists_sql(alias: str = "kh") -> str:
    """Biểu thức SQL trả 1/0 (cho cột `dkkh` trong SELECT). Dựng trên `dkkh_exists_cond`."""
    return f"CASE WHEN {dkkh_exists_cond(alias)} THEN 1 ELSE 0 END"


def load_khoa_hoc_by_year(conn, year: Optional[int] = None, with_bc1: bool = False,
                          with_dkkh: bool = False) -> list[dict]:
    """Khóa active, lọc theo năm nếu có. Sort NgayKG DESC, MaKH DESC.

    Mỗi khóa: MaKH, TenKH, HangGPLX, NgayKG, SoHV. `with_bc1=True` kèm cờ
    `bc1` (khóa đích đã lập Báo cáo 1 → cảnh báo, phương án B). `with_dkkh=True`
    kèm cờ `dkkh` (đã kết xuất đăng ký khóa học lên Sở — xem `dkkh_exists_sql`;
    CHỈ bật cho CSDL ĐÍCH vì bảng TRANS_CLI_HangDoiGui chỉ có ở đích).

    MaKH DESC là khóa sắp xếp phụ để thứ tự ổn định khi nhiều khóa cùng NgayKG
    (không có nó, SQL Server trả thứ tự bất định → khóa vừa tạo không chắc lên đầu)."""
    bc1_col = (
        ", CASE WHEN EXISTS (SELECT 1 FROM dbo.BaoCaoI b WHERE b.MaKH = KH.MaKH) "
        "THEN 1 ELSE 0 END AS bc1"
        if with_bc1 else ""
    )
    dkkh_col = f", {dkkh_exists_sql('KH')} AS dkkh" if with_dkkh else ""
    where = "KH.TrangThai = 1"
    params: tuple = ()
    if year is not None:
        where += " AND YEAR(KH.NgayKG) = %s"
        params = (int(year),)
    sql = f"""
        SELECT KH.MaKH, KH.TenKH, KH.HangGPLX, KH.NgayKG,
               (SELECT COUNT(*) FROM dbo.NguoiLX_HoSo HS WHERE HS.MaKhoaHoc = KH.MaKH) AS SoHV
               {bc1_col}{dkkh_col}
        FROM dbo.KhoaHoc KH
        WHERE {where}
        ORDER BY KH.NgayKG DESC, KH.MaKH DESC
    """
    cur = conn.cursor(as_dict=True)
    cur.execute(sql, params) if params else cur.execute(sql)
    rows = cur.fetchall()
    out = []
    for r in rows:
        item = {
            "ma_kh": r["MaKH"],
            "ten_kh": r["TenKH"],
            "hang_gplx": r["HangGPLX"],
            "ngay_kg": r["NgayKG"],
            "so_hv": int(r["SoHV"]) if r["SoHV"] is not None else 0,
        }
        if with_bc1:
            item["bc1"] = bool(r["bc1"])
        if with_dkkh:
            item["dkkh"] = bool(r["dkkh"])
        out.append(item)
    return out


# -------------------------------------------------------------------------
# Mã CSĐT — lấy ĐÚNG cách (không bê từ bản ghi nguồn)
# -------------------------------------------------------------------------

def get_ma_csdt_tu_qtht(conn) -> Optional[str]:
    """Mã CSĐT chuẩn của CSDL đích = QTHT_ThamSoHT.MA_CSDT (vd 75032)."""
    cur = conn.cursor(as_dict=True)
    cur.execute("SELECT GiaTriTS FROM dbo.QTHT_ThamSoHT WHERE TenTS = 'MA_CSDT'")
    r = cur.fetchone()
    return r["GiaTriTS"].strip() if r and r["GiaTriTS"] else None


def get_ma_csdt_of_khoa(conn, ma_kh: str) -> Optional[str]:
    """Mã CSĐT của một khóa đích cụ thể (KhoaHoc.MaCSDT) — dùng khi sinh MaDK."""
    cur = conn.cursor(as_dict=True)
    cur.execute("SELECT MaCSDT FROM dbo.KhoaHoc WHERE MaKH = %s", (ma_kh,))
    r = cur.fetchone()
    return r["MaCSDT"].strip() if r and r["MaCSDT"] else None


def get_khoa_info(conn, ma_kh: str) -> Optional[dict[str, Any]]:
    """MaCSDT + MaSoGTVT + HangGPLX của khóa đích (dựng tham số INSERT)."""
    cur = conn.cursor(as_dict=True)
    cur.execute("SELECT MaCSDT, MaSoGTVT, HangGPLX FROM dbo.KhoaHoc WHERE MaKH = %s", (ma_kh,))
    r = cur.fetchone()
    if not r:
        return None
    return {
        "ma_csdt": (r["MaCSDT"] or "").strip(),
        "ma_so_gtvt": (r["MaSoGTVT"] or "").strip(),
        "hang_gplx": (r["HangGPLX"] or "").strip(),
    }
