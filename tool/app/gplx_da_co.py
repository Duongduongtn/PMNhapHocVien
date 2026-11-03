"""Bổ sung "GPLX đã có" cho học viên đã nạp (QLY-10, TCB-05, TDD §10.7). Dùng chung cho DB Nạp và DB đích.

Ghi bằng UPDATE đúng 6 cột theo MaDK, có điều kiện giá trị cũ. KHÔNG dùng SP gộp (nhánh cập nhật xóa/tạo lại
giấy tờ, ghi đè nhân thân, số hồ sơ) và không dùng usp_NguoiLX_HoSo_Update (ghi đè 65 cột).
"""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3

from app import nap, vps
from app.nap import _GPLX_THAM_SO, dung_chuoi_gplx_da_co

logger = logging.getLogger(__name__)

# Cột DB ↔ trường JSON, cùng thứ tự _GPLX_THAM_SO. NoiCapGPLXDaCo cố ý không đọc, không ghi (TDD §10.6).
GPLX_COT = (("SoGPLXDaCo", "so"), ("HangGPLXDaCo", "hang"), ("NgayTTGPLXDaCo", "ngay_tt"),
            ("NgayCapGPLXDaCo", "ngay_cap"), ("NgayHHGPLXDaCo", "ngay_hh"), ("DonViCapGPLXDaCo", "don_vi"))
TEN_COT = tuple(c for c, _ in GPLX_COT)

# Mã chỉ có ở luật mới; mã còn lại hiện theo luật cũ. `nhom` chỉ để hiện nhãn, không ghi xuống DB.
_HANG_LUAT_MOI = frozenset({"A1m", "A01", "A02", "C1", "D1"})

_SQL_DOC = (
    "SELECT hs.MaKhoaHoc, hs.HangGPLX, nl.HoVaTen, nl.NgaySinh, nl.SoCMT, "
    + ", ".join(f"hs.{c}" for c in TEN_COT)
    + " FROM dbo.NguoiLX_HoSo hs JOIN dbo.NguoiLX nl ON nl.MaDK = hs.MaDK WHERE hs.MaDK = %s"
)
_SQL_GHI = (
    "UPDATE dbo.NguoiLX_HoSo SET " + ", ".join(f"{c} = %s" for c in TEN_COT)
    + " WHERE MaDK = %s AND " + " AND ".join(f"ISNULL({c}, '') = %s" for c in TEN_COT)
)


def tho_tu_dong(row: dict) -> dict[str, str]:
    """Chuỗi thô 6 cột (NULL → ''), giao diện gửi lại nguyên văn khi lưu để so giá trị cũ."""
    return {c: row.get(c) or "" for c in TEN_COT}


def tach_chuoi_gplx(row: dict) -> tuple[list[dict], bool]:
    """6 chuỗi nối `|` → (danh sách bằng, có lệch số phần không). Thiếu phần thì để trống theo vị trí.
    Cột trống hẳn không tính là lệch (bằng mô tô thường không có ngày hết hạn)."""
    tho = tho_tu_dong(row)
    if not any(v.strip() for v in tho.values()):
        return [], False
    phan = {c: tho[c].split("|") for c in TEN_COT}
    n = max(len(p) for p in phan.values())
    lech = any(tho[c].strip() and len(phan[c]) != n for c in TEN_COT)
    ds = []
    for i in range(n):
        b = {f: (phan[c][i].strip() if i < len(phan[c]) else "") for c, f in GPLX_COT}
        b["nhom"] = "moi" if b["hang"] in _HANG_LUAT_MOI else "cu"
        ds.append(b)
    return ds, lech


def gia_tri_ghi(ds: list[dict], hang_dang_ky: str | None, ngay_sinh: str | None) -> dict[str, str | None]:
    """Danh sách bằng → giá trị 6 cột, cùng quy tắc nạp mới (NAP-07). Sai → ValueError. Rỗng → NULL."""
    kq = dung_chuoi_gplx_da_co(ds, hang_dang_ky, ngay_sinh)
    return {c: kq[ts] for (c, _), (ts, _) in zip(GPLX_COT, _GPLX_THAM_SO)}


