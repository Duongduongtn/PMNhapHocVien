"""
build_dvhc_map.py — Dựng bảng tra cứu ánh xạ DVHC cũ -> xã mới 2025 vào SQLite CỤC BỘ của tool.

KHÔNG ghi gì vào GPLX_CSDT (production chỉ bị ĐỌC). Dùng cho thao tác "Đồng bộ danh mục":
  1. Đọc dataset vietnamadminunits (convert_legacy_2025_simple.csv) đóng kèm tool (tự tải nếu thiếu).
  2. Nối SQL Server, ĐỌC DM_DVHC (TrangThai=1) của CHÍNH máy đích — 3321 xã mới / 34 tỉnh.
  3. Đối soát: nối theo TÊN (tỉnh mới + xã mới ngắn) đã chuẩn hóa -> lấy đúng (MaDvhc, MaDVQL)
     của máy đích. (KHÔNG dùng mã GSO của dataset — mã DB khác.)
  4. Dựng lại bảng `dm_dvhc_map` trong SQLite (DROP + tạo + nạp, tham số hóa).
  5. In báo cáo độ phủ (phải đạt 3321/3321 xã DB).

Vì nối theo tên với DM_DVHC của máy đích nên mang tool sang máy/cơ sở khác vẫn ra đúng mã máy đó.
Kết nối lấy từ DBcu/env.txt (gitignore) hoặc biến môi trường SQLSERVER_HOST/DATABASE/USER/PASSWORD.

Chạy:  tool\.venv\Scripts\python.exe tool\db\build_dvhc_map.py [--db <đường_dẫn_sqlite>]
"""
from __future__ import annotations
import os
import re
import sys
import csv
import sqlite3
import argparse
import unicodedata
import urllib.request
from pathlib import Path

# Dùng CHUNG hàm chuẩn hóa với runtime (app.dvhc) — key builder & key tra cứu phải khớp y hệt.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.dvhc import norm_prov, norm_dist, norm_ward  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
CSV_PATH = DATA_DIR / "convert_legacy_2025_simple.csv"
CSV_URL = ("https://raw.githubusercontent.com/tranngocminhhieu/vietnamadminunits/"
           "main/data/interim/convert_legacy_2025_simple.csv")
DEFAULT_SQLITE = DATA_DIR / "dvhc_map.sqlite"   # standalone/verify; app truyền staging.sqlite
EXPECTED_WARDS = 3321                           # số xã mới của DB (TrangThai=1) — mốc đối soát

DDL = """
CREATE TABLE dm_dvhc_map (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  ten_tinh_cu       TEXT NOT NULL,   -- chuẩn hóa: lower, bỏ tiền tố
  ten_huyen_cu      TEXT NOT NULL,
  ten_xa_cu         TEXT NOT NULL,
  ma_dvhc_moi       TEXT NOT NULL,   -- = DM_DVHC.MaDvhc (TrangThai=1) của máy đích
  ma_dvql_moi       TEXT NOT NULL,   -- = DM_DVHC.MaDVQL
  ten_xa_moi        TEXT NOT NULL,   -- tên hiển thị (theo DB)
  ten_tinh_moi      TEXT NOT NULL,
  ten_xa_moi_norm   TEXT NOT NULL,   -- chuẩn hóa tên mới → khớp khi nhập địa chỉ ĐÃ MỚI
  ten_tinh_moi_norm TEXT NOT NULL,
  is_divided        INTEGER NOT NULL DEFAULT 0
)
"""
INDEX_CU = "CREATE INDEX ix_dvhcmap_cu ON dm_dvhc_map(ten_tinh_cu, ten_huyen_cu, ten_xa_cu)"
INDEX_MOI = "CREATE INDEX ix_dvhcmap_moi ON dm_dvhc_map(ten_tinh_moi_norm, ten_xa_moi_norm)"

# Hàm chuẩn hóa (norm_prov/dist/ward) import từ app.dvhc — nguồn duy nhất.

# ---- Kết nối SQL Server (CHỈ ĐỌC) -------------------------------------------
def read_conn_params() -> dict:
    host = os.environ.get("SQLSERVER_HOST")
    db = os.environ.get("SQLSERVER_DATABASE")
    user = os.environ.get("SQLSERVER_USER")
    pwd = os.environ.get("SQLSERVER_PASSWORD")
    env_file = HERE.parent.parent / "DBcu" / "env.txt"
    if (not all([host, db, user, pwd])) and env_file.exists():
        m = {}
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                m[k.strip().lower()] = v.strip()
        host = host or m.get("server name")
        db = db or m.get("database name")
        user = user or m.get("username")
        pwd = pwd or m.get("password")
    if not all([host, db, user, pwd]):
        sys.exit("Thiếu thông số kết nối (đặt biến môi trường SQLSERVER_* hoặc DBcu/env.txt).")
    return {"server": host, "database": db, "user": user, "password": pwd}


