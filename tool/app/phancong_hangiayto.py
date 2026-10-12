"""Phân công GV – xe (PCG-06) — hạn giấy tờ xe/GPLX giáo viên + GV/xe ngưng còn phân công. Chỉ ĐỌC.

TDD §11E.10. Phạm vi TOÀN CƠ SỞ (khác luật ⛔ "hết hạn trước bế giảng" của PCG-04 xét theo từng khóa).
Luật thuần `phan_loai_han` ở `phancong_rules.py`; module này chỉ đọc CDB đích rồi gom nhóm.
"""
from __future__ import annotations

from datetime import date

from app import phancong_rules as rules
from app.phancong_service import iso_ngay

_MUC_UU_TIEN = {rules.HAN_HET: 0, rules.HAN_SAP: 1}


def _s(v) -> str:
    return "" if v is None else str(v).strip()


def _khoa_theo_ma(rows: list[dict], cot_ma: str) -> dict[str, list[dict]]:
    """Gom các khóa chưa bế giảng theo mã xe/GV (bỏ trùng, giữ thứ tự)."""
    out: dict[str, list[dict]] = {}
    for r in rows:
        ds = out.setdefault(_s(r[cot_ma]), [])
        if not any(k["ma_kh"] == r["MaKH"] for k in ds):
            ds.append({"ma_kh": r["MaKH"], "ten_kh": _s(r["TenKH"])})
    return out


def _giay(ten: str, ngay_hh: str, hom_nay: date, nguong: int) -> dict | None:
    """Một loại giấy → {giay, ngay, con_ngay, muc} nếu đỏ/vàng, không thì None."""
    muc = rules.phan_loai_han(ngay_hh, hom_nay, nguong)
    if muc not in _MUC_UU_TIEN:
        return None
    con = (date.fromisoformat(ngay_hh) - hom_nay).days  # âm = đã quá hạn
    return {"giay": ten, "ngay": ngay_hh, "con_ngay": con, "muc": muc}


def _ten_gv(r: dict) -> str:
    return f"{_s(r['HoTenDem'])} {_s(r['TenGV'])}".strip()


def _dong_han(ma_key: str, ma: str, thong_tin: dict, giay: list[dict], khoa: list[dict]) -> dict:
    muc = min((g["muc"] for g in giay), key=lambda m: _MUC_UU_TIEN[m])
    return {ma_key: ma, **thong_tin, "muc": muc, "giay": giay, "khoa": khoa}


def _ngung(rows: list[dict], cot_ma: str, ten_khoa: str, thong_tin) -> list[dict]:
    """Dòng thuộc khóa chưa bế giảng mà danh mục GV/xe đã ngưng (TrangThai=0)."""
    out: dict[str, dict] = {}
    for r in rows:
        if r["TT_DM"] is None or r["TT_DM"]:  # còn hoạt động (hoặc chưa rõ) → không thuộc nhóm này
            continue
        ma = _s(r[cot_ma])
        d = out.setdefault(ma, {ten_khoa: ma, **thong_tin(r), "khoa": []})
        if not any(k["ma_kh"] == r["MaKH"] for k in d["khoa"]):
            d["khoa"].append({"ma_kh": r["MaKH"], "ten_kh": _s(r["TenKH"])})
    return list(out.values())


