"""Phân công GV – xe (PCG, task 86) — ĐỌC CDB đích + dựng đầu vào cho `phancong_rules`.

Chỉ đọc (SELECT tham số hóa). Ghi nằm ở task 87. Không đụng DB Nạp.
TDD §11E.1/§11E.2. Schema đã verify 10/10/2026: `KhoaHoc_GiaoVien` (cờ `IsKhoaHocGiaoVien`
1=GV thuộc khóa, 0=phân công), `KhoaHoc_XeTap` (cờ `IsKhoaHocXeTap` 1=xe thuộc khóa, 0=ghép xe).
"""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Iterable

from app import phancong_rules as rules
from app import sync_helpers

_CHUNK = 200


# ── Chuẩn hóa dữ liệu ──
def chunks(xs: list, n: int = _CHUNK):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def iso_dt(v: Any) -> str:
    """datetime/chuỗi → 'YYYY-MM-DDTHH:MM' (giữ phút, bỏ giây). Rỗng/None → ''."""
    if v is None or v == "":
        return ""
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%dT%H:%M")
    if isinstance(v, date):
        return v.strftime("%Y-%m-%d") + "T00:00"
    s = str(v).strip().replace(" ", "T")
    if len(s) == 10:
        return s + "T00:00"
    return s[:16]


def iso_ngay(v: Any) -> str:
    return iso_dt(v)[:10]


def doc_mon(ma_mon: Any, ten_mon: Any, ten_sang_id: dict[str, int] | None = None) -> list[int]:
    """Đọc môn của một dòng phân công — 3 định dạng đã gặp trong CDB:
    ① `MaMonHoc` có giá trị (trước 07/2026) ② `TenMonHoc` = danh sách mã "1,8" (từ 29/07/2026,
    `MaMonHoc` NULL) ③ `TenMonHoc` = tên môn. Không nhận ra → []."""
    if ma_mon not in (None, ""):
        try:
            return [int(ma_mon)]
        except (TypeError, ValueError):
            pass
    t = str(ten_mon or "").strip()
    if not t:
        return []
    if re.fullmatch(r"\d+(\s*,\s*\d+)*", t):
        return sorted({int(x) for x in t.split(",")})
    if ten_sang_id:
        ids = [ten_sang_id[p.strip().lower()] for p in re.split(r"[;+]", t) if p.strip().lower() in ten_sang_id]
        return sorted(set(ids))
    return []


def ghi_mon(ids: Iterable[int]) -> str:
    """Định dạng ghi (CDB hiện hành): mã môn ngăn dấu phẩy, tăng dần — `MaMonHoc` để NULL."""
    return ",".join(str(i) for i in sorted({int(i) for i in ids}))


def hang_nhom(hang_dt: str | None) -> str:
    """'B.01' → 'B'; 'C1' → 'C1' (so với `CacHangGPLXDuocDT` của GV)."""
    return (hang_dt or "").strip().upper().split(".")[0]


def tach_hang(s: str | None) -> list[str]:
    return [x.upper() for x in re.split(r"[,;/\s]+", (s or "").strip()) if x]


def gp_het_som_nhat(*ds: Any) -> str:
    """Ngày hết hạn sớm nhất trong (GPXTL, GCNKD); NULL bỏ qua. Cả hai NULL → ''."""
    xs = [iso_ngay(d) for d in ds if d]
    return min(xs) if xs else ""


# ── Đọc CDB ──
def ma_csdt(conn) -> str | None:
    return sync_helpers.get_ma_csdt_tu_qtht(conn)


def ds_mon(conn) -> list[dict]:
    cur = conn.cursor(as_dict=True)
    cur.execute("SELECT MaMH, TenMH FROM dbo.DM_MonHoc WHERE TrangThai = 1 ORDER BY MaMH")
    return [{"id": int(r["MaMH"]), "ten": r["TenMH"]} for r in cur.fetchall()]


def _ten_sang_id(mons: list[dict]) -> dict[str, int]:
    return {m["ten"].strip().lower(): m["id"] for m in mons}


def ds_khoa(conn, ma: str, q: str = "") -> list[dict]:
    cur = conn.cursor(as_dict=True)
    like = f"%{q.strip()}%"
    cur.execute(
        "SELECT TOP 60 kh.MaKH, kh.TenKH, kh.HangGPLX, kh.HangDT, "
        "CONVERT(varchar(10), kh.NgayKG, 120) AS NgayKG, CONVERT(varchar(10), kh.NgayBG, 120) AS NgayBG, "
        f"kh.TongSoHV, {sync_helpers.dkkh_exists_sql('kh')} AS dkkh "
        "FROM dbo.KhoaHoc kh WHERE kh.MaCSDT = %s AND kh.TrangThai = 1 "
        "AND (kh.MaKH LIKE %s OR kh.TenKH LIKE %s) ORDER BY kh.NgayKG DESC, kh.MaKH DESC",
        (ma, like, like),
    )
    return [_khoa_row(r) for r in cur.fetchall()]


