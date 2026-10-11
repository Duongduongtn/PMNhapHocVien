"""Tốt nghiệp & Báo cáo 2 (TNB, task 97) — ĐỌC DB Nạp `GPLX_CSDT` cho "Lập BC2 / Thêm HV".

Chỉ ĐỌC: một lần `EXEC usp_NguoiLX_HoSo_ThemHS_BC2` (cả CSĐT, `@MaKH=''`) + vài `SELECT`
bổ sung; phân nhóm bằng `tn_bc2_rules` (luật thuần). KHÔNG ghi gì (ghi ở task 98+).
TDD §11F.4 (v6.8): SP lọc khóa bằng `LIKE '%'+@MaKH+'%'` và KHÔNG trả `TT_XuLy`/`MaBC2`/hạng/
`NgayBG` → gọi một lần cho cả CSĐT rồi bổ sung cột; đo 11/10/2026 ≈ 3.450 HV trong 0,07–0,12 giây.
"""
from __future__ import annotations

import calendar
import threading
import time
from datetime import date
from typing import Any, Callable, Iterable

from app import tn_bc2_rules as rules

CACHE_GIAY = 30
TOI_DA_KHONG_DUOC = 500          # trần số dòng "Không đưa được" của khóa chọn, trả về một lần
_KHOI_IN = 900                   # pymssql: tối đa ~2100 tham số → chia khối

_Q_BC1 = "SELECT MaBCI, MaKH, SoBaoCao, SoHocSinh FROM BaoCaoI"
_Q_BC2 = "SELECT MaBCII, MaBCI, SoBaoCao, TrangThai, TongSoThiSinh FROM BaoCaoII"
_Q_KHOA = "SELECT MaKH, TenKH, HangGPLX, NgayBG FROM KhoaHoc"
_Q_HANG_KHOA = "SELECT MaKH, TenKH, HangGPLX, NgayBG FROM KhoaHoc WHERE MaKH = %s"
_Q_BO_SUNG = ("SELECT h.MaDK, h.TT_XuLy, h.MaBC2, h.HangGPLX, h.SoGiayCNTN, k.NgayBG "
              "FROM NguoiLX_HoSo h JOIN KhoaHoc k ON k.MaKH = h.MaKhoaHoc WHERE h.MaDK IN ({ph})")
_Q_KHONG_DUOC = ("SELECT h.MaDK, h.SoHoSo, n.HoVaTen, n.NgaySinh, n.SoCMT, h.SoGiayCNTN, h.HangGPLX, "
                 "h.TT_XuLy, h.MaBC2, h.MaKhoaHoc, k.TenKH, k.NgayBG "
                 "FROM NguoiLX_HoSo h JOIN NguoiLX n ON n.MaDK = h.MaDK "
                 "JOIN KhoaHoc k ON k.MaKH = h.MaKhoaHoc "
                 "WHERE h.MaKhoaHoc = %s AND h.TT_XuLy NOT IN ('03','09','14','17','18')")
_SP_UNG_VIEN = "EXEC usp_NguoiLX_HoSo_ThemHS_BC2 %s,%s,%s,%s,%s,%s,%s,%s,%s"


class LoiNghiepVu(Exception):
    """Lỗi người dùng gây ra (router đổi thành HTTP 4xx)."""

    def __init__(self, ma: str, noi_dung: str, http: int = 400):
        super().__init__(noi_dung)
        self.ma, self.noi_dung, self.http = ma, noi_dung, http


# ── Tiện ích ──
def _s(v: Any) -> str:
    return "" if v is None else str(v).strip()


def _ngay_iso(v: Any) -> str:
    if v is None:
        return ""
    if hasattr(v, "strftime"):
        return v.strftime("%Y-%m-%d")
    return str(v)[:10]


def _ngay_sinh_vn(v: Any) -> str:
    """`NguoiLX.NgaySinh` varchar(8) 'yyyymmdd' → 'dd/mm/yyyy' (đúng cách SP định dạng)."""
    t = _s(v)
    return t if len(t) < 7 else f"{t[6:8]}/{t[4:6]}/{t[0:4]}"


def hom_nay_iso() -> str:
    return date.today().isoformat()


def moc_cua_so_khoa(hom_nay: str) -> str:
    """"Hôm nay − 1 tháng − 1 năm": 11/10/2026 → 2025-09-11 (PRD TNB-01, cận dưới khóa mặc định)."""
    y, m, d = (int(x) for x in hom_nay[:10].split("-"))
    y -= 1
    m -= 1
    if m == 0:
        y, m = y - 1, 12
    return f"{y:04d}-{m:02d}-{min(d, calendar.monthrange(y, m)[1]):02d}"