def doc_dong(cur, ma_dk: str) -> dict | None:
    cur.execute(_SQL_DOC, (ma_dk,))
    return cur.fetchone()


def ket_qua_doc(ma_dk: str, row: dict, chan: str | None) -> dict:
    """Dữ liệu mở khối GPLX. `chan` là lý do không được lưu; None = lưu được."""
    ds, lech = tach_chuoi_gplx(row)
    return {
        "ma_dk": ma_dk,
        "ho_ten": row.get("HoVaTen"),
        "ma_kh": row.get("MaKhoaHoc"),
        "hang_khoa": (row.get("HangGPLX") or "").strip(),
        "chan": chan,
        "gplx": ds,
        "lech": lech,
        "tho": tho_tu_dong(row),
    }


def ghi(cur, ma_dk: str, row: dict, ds: list[dict], tho: dict[str, str]) -> bool:
    """UPDATE đúng 6 cột nếu DB còn đúng chuỗi thô đã đọc lúc mở. Trả False khi dữ liệu đã đổi.
    Sai dữ liệu → ValueError. Không đổi TT_XuLy hay cột nào khác."""
    moi = gia_tri_ghi(ds, row.get("HangGPLX"), row.get("NgaySinh"))
    cur.execute(_SQL_GHI, (*[moi[c] for c in TEN_COT], ma_dk, *[tho[c] for c in TEN_COT]))
    return cur.rowcount > 0


# ---- Bản app web chờ duyệt (QLY-10, TDD §10.7) ------------------------------
_LO_DB = 500
_TRANG_VPS_TOI_DA = 50
_DDL_XU_LY = "CREATE TABLE IF NOT EXISTS gplx_da_xu_ly (uuid TEXT PRIMARY KEY, dau_van TEXT NOT NULL, luc TEXT NOT NULL)"


def dau_van(uuid: str, ds: list[dict]) -> str:
    """Nhận diện đúng một bản app web đã xử lý. Chỉ để so khớp, không coi là che giấu dữ liệu."""
    return hashlib.sha256(f"{uuid}{json.dumps(ds, ensure_ascii=False, sort_keys=True)}".encode()).hexdigest()


def _chuan_db(row: dict) -> tuple[str, ...]:
    return tuple("|".join(p.strip() for p in (row.get(c) or "").split("|")) for c in TEN_COT)


def _chuan_web(ds: list[dict]) -> tuple[str, ...]:
    return tuple("|".join(str(b.get(f) or "").strip() for b in ds) for _, f in GPLX_COT)


def _hang(ds: list[dict]) -> list[dict]:
    return [{"hang": b.get("hang") or "", "nhom": b.get("nhom") or "cu"} for b in ds]


def _conn_xu_ly() -> sqlite3.Connection:
    conn = nap._keo_conn()
    conn.execute(_DDL_XU_LY)
    conn.execute("DELETE FROM gplx_da_xu_ly WHERE luc < datetime('now', '-30 day')")  # cùng nhóm dữ liệu máy tool, 30 ngày
    return conn


def da_xu_ly() -> dict[str, str]:
    """Sổ dấu vân lỗi → coi như rỗng: tệ nhất cảnh báo hiện lại, không mất cả danh sách."""
    try:
        conn = _conn_xu_ly()
        try:
            conn.commit()
            return dict(conn.execute("SELECT uuid, dau_van FROM gplx_da_xu_ly").fetchall())
        finally:
            conn.close()
    except sqlite3.Error:
        logger.warning("Không đọc được dấu vân GPLX ở máy tool.")
        return {}


