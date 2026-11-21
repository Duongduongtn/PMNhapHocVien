"""In Báo cáo 2 — kho SQLite phía tool (TNB-08, task 165). TDD §11F.9.

Lưu lựa chọn phần thi theo BC2, sổ phần thi đã đạt cộng dồn theo học viên, lần in và tóm tắt cho cột "Bản in".
**Không ghi DB Nạp.** Không lưu họ tên / số CMT — chỉ `ma_dk`, phần thi, mã kết quả, điểm, tên đăng nhập.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator

from app import paths

DB_PATH = paths.DATA_DIR / "db" / "data" / "tnbc2_ban_in.sqlite"

NGUON_SO = "so"      # cộng từ kết quả Sở trả về (đọc DB Nạp)
NGUON_SUA = "sua"    # user bấm ô phần thi
NGUON_IN = "in"      # chụp phần thi của BC2 lúc In / Lưu PDF (kể cả dòng giữ mặc định)
NGUON_CHON = (NGUON_SUA, NGUON_IN)

_DDL = (
    "CREATE TABLE IF NOT EXISTS noi_dung_thi ("
    "ma_bc2 TEXT NOT NULL, ma_dk TEXT NOT NULL, ma_nd INTEGER, phai_thi TEXT NOT NULL, da_thi INTEGER NOT NULL, "
    "nguoi TEXT, luc TEXT NOT NULL, PRIMARY KEY (ma_bc2, ma_dk))",
    "CREATE TABLE IF NOT EXISTS so_phan_thi ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, ma_dk TEXT NOT NULL, ma_bc2 TEXT, phan_thi TEXT, ket_qua_sh TEXT, "
    "diem_lt INTEGER, diem_h INTEGER, diem_d INTEGER, ma_ky_sh TEXT, da_dat TEXT NOT NULL, da_thi INTEGER NOT NULL, "
    "nguon TEXT NOT NULL CHECK (nguon IN ('so','sua','in')), nguoi TEXT, luc TEXT NOT NULL)",
    "CREATE INDEX IF NOT EXISTS ix_so_phan_thi_dk ON so_phan_thi (ma_dk, id)",
    "CREATE TABLE IF NOT EXISTS lan_in ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, ma_bc2 TEXT NOT NULL, luc TEXT NOT NULL, nguoi TEXT, so_hv INTEGER, "
    "so_chon_lai INTEGER)",
    "CREATE TABLE IF NOT EXISTS bc2_tom_tat ("
    "ma_bc2 TEXT PRIMARY KEY, so_chon_lai INTEGER, so_can_chon INTEGER, luc TEXT NOT NULL)",
)


def _bay_gio() -> str:
    return datetime.now().isoformat(timespec="seconds")


@contextmanager
def _ket_noi(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Kết nối SQLite: commit khi xong, rollback khi lỗi, luôn đóng."""
    p = Path(db_path) if db_path else DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    try:
        conn.row_factory = sqlite3.Row
        for ddl in _DDL:
            conn.execute(ddl)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ds(v: str | None) -> list[str]:
    return json.loads(v) if v else []


def doc_lua_chon(ma_bc2: str, db_path: Path | None = None) -> dict[str, dict]:
    """Lựa chọn đã lưu của một BC2: {ma_dk: {phai_thi, da_thi, ma_nd, nguoi, luc}}."""
    with _ket_noi(db_path) as conn:
        rows = conn.execute("SELECT * FROM noi_dung_thi WHERE ma_bc2 = ?", (ma_bc2,)).fetchall()
    return {r["ma_dk"]: {"phai_thi": _ds(r["phai_thi"]), "da_thi": bool(r["da_thi"]), "ma_nd": r["ma_nd"],
                         "nguoi": r["nguoi"], "luc": r["luc"]} for r in rows}


def so_moi_nhat(ds_ma_dk: Iterable[str], tru_ma_bc2: str | None = None, db_path: Path | None = None) -> dict[str, dict]:
    """Dòng sổ mới nhất mỗi học viên: {ma_dk: {dat, da_thi, nguon, ma_bc2, phan_thi, ket_qua_sh, ma_ky_sh, luc}}.
    `tru_ma_bc2`: bỏ các dòng "Anh sửa" của chính BC2 đó (để tính mặc định khi đang sửa BC2 này)."""
    ds = list(dict.fromkeys(ds_ma_dk))
    out: dict[str, dict] = {}
    if not ds:
        return out
    with _ket_noi(db_path) as conn:
        for i in range(0, len(ds), 500):
            phan = ds[i:i + 500]
            dk = f"ma_dk IN ({','.join('?' * len(phan))})"
            ts = list(phan)
            if tru_ma_bc2:
                dk += " AND NOT (nguon IN ('sua','in') AND ma_bc2 = ?)"
                ts.append(tru_ma_bc2)
            q = ("SELECT s.* FROM so_phan_thi s JOIN (SELECT ma_dk, MAX(id) id FROM so_phan_thi "
                 f"WHERE {dk} GROUP BY ma_dk) m ON m.id = s.id")
            for r in conn.execute(q, ts).fetchall():
                out[r["ma_dk"]] = {"dat": _ds(r["da_dat"]), "da_thi": bool(r["da_thi"]), "nguon": r["nguon"],
                                   "ma_bc2": r["ma_bc2"], "phan_thi": _ds(r["phan_thi"]), "ket_qua_sh": r["ket_qua_sh"],
                                   "ma_ky_sh": r["ma_ky_sh"], "luc": r["luc"]}
    return out