def _khoa_row(r: dict) -> dict:
    return {
        "ma_kh": r["MaKH"], "ten_kh": r["TenKH"], "hang_gplx": (r["HangGPLX"] or "").strip(),
        "hang_dt": (r["HangDT"] or "").strip(), "hang_nhom": hang_nhom(r["HangDT"]),
        "hang_xe": (r["HangGPLX"] or "").strip(), "kg": r["NgayKG"], "bg": r["NgayBG"],
        "so_hv": int(r["TongSoHV"] or 0), "da_dkkh": bool(r["dkkh"]),
    }


def doc_khoa(conn, ma: str, ma_kh: str) -> dict | None:
    cur = conn.cursor(as_dict=True)
    cur.execute(
        "SELECT kh.MaKH, kh.TenKH, kh.HangGPLX, kh.HangDT, "
        "CONVERT(varchar(10), kh.NgayKG, 120) AS NgayKG, CONVERT(varchar(10), kh.NgayBG, 120) AS NgayBG, "
        f"kh.TongSoHV, {sync_helpers.dkkh_exists_sql('kh')} AS dkkh "
        "FROM dbo.KhoaHoc kh WHERE kh.MaCSDT = %s AND kh.MaKH = %s",
        (ma, ma_kh),
    )
    r = cur.fetchone()
    return _khoa_row(r) if r else None


def hien_trang(conn, ma_kh: str, mons: list[dict]) -> dict:
    """Danh sách GV/phân công/xe/ghép xe hiện có của khóa (chỉ dòng TrangThai=1), kèm id dòng CDB."""
    t2i = _ten_sang_id(mons)
    cur = conn.cursor(as_dict=True)
    cur.execute(
        "SELECT g.MaLichLV, g.MaGV, g.IsKhoaHocGiaoVien AS la_ds, g.NgayBD, g.NgayKT, g.MaMonHoc, g.TenMonHoc "
        "FROM dbo.KhoaHoc_GiaoVien g WHERE g.MaKH = %s AND g.TrangThai = 1 ORDER BY g.MaLichLV",
        (ma_kh,),
    )
    gv_khoa, pc = [], []
    for r in cur.fetchall():
        if r["la_ds"]:
            gv_khoa.append({"id": int(r["MaLichLV"]), "ma": r["MaGV"].strip()})
        else:
            pc.append({"id": int(r["MaLichLV"]), "ma": r["MaGV"].strip(), "mon": doc_mon(r["MaMonHoc"], r["TenMonHoc"], t2i),
                       "tu": iso_dt(r["NgayBD"]), "den": iso_dt(r["NgayKT"])})
    cur.execute(
        "SELECT x.MaLichSD, x.BienSoXe, x.MaGV, x.IsKhoaHocXeTap AS la_ds, x.NgayBD, x.NgayKT, x.DiaDiem "
        "FROM dbo.KhoaHoc_XeTap x WHERE x.MaKH = %s AND x.TrangThai = 1 ORDER BY x.MaLichSD",
        (ma_kh,),
    )
    xe_khoa, ghep = [], []
    for r in cur.fetchall():
        if r["la_ds"]:
            xe_khoa.append({"id": int(r["MaLichSD"]), "bs": r["BienSoXe"].strip()})
        else:
            ghep.append({"id": int(r["MaLichSD"]), "ma": (r["MaGV"] or "").strip(), "xe": r["BienSoXe"].strip(),
                         "tu": iso_dt(r["NgayBD"]), "den": iso_dt(r["NgayKT"]), "dia_diem": (r["DiaDiem"] or "").strip()})
    return {"gv_khoa": gv_khoa, "pc": pc, "xe_khoa": xe_khoa, "ghep": ghep}


def _gv_row(r: dict) -> dict:
    return {
        "ma": r["MaGV"].strip(), "ten": f"{(r['HoTenDem'] or '').strip()} {(r['TenGV'] or '').strip()}".strip(),
        "loai": (r["LoaiHinh_DaoTao"] or "").strip().upper()[:2],
        "active": bool(r["TrangThai"]), "hang_gplx": (r["HangGPLX"] or "").strip(),
        "hang_duoc_day": tach_hang(r["CacHangGPLXDuocDT"]),
    }


def _xe_row(r: dict) -> dict:
    return {
        "bs": r["BienSoXe"].strip(), "hang": (r["HangGPLXXe"] or "").strip(), "active": bool(r["TrangThai"]),
        "gp_het": gp_het_som_nhat(r["NgayHHGPXTL"], r["NgayHHGCNKD"]),
    }


_SQL_GV = ("SELECT MaGV, HoTenDem, TenGV, LoaiHinh_DaoTao, TrangThai, HangGPLX, CacHangGPLXDuocDT "
           "FROM dbo.GiaoVien WHERE MaCSDT = %s{ids} ORDER BY TenGV, HoTenDem")
_SQL_XE = ("SELECT BienSoXe, HangGPLXXe, NgayHHGPXTL, NgayHHGCNKD, TrangThai "
           "FROM dbo.XeTap WHERE MaCSDT = %s{ids} ORDER BY BienSoXe")