def _chia(ds: list, n: int) -> Iterable[list]:
    for i in range(0, len(ds), n):
        yield ds[i:i + n]


# ── Đọc tập ứng viên của một loại (có cache ngắn) ──
_cache: dict[str, tuple[float, dict]] = {}
_khoa_cache = threading.Lock()


def bo_cache() -> None:
    """"Làm tươi" / sau mỗi lần ghi."""
    with _khoa_cache:
        _cache.clear()


def tai_tap(cur, loai: str, hom_nay: str) -> dict:
    """Đọc từ DB (không cache): HV trong SP + cột bổ sung + BC1/BC2/khóa."""
    hang_dt = "A1" if loai == "moto" else ""
    cur.execute(_SP_UNG_VIEN, ("", "", "", "", "", "", hang_dt, 0, ""))
    sp = cur.fetchall()
    ma_dks = sorted({_s(r["MaDK"]) for r in sp})
    bo_sung: dict[str, dict] = {}
    for khoi in _chia(ma_dks, _KHOI_IN):
        cur.execute(_Q_BO_SUNG.format(ph=",".join(["%s"] * len(khoi))), tuple(khoi))
        for r in cur.fetchall():
            bo_sung[_s(r["MaDK"])] = r

    hvs = []
    for r in sp:
        ma_dk = _s(r["MaDK"])
        b = bo_sung.get(ma_dk)
        if b is None:      # HV biến mất giữa hai truy vấn (PM cũ vừa xóa) → bỏ
            continue
        hvs.append({
            "ma_dk": ma_dk, "so_ho_so": _s(r.get("SoHoSo")), "ten": _s(r.get("HoVaTen")),
            "ngay_sinh": _s(r.get("NgaySinh")), "cmt": _s(r.get("SoCMT")),
            "so_giay": _s(b.get("SoGiayCNTN")), "hang": _s(b.get("HangGPLX")),
            "ma_kh": _s(r.get("MaKH")), "ten_kh": _s(r.get("TenKH")),
            "tt": _s(b.get("TT_XuLy")), "ma_bc2": _s(b.get("MaBC2")), "bg": _ngay_iso(b.get("NgayBG")),
        })

    cur.execute(_Q_BC1)
    bc1_theo_khoa = {_s(r["MaKH"]): {"ma_bci": _s(r["MaBCI"]), "so_bao_cao": _s(r["SoBaoCao"]),
                                     "so_hoc_sinh": r.get("SoHocSinh")} for r in cur.fetchall()}
    cur.execute(_Q_BC2)
    bc2_map: dict[str, int] = {}
    bc2_bci: dict[str, str] = {}
    bc2_theo_bc1: dict[str, list[dict]] = {}
    for r in cur.fetchall():
        ma = _s(r["MaBCII"])
        tt = 1 if r.get("TrangThai") in (1, True, "1") else 0
        bc2_map[ma] = tt
        bc2_bci[ma] = _s(r["MaBCI"])
        bc2_theo_bc1.setdefault(_s(r["MaBCI"]), []).append(
            {"ma": ma, "trang_thai": tt, "tong_ghi": r.get("TongSoThiSinh")})
    cur.execute(_Q_KHOA)
    khoa = {_s(r["MaKH"]): {"ten_kh": _s(r["TenKH"]), "hang": _s(r["HangGPLX"]), "bg": _ngay_iso(r["NgayBG"])}
            for r in cur.fetchall()}
    return {"loai": loai, "hom_nay": hom_nay, "hvs": hvs, "bc1_theo_khoa": bc1_theo_khoa,
            "bc2_map": bc2_map, "bc2_bci": bc2_bci, "bc2_theo_bc1": bc2_theo_bc1, "khoa": khoa}


def lay_tap(cur_factory: Callable, loai: str, hom_nay: str | None = None, lam_tuoi: bool = False,
            now: Callable[[], float] = time.monotonic) -> dict:
    """Tập ứng viên của `loai`, cache ~30 giây. `cur_factory()` trả context manager cursor dict."""
    hom_nay = hom_nay or hom_nay_iso()
    khoa_c = f"{loai}|{hom_nay}"
    if not lam_tuoi:
        with _khoa_cache:
            c = _cache.get(khoa_c)
            if c and now() - c[0] < CACHE_GIAY:
                return c[1]
    with cur_factory() as cur:
        tap = tai_tap(cur, loai, hom_nay)
    with _khoa_cache:
        _cache[khoa_c] = (now(), tap)
    return tap


