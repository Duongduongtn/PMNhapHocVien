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