def ds_giao_vien(conn, ma: str, ids: list[str] | None = None) -> list[dict]:
    cur = conn.cursor(as_dict=True)
    if ids is None:
        cur.execute(_SQL_GV.format(ids=""), (ma,))
        return [_gv_row(r) for r in cur.fetchall()]
    out = []
    for ch in chunks(sorted(set(ids))):
        cur.execute(_SQL_GV.format(ids=" AND MaGV IN (" + ", ".join(["%s"] * len(ch)) + ")"), (ma, *ch))
        out += [_gv_row(r) for r in cur.fetchall()]
    return out


def ds_xe(conn, ma: str, ids: list[str] | None = None) -> list[dict]:
    cur = conn.cursor(as_dict=True)
    if ids is None:
        cur.execute(_SQL_XE.format(ids=""), (ma,))
        return [_xe_row(r) for r in cur.fetchall()]
    out = []
    for ch in chunks(sorted(set(ids))):
        cur.execute(_SQL_XE.format(ids=" AND BienSoXe IN (" + ", ".join(["%s"] * len(ch)) + ")"), (ma, *ch))
        out += [_xe_row(r) for r in cur.fetchall()]
    return out


def ban_khac(conn, ma_kh: str, gv_ids: list[str], xe_ids: list[str]) -> tuple[dict, dict]:
    """"Bận" của GV/xe ở các khóa KHÁC (dòng cờ=0, TrangThai=1, có đủ NgayBD/NgayKT).

    Không gồm khóa đang sửa: bản nháp đã chứa toàn bộ trạng thái khóa này, luật tự so các
    dòng trong bản nháp với nhau (không để dòng cũ trong CDB của chính khóa này cản bản sửa)."""
    cur = conn.cursor(as_dict=True)
    ban_gv: dict[str, list[dict]] = {}
    for ch in chunks(sorted(set(gv_ids))):
        cur.execute(
            "SELECT g.MaGV, g.MaKH, kh.TenKH, g.NgayBD, g.NgayKT, CONVERT(varchar(10), kh.NgayBG, 120) AS NgayBG "
            "FROM dbo.KhoaHoc_GiaoVien g JOIN dbo.KhoaHoc kh ON kh.MaKH = g.MaKH "
            "WHERE g.IsKhoaHocGiaoVien = 0 AND g.TrangThai = 1 AND g.MaKH <> %s "
            "AND g.NgayBD IS NOT NULL AND g.NgayKT IS NOT NULL AND g.MaGV IN (" + ", ".join(["%s"] * len(ch)) + ")",
            (ma_kh, *ch),
        )
        for r in cur.fetchall():
            ban_gv.setdefault(r["MaGV"].strip(), []).append(
                {"khoa": r["TenKH"], "tu": iso_dt(r["NgayBD"]), "den": iso_dt(r["NgayKT"]), "bg": r["NgayBG"]})
    ban_xe: dict[str, list[dict]] = {}
    for ch in chunks(sorted(set(xe_ids))):
        cur.execute(
            "SELECT x.BienSoXe, x.MaKH, kh.TenKH, x.NgayBD, x.NgayKT, CONVERT(varchar(10), kh.NgayBG, 120) AS NgayBG "
            "FROM dbo.KhoaHoc_XeTap x JOIN dbo.KhoaHoc kh ON kh.MaKH = x.MaKH "
            "WHERE x.IsKhoaHocXeTap = 0 AND x.TrangThai = 1 AND x.MaKH <> %s "
            "AND x.NgayBD IS NOT NULL AND x.NgayKT IS NOT NULL AND x.BienSoXe IN (" + ", ".join(["%s"] * len(ch)) + ")",
            (ma_kh, *ch),
        )
        for r in cur.fetchall():
            ban_xe.setdefault(r["BienSoXe"].strip(), []).append(
                {"khoa": r["TenKH"], "tu": iso_dt(r["NgayBD"]), "den": iso_dt(r["NgayKT"]), "bg": r["NgayBG"]})
    return ban_gv, ban_xe


