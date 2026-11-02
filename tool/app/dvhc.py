"""NAP-03 — Map địa chỉ hành chính cũ → xã mới 2025.

- Chuẩn hóa tên (NGUỒN DUY NHẤT, dùng cả builder dm_dvhc_map lẫn tra cứu runtime —
  hai bên phải chuẩn hóa y hệt thì key mới khớp).
- tra_map(): tra bảng dm_dvhc_map (SQLite cục bộ) theo địa chỉ cũ đã chuẩn hóa.
- ds_tinh()/ds_xa(): danh sách Tỉnh/Xã MỚI (TrangThai=1) cho popup chọn tay.
"""
from __future__ import annotations
import re
import sqlite3
import unicodedata

from app import paths
from app.db import sqlserver_cursor, sqlserver_cursor_dich


def _cur_dvhc(db: str | None):
    """Cursor danh mục: DB đích khi có `db` (TCB-03, theo target_key), ngược lại DB Nạp.
    Cùng host/user/password — chỉ khác database (xem app/db.py)."""
    return sqlserver_cursor_dich(db) if db else sqlserver_cursor()

# Map DVHC là dữ liệu CHỈ ĐỌC gói kèm (dev: tool/db/data; bản .exe: _MEIPASS\db\data — DGT-01).
MAP_SQLITE = paths.BUNDLE_DIR / "db" / "data" / "dvhc_map.sqlite"

# ---- Chuẩn hóa tên (đặc tả verify 30/09/2026) -------------------------------
_PROV_PREFIX = re.compile(r"^(thành phố|tỉnh|tp\.?)\s+")
_DIST_PREFIX = re.compile(r"^(thành phố|quận|huyện|thị xã|tp\.?)\s+")
_WARD_PREFIX = re.compile(r"^(phường|xã|thị trấn|tt\.?)\s+")


def _base(s: str) -> str:
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


# ---- Tra bảng ánh xạ (SQLite cục bộ) ----------------------------------------
def _pack(r0, divided: bool) -> dict:
    return {
        "matched": True,
        "divided": divided,
        "ma_dvhc": r0[0],
        "ma_dvql": r0[1],
        "ten_xa": r0[2],
        "ten_tinh": r0[3],
    }


def tra_map(tinh: str, huyen: str, xa: str) -> dict | None:
    """Tra địa chỉ CŨ hoặc ĐÃ MỚI → xã mới. None nếu bảng chưa dựng hoặc không khớp.

    PRD NAP-03: "địa chỉ mới HOẶC cũ khớp map".
    - Thử key CŨ (tỉnh/huyện/xã cũ) trước.
    - Trượt → thử địa chỉ ĐÃ MỚI (tỉnh+xã mới) theo tên chuẩn hóa.
    divided=True (xã cũ chia nhiều xã mới, hoặc is_divided) → UI cho chọn tay, không auto-điền.
    """
    if not MAP_SQLITE.exists():
        return None
    conn = sqlite3.connect(str(MAP_SQLITE))
    try:
        # 1) Địa chỉ CŨ
        rows = conn.execute(
            "SELECT ma_dvhc_moi, ma_dvql_moi, ten_xa_moi, ten_tinh_moi, is_divided "
            "FROM dm_dvhc_map WHERE ten_tinh_cu=? AND ten_huyen_cu=? AND ten_xa_cu=?",
            (norm_prov(tinh), norm_dist(huyen), norm_ward(xa)),
        ).fetchall()
        if rows:
            distinct_new = {(r[0], r[1]) for r in rows}
            return _pack(rows[0], len(distinct_new) > 1 or any(r[4] for r in rows))

        # 2) Địa chỉ ĐÃ MỚI (model 2 cấp: tỉnh + xã, bỏ qua huyện)
        rows = conn.execute(
            "SELECT ma_dvhc_moi, ma_dvql_moi, ten_xa_moi, ten_tinh_moi "
            "FROM dm_dvhc_map WHERE ten_tinh_moi_norm=? AND ten_xa_moi_norm=?",
            (norm_prov(tinh), norm_ward(xa)),
        ).fetchall()
        if rows:
            distinct_new = {(r[0], r[1]) for r in rows}
            return _pack(rows[0], len(distinct_new) > 1)  # cùng xã mới → divided=False
    finally:
        conn.close()
    return None