def loai_cua_khoa(cur, ma_kh: str) -> dict:
    cur.execute(_Q_HANG_KHOA, (ma_kh,))
    r = cur.fetchone()
    if not r:
        raise LoiNghiepVu("khoa_khong_ton_tai", f"Không có khóa {ma_kh}", 404)
    return {"ma_kh": _s(r["MaKH"]), "ten_kh": _s(r["TenKH"]), "loai": rules.loai_hang(r["HangGPLX"]),
            "bg": _ngay_iso(r["NgayBG"])}


# ── Phân nhóm ──
def _ctx(tap: dict, ma_kh_chon: str, ma_bc2_dang_them: str = "") -> dict:
    return {"hom_nay": tap["hom_nay"], "ma_kh_chon": ma_kh_chon, "bc2_map": tap["bc2_map"],
            "ma_bc2_dang_them": ma_bc2_dang_them}


def _muc_hv(hv: dict, n: dict) -> dict:
    return {
        "ma_dk": hv["ma_dk"], "so_ho_so": hv.get("so_ho_so", ""), "ten": hv["ten"], "ngay_sinh": hv.get("ngay_sinh", ""),
        "cmt": hv["cmt"], "so_giay": hv["so_giay"], "hang": hv["hang"], "ma_kh": hv["ma_kh"], "ten_kh": hv["ten_kh"],
        "tt": hv["tt"], "ten_trang_thai": n["ten_trang_thai"], "ma_bc2": hv["ma_bc2"], "bg": hv["bg"],
        "nhom": n["nhom"], "ma_ly_do": n["ma_ly_do"], "ly_do": n["ly_do"], "goi_y_xu_ly": n["goi_y_xu_ly"],
        "tich_san": n["tich_san"], "tuoi_thang": n["tuoi_thang"], "trong_nguong": n.get("trong_nguong", False),
    }


def kiem_dau_vao(tap: dict, ma_kh: str, ma_bc2: str = "") -> None:
    """Kiểm khóa/BC2 trước khi liệt kê ứng viên (đọc, báo sớm — phần ghi kiểm lại ở task 99):
    BC2 phải tồn tại, thuộc BC1 của đúng khóa, còn mở; chưa có BC2 thì khóa phải có BC1."""
    bc1 = tap["bc1_theo_khoa"].get(ma_kh)
    if not ma_bc2:
        if bc1 is None:
            raise LoiNghiepVu("khoa_chua_co_bc1", f"Khóa {ma_kh} chưa có BC1 — chưa lập BC2 được", 409)
        return
    tt = tap["bc2_map"].get(ma_bc2)
    if tt is None:
        raise LoiNghiepVu("bc2_khong_ton_tai", f"Không có BC2 số {ma_bc2}", 404)
    if bc1 is None or tap["bc2_bci"].get(ma_bc2) != bc1["ma_bci"]:
        raise LoiNghiepVu("bc2_khac_khoa", f"BC2 số {ma_bc2} không thuộc khóa {ma_kh} (khác BC1)", 409)
    if tt != 0:
        raise LoiNghiepVu("bc2_da_dong", f"BC2 số {ma_bc2} đã đóng — không thêm học viên được", 409)