def ha_muc_du_lieu_cu(vande: list[dict], hien: dict, gv_khoa: list[str], pc: list[dict],
                      xe_khoa: list[str], ghep: list[dict]) -> list[dict]:
    """Dòng GIỮ NGUYÊN như đang có trong CDB mà vi phạm luật → hạ ⛔ xuống ⚠ ("dữ liệu cũ").

    Lý do: khóa cũ có nhiều lệch sẵn (xe không có trong danh sách xe, xe hết hạn sau khi đã ghép…);
    nếu chặn thì nhân viên không ghi nổi một thay đổi nhỏ mà không sửa hết dữ liệu cũ. Dòng
    MỚI/SỬA vẫn bị chặn đủ. Lỗi do dòng mới gây ra nằm trên dòng mới nên vẫn chặn."""
    cu_pc = {str(p["id"]) for p in pc for o in hien["pc"]
             if str(o["id"]) == str(p.get("id")) and o["ma"] == p["ma"]
             and sorted(o["mon"]) == sorted(p["mon"]) and o["tu"] == p["tu"] and o["den"] == p["den"]}
    cu_gh = {(m["ma"], m["xe"]) for m in ghep for o in hien["ghep"]
             if o["ma"] == m["ma"] and o["xe"] == m["xe"] and o["tu"] == m["tu"] and o["den"] == m["den"]}
    cu_gv = {g for g in gv_khoa if any(o["ma"] == g for o in hien["gv_khoa"])}
    cu_xe = {x for x in xe_khoa if any(o["bs"] == x for o in hien["xe_khoa"])}
    # Lỗi do bản nháp TỰ làm lệch (gỡ GV/xe/thực hành mà vẫn giữ dòng phụ thuộc) KHÔNG phải dữ liệu cũ:
    # chỉ hạ mức khi chỗ phụ thuộc đã hỏng sẵn trong CDB trước khi sửa.
    gv_cdb = {o["ma"] for o in hien["gv_khoa"]}
    xe_cdb = {o["bs"] for o in hien["xe_khoa"]}
    th_cdb = {o["ma"] for o in hien["pc"] if rules.MON_THUC_HANH in o["mon"]}
    hong_san = {"gv_ngoai_khoa": lambda ma, xe: ma not in gv_cdb,
                "gv_khong_day_th": lambda ma, xe: ma not in th_cdb,
                "xe_ngoai_khoa": lambda ma, xe: xe not in xe_cdb}
    ma_gh_cu = {ma for ma, _ in cu_gh}
    out = []
    for v in vande:
        ref = v.get("ref") or ""
        if ref.startswith("gh-"):
            ma = ref[3:]
            cu = (ma, v["xe"]) in cu_gh if v.get("xe") is not None else ma in ma_gh_cu
        else:
            cu = ((ref.startswith("pc-") and ref[3:] in cu_pc)
                  or (ref.startswith("gv-") and ref[3:] in cu_gv) or (ref.startswith("xe-") and ref[3:] in cu_xe))
        if cu and v["ma"] in hong_san:
            ma_gv = ref[3:] if ref.startswith("gh-") else (ref[3:] if ref.startswith("gv-") else "")
            if ref.startswith("pc-"):  # gv_ngoai_khoa trên phân công: lấy mã GV từ bản nháp
                ma_gv = next((p["ma"] for p in pc if str(p.get("id")) == ref[3:]), "")
            cu = hong_san[v["ma"]](ma_gv, v.get("xe"))
        if cu and v["muc"] == rules.CHAN:
            v = {**v, "muc": rules.CANH_BAO, "du_lieu_cu": True,
                 "noi_dung": "Dữ liệu cũ trong CDB: " + v["noi_dung"]}
        out.append(v)
    return out


def _ngu_canh(conn, ma: str, ma_kh: str, ban_nhap: dict) -> dict:
    """Nạp mọi thứ luật cần cho bản nháp `ban_nhap` (dùng chung cho kiểm tra + gợi ý ghép xe)."""
    kh = doc_khoa(conn, ma, ma_kh)
    if kh is None:
        raise KeyError("khong_thay_khoa")
    mons = ds_mon(conn)
    gv_khoa = [s.strip() for s in ban_nhap.get("gv_khoa", [])]
    pc = [{"id": p.get("id"), "ma": p["ma"].strip(), "mon": [int(i) for i in p.get("mon", [])],
           "tu": iso_dt(p.get("tu")), "den": iso_dt(p.get("den"))} for p in ban_nhap.get("pc", [])]
    xe_khoa = [s.strip() for s in ban_nhap.get("xe_khoa", [])]
    ghep = [{"ma": m["ma"].strip(), "xe": (m.get("xe") or "").strip(),
             "tu": iso_dt(m.get("tu")), "den": iso_dt(m.get("den"))} for m in ban_nhap.get("ghep", [])]
    gv_ids = sorted({*gv_khoa, *[p["ma"] for p in pc], *[m["ma"] for m in ghep]})
    xe_ids = sorted({*xe_khoa, *[m["xe"] for m in ghep if m["xe"]]})
    gvm = {g["ma"]: g for g in ds_giao_vien(conn, ma, gv_ids)} if gv_ids else {}
    xem = {x["bs"]: x for x in ds_xe(conn, ma, xe_ids)} if xe_ids else {}
    ban_gv, ban_xe = ban_khac(conn, ma_kh, gv_ids, xe_ids)
    khoa_luat = {"ma": kh["ma_kh"], "kg": kh["kg"], "bg": kh["bg"], "hang_nhom": kh["hang_nhom"],
                 "hang_xe": kh["hang_xe"], "da_dkkh": kh["da_dkkh"]}
    return {"mons": mons, "gv_khoa": gv_khoa, "pc": pc, "xe_khoa": xe_khoa, "ghep": ghep, "gvm": gvm,
            "xem": xem, "ban_gv": ban_gv, "ban_xe": ban_xe, "khoa_luat": khoa_luat,
            "ten_mon": {m["id"]: m["ten"] for m in mons}}


