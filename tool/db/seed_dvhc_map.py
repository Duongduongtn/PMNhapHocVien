"""
seed_dvhc_map.py — Sinh script nạp bảng phụ DM_DVHC_MAP (ánh xạ DVHC cũ -> xã mới 2025).

Luồng (CHỈ ĐỌC DB — không ghi production):
  1. Đọc dataset vietnamadminunits (convert_legacy_2025_simple.csv) ở data/ (tự tải nếu thiếu).
  2. Nối SQL Server, đọc DM_DVHC (TrangThai=1) — 3321 xã mới / 34 tỉnh.
  3. Đối soát: nối theo TÊN (tỉnh mới + xã mới ngắn) đã chuẩn hóa -> lấy đúng (MaDvhc, MaDVQL) của DB.
     (KHÔNG dùng mã GSO của dataset — mã DB khác.)
  4. In báo cáo độ phủ (phải đạt 3321/3321 xã DB).
  5. Ghi 02_seed_dm_dvhc_map.sql để chạy trên SSMS sau 01_create.

Kết nối lấy từ DBcu/env.txt (gitignore) hoặc biến môi trường SQLSERVER_HOST/DB/USER/PASSWORD.
Chạy:  tool\.venv\Scripts\python.exe tool\db\seed_dvhc_map.py
"""
from __future__ import annotations
import os
import re
import sys
import csv
import unicodedata
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
CSV_PATH = DATA_DIR / "convert_legacy_2025_simple.csv"
CSV_URL = ("https://raw.githubusercontent.com/tranngocminhhieu/vietnamadminunits/"
           "main/data/interim/convert_legacy_2025_simple.csv")
SEED_OUT = HERE / "02_seed_dm_dvhc_map.sql"
EXPECTED_WARDS = 3321          # số xã mới của DB (TrangThai=1) — mốc đối soát
ROWS_PER_INSERT = 1000         # SQL Server tối đa 1000 dòng / câu INSERT ... VALUES

# ---- Chuẩn hóa tên để nối khớp (theo đặc tả đã verify 30/09/2026) -----------
_PROV_PREFIX = re.compile(r"^(thành phố|tỉnh|tp\.?)\s+")
_DIST_PREFIX = re.compile(r"^(thành phố|quận|huyện|thị xã|tp\.?)\s+")
_WARD_PREFIX = re.compile(r"^(phường|xã|thị trấn|tt\.?)\s+")