# ---- Danh sách Tỉnh/Xã mới cho chọn tay (query DB thật) ----------------------
def ds_tinh(db: str | None = None) -> list[dict]:
    """34 tỉnh mới: DISTINCT MaDVQL + tên tách từ TenDayDu (TrangThai=1).

    Không dùng usp_DM_DVHC_SelectAll_Tinh (chỉ trả đơn vị cũ TW/TI) — xem CHANGES #2.
    `db` có giá trị → đọc danh mục ở DB đích (TCB-03), ngược lại DB Nạp.
    """
    with _cur_dvhc(db) as cur:
        cur.execute("SELECT MaDVQL, MIN(TenDayDu) AS td FROM DM_DVHC WHERE TrangThai=1 GROUP BY MaDVQL")
        rows = cur.fetchall()
    out = []
    for r in rows:
        td = r["td"] or ""
        ten = td.rsplit(",", 1)[-1].strip() if "," in td else td
        out.append({"ma_dvql": r["MaDVQL"], "ten_tinh": ten})
    out.sort(key=lambda x: x["ten_tinh"])
    return out


def ds_xa(ma_dvql: str, db: str | None = None) -> list[dict]:
    """Xã/phường MỚI theo tỉnh: qua SP + lọc TrangThai=1 ở app (SP không lọc).
    `db` có giá trị → đọc ở DB đích (TCB-03)."""
    with _cur_dvhc(db) as cur:
        cur.execute("EXEC usp_DM_DVHC_SelectDanhSachXaPhuongTheoTinh %s", (ma_dvql,))
        rows = cur.fetchall()
    return [
        {"ma_dvhc": r["MaDvhc"], "ma_dvql": r["MaDVQL"], "ten_xa": r["TenNganGon"]}
        for r in rows
        if r.get("TrangThai") == 1
    ]


def ds_noi_cap_gplx() -> list[dict]:
    """Danh sách 'Nơi cấp' của GPLX đã có (NAP-07, TDD §10.6): DM_DonViGTVT cấp Sở, nguồn phần mềm cũ dùng in tờ khai
    (usf_QuangLA_PM4_ThuNhanHS_getTenDVCap). KHÔNG dùng DM_DVHC: cùng mã khác tên, vd '80' là Long An ở đây, Tây Ninh ở kia."""
    with _cur_dvhc(None) as cur:
        cur.execute("SELECT MaDV, TenDV FROM DM_DonViGTVT WHERE LoaiDV='SO' ORDER BY MaDV")
        rows = cur.fetchall()
    return [{"ma": r["MaDV"], "ten": f'{r["MaDV"]} — {(r["TenDV"] or "").strip()}'} for r in rows]


def ds_so_gtvt(db: str | None = None) -> list[dict]:
    """Danh sách 'Nơi cấp' căn cước cho combobox — đọc DM_DVHC (mã 2 ký tự = MaDvhc).

    NoiCapCMT lưu theo MaDvhc của DM_DVHC: mã tỉnh (LoaiDvhc 'TW'/'TI', chỉ tỉnh đang hiệu
    lực TrangThai=1) + nhóm Cục (LoaiDvhc 'C', gồm '00'='Cục QLHC' cho căn cước — hiện bất kể
    TrangThai để operator chọn được). Trước 06/10 lấy từ DM_DonViGTVT (Sở GTVT) — đổi để có
    'Cục QLHC' và khớp danh mục NoiCapCMT thật sự tham chiếu. `db` có giá trị → đọc DB đích (TCB-03).
    Tên hàm giữ `ds_so_gtvt` để không phá caller; nội dung đã là DM_DVHC."""
    with _cur_dvhc(db) as cur:
        cur.execute("SELECT MaDvhc, TenNganGon FROM DM_DVHC "
                    "WHERE LEN(MaDvhc)=2 AND (LoaiDvhc='C' OR (LoaiDvhc IN ('TW','TI') AND TrangThai=1)) "
                    "ORDER BY LoaiDvhc, TenNganGon")
        rows = cur.fetchall()
    return [{"ma": r["MaDvhc"], "ten": (r["TenNganGon"] or "").strip()} for r in rows]