def kiem_tra(conn, ma: str, ma_kh: str, ban_nhap: dict, hom_nay: str | None = None) -> dict:
    """Chạy toàn bộ luật cho bản nháp `ban_nhap` {gv_khoa, pc, xe_khoa, ghep} của khóa `ma_kh`.

    Không ghi gì. Trả {vande, tom_tat, co_chan}. Server là nguồn luật duy nhất (UI chỉ hiển thị)."""
    c = _ngu_canh(conn, ma, ma_kh, ban_nhap)
    vande = rules.kiem_tra_khoa(
        c["khoa_luat"], c["gvm"], c["xem"], c["gv_khoa"], c["pc"], c["xe_khoa"], c["ghep"], c["ban_gv"], c["ban_xe"],
        hom_nay or date.today().isoformat(), c["ten_mon"],
    )
    vande = ha_muc_du_lieu_cu(vande, hien_trang(conn, ma_kh, c["mons"]), c["gv_khoa"], c["pc"], c["xe_khoa"], c["ghep"])
    return {"vande": vande, "tom_tat": rules.tom_tat(vande), "co_chan": rules.co_chan(vande)}


def goi_y_ghep_xe(conn, ma: str, ma_kh: str, ban_nhap: dict, hom_nay: str | None = None) -> dict:
    """Gợi ý xe cho các GV có phân công Thực hành lái xe mà chưa có xe. KHÔNG ghi.

    Mỗi GV một xe, mỗi xe một GV; chỉ xe đã thuộc khóa; loại xe bị ⛔ theo luật; ưu tiên xe ít cảnh báo
    nhất (đúng hạng, không chạy khóa khác). GV không có xe hợp lệ → xe="" kèm lý do."""
    c = _ngu_canh(conn, ma, ma_kh, ban_nhap)
    hom_nay = hom_nay or date.today().isoformat()
    da_ghep_gv = {m["ma"] for m in c["ghep"] if m["xe"]}
    xe_dung = {m["xe"] for m in c["ghep"] if m["xe"]}
    ghep = list(c["ghep"])
    out: list[dict] = []
    for g in c["gv_khoa"]:
        th = [p for p in c["pc"] if p["ma"] == g and rules.MON_THUC_HANH in p["mon"] and p["tu"] and p["den"]]
        if g in da_ghep_gv or not th:
            continue
        tu, den = min(p["tu"] for p in th), max(p["den"] for p in th)
        ten = (c["gvm"].get(g) or {}).get("ten") or g
        tot: tuple[int, str, list[str]] | None = None
        for bs in c["xe_khoa"]:
            if bs in xe_dung:
                continue
            thu = ghep + [{"ma": g, "xe": bs, "tu": tu, "den": den}]
            vd = rules.kiem_tra_khoa(c["khoa_luat"], c["gvm"], c["xem"], c["gv_khoa"], c["pc"], c["xe_khoa"], thu,
                                     c["ban_gv"], c["ban_xe"], hom_nay, c["ten_mon"])
            lien_quan = [v for v in vd if v["ref"] in (f"gh-{g}", f"xe-{bs}")]
            if any(v["muc"] == rules.CHAN for v in lien_quan):
                continue
            cb = [v["noi_dung"] for v in lien_quan if v["muc"] == rules.CANH_BAO]
            if tot is None or (len(cb), bs) < (tot[0], tot[1]):
                tot = (len(cb), bs, cb)
        if tot is None:
            out.append({"ma": g, "ten": ten, "xe": "", "tu": iso_dt(tu), "den": iso_dt(den), "canh_bao": [],
                        "ly_do": "Không có xe nào trong khóa còn trống và hợp lệ cho khoảng ngày này."})
        else:
            xe_dung.add(tot[1])
            ghep.append({"ma": g, "xe": tot[1], "tu": tu, "den": den})
            out.append({"ma": g, "ten": ten, "xe": tot[1], "tu": iso_dt(tu), "den": iso_dt(den),
                        "canh_bao": tot[2], "ly_do": ""})
    return {"goi_y": out}


# ══════════════════════════════════════════════════════════════════════
# GHI (task 87) — TDD §11E.6. Server suy ra thay đổi từ trạng thái mong muốn so với CDB,
# kiểm lại TOÀN BỘ luật, rồi ghi từng dòng bằng SP. KHÔNG dùng SP xóa lan.
# ══════════════════════════════════════════════════════════════════════
class LoiNghiepVu(Exception):
    """Lỗi nghiệp vụ có mã (router đổi sang HTTP 400/409)."""

    def __init__(self, ma: str, thong_bao: str, du_lieu: dict | None = None, http: int = 409):
        super().__init__(thong_bao)
        self.ma, self.thong_bao, self.du_lieu, self.http = ma, thong_bao, du_lieu or {}, http


def _id_cdb(v: Any) -> int | None:
    """id dòng CDB (MaLichLV/MaLichSD) hoặc None nếu là id tạm của giao diện ("n1")."""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.strip().isdigit():
        return int(v.strip())
    return None


def _dt(s: str) -> datetime:
    return datetime.strptime(iso_dt(s), "%Y-%m-%dT%H:%M")