def lich_su(ma_dk: str, db_path: Path | None = None) -> list[dict]:
    with _ket_noi(db_path) as conn:
        rows = conn.execute("SELECT * FROM so_phan_thi WHERE ma_dk = ? ORDER BY id", (ma_dk,)).fetchall()
    return [{"ma_bc2": r["ma_bc2"], "phan_thi": _ds(r["phan_thi"]), "ket_qua_sh": r["ket_qua_sh"],
             "diem": [r["diem_lt"], r["diem_h"], r["diem_d"]], "dat": _ds(r["da_dat"]), "nguon": r["nguon"],
             "luc": r["luc"]} for r in rows]


def luu_lua_chon(ma_bc2: str, ds: Iterable[dict], nguoi: str, db_path: Path | None = None) -> int:
    """Lưu lựa chọn của user cho BC2 (mỗi dòng {ma_dk, phai_thi|None, dat, da_thi, ma_nd, mac_dinh, ket_qua_sh,
    ma_ky_sh} — hai trường cuối = kết quả/kỳ ở DB Nạp lúc chọn, để nhận ra kết quả kỳ mới).
    `phai_thi` None hoặc `mac_dinh=True` = về mặc định: xóa lựa chọn của BC2 này VÀ các dòng sổ "Anh sửa" của
    học viên ở BC2 này (nếu không, BC2 kế tiếp vẫn điền theo lựa chọn đã bỏ); các dòng "đã in"/"kết quả Sở" giữ nguyên.
    Có lựa chọn → ghi `noi_dung_thi` và thêm dòng sổ nguồn `sua` (gốc cho lần sau)."""
    luc = _bay_gio()
    n = 0
    with _ket_noi(db_path) as conn:
        for d in ds:
            ma_dk = d["ma_dk"]
            if d.get("phai_thi") is None or d.get("mac_dinh"):
                conn.execute("DELETE FROM noi_dung_thi WHERE ma_bc2 = ? AND ma_dk = ?", (ma_bc2, ma_dk))
                conn.execute("DELETE FROM so_phan_thi WHERE ma_bc2 = ? AND ma_dk = ? AND nguon = ?", (ma_bc2, ma_dk, NGUON_SUA))
                n += 1
                continue
            conn.execute(
                "INSERT INTO noi_dung_thi (ma_bc2, ma_dk, ma_nd, phai_thi, da_thi, nguoi, luc) VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT(ma_bc2, ma_dk) DO UPDATE SET ma_nd=excluded.ma_nd, phai_thi=excluded.phai_thi, "
                "da_thi=excluded.da_thi, nguoi=excluded.nguoi, luc=excluded.luc",
                (ma_bc2, ma_dk, d.get("ma_nd"), json.dumps(list(d["phai_thi"]), ensure_ascii=False),
                 1 if d.get("da_thi") else 0, nguoi, luc))
            conn.execute(
                "INSERT INTO so_phan_thi (ma_dk, ma_bc2, phan_thi, ket_qua_sh, ma_ky_sh, da_dat, da_thi, nguon, nguoi, luc) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (ma_dk, ma_bc2, json.dumps(list(d["phai_thi"]), ensure_ascii=False), d.get("ket_qua_sh"),
                 d.get("ma_ky_sh"), json.dumps(list(d.get("dat") or []), ensure_ascii=False),
                 1 if d.get("da_thi") else 0, NGUON_SUA, nguoi, luc))
            n += 1
    return n