def khoa_san_sang(tap: dict, loai: str, cu: bool = False, thi_lai_thang: int = rules.THI_LAI_THANG_MAC_DINH) -> dict:
    """Bước ①: các khóa đã bế giảng kèm đếm Sẵn sàng / Thi lại / Cần xem.

    Đếm từ CHÍNH tập đã tải (không gọi SP theo từng khóa). `thi_lai` = tổng HV thi lại trong
    `thi_lai_thang` tháng (như nhau cho mọi khóa — thi lại tính bất kể khóa); `thi_lai_cua_khoa` =
    HV thi lại thuộc đúng khóa đó. Khóa hiện nếu còn HV Sẵn sàng/Cần xem/Thi lại của chính nó.
    """
    dem_san: dict[str, int] = {}
    dem_xem: dict[str, int] = {}
    dem_thi_cua: dict[str, int] = {}
    thi_trong = thi_tat_ca = 0
    for hv in tap["hvs"]:
        n = rules.phan_nhom(hv, loai, _ctx(tap, hv["ma_kh"]), thi_lai_thang)
        if n is None:
            continue
        mk = hv["ma_kh"]
        if n["nhom"] == rules.SAN_SANG:
            dem_san[mk] = dem_san.get(mk, 0) + 1
        elif n["nhom"] == rules.CAN_XEM:
            dem_xem[mk] = dem_xem.get(mk, 0) + 1
        elif n["nhom"] == rules.THI_LAI:
            dem_thi_cua[mk] = dem_thi_cua.get(mk, 0) + 1
            thi_tat_ca += 1
            thi_trong += 1 if n.get("trong_nguong") else 0
    moc = moc_cua_so_khoa(tap["hom_nay"])
    out = []
    for ma_kh, k in tap["khoa"].items():
        if rules.loai_hang(k["hang"]) != loai or not k["bg"] or k["bg"] > tap["hom_nay"]:
            continue
        if k["bg"] < moc and not cu:
            continue
        tong = dem_san.get(ma_kh, 0) + dem_xem.get(ma_kh, 0) + dem_thi_cua.get(ma_kh, 0)
        if tong == 0:
            continue
        bc1 = tap["bc1_theo_khoa"].get(ma_kh)
        out.append({
            "ma_kh": ma_kh, "ten_kh": k["ten_kh"], "ngay_bg": k["bg"], "khoa_cu": k["bg"] < moc,
            "co_bc1": bc1 is not None, "so_bc1": bc1["so_bao_cao"] if bc1 else "",
            "bc2_cua_khoa": tap["bc2_theo_bc1"].get(bc1["ma_bci"], []) if bc1 else [],
            "san_sang": dem_san.get(ma_kh, 0), "can_xem": dem_xem.get(ma_kh, 0),
            "thi_lai": thi_trong, "thi_lai_cua_khoa": dem_thi_cua.get(ma_kh, 0),
        })
    out.sort(key=lambda x: x["ngay_bg"], reverse=True)
    return {"loai": loai, "hom_nay": tap["hom_nay"], "thi_lai_thang": thi_lai_thang,
            "thi_lai_tat_ca": thi_tat_ca, "khoa": out}


def ung_vien(tap: dict, khoa_chon: dict, ma_bc2: str = "", thi_lai_thang: int = rules.THI_LAI_THANG_MAC_DINH,
             khong_duoc_them: list[dict] | None = None) -> dict:
    """Bước ②: bốn nhóm HV cho khóa `khoa_chon` ({ma_kh, ten_kh, loai, bg}).

    `khong_duoc_them` = HV của khóa ở trạng thái ngoài tập của SP (`11/13/16/19` và trạng thái lạ
    `01/02/04/10/12`…) — SP không trả họ, nên đọc thêm để giải thích vì sao không thêm được /
    cho "Cứu trạng thái" ngay trên dòng; cắt trần `TOI_DA_KHONG_DUOC` cho nhóm Không đưa được.
    """
    loai, ma_kh = khoa_chon["loai"], khoa_chon["ma_kh"]
    ctx = _ctx(tap, ma_kh, ma_bc2)
    nhom: dict[str, list] = {rules.SAN_SANG: [], rules.THI_LAI: [], rules.CAN_XEM: [], rules.KHONG_DUOC: []}
    for hv in list(tap["hvs"]) + list(khong_duoc_them or []):
        n = rules.phan_nhom(hv, loai, ctx, thi_lai_thang)
        if n is None:
            continue
        if n["nhom"] == rules.KHONG_DUOC and hv["ma_kh"] != ma_kh:
            continue   # "Không đưa được" chỉ nói về học viên của khóa đang chọn (HV khóa khác không liên quan)
        nhom[n["nhom"]].append(_muc_hv(hv, n))
    tong_khong = len(nhom[rules.KHONG_DUOC])
    nhom[rules.KHONG_DUOC] = nhom[rules.KHONG_DUOC][:TOI_DA_KHONG_DUOC]
    thi_lai = nhom[rules.THI_LAI]
    bc1 = tap["bc1_theo_khoa"].get(ma_kh)
    return {
        "ma_kh": ma_kh, "ten_kh": khoa_chon["ten_kh"], "loai": loai, "hom_nay": tap["hom_nay"],
        "thi_lai_thang": thi_lai_thang, "ma_bc2": ma_bc2,
        "bc1": ({"ma_bci": bc1["ma_bci"], "so_bao_cao": bc1["so_bao_cao"], "so_hoc_sinh": bc1["so_hoc_sinh"]}
                if bc1 else None),
        "bc2_cua_khoa": tap["bc2_theo_bc1"].get(bc1["ma_bci"], []) if bc1 else [],
        "nhom": nhom,
        "dem": {"san_sang": len(nhom[rules.SAN_SANG]), "thi_lai": len(thi_lai),
                "thi_lai_trong_nguong": sum(1 for x in thi_lai if x["trong_nguong"]),
                "can_xem": len(nhom[rules.CAN_XEM]), "khong_duoc": tong_khong},
    }