def tinh_thay_doi(hien: dict, gv_khoa: list[str], pc: list[dict], xe_khoa: list[str], ghep: list[dict]) -> dict:
    """So trạng thái mong muốn với CDB hiện tại → các nhóm thêm/sửa/xóa (mỗi dòng kèm id CDB nếu có)."""
    h_pc = {int(o["id"]): o for o in hien["pc"]}
    h_gh = {int(o["id"]): o for o in hien["ghep"]}
    td: dict[str, Any] = {k: [] for k in
                          ("gv_them", "gv_go", "pc_them", "pc_sua", "pc_xoa", "xe_them", "xe_go", "gh_them", "gh_sua", "gh_xoa")}
    h_gv = {o["ma"]: o for o in hien["gv_khoa"]}
    for ma in dict.fromkeys(gv_khoa):
        if ma not in h_gv:
            td["gv_them"].append({"ma": ma})
    for ma, o in h_gv.items():
        if ma not in set(gv_khoa):
            td["gv_go"].append({"id": o["id"], "ma": ma})
    seen: set[int] = set()
    for p in pc:
        i = _id_cdb(p.get("id"))
        if i is not None and i in h_pc:
            seen.add(i)
            o = h_pc[i]
            if (o["ma"], sorted(o["mon"]), o["tu"], o["den"]) != (p["ma"], sorted(p["mon"]), p["tu"], p["den"]):
                td["pc_sua"].append({**p, "id": i})
        else:
            td["pc_them"].append(p)
    for i, o in h_pc.items():
        if i not in seen:
            td["pc_xoa"].append(o)
    h_xe = {o["bs"]: o for o in hien["xe_khoa"]}
    for bs in dict.fromkeys(xe_khoa):
        if bs not in h_xe:
            td["xe_them"].append({"bs": bs})
    for bs, o in h_xe.items():
        if bs not in set(xe_khoa):
            td["xe_go"].append({"id": o["id"], "bs": bs})
    seen = set()
    for m in ghep:
        if not m.get("xe"):
            continue
        i = _id_cdb(m.get("id"))
        if i is not None and i in h_gh:
            seen.add(i)
            o = h_gh[i]
            if (o["ma"], o["xe"], o["tu"], o["den"]) != (m["ma"], m["xe"], m["tu"], m["den"]):
                td["gh_sua"].append({**m, "id": i})
        else:
            td["gh_them"].append(m)
    for i, o in h_gh.items():
        if i not in seen:
            td["gh_xoa"].append(o)
    td["tong"] = sum(len(v) for k, v in td.items() if k != "tong")
    return td


def _exec(sp: str, params: dict) -> tuple[str, tuple]:
    cols = list(params)
    return ("EXEC dbo." + sp + " " + ", ".join(f"@{c}=%s" for c in cols), tuple(params[c] for c in cols))


DIA_DIEM_MAC_DINH = "tại trung tâm Thành Đạt và trên đường"


def dia_diem_mac_dinh(conn) -> str:
    cur = conn.cursor(as_dict=True)
    cur.execute("SELECT TOP 1 DiaDiem FROM dbo.KhoaHoc_XeTap WHERE IsKhoaHocXeTap = 0 AND DiaDiem IS NOT NULL "
                "GROUP BY DiaDiem ORDER BY COUNT(*) DESC")
    r = cur.fetchone()
    # Địa điểm phổ biến nhất của cơ sở; CDB chưa có dòng nào thì dùng mặc định theo PRD (PCG-03).
    return (r["DiaDiem"] or "").strip() if r and r["DiaDiem"] else DIA_DIEM_MAC_DINH


def fmt_range(d: dict) -> str:
    return rules.fmt_khoang(iso_dt(d.get("tu")), iso_dt(d.get("den")))