def ghi_ket_qua(ds: Iterable[dict], db_path: Path | None = None) -> int:
    """Cộng kết quả Sở trả về vào sổ (mỗi dòng {ma_dk, ma_bc2, phan_thi, ket_qua_sh, diem:[lt,h,d], ma_ky_sh,
    dat, da_thi}). Bên gọi đã tính `dat` = đạt cũ ∪ phần vừa đạt; ở đây chỉ ghi, nguồn `so`."""
    luc = _bay_gio()
    n = 0
    with _ket_noi(db_path) as conn:
        for d in ds:
            diem = list(d.get("diem") or [None, None, None]) + [None, None, None]
            conn.execute(
                "INSERT INTO so_phan_thi (ma_dk, ma_bc2, phan_thi, ket_qua_sh, diem_lt, diem_h, diem_d, ma_ky_sh, "
                "da_dat, da_thi, nguon, nguoi, luc) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (d["ma_dk"], d.get("ma_bc2"), json.dumps(list(d.get("phan_thi") or []), ensure_ascii=False),
                 d.get("ket_qua_sh"), diem[0], diem[1], diem[2], d.get("ma_ky_sh"),
                 json.dumps(list(d.get("dat") or []), ensure_ascii=False), 1, NGUON_SO, "", luc))
            n += 1
    return n


def chup_phan_thi(ma_bc2: str, ds: Iterable[dict], nguoi: str, db_path: Path | None = None) -> int:
    """Lúc In / Lưu PDF: ghi phần thi của từng HV trong BC2 (nguồn `in`) để kỳ sau biết đã thi phần nào.
    Mỗi dòng {ma_dk, phai_thi, dat, da_thi, ket_qua_sh, ma_ky_sh}. Bỏ dòng trùng y hệt lần ghi trước."""
    luc = _bay_gio()
    n = 0
    with _ket_noi(db_path) as conn:
        for d in ds:
            phai = json.dumps(list(d["phai_thi"]), ensure_ascii=False)
            cu = conn.execute("SELECT phan_thi, nguon, ma_bc2 FROM so_phan_thi WHERE ma_dk = ? ORDER BY id DESC LIMIT 1",
                              (d["ma_dk"],)).fetchone()
            if cu and cu["ma_bc2"] == ma_bc2 and cu["nguon"] == NGUON_IN and cu["phan_thi"] == phai:   # chỉ bỏ trùng lần In liền trước
                continue
            conn.execute(
                "INSERT INTO so_phan_thi (ma_dk, ma_bc2, phan_thi, ket_qua_sh, ma_ky_sh, da_dat, da_thi, nguon, nguoi, luc) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (d["ma_dk"], ma_bc2, phai, d.get("ket_qua_sh"), d.get("ma_ky_sh"),
                 json.dumps(list(d.get("dat") or []), ensure_ascii=False), 1 if d.get("da_thi") else 0,
                 NGUON_IN, nguoi, luc))
            n += 1
    return n


def ghi_tom_tat(ma_bc2: str, so_chon_lai: int, so_can_chon: int, db_path: Path | None = None) -> None:
    with _ket_noi(db_path) as conn:
        conn.execute(
            "INSERT INTO bc2_tom_tat (ma_bc2, so_chon_lai, so_can_chon, luc) VALUES (?,?,?,?) "
            "ON CONFLICT(ma_bc2) DO UPDATE SET so_chon_lai=excluded.so_chon_lai, so_can_chon=excluded.so_can_chon, "
            "luc=excluded.luc", (ma_bc2, so_chon_lai, so_can_chon, _bay_gio()))


def ghi_lan_in(ma_bc2: str, nguoi: str, so_hv: int, so_chon_lai: int, db_path: Path | None = None) -> None:
    with _ket_noi(db_path) as conn:
        conn.execute("INSERT INTO lan_in (ma_bc2, luc, nguoi, so_hv, so_chon_lai) VALUES (?,?,?,?,?)",
                     (ma_bc2, _bay_gio(), nguoi, so_hv, so_chon_lai))


def ban_in_cho_ds(ds_ma_bc2: Iterable[str], db_path: Path | None = None) -> dict[str, dict]:
    """Cột "Bản in" ở Danh sách BC2: {ma_bc2: {da_in_luc, so_chon_lai, so_can_chon, dang_chon}} — chỉ đọc SQLite."""
    ds = list(dict.fromkeys(ds_ma_bc2))
    out: dict[str, dict] = {}
    if not ds:
        return out
    with _ket_noi(db_path) as conn:
        for i in range(0, len(ds), 500):
            phan = ds[i:i + 500]
            ph = ",".join("?" * len(phan))
            for r in conn.execute(f"SELECT * FROM bc2_tom_tat WHERE ma_bc2 IN ({ph})", phan).fetchall():
                out[r["ma_bc2"]] = {"da_in_luc": None, "so_chon_lai": r["so_chon_lai"], "so_can_chon": r["so_can_chon"]}
            q = f"SELECT ma_bc2, MAX(luc) luc FROM lan_in WHERE ma_bc2 IN ({ph}) GROUP BY ma_bc2"
            for r in conn.execute(q, phan).fetchall():
                out.setdefault(r["ma_bc2"], {"da_in_luc": None, "so_chon_lai": 0, "so_can_chon": 0})["da_in_luc"] = r["luc"]
    return out