def load_db_wards(params: dict):
    """Đọc DM_DVHC (TrangThai=1). Trả lookup key->(MaDvhc, MaDVQL, ten_xa_DB, ten_tinh_DB).

    ten_xa_DB = TenNganGon, ten_tinh_DB = phần tỉnh tách từ TenDayDu — để hiển thị THEO DB (PRD NAP-03).
    """
    import pymssql  # lazy import
    conn = pymssql.connect(login_timeout=8, charset="UTF-8", **params)
    try:
        cur = conn.cursor()
        cur.execute("SELECT MaDvhc, MaDVQL, TenNganGon, TenDayDu FROM DM_DVHC WHERE TrangThai=1")
        rows = cur.fetchall()
    finally:
        conn.close()

    lookup: dict[tuple[str, str], tuple[str, str, str, str]] = {}
    collisions: list = []
    db_ward_keys: set[tuple[str, str]] = set()
    for ma_dvhc, ma_dvql, ten_ngan, ten_day in rows:
        ten_tinh_db = ten_day.rsplit(",", 1)[-1].strip() if ten_day and "," in ten_day else (ten_day or "")
        key = (norm_prov(ten_tinh_db), norm_ward(ten_ngan))
        db_ward_keys.add(key)
        val = (ma_dvhc, ma_dvql, ten_ngan, ten_tinh_db)
        if key in lookup and lookup[key][:2] != (ma_dvhc, ma_dvql):
            collisions.append((key, lookup[key][:2], (ma_dvhc, ma_dvql)))
        lookup[key] = val
    return lookup, db_ward_keys, collisions, len(rows)


# ---- Dataset ----------------------------------------------------------------
def ensure_csv():
    if CSV_PATH.exists():
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Tải dataset: {CSV_URL}")
    urllib.request.urlretrieve(CSV_URL, CSV_PATH)


def read_csv_rows():
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        yield from csv.DictReader(f)


# ---- Nạp SQLite (tham số hóa) -----------------------------------------------
def write_sqlite(sqlite_path: Path, rows: list[tuple]):
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(sqlite_path))
    try:
        conn.execute("DROP TABLE IF EXISTS dm_dvhc_map")  # dựng lại sạch mỗi lần đồng bộ
        conn.execute(DDL)
        conn.executemany(
            "INSERT INTO dm_dvhc_map "
            "(ten_tinh_cu, ten_huyen_cu, ten_xa_cu, ma_dvhc_moi, ma_dvql_moi, "
            " ten_xa_moi, ten_tinh_moi, ten_xa_moi_norm, ten_tinh_moi_norm, is_divided) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            rows,
        )
        conn.execute(INDEX_CU)
        conn.execute(INDEX_MOI)
        conn.commit()
    finally:
        conn.close()


# ---- Dựng bảng (hàm app gọi) ------------------------------------------------
def build(sqlite_path: Path, conn_params: dict) -> dict:
    """Đối soát + nạp SQLite. Trả báo cáo độ phủ. KHÔNG ghi gì vào SQL Server."""
    ensure_csv()
    lookup, db_ward_keys, collisions, n_db = load_db_wards(conn_params)

    rows: list[tuple] = []
    unmatched: list[tuple[str, str, str]] = []
    hit_db_keys: set[tuple[str, str]] = set()
    for row in read_csv_rows():
        key = (norm_prov(row["newProvince"]), norm_ward(row["newWardShort"]))
        hit = lookup.get(key)
        if hit is None:
            unmatched.append((row["newProvince"], row["newWardShort"], row["ward"]))
            continue
        hit_db_keys.add(key)
        ma_dvhc, ma_dvql, ten_xa_db, ten_tinh_db = hit
        rows.append((
            norm_prov(row["province"]),
            norm_dist(row["district"]),
            norm_ward(row["ward"]),
            ma_dvhc,
            ma_dvql,
            ten_xa_db,                 # tên hiển thị THEO DB (TenNganGon), không theo dataset
            ten_tinh_db,               # tên tỉnh THEO DB (tách từ TenDayDu)
            norm_ward(ten_xa_db),      # chuẩn hóa tên mới → khớp khi nhập địa chỉ ĐÃ MỚI
            norm_prov(ten_tinh_db),
            1 if str(row.get("isDividedWard", "")).strip().lower() in ("true", "1") else 0,
        ))

    write_sqlite(sqlite_path, rows)
    return {
        "n_db_wards": n_db,
        "n_rows": len(rows),
        "n_unmatched": len(unmatched),
        "covered": len(db_ward_keys & hit_db_keys),
        "missing": sorted(db_ward_keys - hit_db_keys),
        "collisions": collisions,
        "unmatched_sample": unmatched[:5],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_SQLITE), help="Đường dẫn file SQLite đích")
    args = ap.parse_args()

    params = read_conn_params()
    print(f"Nối SQL Server {params['server']} / {params['database']} (chỉ đọc DM_DVHC)…")
    rep = build(Path(args.db), params)

    print(f"DM_DVHC TrangThai=1: {rep['n_db_wards']} xã mới.")
    if rep["collisions"]:
        print(f"⚠️  {len(rep['collisions'])} khóa (tỉnh, xã) trùng trong DB — ví dụ: {rep['collisions'][:3]}")
    print("\n========== ĐỐI SOÁT ==========")
    print(f"Dòng ánh xạ nạp SQLite : {rep['n_rows']}")
    print(f"Dòng CSV không khớp     : {rep['n_unmatched']}")
    print(f"Độ phủ xã mới DB       : {rep['covered']}/{rep['n_db_wards']}")
    print(f"Đã ghi SQLite          : {args.db}")
    if rep["missing"]:
        print(f"⚠️  {len(rep['missing'])} xã DB chưa phủ — ví dụ: {rep['missing'][:5]}")
    if rep["unmatched_sample"]:
        print(f"ℹ️  Ví dụ CSV không khớp: {rep['unmatched_sample']}")

    ok = (rep["covered"] == rep["n_db_wards"] == EXPECTED_WARDS)
    print("KẾT QUẢ:", "✅ ĐỦ 3321/3321" if ok else "⚠️ CHƯA đủ phủ — xem cảnh báo trên")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