def _dung_buoc(conn, ma_kh: str, td: dict, gvm: dict, nguoi: str, now: datetime) -> list[dict]:
    """Dựng danh sách bước ghi theo thứ tự xóa → thêm → sửa. Mỗi bước {loai, mo_ta, sql, params}."""
    cur = conn.cursor(as_dict=True)
    nguoi = (nguoi or "")[:30]
    ten = lambda ma: (gvm.get(ma) or {}).get("ten") or ma  # noqa: E731
    loai = lambda ma: ((gvm.get(ma) or {}).get("loai") or "")[:2]  # noqa: E731
    dd = dia_diem_mac_dinh(conn) if td["gh_them"] else ""
    buoc: list[dict] = []

    def them(loai_, mo_ta, sp, params):
        sql, p = _exec(sp, params)
        buoc.append({"loai": loai_, "mo_ta": mo_ta, "sql": sql, "params": p})

    # 1) xóa — từng dòng theo MaLichLV/MaLichSD
    for o in td["gh_xoa"]:
        them("gh_xoa", f"Xóa ghép xe {o['xe']} ↔ {ten(o['ma'])}", "usp_LSD_KhoaHoc_Xetap_Delete", {"MaLichSD": int(o["id"])})
    for o in td["pc_xoa"]:
        them("pc_xoa", f"Xóa phân công {ten(o['ma'])} ({ghi_mon(o['mon'])})", "usp_LLV_KhoaHoc_GiaoVien_Delete", {"MaLichLV": int(o["id"])})
    for o in td["gv_go"]:
        them("gv_go", f"Gỡ GV {ten(o['ma'])} khỏi khóa", "usp_LLV_KhoaHoc_GiaoVien_Delete", {"MaLichLV": int(o["id"])})
    for o in td["xe_go"]:
        them("xe_go", f"Gỡ xe {o['bs']} khỏi khóa", "usp_LSD_KhoaHoc_Xetap_Delete", {"MaLichSD": int(o["id"])})
    # 2) thêm
    for o in td["gv_them"]:
        them("gv_them", f"Thêm GV {ten(o['ma'])} vào khóa", "usp_KhoaHoc_GiaoVien_Insert", {
            "MaKH": ma_kh, "MaGV": o["ma"], "TenGV": ten(o["ma"]), "BienSoXe": "", "LoaiGV": loai(o["ma"]), "SoHV": None,
            "NgayHL": None, "NgayHetHL": None, "GhiChu": "", "TrangThai": 1, "NguoiTao": nguoi, "NguoiSua": nguoi,
            "NgayTao": now, "NgaySua": now})
    for o in td["xe_them"]:
        them("xe_them", f"Thêm xe {o['bs']} vào khóa", "usp_KhoaHoc_XeTap_Insert", {
            "MaKH": ma_kh, "BienSoXe": o["bs"], "MaGV": None, "MaHV": None, "DiaDiem": None, "GhiChu": "",
            "TrangThai": 1, "NguoiTao": nguoi, "NguoiSua": nguoi, "NgayTao": now, "NgaySua": now})
    for p in td["pc_them"]:
        them("pc_them", f"Thêm phân công {ten(p['ma'])} ({ghi_mon(p['mon'])}) {fmt_range(p)}", "usp_LichLV_KhoaHoc_GiaoVien_Insert", {
            "MaKH": ma_kh, "MaGV": p["ma"], "TenGV": ten(p["ma"]), "BienSoXe": "", "LoaiGV": loai(p["ma"]), "SoHV": None,
            "NgayHL": None, "NgayHetHL": None, "GhiChu": "", "TrangThai": 1, "NguoiTao": nguoi, "NguoiSua": nguoi,
            "NgayTao": now, "NgaySua": now, "NgayBD": _dt(p["tu"]), "NgayKT": _dt(p["den"]),
            "IsKhoaHocGiaoVien": 0, "MaMonHoc": None, "TenMonHoc": ghi_mon(p["mon"])})
    for m in td["gh_them"]:
        them("gh_them", f"Ghép xe {m['xe']} ↔ {ten(m['ma'])} {fmt_range(m)}", "LichSD_KhoaHoc_XeTap_Insert", {
            "MaKH": ma_kh, "MaGV": m["ma"], "TenGV": ten(m["ma"]), "BienSoXe": m["xe"], "MaHV": None, "TenHV": None,
            "DiaDiem": (m.get("dia_diem") or dd or None), "GhiChu": "", "TrangThai": 1, "NguoiTao": nguoi,
            "NguoiSua": nguoi, "NgayTao": now, "NgaySua": now, "NgayBD": _dt(m["tu"]), "NgayKT": _dt(m["den"]),
            "IsKhoaHocXeTap": 0})
    # 3) sửa — SP Update đè cả NguoiTao/NgayTao → đọc dòng hiện có và truyền lại
    for p in td["pc_sua"]:
        cur.execute("SELECT NguoiTao, NgayTao, SoHV, NgayHL, NgayHetHL, BienSoXe, GhiChu FROM dbo.KhoaHoc_GiaoVien "
                    "WHERE MaLichLV = %s", (int(p["id"]),))
        o = cur.fetchone() or {}
        them("pc_sua", f"Sửa phân công {ten(p['ma'])} ({ghi_mon(p['mon'])}) {fmt_range(p)}", "usp_LichLV_KhoaHoc_GiaoVien_Update", {
            "MaKH": ma_kh, "MaGV": p["ma"], "TenGV": ten(p["ma"]), "BienSoXe": o.get("BienSoXe") or "",
            "LoaiGV": loai(p["ma"]), "SoHV": o.get("SoHV"), "NgayHL": o.get("NgayHL"), "NgayHetHL": o.get("NgayHetHL"),
            "GhiChu": o.get("GhiChu") or "", "TrangThai": 1, "NguoiTao": o.get("NguoiTao") or nguoi, "NguoiSua": nguoi,
            "NgayTao": o.get("NgayTao") or now, "NgaySua": now, "NgayBD": _dt(p["tu"]), "NgayKT": _dt(p["den"]),
            "IsKhoaHocGiaoVien": 0, "MaMonHoc": None, "TenMonHoc": ghi_mon(p["mon"]), "MaLichLV": int(p["id"])})
    for m in td["gh_sua"]:
        cur.execute("SELECT NguoiTao, NgayTao, MaHV, TenHV, DiaDiem, GhiChu FROM dbo.KhoaHoc_XeTap WHERE MaLichSD = %s",
                    (int(m["id"]),))
        o = cur.fetchone() or {}
        them("gh_sua", f"Sửa ghép xe {m['xe']} ↔ {ten(m['ma'])} {fmt_range(m)}", "usp_LichSD_KhoaHoc_XeTap_Update", {
            "MaKH": ma_kh, "MaGV": m["ma"], "TenGV": ten(m["ma"]), "BienSoXe": m["xe"], "MaHV": o.get("MaHV"),
            "TenHV": o.get("TenHV"), "DiaDiem": (m.get("dia_diem") or o.get("DiaDiem") or dd or None),
            "GhiChu": o.get("GhiChu") or "", "TrangThai": 1, "NguoiTao": o.get("NguoiTao") or nguoi,
            "NguoiSua": nguoi, "NgayTao": o.get("NgayTao") or now, "NgaySua": now, "NgayBD": _dt(m["tu"]),
            "NgayKT": _dt(m["den"]), "IsKhoaHocXeTap": 0, "MaLichSD": int(m["id"])})
    return buoc