def danh_dau_xu_ly(uuid: str, dv: str) -> None:
    conn = _conn_xu_ly()
    try:
        conn.execute("INSERT OR REPLACE INTO gplx_da_xu_ly (uuid, dau_van, luc) VALUES (?, ?, datetime('now'))", (uuid, dv))
        conn.commit()
    finally:
        conn.close()


def danh_dau_sau_luu(uuid: str, dv: str) -> None:
    """DB đã ghi xong: lỗi ở đây chỉ làm cảnh báo hiện lại, không sai dữ liệu nên không báo lỗi lưu."""
    try:
        danh_dau_xu_ly(uuid, dv)
    except sqlite3.Error:
        logger.warning("Không ghi được dấu vân GPLX ở máy tool.")


def lay_ban_web(vps_token: str | None) -> list[dict]:
    """Toàn bộ bản bổ sung từ VPS. Hai uuid cùng ma_dk → giữ bản updated_at mới nhất. Lỗi → VpsLoi."""
    moi_nhat: dict[str, dict] = {}
    cursor = None
    for _ in range(_TRANG_VPS_TOI_DA):
        trang = vps.gplx_bo_sung(vps_token, cursor)
        for x in trang.get("items", []):
            ma = (x.get("ma_dk") or "").strip()
            if ma and (ma not in moi_nhat or str(x.get("updated_at")) > str(moi_nhat[ma].get("updated_at"))):
                moi_nhat[ma] = {**x, "ma_dk": ma}
        if not trang.get("co_tiep"):
            break
        cursor = trang.get("cursor")
    return list(moi_nhat.values())


_SQL_LO = (
    "SELECT hs.MaDK, hs.MaKhoaHoc, nl.HoVaTen, kh.TenKH, " + ", ".join(f"hs.{c}" for c in TEN_COT)
    + " FROM dbo.NguoiLX_HoSo hs JOIN dbo.NguoiLX nl ON nl.MaDK = hs.MaDK"
    " LEFT JOIN dbo.KhoaHoc kh ON kh.MaKH = hs.MaKhoaHoc WHERE hs.MaDK IN ({})"
)


def doc_lo_db(cur, ma_dks: list[str]) -> dict[str, dict]:
    """Đọc DB theo lô tối đa 500 MaDK (SQL Server giới hạn 2.100 tham số mỗi câu lệnh)."""
    kq: dict[str, dict] = {}
    for i in range(0, len(ma_dks), _LO_DB):
        lo = ma_dks[i:i + _LO_DB]
        cur.execute(_SQL_LO.format(", ".join(["%s"] * len(lo))), tuple(lo))
        for r in cur.fetchall():
            kq[r["MaDK"]] = r
    return kq


def loc_canh_bao(ban_web: list[dict], dong_db: dict[str, dict], xu_ly: dict[str, str]) -> list[dict]:
    """Hồ sơ cần cảnh báo: chưa xử lý đúng bản này và khác DB. Danh sách không trả số GPLX, chỉ hạng."""
    kq = []
    for x in ban_web:
        ds = x.get("gplx_da_co") or []
        uuid, ma_dk = str(x.get("uuid")), x.get("ma_dk")
        dv = dau_van(uuid, ds)
        if xu_ly.get(uuid) == dv:
            continue
        row = dong_db.get(ma_dk)
        if row and _chuan_db(row) == _chuan_web(ds):
            continue
        hang_db = _hang(tach_chuoi_gplx(row)[0]) if row else []
        kq.append({
            "uuid": uuid, "ma_dk": ma_dk, "dau_van": dv, "nguoi_gui": x.get("nguoi_gui"), "updated_at": x.get("updated_at"),
            "ho_ten": row.get("HoVaTen") if row else None, "ma_kh": row.get("MaKhoaHoc") if row else None,
            "ten_kh": row.get("TenKH") if row else None, "hang_db": hang_db, "hang_web": _hang(ds), "khong_thay": not row,
        })
    kq.sort(key=lambda d: str(d["updated_at"]), reverse=True)
    return kq
