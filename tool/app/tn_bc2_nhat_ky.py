"""Tốt nghiệp & Báo cáo 2 (TNB, task 98) — nhật ký thao tác ghi DB Nạp (SQLite phía tool).

Mẫu `phancong_nhat_ky.py`. Ghi TRƯỚC khi ghi DB (`bat_dau`), cập nhật sau khi xong/lỗi
(`ket_thuc`) — đứt giữa chừng vẫn biết đã làm tới đâu. **Không lưu họ tên / số CMT**: chỉ `ma_dk`,
số lượng, loại thao tác, kết quả, tên đăng nhập (TDD §11F.0). File riêng, không dùng chung
staging.sqlite của Nạp.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from app import paths

DB_PATH = paths.DATA_DIR / "db" / "data" / "tnbc2_nhat_ky.sqlite"

# Loại thao tác
TAO_BC2 = "tao_bc2"
THEM_HV = "them_hv"
GO_HV = "go_hv"
XOA_BC2 = "xoa_bc2"
TOT_NGHIEP = "tot_nghiep"
HUY_TOT_NGHIEP = "huy_tot_nghiep"
CUU = "cuu_trang_thai"

_CAM = {"ten", "ho_ten", "ho_va_ten", "cmt", "so_cmt", "so_cmnd", "ngay_sinh", "hoten"}

_DDL = (
    "CREATE TABLE IF NOT EXISTS tnbc2_nhat_ky ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, luc TEXT NOT NULL, nguoi TEXT, loai TEXT NOT NULL, "
    "ma_kh TEXT, ma_bc2 TEXT, lo_id TEXT, so_hv INTEGER, tom_tat TEXT, chi_tiet_json TEXT, "
    "ket_qua_json TEXT, trang_thai TEXT NOT NULL DEFAULT 'bat_dau')"
)


_DDL_LO = (
    "CREATE TABLE IF NOT EXISTS tnbc2_lo ("
    "lo_id TEXT PRIMARY KEY, luc TEXT NOT NULL, nguoi TEXT, loai TEXT NOT NULL, ma_kh TEXT, ma_bc2 TEXT, "
    "lo_goc TEXT, tong INTEGER, trang_thai TEXT NOT NULL DEFAULT 'dang_chay', hoan_tac_boi TEXT, "
    "ket_qua_json TEXT, luc_xong TEXT)"
)
_DDL_LO_HV = (
    "CREATE TABLE IF NOT EXISTS tnbc2_lo_hv ("
    "lo_id TEXT NOT NULL, ma_dk TEXT NOT NULL, ket_qua TEXT NOT NULL, ma_ly_do TEXT, luc TEXT, "
    "PRIMARY KEY (lo_id, ma_dk))"
)

LO_LAP = "lap"
LO_HOAN_TAC = "hoan_tac"
LO_TOT_NGHIEP = "tot_nghiep"  # ghi tốt nghiệp ô tô (không có BC2)
LO_HUY_TOT_NGHIEP = "huy_tot_nghiep"
LO_CUU = "cuu"                      # cứu trạng thái một HV (kết quả giữ tt_cu/tt_moi để hoàn tác)
LO_CUU_HOAN_TAC = "cuu_hoan_tac"
LO_GO = "go"                  # gỡ HV thủ công (khác hoàn tác lô; không phải "lần thêm" nên không che lô thêm)


def _loc_pii(v: Any) -> Any:
    """Bỏ mọi khóa mang họ tên / CMT / ngày sinh (đệ quy) — nhật ký chỉ cần `ma_dk` và số lượng."""
    if isinstance(v, dict):
        return {k: _loc_pii(x) for k, x in v.items() if str(k).lower() not in _CAM}
    if isinstance(v, (list, tuple)):
        return [_loc_pii(x) for x in v]
    return v


def _ket_noi(db_path: Path | None = None) -> sqlite3.Connection:
    p = Path(db_path) if db_path else DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    conn.execute(_DDL)
    conn.execute(_DDL_LO)
    conn.execute(_DDL_LO_HV)
    return conn


def bat_dau(nguoi: str, loai: str, ma_kh: str = "", ma_bc2: str = "", so_hv: int = 0, tom_tat: str = "",
            chi_tiet: dict | None = None, lo_id: str = "", db_path: Path | None = None) -> int:
    conn = _ket_noi(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO tnbc2_nhat_ky (luc, nguoi, loai, ma_kh, ma_bc2, lo_id, so_hv, tom_tat, chi_tiet_json, trang_thai) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), nguoi, loai, ma_kh, ma_bc2, lo_id, so_hv, tom_tat,
             json.dumps(_loc_pii(chi_tiet or {}), ensure_ascii=False), "bat_dau"))
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def ket_thuc(id_: int, trang_thai: str, ket_qua: dict | None = None, db_path: Path | None = None) -> None:
    """trang_thai: 'xong' | 'loi_giua_chung' | 'that_bai' | 'da_ton_tai'."""
    conn = _ket_noi(db_path)
    try:
        conn.execute("UPDATE tnbc2_nhat_ky SET trang_thai=?, ket_qua_json=? WHERE id=?",
                     (trang_thai, json.dumps(_loc_pii(ket_qua or {}), ensure_ascii=False), id_))
        conn.commit()
    finally:
        conn.close()


def gan_day(loai: str | None = None, ma_bc2: str | None = None, gioi_han: int = 50,
            db_path: Path | None = None) -> list[dict]:
    conn = _ket_noi(db_path)
    try:
        sql, args = "SELECT * FROM tnbc2_nhat_ky", []
        dk = []
        if loai:
            dk.append("loai = ?")
            args.append(loai)
        if ma_bc2:
            dk.append("ma_bc2 = ?")
            args.append(ma_bc2)
        if dk:
            sql += " WHERE " + " AND ".join(dk)
        sql += " ORDER BY id DESC LIMIT ?"
        args.append(int(gioi_han))
        out = []
        for r in conn.execute(sql, args).fetchall():
            d = dict(r)
            d["chi_tiet"] = json.loads(d.pop("chi_tiet_json") or "{}")
            d["ket_qua"] = json.loads(d.pop("ket_qua_json") or "{}")
            out.append(d)
        return out
    finally:
        conn.close()


# ── Lô thao tác (thêm HV / hoàn tác): nguồn của "Làm tiếp", tiến độ sau khi tool khởi động lại và Hoàn tác ──
def lo_bat_dau(lo_id: str, nguoi: str, loai: str, ma_kh: str = "", ma_bc2: str = "", tong: int = 0,
               lo_goc: str = "", db_path: Path | None = None) -> bool:
    """Tạo lô nếu chưa có (idempotent theo `lo_id`). True = tạo mới; False = đã có từ trước."""
    conn = _ket_noi(db_path)
    try:
        cur = conn.execute(
            "INSERT OR IGNORE INTO tnbc2_lo (lo_id, luc, nguoi, loai, ma_kh, ma_bc2, lo_goc, tong, trang_thai) "
            "VALUES (?,?,?,?,?,?,?,?, 'dang_chay')",
            (lo_id, datetime.now().isoformat(timespec="seconds"), nguoi, loai, ma_kh, ma_bc2, lo_goc, tong))
        conn.commit()
        return cur.rowcount == 1
    finally:
        conn.close()


def lo_cap_nhat(lo_id: str, db_path: Path | None = None, **truong: Any) -> None:
    """Cập nhật các cột của lô: ma_bc2, tong, trang_thai, hoan_tac_boi, ket_qua (dict), luc_xong."""
    cot = {"ma_bc2", "tong", "trang_thai", "hoan_tac_boi", "luc_xong"}
    sets, args = [], []
    for k, v in truong.items():
        if k == "ket_qua":
            sets.append("ket_qua_json = ?")
            args.append(json.dumps(_loc_pii(v or {}), ensure_ascii=False))
        elif k in cot:
            sets.append(f"{k} = ?")
            args.append(v)
        else:
            raise KeyError(k)
    if not sets:
        return
    conn = _ket_noi(db_path)
    try:
        conn.execute(f"UPDATE tnbc2_lo SET {', '.join(sets)} WHERE lo_id = ?", (*args, lo_id))
        conn.commit()
    finally:
        conn.close()


def lo_ghi_hv(lo_id: str, ma_dk: str, ket_qua: str, ma_ly_do: str = "", db_path: Path | None = None) -> None:
    """Ghi NGAY một học viên của lô (`da_them` / `da_co_tu_truoc` / `bo_qua` / `loi` / `da_go`)."""
    conn = _ket_noi(db_path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO tnbc2_lo_hv (lo_id, ma_dk, ket_qua, ma_ly_do, luc) VALUES (?,?,?,?,?)",
            (lo_id, ma_dk, ket_qua, ma_ly_do, datetime.now().isoformat(timespec="seconds")))
        conn.commit()
    finally:
        conn.close()


def lo_lay(lo_id: str, db_path: Path | None = None) -> dict | None:
    conn = _ket_noi(db_path)
    try:
        r = conn.execute("SELECT * FROM tnbc2_lo WHERE lo_id = ?", (lo_id,)).fetchone()
        if r is None:
            return None
        d = dict(r)
        d["ket_qua"] = json.loads(d.pop("ket_qua_json") or "{}")
        return d
    finally:
        conn.close()


def lo_hv(lo_id: str, db_path: Path | None = None) -> list[dict]:
    conn = _ket_noi(db_path)
    try:
        return [dict(r) for r in conn.execute(
            "SELECT ma_dk, ket_qua, ma_ly_do, luc FROM tnbc2_lo_hv WHERE lo_id = ? ORDER BY rowid", (lo_id,))]
    finally:
        conn.close()


def lo_lap_gan_nhat_cua_bc2(ma_bc2: str, db_path: Path | None = None) -> dict | None:
    """Lô THÊM HV gần nhất của một BC2 mà ĐÃ THÊM ít nhất một HV (nguồn của "Hoàn tác lần vừa rồi";
    lô không thêm được ai không phải "lần thêm" nên không che mất lô thật trước đó)."""
    conn = _ket_noi(db_path)
    try:
        r = conn.execute(
            "SELECT lo_id FROM tnbc2_lo WHERE ma_bc2 = ? AND loai = ? AND EXISTS "
            "(SELECT 1 FROM tnbc2_lo_hv h WHERE h.lo_id = tnbc2_lo.lo_id AND h.ket_qua = 'da_them') "
            "ORDER BY luc DESC, rowid DESC LIMIT 1", (ma_bc2, LO_LAP)).fetchone()
    finally:
        conn.close()
    return lo_lay(r["lo_id"], db_path) if r else None
