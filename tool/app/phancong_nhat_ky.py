"""Phân công GV – xe (PCG, task 87) — nhật ký thao tác ghi vào CDB (SQLite phía tool).

CDB hiện để `NguoiTao` trống 100% nên không truy được ai phân công; nhật ký này ghi: ai ·
lúc nào · khóa · thay đổi gì · kết quả từng dòng. Ghi TRƯỚC khi ghi CDB (trạng thái `bat_dau`),
cập nhật sau khi xong/lỗi. File riêng, không dùng chung staging.sqlite của Nạp.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app import paths

DB_PATH = paths.DATA_DIR / "db" / "data" / "phancong_nhat_ky.sqlite"

_DDL = (
    "CREATE TABLE IF NOT EXISTS phancong_nhat_ky ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, luc TEXT NOT NULL, nguoi TEXT, ma_kh TEXT NOT NULL, "
    "tom_tat TEXT, thay_doi_json TEXT, ket_qua_json TEXT, trang_thai TEXT NOT NULL DEFAULT 'bat_dau')"
)


def _ket_noi(db_path: Path | None = None) -> sqlite3.Connection:
    p = Path(db_path) if db_path else DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    conn.execute(_DDL)
    return conn


def bat_dau(nguoi: str, ma_kh: str, tom_tat: str, thay_doi: dict, db_path: Path | None = None) -> int:
    conn = _ket_noi(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO phancong_nhat_ky (luc, nguoi, ma_kh, tom_tat, thay_doi_json, trang_thai) VALUES (?,?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), nguoi, ma_kh, tom_tat,
             json.dumps(thay_doi, ensure_ascii=False), "bat_dau"),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def ket_thuc(id_: int, trang_thai: str, ket_qua: dict, db_path: Path | None = None) -> None:
    """trang_thai: 'xong' | 'loi_giua_chung' | 'that_bai'."""
    conn = _ket_noi(db_path)
    try:
        conn.execute("UPDATE phancong_nhat_ky SET trang_thai=?, ket_qua_json=? WHERE id=?",
                     (trang_thai, json.dumps(ket_qua, ensure_ascii=False), id_))
        conn.commit()
    finally:
        conn.close()


def gan_day(ma_kh: str | None = None, gioi_han: int = 50, db_path: Path | None = None) -> list[dict]:
    conn = _ket_noi(db_path)
    try:
        if ma_kh:
            rows = conn.execute("SELECT * FROM phancong_nhat_ky WHERE ma_kh=? ORDER BY id DESC LIMIT ?",
                                (ma_kh, gioi_han)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM phancong_nhat_ky ORDER BY id DESC LIMIT ?", (gioi_han,)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["thay_doi"] = json.loads(d.pop("thay_doi_json") or "{}")
            d["ket_qua"] = json.loads(d.pop("ket_qua_json") or "{}")
            out.append(d)
        return out
    finally:
        conn.close()