def ghi(conn, ma: str, ma_kh: str, ban_nhap: dict, nguoi: str, da_xem_canh_bao: bool,
        xac_nhan_csdl_that: bool, nhat_ky=None, hom_nay: str | None = None) -> dict:
    """Ghi bản nháp vào CDB. Thứ tự gác: (1) xác nhận CSDL thật → (2) kiểm lại toàn bộ luật,
    còn ⛔ → 409 → (3) còn ⚠ mà chưa xác nhận → 409 → (4) ghi từng dòng. Lỗi giữa chừng: dừng,
    trả `da_ghi`/`chua_ghi`. Không tự rollback phần đã ghi (mỗi SP một giao dịch riêng)."""
    if not xac_nhan_csdl_that:
        raise LoiNghiepVu("thieu_xac_nhan_csdl_that", "Cần xác nhận đây là CSDL thật trước khi ghi.", http=400)
    mons = ds_mon(conn)
    hien = hien_trang(conn, ma_kh, mons)
    gv_khoa = [s.strip() for s in ban_nhap.get("gv_khoa", [])]
    pc = [{"id": p.get("id"), "ma": p["ma"].strip(), "mon": [int(i) for i in p.get("mon", [])],
           "tu": iso_dt(p.get("tu")), "den": iso_dt(p.get("den"))} for p in ban_nhap.get("pc", [])]
    xe_khoa = [s.strip() for s in ban_nhap.get("xe_khoa", [])]
    ghep = [{"id": m.get("id"), "ma": m["ma"].strip(), "xe": (m.get("xe") or "").strip(), "tu": iso_dt(m.get("tu")),
             "den": iso_dt(m.get("den")), "dia_diem": (m.get("dia_diem") or "").strip()} for m in ban_nhap.get("ghep", [])]
    td = tinh_thay_doi(hien, gv_khoa, pc, xe_khoa, ghep)
    if td["tong"] == 0:
        return {"ok": True, "da_ghi": [], "chua_ghi": [], "loi": None, "thong_bao": "Không có thay đổi để ghi.",
                "hien_trang": hien}
    # CHANGES #58: không có thay đổi thì khỏi hỏi cảnh báo — cổng luật chỉ áp khi thật sự có dòng để ghi.
    kq = kiem_tra(conn, ma, ma_kh, ban_nhap, hom_nay)
    if kq["co_chan"]:
        raise LoiNghiepVu("con_loi_chan", "Còn lỗi chặn — sửa hết mới ghi được.", {"vande": kq["vande"]})
    n_canh_bao = kq["tom_tat"]["canh_bao"]
    if n_canh_bao and not da_xem_canh_bao:
        raise LoiNghiepVu("thieu_xac_nhan_canh_bao", f"Còn {n_canh_bao} cảnh báo — cần xác nhận đã xem.",
                          {"so_canh_bao": n_canh_bao, "vande": [v for v in kq["vande"] if v["muc"] == rules.CANH_BAO]})
    ids = sorted({*gv_khoa, *[p["ma"] for p in pc], *[m["ma"] for m in ghep]})
    gvm = {g["ma"]: g for g in ds_giao_vien(conn, ma, ids)} if ids else {}
    buoc = _dung_buoc(conn, ma_kh, td, gvm, nguoi, datetime.now())

    nk = nhat_ky.bat_dau(nguoi, ma_kh, f"{td['tong']} thay đổi", {k: v for k, v in td.items() if k != "tong"}) if nhat_ky else None
    cur = conn.cursor(as_dict=True)
    da_ghi: list[dict] = []
    loi = None
    for b in buoc:
        try:
            cur.execute(b["sql"], b["params"])
            da_ghi.append({"loai": b["loai"], "mo_ta": b["mo_ta"]})
        except Exception as e:  # noqa: BLE001 — dừng, báo đã/chưa ghi
            loi = type(e).__name__
            break
    chua_ghi = [{"loai": b["loai"], "mo_ta": b["mo_ta"]} for b in buoc[len(da_ghi):]]
    ok = loi is None
    ket_qua = {"da_ghi": da_ghi, "chua_ghi": chua_ghi, "loi": loi}
    if nk is not None:
        nhat_ky.ket_thuc(nk, "xong" if ok else ("loi_giua_chung" if da_ghi else "that_bai"), ket_qua)
    return {"ok": ok, **ket_qua, "hien_trang": hien_trang(conn, ma_kh, mons)}