def doc_ngoai_tap_cua_khoa(cur, ma_kh: str) -> list[dict]:
    """HV của khóa có `TT_XuLy` ngoài `{03,09,14,17,18}` (SP không trả): `11/13/16/19` → Không đưa
    được; trạng thái lạ (`01/02/04/10/12`…) → Cần xem kèm gợi ý Cứu trạng thái."""
    cur.execute(_Q_KHONG_DUOC, (ma_kh,))
    out = []
    for r in cur.fetchall():
        out.append({
            "ma_dk": _s(r["MaDK"]), "so_ho_so": _s(r.get("SoHoSo")), "ten": _s(r.get("HoVaTen")),
            "ngay_sinh": _ngay_sinh_vn(r.get("NgaySinh")), "cmt": _s(r.get("SoCMT")),
            "so_giay": _s(r.get("SoGiayCNTN")), "hang": _s(r.get("HangGPLX")), "ma_kh": _s(r.get("MaKhoaHoc")),
            "ten_kh": _s(r.get("TenKH")), "tt": _s(r.get("TT_XuLy")), "ma_bc2": _s(r.get("MaBC2")),
            "bg": _ngay_iso(r.get("NgayBG")),
        })
    return out


def khop_danh_sach(tap: dict, khoa_chon: dict, dong: Iterable[str], ma_bc2: str = "",
                   khong_duoc_them: list[dict] | None = None) -> dict:
    """Dán danh sách CMT / mã đăng ký → HV tương ứng. Chỉ HV thuộc `san_sang`/`thi_lai` là
    "khop" (được tích); khớp nhưng ở nhóm khác → `khong_dua_duoc` kèm lý do; còn lại `khong_khop`."""
    vde = rules.kiem_danh_sach_dan(dong)
    if vde:
        raise LoiNghiepVu(vde[0]["ma"], vde[0]["noi_dung"], 400)
    loai, ma_kh = khoa_chon["loai"], khoa_chon["ma_kh"]
    ctx = _ctx(tap, ma_kh, ma_bc2)
    tat_ca = list(tap["hvs"]) + list(khong_duoc_them or [])
    theo_cmt: dict[str, list[dict]] = {}
    theo_ma: dict[str, dict] = {}
    for hv in tat_ca:
        theo_ma[hv["ma_dk"].casefold()] = hv
        if hv["cmt"]:
            theo_cmt.setdefault(hv["cmt"].casefold(), []).append(hv)
    khop, khong_dua_duoc, khong_khop = [], [], []
    da_lay: set[str] = set()
    ds = [_s(x) for x in dong if _s(x)]
    for d in ds:
        key = d.casefold()
        ung = theo_cmt.get(key) or ([theo_ma[key]] if key in theo_ma else [])
        if not ung:
            khong_khop.append(d)
            continue
        for hv in ung:
            if hv["ma_dk"] in da_lay:
                continue
            da_lay.add(hv["ma_dk"])
            n = rules.phan_nhom(hv, loai, ctx)
            if n is not None and n["nhom"] in (rules.SAN_SANG, rules.THI_LAI):
                khop.append({"dong": d, **_muc_hv(hv, n)})
            else:
                g = rules.giai_thich_khong_hien(hv, loai, ctx)
                khong_dua_duoc.append({"dong": d, "ma_dk": hv["ma_dk"], "ten": hv["ten"], "cmt": hv["cmt"],
                                       "ma_ly_do": g["ma"], "ly_do": g["noi_dung"],
                                       "goi_y_xu_ly": g.get("goi_y_xu_ly")})
    return {"ma_kh": ma_kh, "tong_dong": len(ds), "so_khop": len(khop), "khop": khop,
            "khong_dua_duoc": khong_dua_duoc, "khong_khop": khong_khop}
