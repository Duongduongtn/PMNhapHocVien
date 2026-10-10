"""KQD-05 mở rộng (task 83) — nhật ký "sửa sau khi đã gửi Sở" + phân loại HV được chọn.

Nghiệp vụ: HV đã kết xuất (`TT_XuLy=12`) mà gói đã gửi Sở vẫn được mở sửa điểm theo
TỪNG HV (TDD §11D.7b, decisions §21). Nhật ký này giữ: điểm trước khi mở, lý do, người,
giờ — và đánh dấu HV nào còn "chờ kết xuất lại" để tab Theo dõi kết xuất hiện khối đỏ.

Nhật ký ghi TRƯỚC khi UPDATE CDB đích: nếu ghi lỗi thì chưa đụng DB đích. HV nào sau đó
không lùi được thì dòng nhật ký chuyển 'huy' để không hiện khối đỏ oan.
Lưu SQLite phía tool (file riêng — không dùng chung staging.sqlite của Nạp).
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app import paths

# Dev: tool/db/data · .exe: %APPDATA%\pmcsdtlx-tool\db\data (cùng thư mục với staging.sqlite).
DB_PATH = paths.DATA_DIR / "db" / "data" / "sua_sau_gui.sqlite"

CHO_KX = "cho_kx"      # đã mở sửa, chưa kết xuất lại
DA_KX = "da_kx"        # HV đã về 12 (hoặc xa hơn) — phần mềm CDB đã kết xuất lại
HUY = "huy"            # ghi nhật ký rồi nhưng UPDATE không lùi được HV

# TT_XuLy coi như "đã kết xuất lại / Sở đã phản hồi" → rời khối đỏ.
TT_DA_KX = ("12", "13", "14", "90")

_DDL = (
    "CREATE TABLE IF NOT EXISTS sua_sau_gui ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, ma_dk TEXT NOT NULL, ma_kh TEXT, ho_ten TEXT, "
    "diem_truoc_json TEXT, ly_do TEXT NOT NULL, nguoi TEXT, luc_mo TEXT NOT NULL, "
    "trang_thai TEXT NOT NULL DEFAULT 'cho_kx', luc_kx TEXT)"
)
_IDX = "CREATE INDEX IF NOT EXISTS ix_ssg_trang_thai ON sua_sau_gui(trang_thai, ma_dk)"

LY_DO_TOI_DA = 1000   # GiaiTrinh nvarchar(1000)
SO_HV_TOI_DA = 200


def _ket_noi(db_path: Path | None = None) -> sqlite3.Connection:
    p = Path(db_path) if db_path else DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    conn.execute(_DDL)
    conn.execute(_IDX)
    return conn


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ── Phân loại HV được chọn (thuần, không DB) ──
def phan_loai(rows_db: list[dict], ma_dks: list[str]) -> dict:
    """Chia HV được chọn thành: hợp lệ (lùi được) · bỏ qua (kèm lý do) · bị 13 (chặn cả lô).

    `rows_db`: dòng SELECT từ CDB đích (MaDK, TT_XuLy, KetLuanCSDT, …). HV không có trong
    `rows_db` → 'không tìm thấy'. Quy tắc (TDD §11D.7b):
      - TT=13 → chặn CẢ lô (409) — Sở đã duyệt, khóa tuyệt đối.
      - TT≠12 → bỏ qua (không ở trạng thái đã gửi Sở).
      - TT=12 mà KetLuanCSDT NULL → bỏ qua, KHÔNG ép '10' oan (bất thường).
    """
    theo_ma = {str(r["MaDK"]).strip(): r for r in rows_db}
    hop_le: list[dict] = []
    bo_qua: list[dict] = []
    bi_13: list[str] = []
    for ma in ma_dks:
        r = theo_ma.get(ma)
        if r is None:
            bo_qua.append({"ma_dk": ma, "ly_do": "Không tìm thấy hồ sơ ở CSDL đích."})
            continue
        tt = (r.get("TT_XuLy") or "").strip()
        if tt == "13":
            bi_13.append(ma)
        elif tt != "12":
            bo_qua.append({"ma_dk": ma, "ly_do": f"Không ở trạng thái đã gửi Sở (TT_XuLy={tt or 'trống'})."})
        elif r.get("KetLuanCSDT") is None:
            bo_qua.append({"ma_dk": ma, "ly_do": "Chưa có kết luận (bất thường với HV đã kết xuất) — không tự ép Không đạt."})
        else:
            hop_le.append(r)
    return {"hop_le": hop_le, "bo_qua": bo_qua, "bi_13": bi_13}


def diem_json(r: dict) -> str:
    """5 điểm quy đổi + kết luận hiện có của HV (lưu để so 'trước → sau')."""
    def f(k):
        v = r.get(k)
        return float(v) if v is not None else None
    kl = r.get("KetLuanCSDT")
    return json.dumps({
        "ly_thuyet": f("DiemKQLyThuyet"), "mo_phong": f("DiemKQMoPhong"),
        "hinh": f("DiemKQHinh"), "tien_lui": f("DiemKQTienLui"), "duong": f("DiemKQThucHanh"),
        "ket_luan": None if kl is None else ("dat" if int(kl) == 1 else "khong_dat"),
    }, ensure_ascii=False)


# ── Nhật ký (SQLite) ──
def ghi(hv: list[dict], ly_do: str, nguoi: str, db_path: Path | None = None) -> dict[str, int]:
    """Ghi nhật ký cho các HV sắp mở. Trả {ma_dk: id}. Gọi TRƯỚC khi UPDATE CDB đích."""
    conn = _ket_noi(db_path)
    try:
        ids: dict[str, int] = {}
        for r in hv:
            # Mở lại HV đã từng mở: dòng cũ còn 'cho_kx' nghĩa là HV đã về 12 (đã kết xuất lại)
            # rồi được mở lần nữa trước khi ai gọi GET → đóng dòng cũ, tránh khối đỏ trùng HV.
            conn.execute("UPDATE sua_sau_gui SET trang_thai=?, luc_kx=? WHERE ma_dk=? AND trang_thai=?",
                         (DA_KX, _now(), str(r["MaDK"]).strip(), CHO_KX))
            cur = conn.execute(
                "INSERT INTO sua_sau_gui (ma_dk, ma_kh, ho_ten, diem_truoc_json, ly_do, nguoi, luc_mo, trang_thai) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (str(r["MaDK"]).strip(), (r.get("MaKhoaHoc") or "").strip(), (r.get("HoVaTen") or "").strip(),
                 diem_json(r), ly_do, nguoi, _now(), CHO_KX),
            )
            ids[str(r["MaDK"]).strip()] = cur.lastrowid
        conn.commit()
        return ids
    finally:
        conn.close()


def doi_trang_thai(ids: list[int], trang_thai: str, db_path: Path | None = None) -> None:
    """Đổi trạng thái các dòng nhật ký (huy / da_kx). Bỏ qua dòng không còn ở cho_kx."""
    if not ids:
        return
    conn = _ket_noi(db_path)
    try:
        luc = _now() if trang_thai == DA_KX else None
        conn.executemany(
            "UPDATE sua_sau_gui SET trang_thai=?, luc_kx=? WHERE id=? AND trang_thai=?",
            [(trang_thai, luc, i, CHO_KX) for i in ids],
        )
        conn.commit()
    finally:
        conn.close()


def cho_kx(db_path: Path | None = None) -> list[dict]:
    """Các dòng đang chờ kết xuất lại, mới mở nhất trước."""
    conn = _ket_noi(db_path)
    try:
        rows = conn.execute(
            "SELECT id, ma_dk, ma_kh, ho_ten, diem_truoc_json, ly_do, nguoi, luc_mo "
            "FROM sua_sau_gui WHERE trang_thai=? ORDER BY id DESC", (CHO_KX,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