def han_giay_to(conn, ma_csdt: str, hom_nay: date, nguong: int = 30) -> dict:
    cur = conn.cursor(as_dict=True)
    ngay_bg = hom_nay.strftime("%Y%m%d")

    cur.execute("SELECT BienSoXe, HangGPLXXe, NgayHHGPXTL, NgayHHGCNKD FROM dbo.XeTap "
                "WHERE MaCSDT = %s AND TrangThai = 1", (ma_csdt,))
    xe_hd = cur.fetchall()
    cur.execute("SELECT MaGV, HoTenDem, TenGV, HangGPLX, NgayHHGPLX FROM dbo.GiaoVien "
                "WHERE MaCSDT = %s AND TrangThai = 1", (ma_csdt,))
    gv_hd = cur.fetchall()

    # Dòng thuộc khóa chưa bế giảng (mọi cờ) kèm trạng thái danh mục → vừa lấy "khóa đang dùng" vừa lọc nhóm ngưng.
    cur.execute(
        "SELECT x.BienSoXe, xt.HangGPLXXe, xt.TrangThai AS TT_DM, kh.MaKH, kh.TenKH "
        "FROM dbo.KhoaHoc_XeTap x JOIN dbo.KhoaHoc kh ON kh.MaKH = x.MaKH "
        "JOIN dbo.XeTap xt ON xt.BienSoXe = x.BienSoXe AND xt.MaCSDT = kh.MaCSDT "
        "WHERE kh.MaCSDT = %s AND kh.TrangThai = 1 AND kh.NgayBG >= %s AND x.TrangThai = 1 "
        "ORDER BY kh.NgayKG, kh.MaKH", (ma_csdt, ngay_bg))
    xe_khoa = cur.fetchall()
    cur.execute(
        "SELECT g.MaGV, gv.HoTenDem, gv.TenGV, gv.HangGPLX, gv.TrangThai AS TT_DM, kh.MaKH, kh.TenKH "
        "FROM dbo.KhoaHoc_GiaoVien g JOIN dbo.KhoaHoc kh ON kh.MaKH = g.MaKH "
        "JOIN dbo.GiaoVien gv ON gv.MaGV = g.MaGV AND gv.MaCSDT = kh.MaCSDT "
        "WHERE kh.MaCSDT = %s AND kh.TrangThai = 1 AND kh.NgayBG >= %s AND g.TrangThai = 1 "
        "ORDER BY kh.NgayKG, kh.MaKH", (ma_csdt, ngay_bg))
    gv_khoa = cur.fetchall()

    khoa_xe = _khoa_theo_ma(xe_khoa, "BienSoXe")
    khoa_gv = _khoa_theo_ma(gv_khoa, "MaGV")

    xe: dict[str, list[dict]] = {rules.HAN_HET: [], rules.HAN_SAP: [], rules.HAN_CHUA: []}
    for r in xe_hd:
        bs = _s(r["BienSoXe"])
        ng_pxtl, ng_kd = iso_ngay(r["NgayHHGPXTL"]), iso_ngay(r["NgayHHGCNKD"])
        tt = {"hang": _s(r["HangGPLXXe"])}
        if not ng_pxtl and not ng_kd:
            xe[rules.HAN_CHUA].append({"bien_so": bs, **tt, "khoa": khoa_xe.get(bs, [])})
            continue
        giay = [g for g in (_giay("gpxtl", ng_pxtl, hom_nay, nguong),
                            _giay("gcnkd", ng_kd, hom_nay, nguong)) if g]
        if giay:  # cùng ngày → hai loại giấy gộp một dòng
            d = _dong_han("bien_so", bs, tt, giay, khoa_xe.get(bs, []))
            xe[d["muc"]].append(d)

    gv: dict[str, list[dict]] = {rules.HAN_HET: [], rules.HAN_SAP: [], rules.HAN_CHUA: []}
    for r in gv_hd:
        ma = _s(r["MaGV"])
        ng = iso_ngay(r["NgayHHGPLX"])
        tt = {"ho_ten": _ten_gv(r), "hang": _s(r["HangGPLX"])}
        if not ng:
            gv[rules.HAN_CHUA].append({"ma_gv": ma, **tt, "khoa": khoa_gv.get(ma, [])})
            continue
        g = _giay("gplx", ng, hom_nay, nguong)
        if g:
            d = _dong_han("ma_gv", ma, tt, [g], khoa_gv.get(ma, []))
            gv[d["muc"]].append(d)

    for nhom in (xe, gv):
        for muc in (rules.HAN_HET, rules.HAN_SAP):
            nhom[muc].sort(key=lambda d: min(g["ngay"] for g in d["giay"]))

    ngung_xe = _ngung(xe_khoa, "BienSoXe", "bien_so", lambda r: {"hang": _s(r["HangGPLXXe"])})
    ngung_gv = _ngung(gv_khoa, "MaGV", "ma_gv",
                      lambda r: {"ho_ten": _ten_gv(r), "hang": _s(r["HangGPLX"])})

    return {
        "hom_nay": hom_nay.isoformat(), "nguong": nguong,
        "xe": xe, "gv": gv, "ngung": {"xe": ngung_xe, "gv": ngung_gv},
        "dem": {
            "xe_het_han": len(xe[rules.HAN_HET]), "xe_sap_het": len(xe[rules.HAN_SAP]),
            "gv_het_han": len(gv[rules.HAN_HET]), "gv_sap_het": len(gv[rules.HAN_SAP]),
            "xe_chua_khai": len(xe[rules.HAN_CHUA]), "gv_chua_khai": len(gv[rules.HAN_CHUA]),
            "ngung_xe": len(ngung_xe), "ngung_gv": len(ngung_gv),
        },
    }