def _base(s: str) -> str:
    """NFC + đổi dấu nháy cong -> thẳng + lower + gộp khoảng trắng."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFC", str(s))
    s = s.replace("’", "'").replace("‘", "'")
    s = s.strip().lower()
    return re.sub(r"\s+", " ", s).strip()


def norm_prov(s: str) -> str:
    return _PROV_PREFIX.sub("", _base(s)).strip()


def norm_dist(s: str) -> str:
    return _DIST_PREFIX.sub("", _base(s)).strip()


def norm_ward(s: str) -> str:
    return _WARD_PREFIX.sub("", _base(s)).strip()


# ---- Kết nối -----------------------------------------------------------------
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
    """Trả lookup (prov_norm, ward_norm) -> (MaDvhc, MaDVQL) và tập mã xã DB."""
    import pymssql  # lazy import
    conn = pymssql.connect(login_timeout=8, charset="UTF-8", **params)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT MaDvhc, MaDVQL, TenNganGon, TenDayDu "
            "FROM DM_DVHC WHERE TrangThai=1"
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    lookup: dict[tuple[str, str], tuple[str, str]] = {}
    collisions: list = []
    db_ward_keys: set[tuple[str, str]] = set()
    for ma_dvhc, ma_dvql, ten_ngan, ten_day in rows:
        # Tên tỉnh = phần sau dấu phẩy cuối của TenDayDu ("Phường X, Thành phố Y")
        prov_raw = ten_day.rsplit(",", 1)[-1] if ten_day and "," in ten_day else ten_day
        key = (norm_prov(prov_raw), norm_ward(ten_ngan))
        db_ward_keys.add(key)
        if key in lookup and lookup[key] != (ma_dvhc, ma_dvql):
            collisions.append((key, lookup[key], (ma_dvhc, ma_dvql)))
        lookup[key] = (ma_dvhc, ma_dvql)
    return lookup, db_ward_keys, collisions, len(rows)


# ---- Dataset -----------------------------------------------------------------
def ensure_csv():
    if CSV_PATH.exists():
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Tải dataset: {CSV_URL}")
    urllib.request.urlretrieve(CSV_URL, CSV_PATH)


def read_csv_rows():
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        yield from csv.DictReader(f)


# ---- Sinh SQL ----------------------------------------------------------------
def q(s: str) -> str:
    """Giá trị NVARCHAR an toàn: N'...' + nhân đôi dấu nháy đơn."""
    return "N'" + unicodedata.normalize("NFC", str(s)).replace("'", "''") + "'"


def qa(s: str) -> str:
    """Giá trị VARCHAR (mã, ASCII) an toàn: '...' + nhân đôi dấu nháy đơn (không N prefix)."""
    return "'" + str(s).replace("'", "''") + "'"


def write_seed(seed_rows: list[dict]):
    with SEED_OUT.open("w", encoding="utf-8") as f:
        f.write("-- 02_seed_dm_dvhc_map.sql — SINH TỰ ĐỘNG bởi seed_dvhc_map.py. KHÔNG sửa tay.\n")
        f.write("-- Chạy SAU 01_create_dm_dvhc_map.sql, trên SSMS.\n")
        f.write(f"-- Số dòng ánh xạ: {len(seed_rows)}\n\n")
        f.write("USE GPLX_CSDT;\nGO\nSET NOCOUNT ON;\nSET XACT_ABORT ON;\nBEGIN TRAN;\n")
        f.write("TRUNCATE TABLE dbo.DM_DVHC_MAP;\n\n")
        cols = ("TenTinhCu, TenHuyenCu, TenXaCu, MaDvhcMoi, MaDVQLMoi, "
                "TenXaMoi, TenTinhMoi, IsDividedWard")
        for i in range(0, len(seed_rows), ROWS_PER_INSERT):
            chunk = seed_rows[i:i + ROWS_PER_INSERT]
            f.write(f"INSERT INTO dbo.DM_DVHC_MAP ({cols}) VALUES\n")
            vals = []
            for r in chunk:
                vals.append(
                    f"({q(r['tinh_cu'])},{q(r['huyen_cu'])},{q(r['xa_cu'])},"
                    f"{qa(r['ma_dvhc'])},{qa(r['ma_dvql'])},"
                    f"{q(r['xa_moi'])},{q(r['tinh_moi'])},{1 if r['divided'] else 0})"
                )
            f.write(",\n".join(vals) + ";\n\n")
        f.write("COMMIT;\n")
        f.write("PRINT N'Nạp xong DM_DVHC_MAP. Số dòng thực tế xem ở kết quả SELECT bên dưới.';\n")
        f.write("SELECT COUNT(*) AS TongDong, COUNT(DISTINCT MaDvhcMoi+'-'+MaDVQLMoi) AS SoXaMoiPhu FROM dbo.DM_DVHC_MAP;\n")


# ---- Main --------------------------------------------------------------------
def main():
    ensure_csv()
    params = read_conn_params()
    print(f"Nối SQL Server {params['server']} / {params['database']} (chỉ đọc DM_DVHC)…")
    lookup, db_ward_keys, collisions, n_db = load_db_wards(params)
    print(f"DM_DVHC TrangThai=1: {n_db} xã mới.")
    if n_db != EXPECTED_WARDS:
        print(f"⚠️  Số xã mới DB = {n_db}, khác mốc {EXPECTED_WARDS}. Kiểm lại DB trước khi nạp.")
    if collisions:
        print(f"⚠️  {len(collisions)} khóa (tỉnh, xã) trùng trong DB — ví dụ: {collisions[:3]}")

    seed_rows: list[dict] = []
    unmatched: list[tuple[str, str, str]] = []  # dòng CSV không khớp xã DB
    hit_db_keys: set[tuple[str, str]] = set()

    for row in read_csv_rows():
        key = (norm_prov(row["newProvince"]), norm_ward(row["newWardShort"]))
        hit = lookup.get(key)
        if hit is None:
            unmatched.append((row["newProvince"], row["newWardShort"], row["ward"]))
            continue
        hit_db_keys.add(key)
        ma_dvhc, ma_dvql = hit
        seed_rows.append({
            "tinh_cu": norm_prov(row["province"]),
            "huyen_cu": norm_dist(row["district"]),
            "xa_cu": norm_ward(row["ward"]),
            "ma_dvhc": ma_dvhc,
            "ma_dvql": ma_dvql,
            "xa_moi": unicodedata.normalize("NFC", row["newWardShort"].strip()),
            "tinh_moi": unicodedata.normalize("NFC", row["newProvince"].strip()),
            "divided": str(row.get("isDividedWard", "")).strip().lower() in ("true", "1"),
        })

    covered = len(db_ward_keys & hit_db_keys)
    print("\n========== ĐỐI SOÁT ==========")
    print(f"Dòng ánh xạ cũ->mới dùng được : {len(seed_rows)}")
    print(f"Dòng CSV không khớp xã DB     : {len(unmatched)}")
    print(f"Độ phủ xã mới DB             : {covered}/{len(db_ward_keys)}")
    missing = db_ward_keys - hit_db_keys
    if missing:
        print(f"⚠️  {len(missing)} xã DB KHÔNG được dataset phủ — ví dụ: {sorted(missing)[:5]}")
    if unmatched:
        print(f"ℹ️  Ví dụ dòng CSV không khớp: {unmatched[:5]}")

    write_seed(seed_rows)
    ok = (covered == len(db_ward_keys) == EXPECTED_WARDS)
    print(f"\nĐã ghi: {SEED_OUT}")
    print("KẾT QUẢ:", "✅ ĐỦ 3321/3321" if ok else "⚠️ CHƯA đủ phủ — xem cảnh báo trên")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
