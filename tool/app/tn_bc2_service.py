"""Tốt nghiệp & Báo cáo 2 (TNB, task 97) — ĐỌC DB Nạp `GPLX_CSDT` cho "Lập BC2 / Thêm HV".

ĐỌC (task 97): một lần `EXEC usp_NguoiLX_HoSo_ThemHS_BC2` (cả CSĐT, `@MaKH=''`) + vài `SELECT`
bổ sung; phân nhóm bằng `tn_bc2_rules` (luật thuần).
GHI (task 98+): chỉ qua SP có sẵn, trong khóa chung `tnbc2_ghi`, luôn đọc lại trước khi ghi.
TDD §11F.4 (v6.8): SP lọc khóa bằng `LIKE '%'+@MaKH+'%'` và KHÔNG trả `TT_XuLy`/`MaBC2`/hạng/
`NgayBG` → gọi một lần cho cả CSĐT rồi bổ sung cột; đo 11/10/2026 ≈ 3.450 HV trong 0,07–0,12 giây.
"""
from __future__ import annotations

import calendar
import threading
import time
from contextlib import contextmanager
from datetime import date, datetime
from typing import Any, Callable, Iterable

from app import tn_bc2_nhat_ky as nhat_ky
from app import tn_bc2_rules as rules

TEN_KHOA_GHI = "tnbc2_ghi"       # sp_getapplock chung cho MỌI thao tác ghi của phân hệ (TDD §11F.0)
CHO_KHOA_GHI_MS = 15000

CACHE_GIAY = 30
TOI_DA_KHONG_DUOC = 500          # trần số dòng "Không đưa được" của khóa chọn, trả về một lần
_KHOI_IN = 900                   # pymssql: tối đa ~2100 tham số → chia khối

_Q_BC1 = "SELECT MaBCI, MaKH, MaCSDT, SoBaoCao, NgayBaoCao, SoHocSinh FROM BaoCaoI"
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

    def __init__(self, ma: str, noi_dung: str, http: int = 400, du_lieu: dict | None = None):
        super().__init__(noi_dung)
        self.ma, self.noi_dung, self.http, self.du_lieu = ma, noi_dung, http, du_lieu


# ── Tiện ích ──
def _tt_ngoac(tt: str | None, loai: str = "oto") -> str:
    """"Đã vào BC2, chờ kết quả (11)" — tên nghiệp vụ trước, mã chỉ là chú thích trong ngoặc (dòng nhật ký, thông báo)."""
    t = (tt or "").strip() if isinstance(tt, str) or tt is None else str(tt).strip()
    return f"{rules.ten_trang_thai(t, loai)} ({t})" if t else rules.ten_trang_thai(t, loai)


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


_cuu_cache: dict[str, tuple[float, list[dict]]] = {}


def bo_cache() -> None:
    """"Làm tươi" / sau mỗi lần ghi."""
    with _khoa_cache:
        _cache.clear()
        _cuu_cache.clear()


def doc_bc(cur) -> tuple[dict, dict, dict, dict]:
    """Đọc BC1 + BC2 hiện có: (bc1_theo_khoa, bc2_map, bc2_bci, bc2_theo_bc1). Không cache."""
    cur.execute(_Q_BC1)
    bc1_theo_khoa = {_s(r["MaKH"]): {"ma_bci": _s(r["MaBCI"]), "ma_csdt": _s(r.get("MaCSDT")),
                                     "so_bao_cao": _s(r["SoBaoCao"]), "so_hoc_sinh": r.get("SoHocSinh"),
                                     "ngay_bao_cao": _ngay_iso(r.get("NgayBaoCao"))}
                     for r in cur.fetchall()}
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
    return bc1_theo_khoa, bc2_map, bc2_bci, bc2_theo_bc1


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

    bc1_theo_khoa, bc2_map, bc2_bci, bc2_theo_bc1 = doc_bc(cur)
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
        "bc1": ({"ma_bci": bc1["ma_bci"], "so_bao_cao": bc1["so_bao_cao"], "so_hoc_sinh": bc1["so_hoc_sinh"],
                 "ngay_bao_cao": bc1.get("ngay_bao_cao", "")}
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


# ══════════════════════════ GHI (task 98+) ══════════════════════════
@contextmanager
def khoa_ghi(conn, cho_ms: int = CHO_KHOA_GHI_MS):
    """Khóa ghi chung `tnbc2_ghi` (sp_getapplock, mức Session) cho MỌI thao tác ghi của phân hệ.

    Khóa theo BC2 / khóa học KHÔNG đủ: hai BC2 cùng ghi một HV không loại trừ nhau. Hết hạn chờ →
    409 `dang_ghi` (không ghi gì). Luôn nhả ở `finally`; đóng kết nối cũng tự nhả."""
    cur = conn.cursor(as_dict=True)
    cur.execute("DECLARE @r INT; EXEC @r = sp_getapplock @Resource=%s, @LockMode='Exclusive', "
                "@LockOwner='Session', @LockTimeout=%s; SELECT @r AS r", (TEN_KHOA_GHI, cho_ms))
    r = cur.fetchone() or {}
    if r.get("r") is None or int(r["r"]) < 0:
        raise LoiNghiepVu("dang_ghi", "Đang có thao tác ghi khác của phân hệ này — đợi xong rồi thử lại.", 409)
    try:
        yield cur
    finally:
        try:
            cur.execute("EXEC sp_releaseapplock @Resource=%s, @LockOwner='Session'", (TEN_KHOA_GHI,))
        except Exception:  # noqa: BLE001 — kết nối hỏng thì khóa Session tự nhả khi đóng
            pass


def goi_y_so(cur, ma_kh: str, hom_nay: str | None = None) -> dict:
    """Số BC2 gợi ý cho khóa + BC1 + BC2 đã có của BC1 đó (để giao diện cảnh báo). Đọc mới, không cache."""
    hom_nay = hom_nay or hom_nay_iso()
    khoa = loai_cua_khoa(cur, ma_kh)
    bc1_map, bc2_map, _bci, bc2_theo_bc1 = doc_bc(cur)
    bc1 = bc1_map.get(ma_kh)
    so = rules.goi_y_so_bc2(khoa["loai"], list(bc2_map), int(hom_nay[:4]), bc1["so_bao_cao"] if bc1 else None)
    return {
        "ma_kh": ma_kh, "ten_kh": khoa["ten_kh"], "loai": khoa["loai"], "nam": int(hom_nay[:4]), "so": so,
        "co_bc1": bc1 is not None,
        "bc1": ({"ma_bci": bc1["ma_bci"], "so_bao_cao": bc1["so_bao_cao"], "so_hoc_sinh": bc1["so_hoc_sinh"],
                 "ngay_bao_cao": bc1.get("ngay_bao_cao", "")}
                if bc1 else None),
        "bc2_cua_khoa": bc2_theo_bc1.get(bc1["ma_bci"], []) if bc1 else [],
        "trung": rules.khoa_so_bc2(so) in {rules.khoa_so_bc2(m) for m in bc2_map} if so else False,
    }


def _loi_trung_so(e: Exception) -> bool:
    t = str(e)
    return "2627" in t or "PRIMARY KEY" in t.upper() or "duplicate key" in t.lower()


def _luu_loi_lo(lo_id: str, trang_thai: str, loi: dict) -> dict | None:
    """Ghi lỗi của một lần chạy vào lô. Nếu LẦN CHẠY TRƯỚC của cùng `lo_id` đã ghi được một phần
    (`da_them`/`da_go`/`da_ghi`) thì GIỮ danh sách đó (chỉ thêm `loi_lan_cuoi`) — "Làm tiếp" bị 409 không được
    làm mất thông tin đã/chưa ghi. Trả kết quả đã gộp nếu có ghi từ trước, ngược lại None."""
    cu = (nhat_ky.lo_lay(lo_id) or {}).get("ket_qua") or {}
    if any(cu.get(k) for k in ("da_them", "da_go", "da_ghi", "da_huy")):
        gop = {**cu, "loi_lan_cuoi": loi}
        nhat_ky.lo_cap_nhat(lo_id, trang_thai="loi_giua_chung", ket_qua=gop)
        return gop
    nhat_ky.lo_cap_nhat(lo_id, trang_thai=trang_thai, ket_qua={"loi": loi.get("noi_dung") or loi.get("loi") or ""}
                        if "loi_nghiep_vu" not in loi else loi)
    return None


_Q_HV_LAI = ("SELECT h.MaDK, h.SoHoSo, h.TT_XuLy, h.TT_XuLy_Old, h.MaBC2, h.HangGPLX, h.SoGiayCNTN, h.MaKhoaHoc, "
             "k.TenKH, k.NgayBG FROM NguoiLX_HoSo h JOIN KhoaHoc k ON k.MaKH = h.MaKhoaHoc WHERE h.MaDK IN ({ph})")
_Q_HV_MOT = "SELECT TT_XuLy, TT_XuLy_Old, MaBC2, SoHoSo FROM NguoiLX_HoSo WHERE MaDK = %s"


def _kiem_dau_vao_tao(so: str, ghi_chu: str, nguoi: str, ngay_bao_cao: str, hom_nay: str) -> datetime:
    """Kiểm đầu vào tạo BC2 không cần DB; trả ngày báo cáo (00:00)."""
    vde = (rules.kiem_do_dai("so_bao_cao", so) + rules.kiem_do_dai("ghi_chu", ghi_chu)
           + rules.kiem_do_dai("nguoi_tao", nguoi))
    if not so:
        vde.append({"muc": rules.CHAN, "ma": "thieu_so", "ref": "", "noi_dung": "Cần nhập số báo cáo"})
    elif len(so) > rules.DO_DAI_COT["ma_bcii"]:
        vde.append({"muc": rules.CHAN, "ma": "so_qua_dai", "ref": "",
                    "noi_dung": f"Số báo cáo tối đa {rules.DO_DAI_COT['ma_bcii']} ký tự"})
    if vde:
        raise LoiNghiepVu(vde[0]["ma"], vde[0]["noi_dung"], 400)
    try:
        return datetime.strptime((ngay_bao_cao or hom_nay)[:10], "%Y-%m-%d")
    except ValueError:
        raise LoiNghiepVu("ngay_khong_hop_le", "Ngày báo cáo không hợp lệ (dd/mm/yyyy)", 400)


def _tao_bc2_trong_khoa(cur, ma_kh: str, so: str, ngay: datetime, ghi_chu: str, nguoi: str, *,
                        da_xem_canh_bao: bool, tong_so_thi_sinh: int | None, thu_lai: bool,
                        now: datetime | None, lo_id: str = "", yeu_cau_mo: bool = False) -> dict:
    """Lõi tạo BC2 — CHỈ gọi khi đã giữ `khoa_ghi` (dùng chung cho `tao_bc2` và `lap_bc2`)."""
    khoa = loai_cua_khoa(cur, ma_kh)
    bc1_map, bc2_map, bc2_bci, bc2_theo_bc1 = doc_bc(cur)
    bc1 = bc1_map.get(ma_kh)
    if bc1 is None:
        raise LoiNghiepVu("khoa_chua_co_bc1", f"Khóa {ma_kh} chưa có BC1 — chưa lập BC2 được", 409)
    ma_bcii = rules.dang_luu_ma_bcii(so)   # dạng DB (varchar): Đ → Ð
    # trùng số / thử lại sau khi mất kết nối
    co = next((m for m in bc2_map if rules.khoa_so_bc2(m) == rules.khoa_so_bc2(so)), None)
    if co is not None:
        if thu_lai and bc2_bci.get(co) == bc1["ma_bci"]:
            if yeu_cau_mo and bc2_map.get(co) != 0:      # lập + thêm HV: BC2 phải còn MỞ (⛔ thêm vào BC2 đã đóng)
                raise LoiNghiepVu("bc2_da_dong", f"BC2 số {co} đã đóng — không thêm học viên được", 409)
            nhat_ky.ket_thuc(nhat_ky.bat_dau(nguoi, nhat_ky.TAO_BC2, ma_kh, co, 0, f"BC2 {co} đã có"), "da_ton_tai",
                             {"ma_bc2": co})
            return {"ma_bc2": co, "da_ton_tai": True, "ma_kh": ma_kh, "loai": khoa["loai"],
                    "ma_bci": bc1["ma_bci"], "canh_bao": []}
        raise LoiNghiepVu("trung_so", f"Số BC2 {so} đã tồn tại — đổi số khác", 409)
    # cảnh báo: khóa mô tô đã có BC2 (1 khóa = 1 BC1 = 1 BC2)
    canh_bao = []
    if khoa["loai"] == "moto" and bc2_theo_bc1.get(bc1["ma_bci"]):
        so_da_co = ", ".join(b["ma"] for b in bc2_theo_bc1[bc1["ma_bci"]])
        canh_bao.append({"ma": "bc1_da_co_bc2_moto", "noi_dung": f"Khóa này đã có BC2 số {so_da_co}"})
    if canh_bao and not da_xem_canh_bao:
        raise LoiNghiepVu("can_xac_nhan_canh_bao", canh_bao[0]["noi_dung"], 409, {"canh_bao": canh_bao})
    # tổng thí sinh đúng PM cũ (không đếm lại về sau)
    if khoa["loai"] == "moto":
        tong = int(bc1["so_hoc_sinh"] or 0)              # mô tô: luôn = SoHocSinh của BC1 (PRD TNB-03)
    else:
        tong = int(tong_so_thi_sinh or 0)
    # GHI — nhật ký trước, SP có sẵn
    nk = nhat_ky.bat_dau(nguoi, nhat_ky.TAO_BC2, ma_kh, ma_bcii, 0, f"Tạo BC2 {so}",
                         {"so_bao_cao": so, "ma_bci": bc1["ma_bci"], "tong_so_thi_sinh": tong}, lo_id=lo_id)
    luc = now or datetime.now()
    try:
        cur.execute("EXEC usp_BaoCaoII_Insert %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s",
                    (ma_bcii, bc1["ma_bci"], bc1["ma_csdt"], so, ngay, tong, _s(ghi_chu) or None, 0,
                     _s(nguoi), None, luc, luc))
    except Exception as e:  # noqa: BLE001
        nhat_ky.ket_thuc(nk, "that_bai", {"loi": str(e)[:200]})
        if _loi_trung_so(e):
            raise LoiNghiepVu("trung_so", f"Số BC2 {so} đã tồn tại — đổi số khác", 409)
        raise
    try:   # SP đã chạy: lỗi ở bước đọc lại KHÔNG có nghĩa là chưa ghi → loi_giua_chung
        cur.execute("SELECT MaBCII, MaBCI, TrangThai, TongSoThiSinh FROM BaoCaoII WHERE MaBCII = %s", (ma_bcii,))
        dong = cur.fetchone()
    except Exception as e:  # noqa: BLE001
        bo_cache()
        nhat_ky.ket_thuc(nk, "loi_giua_chung", {"loi": str(e)[:200], "ghi_chu": "đã gọi SP, chưa đọc lại được"})
        raise
    if not dong or _s(dong.get("MaBCI")) != bc1["ma_bci"]:
        bo_cache()
        nhat_ky.ket_thuc(nk, "loi_giua_chung", {"loi": "không thấy dòng vừa tạo"})
        raise RuntimeError("Tạo BC2 không thấy dòng vừa ghi — kiểm lại ở danh sách BC2")
    bo_cache()
    nhat_ky.ket_thuc(nk, "xong", {"ma_bc2": ma_bcii, "tong_so_thi_sinh": tong})
    return {"ma_bc2": _s(dong["MaBCII"]), "da_ton_tai": False, "ma_kh": ma_kh, "loai": khoa["loai"],
            "ma_bci": bc1["ma_bci"], "so_bao_cao": so, "ngay_bao_cao": ngay.strftime("%Y-%m-%d"),
            "tong_so_thi_sinh": tong, "trang_thai": 0, "canh_bao": canh_bao}


def tao_bc2(conn, ma_kh: str, so_bao_cao: str, ngay_bao_cao: str, ghi_chu: str, nguoi: str, *,
            da_xem_canh_bao: bool = False, tong_so_thi_sinh: int | None = None, thu_lai: bool = False,
            hom_nay: str | None = None, now: datetime | None = None) -> dict:
    """Tạo BC2 (`usp_BaoCaoII_Insert`, `TrangThai=0` = đang mở), đúng như PM cũ ghi.

    PM cũ: `MaBCII = SoBaoCao`, `NgayBaoCao` 00:00, `GhiChu`/`NguoiSua` NULL, `NgayTao = NgaySua`,
    `MaCSDT` lấy từ BC1. `TongSoThiSinh`: mô tô LUÔN = `BaoCaoI.SoHocSinh`; ô tô = 0 (BC2 rỗng) hoặc
    số HV lúc lập do `/bc2/lap` truyền vào. Đọc lại mọi thứ TRONG khóa ghi.
    Trùng số = chặn (PRD TNB-03). Chỉ khi client báo `thu_lai=True` (gửi lại sau khi không biết
    kết quả lần trước, vd mất kết nối) mà BC2 đó đã có đúng BC1 này thì coi là đã tạo xong
    (`da_ton_tai`) — chống tạo đôi (TDD §11F.3) mà không biến lỗi gõ trùng thành thành công.
    """
    hom_nay = hom_nay or hom_nay_iso()
    so = _s(so_bao_cao)
    ngay = _kiem_dau_vao_tao(so, ghi_chu, nguoi, ngay_bao_cao, hom_nay)
    with khoa_ghi(conn) as cur:
        return _tao_bc2_trong_khoa(cur, ma_kh, so, ngay, ghi_chu, nguoi, da_xem_canh_bao=da_xem_canh_bao,
                                   tong_so_thi_sinh=tong_so_thi_sinh, thu_lai=thu_lai, now=now)


# ── Lập BC2 + thêm HV (TNB-04, task 99) ──
def _doc_hv_lai(cur, ma_dks: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for khoi in _chia(ma_dks, _KHOI_IN):
        cur.execute(_Q_HV_LAI.format(ph=",".join(["%s"] * len(khoi))), tuple(khoi))
        for r in cur.fetchall():
            out[_s(r["MaDK"])] = {
                "ma_dk": _s(r["MaDK"]), "so_ho_so": _s(r.get("SoHoSo")), "tt": _s(r.get("TT_XuLy")),
                "tt_cu": _s(r.get("TT_XuLy_Old")), "ma_bc2": _s(r.get("MaBC2")), "hang": _s(r.get("HangGPLX")),
                "so_giay": _s(r.get("SoGiayCNTN")), "ma_kh": _s(r.get("MaKhoaHoc")), "ten_kh": _s(r.get("TenKH")),
                "bg": _ngay_iso(r.get("NgayBG")), "ten": "", "cmt": "",
            }
    return out


def _doc_mot_hv(cur, ma_dk: str) -> dict | None:
    cur.execute(_Q_HV_MOT, (ma_dk,))
    r = cur.fetchone()
    if not r:
        return None
    return {"tt": _s(r.get("TT_XuLy")), "tt_cu": _s(r.get("TT_XuLy_Old")), "ma_bc2": _s(r.get("MaBC2")),
            "so_ho_so": _s(r.get("SoHoSo"))}


def _chuan_ds(ds: Iterable[str]) -> list[str]:
    seen, out = set(), []
    for x in ds:
        t = _s(x)
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def lap_bc2(conn, *, lo_id: str, ma_kh: str, ma_bc2: str = "", so_bao_cao: str = "", ngay_bao_cao: str = "",
            ghi_chu: str = "", ds_ma_dk: Iterable[str], nguoi: str, da_xem_canh_bao: bool = False,
            hom_nay: str | None = None, now: datetime | None = None,
            bao_tien_do: Callable[[int, int], None] | None = None) -> dict:
    """"Lập BC2 và thêm N học viên" (TDD §11F.4 v6.8). Trong MỘT khóa ghi `tnbc2_ghi`:

    đọc lại cả lô → phân nhóm lại (chỉ `san_sang`/`thi_lai`) → BC2 có sẵn: phải còn MỞ; chưa có: tạo
    với `TongSoThiSinh` = số HV còn lại → từng HV: đọc lại sát trước SP, `usp_NguoiLX_Update_ThemHSBC2`,
    đọc lại sau (cảnh báo `TT_XuLy_Old='11'`), GHI NHẬT KÝ NGAY. HV đã `11` đúng BC2 này (lần chạy trước
    đứt giữa chừng) tính "đã có từ trước" — KHÔNG gọi lại SP (gọi lại sẽ đặt `TT_XuLy_Old='11'`).
    Lỗi DB giữa chừng → trả đã/chưa ghi (`trang_thai='loi_giua_chung'`), "Làm tiếp" = chạy lại cùng `lo_id`.
    """
    hom_nay = hom_nay or hom_nay_iso()
    ds = _chuan_ds(ds_ma_dk)
    vde = rules.kiem_danh_sach_dan(ds)
    if vde:
        raise LoiNghiepVu(vde[0]["ma"], vde[0]["noi_dung"], 400)
    if not ds:
        raise LoiNghiepVu("khong_co_hoc_vien", "Chưa chọn học viên nào để thêm", 400)
    so = _s(so_bao_cao)
    ngay = None if ma_bc2 else _kiem_dau_vao_tao(so, ghi_chu, nguoi, ngay_bao_cao, hom_nay)
    dang_db = rules.dang_luu_ma_bcii(ma_bc2) if ma_bc2 else ""

    with khoa_ghi(conn) as cur:
        khoa = loai_cua_khoa(cur, ma_kh)
        loai = khoa["loai"]
        bc1_map, bc2_map, bc2_bci, _theo = doc_bc(cur)
        truoc = nhat_ky.lo_lay(lo_id)                      # "Làm tiếp": lô cũ đã tạo BC2 rồi → dùng lại
        if not dang_db and truoc and truoc.get("ma_bc2"):
            dang_db = truoc["ma_bc2"]
        kiem_dau_vao({"bc1_theo_khoa": bc1_map, "bc2_map": bc2_map, "bc2_bci": bc2_bci}, ma_kh, dang_db)
        nhat_ky.lo_bat_dau(lo_id, nguoi, nhat_ky.LO_LAP, ma_kh, dang_db, len(ds))
        nk = nhat_ky.bat_dau(nguoi, nhat_ky.THEM_HV, ma_kh, dang_db, len(ds), f"Thêm {len(ds)} HV", {"ma_dk": ds},
                             lo_id=lo_id)
        try:
            return _lap_trong_khoa(cur, nk=nk, lo_id=lo_id, ma_kh=ma_kh, dang_db=dang_db, loai=loai, ds=ds, so=so,
                                   ngay=ngay, ghi_chu=ghi_chu, nguoi=nguoi, da_xem_canh_bao=da_xem_canh_bao,
                                   hom_nay=hom_nay, now=now, bc2_map=bc2_map, bao_tien_do=bao_tien_do,
                                   lo_cu=truoc is not None)
        except Exception as e:  # noqa: BLE001 — đóng nhật ký rồi ném tiếp
            loi = getattr(e, "noi_dung", None) or str(e)
            nhat_ky.ket_thuc(nk, "that_bai", {"loi": loi[:200]})
            _luu_loi_lo(lo_id, "that_bai", {"loi": loi[:200]})
            raise


def _lap_trong_khoa(cur, *, nk, lo_id, ma_kh, dang_db, loai, ds, so, ngay, ghi_chu, nguoi, da_xem_canh_bao,
                    hom_nay, now, bc2_map, bao_tien_do, lo_cu: bool = False) -> dict:
    """Thân của `lap_bc2` (đã giữ khóa ghi): đọc lại → phân nhóm → BC2 → từng HV."""
    da_xong = {h["ma_dk"]: h["ket_qua"] for h in nhat_ky.lo_hv(lo_id)}   # lần chạy trước (Làm tiếp)

    # 1) đọc lại cả lô + phân nhóm lại
    hvs = _doc_hv_lai(cur, ds)
    ctx = {"hom_nay": hom_nay, "ma_kh_chon": ma_kh, "bc2_map": bc2_map, "ma_bc2_dang_them": dang_db}
    du_dieu_kien, da_co, bo_qua = [], [], []
    for ma_dk in ds:
        hv = hvs.get(ma_dk)
        if hv is None:
            bo_qua.append({"ma_dk": ma_dk, "ma_ly_do": "hv_khong_ton_tai", "ly_do": "Không còn học viên này"})
            continue
        if dang_db and hv["tt"] == rules.TT_DA_VAO_BC2 and hv["ma_bc2"] == dang_db:
            da_co.append(ma_dk)                       # đã ở đúng BC2 này (Làm tiếp / PM cũ vừa thêm)
            continue
        n = rules.phan_nhom(hv, loai, ctx)
        if n is not None and n["nhom"] in (rules.SAN_SANG, rules.THI_LAI):
            du_dieu_kien.append(hv)
        else:
            g = rules.giai_thich_khong_hien(hv, loai, ctx)
            bo_qua.append({"ma_dk": ma_dk, "ma_ly_do": g["ma"], "ly_do": g["noi_dung"]})
    if not du_dieu_kien and not da_co and not dang_db:
        nhat_ky.ket_thuc(nk, "that_bai", {"loi": "không có học viên hợp lệ", "bo_qua": len(bo_qua)})
        raise LoiNghiepVu("khong_co_hoc_vien_hop_le", "Không còn học viên nào thêm được — làm tươi danh sách", 409,
                          {"bo_qua": bo_qua})

    # 2) BC2: có sẵn (đã kiểm còn mở ở trên) hoặc tạo mới
    da_tao = False
    if not dang_db:
        tao = _tao_bc2_trong_khoa(cur, ma_kh, so, ngay, ghi_chu, nguoi, da_xem_canh_bao=da_xem_canh_bao,
                                  tong_so_thi_sinh=len(du_dieu_kien), thu_lai=lo_cu, now=now, lo_id=lo_id,
                                  yeu_cau_mo=True)
        dang_db = rules.dang_luu_ma_bcii(tao["ma_bc2"])
        da_tao = not tao["da_ton_tai"]
    nhat_ky.lo_cap_nhat(lo_id, ma_bc2=dang_db)
    for ma_dk in da_co:
        nhat_ky.lo_ghi_hv(lo_id, ma_dk, "da_co_tu_truoc" if da_xong.get(ma_dk) != "da_them" else "da_them")
    for b in bo_qua:
        nhat_ky.lo_ghi_hv(lo_id, b["ma_dk"], "bo_qua", b["ma_ly_do"])

    # 3) từng HV
    da_them, chua_ghi, canh_bao, loi = [], [], [], None
    xu_ly = 0
    for idx, hv in enumerate(du_dieu_kien):
        ma_dk = hv["ma_dk"]
        try:
            moi = _doc_mot_hv(cur, ma_dk)                 # đọc lại SÁT trước SP
            if moi is None or moi["tt"] != hv["tt"] or moi["ma_bc2"] != hv["ma_bc2"]:
                bo_qua.append({"ma_dk": ma_dk, "ma_ly_do": "doi_giua_chung",
                               "ly_do": "Phần mềm cũ vừa đổi học viên này — không ghi đè"})
                nhat_ky.lo_ghi_hv(lo_id, ma_dk, "bo_qua", "doi_giua_chung")
                continue
            cur.execute("EXEC usp_NguoiLX_Update_ThemHSBC2 %s,%s,%s", (ma_dk, moi["so_ho_so"][:5], dang_db))
            nhat_ky.lo_ghi_hv(lo_id, ma_dk, "da_them")    # GHI NGAY sau SP thành công (trước mọi lệnh đọc lại)
            da_them.append(ma_dk)
            try:   # đọc lại SAU SP chỉ để cảnh báo — lỗi ở đây KHÔNG làm HV này thành "chưa ghi"
                sau = _doc_mot_hv(cur, ma_dk) or {}
            except Exception:  # noqa: BLE001
                canh_bao.append({"ma_dk": ma_dk, "ma": "khong_doc_lai_duoc",
                                 "noi_dung": "Đã ghi nhưng chưa đọc lại được học viên này — kiểm lại ở danh sách BC2"})
                continue
            if sau.get("tt") != rules.TT_DA_VAO_BC2 or sau.get("ma_bc2") != dang_db:
                canh_bao.append({"ma_dk": ma_dk, "ma": "khong_khop_sau_ghi",
                                 "noi_dung": "Sau khi ghi, trạng thái học viên không như mong đợi — kiểm lại"})
            elif sau.get("tt_cu") == rules.TT_DA_VAO_BC2:
                canh_bao.append({"ma_dk": ma_dk, "ma": "trang_thai_cu_la_11",
                                 "noi_dung": "Trạng thái cũ đang là 'Đã vào BC2' — gỡ ra sẽ không về đúng"})
        except Exception as e:  # noqa: BLE001 — lỗi DB: dừng, báo đã/chưa ghi, cho "Làm tiếp"
            loi = {"ma_dk": ma_dk, "noi_dung": str(e)[:200]}
            chua_ghi = [h["ma_dk"] for h in du_dieu_kien[idx:]]
            for m in chua_ghi:
                nhat_ky.lo_ghi_hv(lo_id, m, "chua_ghi", "loi_db")
            break
        finally:
            xu_ly += 1
            if bao_tien_do:
                bao_tien_do(xu_ly, len(du_dieu_kien))

    bo_cache()
    trang_thai = "loi_giua_chung" if loi else "xong"
    kq = {"lo_id": lo_id, "ma_bc2": dang_db, "da_tao_bc2": da_tao, "loai": loai, "tong": len(ds),
          "da_them": da_them, "da_co_tu_truoc": da_co, "bo_qua": bo_qua, "chua_ghi": chua_ghi,
          "canh_bao": canh_bao, "loi": loi, "trang_thai": trang_thai}
    nhat_ky.lo_cap_nhat(lo_id, trang_thai=trang_thai, ket_qua={k: v for k, v in kq.items() if k != "lo_id"},
                        luc_xong=datetime.now().isoformat(timespec="seconds"))
    nhat_ky.ket_thuc(nk, trang_thai, {"da_them": len(da_them), "bo_qua": len(bo_qua), "chua_ghi": len(chua_ghi)})
    return kq


def hoan_tac(conn, *, ma_bc2: str, lo_id: str, nguoi: str, bao_tien_do: Callable[[int, int], None] | None = None) -> dict:
    """Hoàn tác lần thêm gần nhất của MỘT BC2 (một lần): gỡ đúng các HV mà lô đó đã thêm, chỉ khi còn
    `11` và đúng `MaBC2`, BC2 còn mở. HV PM cũ đã đổi (có kết quả…) → bỏ qua kèm lý do."""
    dang_db = rules.dang_luu_ma_bcii(ma_bc2)
    with khoa_ghi(conn) as cur:
        _b1, bc2_map, _bci, _t = doc_bc(cur)
        tt = bc2_map.get(dang_db, bc2_map.get(ma_bc2))
        if tt is None:
            raise LoiNghiepVu("bc2_khong_ton_tai", f"Không có BC2 số {ma_bc2}", 404)
        if tt != 0:
            raise LoiNghiepVu("bc2_da_dong", f"BC2 số {ma_bc2} đã đóng — không gỡ được", 409)
        goc = nhat_ky.lo_lap_gan_nhat_cua_bc2(dang_db)
        if goc is None:
            raise LoiNghiepVu("khong_co_lo", "Không có lần thêm nào của BC2 này để hoàn tác", 404)
        if goc.get("hoan_tac_boi"):
            raise LoiNghiepVu("da_hoan_tac", "Lần thêm gần nhất của BC2 này đã được hoàn tác", 409)
        nhat_ky.lo_bat_dau(lo_id, nguoi, nhat_ky.LO_HOAN_TAC, goc.get("ma_kh") or "", dang_db, 0, goc["lo_id"])
        ds = [h["ma_dk"] for h in nhat_ky.lo_hv(goc["lo_id"]) if h["ket_qua"] == "da_them"]
        nk = nhat_ky.bat_dau(nguoi, nhat_ky.GO_HV, goc.get("ma_kh") or "", dang_db, len(ds), f"Hoàn tác lô {goc['lo_id']}",
                             {"ma_dk": ds, "lo_goc": goc["lo_id"]}, lo_id=lo_id)
        nhat_ky.lo_cap_nhat(lo_id, tong=len(ds))
        da_go, bo_qua, loi = [], [], None
        for idx, ma_dk in enumerate(ds):
            try:
                hv = _doc_mot_hv(cur, ma_dk)
                if hv is None or hv["tt"] != rules.TT_DA_VAO_BC2 or hv["ma_bc2"] != dang_db:
                    bo_qua.append({"ma_dk": ma_dk, "ma_ly_do": "khong_con_o_bc2",
                                   "ly_do": "Học viên không còn ở BC2 này hoặc đã có kết quả — không gỡ"})
                    nhat_ky.lo_ghi_hv(lo_id, ma_dk, "bo_qua", "khong_con_o_bc2")
                    continue
                if not hv["tt_cu"]:
                    bo_qua.append({"ma_dk": ma_dk, "ma_ly_do": "thieu_trang_thai_cu",
                                   "ly_do": "Không có trạng thái cũ để quay về — gỡ ở màn BC2 và chọn trạng thái"})
                    nhat_ky.lo_ghi_hv(lo_id, ma_dk, "bo_qua", "thieu_trang_thai_cu")
                    continue
                if hv["tt_cu"] == rules.TT_DA_VAO_BC2:      # gỡ ra sẽ là TT_XuLy='11' mà MaBC2='' → HV kẹt
                    bo_qua.append({"ma_dk": ma_dk, "ma_ly_do": "trang_thai_cu_la_11",
                                   "ly_do": "Trạng thái cũ của học viên cũng là 'Đã vào BC2' — gỡ ra sẽ không về đúng, "
                                            "dùng Cứu trạng thái"})
                    nhat_ky.lo_ghi_hv(lo_id, ma_dk, "bo_qua", "trang_thai_cu_la_11")
                    continue
                cur.execute("EXEC usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2 %s,%s,%s,%s",
                            (ma_dk, hv["so_ho_so"][:5], dang_db, 101))
                nhat_ky.lo_ghi_hv(lo_id, ma_dk, "da_go")
                da_go.append(ma_dk)
            except Exception as e:  # noqa: BLE001
                loi = {"ma_dk": ma_dk, "noi_dung": str(e)[:200]}
                break
            finally:
                if bao_tien_do:
                    bao_tien_do(idx + 1, len(ds))
        bo_cache()
        trang_thai = "loi_giua_chung" if loi else "xong"
        if not loi:
            nhat_ky.lo_cap_nhat(goc["lo_id"], hoan_tac_boi=lo_id)
        kq = {"lo_id": lo_id, "lo_goc": goc["lo_id"], "ma_bc2": dang_db, "tong": len(ds), "da_go": da_go,
              "bo_qua": bo_qua, "loi": loi, "trang_thai": trang_thai}
        nhat_ky.lo_cap_nhat(lo_id, trang_thai=trang_thai, ket_qua={k: v for k, v in kq.items() if k != "lo_id"},
                            luc_xong=datetime.now().isoformat(timespec="seconds"))
        nhat_ky.ket_thuc(nk, trang_thai, {"da_go": len(da_go), "bo_qua": len(bo_qua)})
        return kq


# ── Chạy nền + tiến độ ──
_JOBS: dict[str, dict] = {}
_JOBS_KHOA = threading.Lock()
_XONG = ("xong", "loi_giua_chung", "that_bai")


def _tom_tat_job(lo_id: str, j: dict) -> dict:
    d = {"lo_id": lo_id, "trang_thai": j["trang_thai"], "xu_ly": j.get("xu_ly", 0), "tong": j.get("tong", 0),
         "xong": j["trang_thai"] in _XONG}
    d.update(j.get("ket_qua") or {})
    if j.get("loi_nghiep_vu"):
        d["loi_nghiep_vu"] = j["loi_nghiep_vu"]
    return d


def trang_thai_lo(lo_id: str) -> dict | None:
    """Tiến độ của một lô: bộ nhớ (đang chạy) hoặc sqlite (tool đã khởi động lại)."""
    with _JOBS_KHOA:
        j = _JOBS.get(lo_id)
        if j is not None:
            return _tom_tat_job(lo_id, j)
    lo = nhat_ky.lo_lay(lo_id)
    if lo is None:
        return None
    ts = {"lo_id": lo_id, "trang_thai": lo["trang_thai"], "tong": lo["tong"] or 0, "ma_bc2": lo["ma_bc2"],
          "xong": lo["trang_thai"] in _XONG}
    ts.update(lo.get("ket_qua") or {})
    if lo["trang_thai"] == "dang_chay":     # tool chết giữa chừng — có thể "Làm tiếp" bằng cùng lo_id
        hv = nhat_ky.lo_hv(lo_id)
        ts["da_them"] = [h["ma_dk"] for h in hv if h["ket_qua"] == "da_them"]
        ts["da_ghi"] = [{"ma_dk": h["ma_dk"], "ket_qua": h["ma_ly_do"]} for h in hv if h["ket_qua"] == "da_ghi"]
        ts["da_huy"] = [{"ma_dk": h["ma_dk"], "so_giay_cu": h["ma_ly_do"]} for h in hv if h["ket_qua"] == "da_huy"]
        ts["bi_gian_doan"] = True
    return ts


def khoi_chay(lo_id: str, ham: Callable[..., dict], cac_doi_so: dict, cho_ket_noi: Callable, dong_bo: bool = False) -> dict:
    """Chạy `ham(conn, bao_tien_do=..., **cac_doi_so)` ở nền, idempotent theo `lo_id`:
    đang chạy / đã xong → trả trạng thái hiện tại (KHÔNG chạy lần hai); dở dang (tool chết) → chạy lại
    ("Làm tiếp"). `cho_ket_noi` là context manager mở kết nối riêng cho thread."""
    with _JOBS_KHOA:
        j = _JOBS.get(lo_id)
        if j is not None and j["trang_thai"] in ("dang_chay", "xong"):
            return _tom_tat_job(lo_id, j)
    lo = nhat_ky.lo_lay(lo_id)
    if lo is not None and lo["trang_thai"] == "xong":
        return trang_thai_lo(lo_id)
    with _JOBS_KHOA:
        j = _JOBS.get(lo_id)
        if j is not None and j["trang_thai"] == "dang_chay":     # đua hai POST cùng lúc
            return _tom_tat_job(lo_id, j)
        _JOBS[lo_id] = job = {"trang_thai": "dang_chay", "xu_ly": 0, "tong": 0, "ket_qua": None}

    def _tien_do(xu_ly: int, tong: int) -> None:
        job["xu_ly"], job["tong"] = xu_ly, tong

    def _chay() -> None:
        try:
            with cho_ket_noi() as conn:
                kq = ham(conn, bao_tien_do=_tien_do, **cac_doi_so)
            job["ket_qua"] = {k: v for k, v in kq.items() if k != "lo_id"}
            job["trang_thai"] = kq.get("trang_thai", "xong")
        except LoiNghiepVu as e:
            job["loi_nghiep_vu"] = {"ma": e.ma, "noi_dung": e.noi_dung, **(e.du_lieu or {})}
            job["trang_thai"] = "that_bai"
            gop = _luu_loi_lo(lo_id, "that_bai", {"loi_nghiep_vu": job["loi_nghiep_vu"]})
            if gop is not None:          # lần trước đã ghi một phần → giữ danh sách đã ghi cho GET /bc2/lo/{id}
                job["ket_qua"] = {k: v for k, v in gop.items() if k != "lo_id"}
                job["trang_thai"] = "loi_giua_chung"
        except Exception as e:  # noqa: BLE001
            job["loi_nghiep_vu"] = {"ma": "loi_he_thong", "noi_dung": str(e)[:200]}
            job["trang_thai"] = "loi_giua_chung"
            gop = _luu_loi_lo(lo_id, "loi_giua_chung", {"loi_nghiep_vu": job["loi_nghiep_vu"]})
            if gop is not None:
                job["ket_qua"] = {k: v for k, v in gop.items() if k != "lo_id"}

    if dong_bo:
        _chay()
    else:
        threading.Thread(target=_chay, name=f"tnbc2-{lo_id}", daemon=True).start()
    with _JOBS_KHOA:
        return _tom_tat_job(lo_id, job)


def quen_job(lo_id: str) -> None:
    """Chỉ dùng cho test."""
    with _JOBS_KHOA:
        _JOBS.pop(lo_id, None)


# ══════════════ Xem / gỡ / xóa BC2 (TNB-05, task 100) ══════════════
_Q_BC2_MOT = ("SELECT MaBCII, MaBCI, SoBaoCao, NgayBaoCao, TongSoThiSinh, TrangThai, NguoiTao, NgayTao "
              "FROM BaoCaoII WHERE MaBCII = %s")
_Q_HV_CUA_BC2 = ("SELECT h.MaDK, h.SoHoSo, n.HoVaTen, n.NgaySinh, n.SoCMT, h.HangGPLX, h.TT_XuLy, h.TT_XuLy_Old, "
                 "h.MaBC2, h.SoGiayCNTN, h.MaKhoaHoc, k.TenKH, k.NgayBG "
                 "FROM NguoiLX_HoSo h LEFT JOIN NguoiLX n ON n.MaDK = h.MaDK "
                 "LEFT JOIN KhoaHoc k ON k.MaKH = h.MaKhoaHoc "
                 "WHERE h.MaBC2 = %s ORDER BY k.MaKH, n.TenNLX, n.HoDemNLX")
_Q_DEM_HV_BC2 = "SELECT COUNT(*) AS n FROM NguoiLX_HoSo WHERE MaBC2 = %s"


def _doc_bc2_mot(cur, dang_db: str) -> dict | None:
    cur.execute(_Q_BC2_MOT, (dang_db,))
    r = cur.fetchone()
    if not r:
        return None
    return {"ma": _s(r["MaBCII"]), "ma_bci": _s(r["MaBCI"]), "so_bao_cao": _s(r.get("SoBaoCao")),
            "ngay_bao_cao": _ngay_iso(r.get("NgayBaoCao")), "tong_ghi": r.get("TongSoThiSinh"),
            "trang_thai": 1 if r.get("TrangThai") in (1, True, "1") else 0,
            "nguoi_tao": _s(r.get("NguoiTao")), "ngay_tao": _ngay_iso(r.get("NgayTao"))}


def _ly_do_khoa(hv: dict, bc2_dong: bool) -> str:
    if bc2_dong:
        return "BC2 đã đóng — không gỡ được"
    if hv["tt"] == rules.TT_DA_VAO_BC2 and hv["tt_cu"] == rules.TT_DA_VAO_BC2:
        return ("Trạng thái trước đó của học viên cũng là \"Đã vào BC2\" — gỡ ra sẽ không về đúng, "
                "xử lý ở phần mềm cũ")
    if hv["tt"] != rules.TT_DA_VAO_BC2:
        return (f"Đã chuyển sang \"{rules.ten_trang_thai(hv['tt'], hv['loai'])}\" — gỡ khỏi BC2 sẽ làm mất kết quả; "
                "dùng Cứu trạng thái nếu cần")
    return ""


def chi_tiet_bc2(cur, ma_bc2: str) -> dict:
    """Chi tiết một BC2 + danh sách HV (màn xem/gỡ). `go_duoc` = còn `11`, đúng BC2, BC2 còn mở.
    Tìm kiếm / chọn nhiều làm ở giao diện. 404 nếu không có BC2."""
    dang_db = rules.dang_luu_ma_bcii(ma_bc2)
    bc2 = _doc_bc2_mot(cur, dang_db)
    if bc2 is None:
        raise LoiNghiepVu("bc2_khong_ton_tai", f"Không có BC2 số {ma_bc2}", 404)
    bc1_map, _m, _b, _t = doc_bc(cur)
    ma_kh = next((k for k, b in bc1_map.items() if b["ma_bci"] == bc2["ma_bci"]), "")
    khoa = {"ten_kh": "", "loai": ""}
    if ma_kh:
        try:
            khoa = loai_cua_khoa(cur, ma_kh)
        except LoiNghiepVu:
            pass
    dong = bc2["trang_thai"] == 1
    cur.execute(_Q_HV_CUA_BC2, (dang_db,))
    dong_hv = cur.fetchall()
    loai = khoa["loai"] or (rules.loai_hang(dong_hv[0].get("HangGPLX")) if dong_hv else "")
    hocvien = []
    for r in dong_hv:
        hv = {"ma_dk": _s(r["MaDK"]), "so_ho_so": _s(r.get("SoHoSo")), "ten": _s(r.get("HoVaTen")),
              "ngay_sinh": _ngay_sinh_vn(r.get("NgaySinh")), "cmt": _s(r.get("SoCMT")), "hang": _s(r.get("HangGPLX")),
              "tt": _s(r.get("TT_XuLy")), "tt_cu": _s(r.get("TT_XuLy_Old")), "ma_bc2": _s(r.get("MaBC2")),
              "so_giay": _s(r.get("SoGiayCNTN")), "ma_kh": _s(r.get("MaKhoaHoc")), "ten_kh": _s(r.get("TenKH")),
              "bg": _ngay_iso(r.get("NgayBG")), "loai": rules.loai_hang(r.get("HangGPLX"))}
        ly = _ly_do_khoa(hv, dong)
        canh_bao = hv["tt"] == rules.TT_DA_VAO_BC2 and hv["tt_cu"] == ""     # gỡ ra sẽ về giá trị rỗng
        hocvien.append({
            "ma_dk": hv["ma_dk"], "so_ho_so": hv["so_ho_so"], "ten": hv["ten"], "ngay_sinh": hv["ngay_sinh"],
            "cmt": hv["cmt"], "hang": hv["hang"], "ma_kh": hv["ma_kh"], "ten_kh": hv["ten_kh"], "tt": hv["tt"],
            "ten_trang_thai": rules.ten_trang_thai(hv["tt"], hv["loai"]), "tt_cu": hv["tt_cu"],
            "ten_trang_thai_cu": rules.ten_trang_thai(hv["tt_cu"], hv["loai"]) if hv["tt_cu"] else "",
            "go_duoc": not ly, "ly_do_khoa": ly, "canh_bao_tt_cu": canh_bao,
            "khac_khoa_bc1": bool(ma_kh) and hv["ma_kh"] != ma_kh,
        })
    return {
        "ma_bc2": bc2["ma"], "so_bao_cao": bc2["so_bao_cao"], "ngay_bao_cao": bc2["ngay_bao_cao"],
        "trang_thai": bc2["trang_thai"], "dang_mo": not dong, "nguoi_tao": bc2["nguoi_tao"],
        "ngay_tao": bc2["ngay_tao"], "ma_bci": bc2["ma_bci"], "ma_kh": ma_kh, "ten_kh": khoa.get("ten_kh", ""),
        "loai": loai, "tong_ghi": bc2["tong_ghi"], "hv_thuc_te": len(hocvien),
        "lech": bc2["tong_ghi"] is not None and int(bc2["tong_ghi"] or 0) != len(hocvien),
        "hoc_vien": hocvien, "xoa_duoc": (not dong) and len(hocvien) == 0,
    }


def _phan_loai_go(cur, dang_db: str, ds: list[str]) -> tuple[list[dict], list[dict], list[dict]]:
    """Đọc lại các HV muốn gỡ: (gỡ được, bỏ qua kèm lý do, cảnh báo `TT_XuLy_Old` rỗng/`11`)."""
    hvs = _doc_hv_lai(cur, ds)
    ung_vien_go, bo_qua, canh_bao = [], [], []
    for ma_dk in ds:
        hv = hvs.get(ma_dk)
        if hv is None:
            bo_qua.append({"ma_dk": ma_dk, "ma_ly_do": "hv_khong_ton_tai", "ly_do": "Không còn học viên này"})
        elif hv["ma_bc2"] != dang_db:
            bo_qua.append({"ma_dk": ma_dk, "ma_ly_do": "khong_con_o_bc2",
                           "ly_do": "Học viên không còn ở BC2 này (PM cũ vừa đổi)"})
        elif hv["tt"] != rules.TT_DA_VAO_BC2:
            bo_qua.append({"ma_dk": ma_dk, "ma_ly_do": "da_co_ket_qua",
                           "ly_do": f"Đã chuyển sang \"{rules.ten_trang_thai(hv['tt'], rules.loai_hang(hv['hang']))}\" "
                                    "— gỡ khỏi BC2 sẽ làm mất kết quả"})
        elif hv["tt_cu"] == rules.TT_DA_VAO_BC2:
            bo_qua.append({"ma_dk": ma_dk, "ma_ly_do": "trang_thai_cu_la_11",
                           "ly_do": "Trạng thái trước đó cũng là 'Đã vào BC2' — gỡ ra sẽ không về đúng "
                                    "(kẹt 'Đã vào BC2' mà không có BC2), xử lý ở phần mềm cũ"})
        else:
            ung_vien_go.append(hv)
            if not hv["tt_cu"]:
                canh_bao.append({"ma_dk": ma_dk, "ma": "trang_thai_cu_rong",
                                 "noi_dung": "Không có trạng thái cũ để quay về — gỡ ra học viên sẽ về giá trị rỗng"})
    return ung_vien_go, bo_qua, canh_bao


def kiem_truoc_go(cur, ma_bc2: str, ds_ma_dk: Iterable[str], da_xem_canh_bao: bool) -> list[str]:
    """Kiểm nhanh ĐỒNG BỘ (router gọi trước khi chạy nền): BC2 tồn tại + còn mở, danh sách hợp lệ,
    cảnh báo `TT_XuLy_Old` chưa xác nhận → 409. Trả danh sách đã chuẩn hoá."""
    ds = _chuan_ds(ds_ma_dk)
    vde = rules.kiem_danh_sach_dan(ds)
    if vde:
        raise LoiNghiepVu(vde[0]["ma"], vde[0]["noi_dung"], 400)
    if not ds:
        raise LoiNghiepVu("khong_co_hoc_vien", "Chưa chọn học viên nào để gỡ", 400)
    dang_db = rules.dang_luu_ma_bcii(ma_bc2)
    bc2 = _doc_bc2_mot(cur, dang_db)
    if bc2 is None:
        raise LoiNghiepVu("bc2_khong_ton_tai", f"Không có BC2 số {ma_bc2}", 404)
    if bc2["trang_thai"] != 0:
        raise LoiNghiepVu("bc2_da_dong", f"BC2 số {ma_bc2} đã đóng — không gỡ được", 409)
    _g, _b, canh_bao = _phan_loai_go(cur, dang_db, ds)
    if canh_bao and not da_xem_canh_bao:
        raise LoiNghiepVu("can_xac_nhan_canh_bao", canh_bao[0]["noi_dung"], 409, {"canh_bao": canh_bao})
    return ds


def go_hv(conn, *, ma_bc2: str, lo_id: str, ds_ma_dk: Iterable[str], nguoi: str, da_xem_canh_bao: bool = False,
          bao_tien_do: Callable[[int, int], None] | None = None) -> dict:
    """Gỡ HV đã chọn khỏi BC2 đang mở (TNB-05): trong khóa ghi, BC2 phải còn MỞ; đọc lại, chỉ HV còn `11`
    và đúng `MaBC2`; đọc lại SÁT trước SP; `usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2 @TrangThaiXuLy=101`;
    ghi nhật ký từng HV ngay sau SP. `TT_XuLy_Old` rỗng/`11` cần `da_xem_canh_bao`."""
    ds = _chuan_ds(ds_ma_dk)
    vde = rules.kiem_danh_sach_dan(ds)
    if vde:
        raise LoiNghiepVu(vde[0]["ma"], vde[0]["noi_dung"], 400)
    if not ds:
        raise LoiNghiepVu("khong_co_hoc_vien", "Chưa chọn học viên nào để gỡ", 400)
    dang_db = rules.dang_luu_ma_bcii(ma_bc2)
    with khoa_ghi(conn) as cur:
        bc2 = _doc_bc2_mot(cur, dang_db)
        if bc2 is None:
            raise LoiNghiepVu("bc2_khong_ton_tai", f"Không có BC2 số {ma_bc2}", 404)
        if bc2["trang_thai"] != 0:
            raise LoiNghiepVu("bc2_da_dong", f"BC2 số {ma_bc2} đã đóng — không gỡ được", 409)
        da_go_truoc = {h["ma_dk"] for h in nhat_ky.lo_hv(lo_id) if h["ket_qua"] == "da_go"}   # "Làm tiếp"
        ds_moi = [m for m in ds if m not in da_go_truoc]
        ung_vien_go, bo_qua, canh_bao = _phan_loai_go(cur, dang_db, ds_moi)
        if canh_bao and not da_xem_canh_bao:
            raise LoiNghiepVu("can_xac_nhan_canh_bao", canh_bao[0]["noi_dung"], 409, {"canh_bao": canh_bao})
        nhat_ky.lo_bat_dau(lo_id, nguoi, nhat_ky.LO_GO, "", dang_db, len(ds))
        nk = nhat_ky.bat_dau(nguoi, nhat_ky.GO_HV, "", dang_db, len(ds), f"Gỡ {len(ds)} HV khỏi BC2 {ma_bc2}",
                             {"ma_dk": ds}, lo_id=lo_id)
        for b in bo_qua:
            nhat_ky.lo_ghi_hv(lo_id, b["ma_dk"], "bo_qua", b["ma_ly_do"])
        da_go, chua_ghi, loi = sorted(da_go_truoc, key=ds.index), [], None
        for idx, hv in enumerate(ung_vien_go):
            ma_dk = hv["ma_dk"]
            try:
                moi = _doc_mot_hv(cur, ma_dk)                  # đọc lại SÁT trước SP
                if moi is None or moi["tt"] != rules.TT_DA_VAO_BC2 or moi["ma_bc2"] != dang_db:
                    bo_qua.append({"ma_dk": ma_dk, "ma_ly_do": "doi_giua_chung",
                                   "ly_do": "Phần mềm cũ vừa đổi học viên này — không gỡ"})
                    nhat_ky.lo_ghi_hv(lo_id, ma_dk, "bo_qua", "doi_giua_chung")
                    continue
                cur.execute("EXEC usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2 %s,%s,%s,%s",
                            (ma_dk, moi["so_ho_so"][:5], dang_db, 101))
                nhat_ky.lo_ghi_hv(lo_id, ma_dk, "da_go")       # GHI NGAY sau SP thành công
                da_go.append(ma_dk)
            except Exception as e:  # noqa: BLE001 — lỗi DB: dừng, báo đã/chưa gỡ
                loi = {"ma_dk": ma_dk, "noi_dung": str(e)[:200]}
                chua_ghi = [h["ma_dk"] for h in ung_vien_go[idx:]]
                for m in chua_ghi:
                    nhat_ky.lo_ghi_hv(lo_id, m, "chua_ghi", "loi_db")
                break
            finally:
                if bao_tien_do:
                    bao_tien_do(idx + 1, len(ung_vien_go))
        bo_cache()
        trang_thai = "loi_giua_chung" if loi else "xong"
        kq = {"lo_id": lo_id, "ma_bc2": dang_db, "tong": len(ds), "da_go": da_go, "bo_qua": bo_qua,
              "chua_ghi": chua_ghi, "canh_bao": canh_bao, "loi": loi, "trang_thai": trang_thai}
        nhat_ky.lo_cap_nhat(lo_id, trang_thai=trang_thai, ket_qua={k: v for k, v in kq.items() if k != "lo_id"},
                            luc_xong=datetime.now().isoformat(timespec="seconds"))
        nhat_ky.ket_thuc(nk, trang_thai, {"da_go": len(da_go), "bo_qua": len(bo_qua), "chua_ghi": len(chua_ghi)})
        return kq


def xoa_bc2(conn, ma_bc2: str, nguoi: str) -> dict:
    """Xóa một BC2 RỖNG và còn MỞ (`usp_BaoCaoII_Delete`). SP chỉ xóa đúng dòng BC2, không kiểm HV và
    `MaBC2` không có khóa ngoại → phải ĐẾM `MaBC2` (mọi `TT_XuLy`; `TongSoThiSinh` không phải số đếm)
    ngay trước SP, trong khóa ghi. BC2 đã đóng (đã gửi) không xóa ở tool."""
    dang_db = rules.dang_luu_ma_bcii(ma_bc2)
    with khoa_ghi(conn) as cur:
        bc2 = _doc_bc2_mot(cur, dang_db)
        if bc2 is None:
            raise LoiNghiepVu("bc2_khong_ton_tai", f"Không có BC2 số {ma_bc2}", 404)
        if bc2["trang_thai"] != 0:
            raise LoiNghiepVu("bc2_da_dong", f"BC2 số {ma_bc2} đã đóng — không xóa ở tool", 409)
        cur.execute(_Q_DEM_HV_BC2, (dang_db,))
        n = int((cur.fetchone() or {}).get("n") or 0)
        if n > 0:
            raise LoiNghiepVu("con_hoc_vien", f"BC2 số {ma_bc2} còn {n} học viên — gỡ hết trước khi xóa", 409,
                              {"so_hv": n})
        nk = nhat_ky.bat_dau(nguoi, nhat_ky.XOA_BC2, "", dang_db, 0, f"Xóa BC2 {ma_bc2}", {"ma_bc2": dang_db})
        try:
            cur.execute("EXEC usp_BaoCaoII_Delete %s", (dang_db,))
        except Exception as e:  # noqa: BLE001
            nhat_ky.ket_thuc(nk, "that_bai", {"loi": str(e)[:200]})
            raise
        con = _doc_bc2_mot(cur, dang_db)
        bo_cache()
        if con is not None:
            nhat_ky.ket_thuc(nk, "loi_giua_chung", {"loi": "BC2 vẫn còn sau khi xóa"})
            raise RuntimeError("Xóa BC2 không thấy hiệu lực — kiểm lại ở danh sách BC2")
        nhat_ky.ket_thuc(nk, "xong", {"ma_bc2": dang_db})
        return {"ma_bc2": dang_db, "da_xoa": True}


# ══════════════ Tốt nghiệp ô tô — ĐỌC + XEM LẠI (TNB-01, task 101) ══════════════
_Q_KHOA_TN = ("SELECT k.MaKH, k.TenKH, k.HangGPLX, k.NgayKG, k.NgayBG, COUNT(h.MaDK) AS tong, "
              "SUM(CASE WHEN h.TT_XuLy = '03' AND ISNULL(h.MaBC2,'') = '' THEN 1 ELSE 0 END) AS c03, "
              "SUM(CASE WHEN h.TT_XuLy = '09' AND ISNULL(h.MaBC2,'') = '' THEN 1 ELSE 0 END) AS c09, "
              "SUM(CASE WHEN h.TT_XuLy IN ('11','12','13','14','16','17','18','19') OR ISNULL(h.MaBC2,'') <> '' "
              "THEN 1 ELSE 0 END) AS c_bc2 "
              "FROM KhoaHoc k LEFT JOIN NguoiLX_HoSo h ON h.MaKhoaHoc = k.MaKH "
              "GROUP BY k.MaKH, k.TenKH, k.HangGPLX, k.NgayKG, k.NgayBG")
_COT_TN = ("h.MaDK, h.SoHoSo, n.HoVaTen, n.NgaySinh, n.SoCMT, h.HangGPLX, h.TT_XuLy, h.MaBC2, h.MaKhoaHoc, "
           "h.SoGiayCNTN, h.SoSoTN, h.NgayVaoSoTN, h.SoQuyetDinhTN, h.NgayRaQDTN, h.NgayInGiayTN, h.SoCCN")
_Q_HV_TN_KHOA = (f"SELECT {_COT_TN} FROM NguoiLX_HoSo h LEFT JOIN NguoiLX n ON n.MaDK = h.MaDK "
                 "WHERE h.MaKhoaHoc = %s ORDER BY n.TenNLX, n.HoDemNLX")
_Q_HV_TN_IN = (f"SELECT {_COT_TN} FROM NguoiLX_HoSo h LEFT JOIN NguoiLX n ON n.MaDK = h.MaDK "
               "WHERE h.MaDK IN ({ph})")
_Q_SO_GIAY_MOI_NHAT = ("SELECT TOP 1 SoGiayCNTN, NgayInGiayTN FROM NguoiLX_HoSo WHERE SoGiayCNTN LIKE '%|%' "
                       "ORDER BY NgayInGiayTN DESC")
_Q_SO_GIAY_THEO_TIEN_TO = "SELECT SoGiayCNTN, NgayInGiayTN FROM NguoiLX_HoSo WHERE SoGiayCNTN LIKE %s"
_Q_SO_GIAY_TRUNG = ("SELECT MaDK, SoGiayCNTN FROM NguoiLX_HoSo "
                    "WHERE REPLACE(ISNULL(SoGiayCNTN,''), '|', '') IN ({ph})")


def _hv_tn(r: dict) -> dict:
    return {
        "ma_dk": _s(r["MaDK"]), "so_ho_so": _s(r.get("SoHoSo")), "ten": _s(r.get("HoVaTen")),
        "ngay_sinh": _ngay_sinh_vn(r.get("NgaySinh")), "cmt": _s(r.get("SoCMT")), "hang": _s(r.get("HangGPLX")),
        "tt": _s(r.get("TT_XuLy")), "ma_bc2": _s(r.get("MaBC2")), "ma_kh": _s(r.get("MaKhoaHoc")),
        "so_giay": _s(r.get("SoGiayCNTN")), "so_so_tn": _s(r.get("SoSoTN")),
        "ngay_vao_so": _ngay_iso(r.get("NgayVaoSoTN")), "so_quyet_dinh": _s(r.get("SoQuyetDinhTN")),
        "ngay_ra_qd": _ngay_iso(r.get("NgayRaQDTN")), "ngay_in": _ngay_iso(r.get("NgayInGiayTN")),
        "so_ccn": _s(r.get("SoCCN")),
    }


def so_giay_ke_tiep_db(cur) -> str:
    """Số giấy gợi ý kế tiếp (dãy chung toàn cơ sở): tiền tố của số in gần nhất, MAX + 1."""
    cur.execute(_Q_SO_GIAY_MOI_NHAT)
    r = cur.fetchone()
    if not r:
        return ""
    t = rules.tach_so_giay(r.get("SoGiayCNTN"))
    if not t:
        return ""
    cur.execute(_Q_SO_GIAY_THEO_TIEN_TO, (t[0] + "|%",))
    return rules.so_giay_ke_tiep((_s(x["SoGiayCNTN"]), _ngay_iso(x.get("NgayInGiayTN"))) for x in cur.fetchall())


def khoa_tot_nghiep(cur, loai: str = "oto", cu: bool = False, hom_nay: str | None = None) -> dict:
    """Danh sách khóa cho màn Tốt nghiệp: mặc định đã bế giảng từ "hôm nay − 1 tháng − 1 năm"; `cu` = mọi khóa.
    Khóa chưa bế giảng vẫn hiện nhưng `ghi_duoc=False` (chỉ xem)."""
    hom_nay = hom_nay or hom_nay_iso()
    moc = moc_cua_so_khoa(hom_nay)
    cur.execute(_Q_KHOA_TN)
    out = []
    for r in cur.fetchall():
        bg = _ngay_iso(r.get("NgayBG"))
        if rules.loai_hang(r.get("HangGPLX")) != loai or not bg:
            continue
        if not cu and bg < moc:
            continue
        out.append({"ma_kh": _s(r["MaKH"]), "ten_kh": _s(r["TenKH"]), "hang": _s(r.get("HangGPLX")),
                    "ngay_kg": _ngay_iso(r.get("NgayKG")), "ngay_bg": bg, "ghi_duoc": bg <= hom_nay,
                    "khoa_cu": bg < moc, "tong": int(r.get("tong") or 0), "chua_tot_nghiep": int(r.get("c03") or 0),
                    "da_tot_nghiep": int(r.get("c09") or 0), "da_vao_bc2": int(r.get("c_bc2") or 0)})
    out.sort(key=lambda x: x["ngay_bg"], reverse=True)
    return {"loai": loai, "hom_nay": hom_nay, "moc_cua_so": moc, "khoa": out,
            "so_giay_ke_tiep": so_giay_ke_tiep_db(cur)}


def _khoa_oto_hoac_loi(cur, ma_kh: str) -> dict:
    khoa = loai_cua_khoa(cur, ma_kh)
    if khoa["loai"] != "oto":
        raise LoiNghiepVu("chi_o_to", "Mô tô không có bước tốt nghiệp — chỉ khóa ô tô mới cập nhật tốt nghiệp", 400)
    return khoa


def hv_tot_nghiep(cur, ma_kh: str, q: str = "", trang_thai: str = "", hom_nay: str | None = None) -> dict:
    """HV ô tô của một khóa kèm sổ/quyết định/số giấy. `q`: tên không dấu / CMT / mã đăng ký.
    `trang_thai`: `chua_tot_nghiep` | `da_tot_nghiep` | `da_vao_bc2` | '' (tất cả)."""
    hom_nay = hom_nay or hom_nay_iso()
    khoa = _khoa_oto_hoac_loi(cur, ma_kh)
    moc = moc_cua_so_khoa(hom_nay)
    cur.execute(_Q_HV_TN_KHOA, (ma_kh,))
    tat_ca = [_hv_tn(r) for r in cur.fetchall()]
    tat_ca = [h for h in tat_ca if rules.loai_hang(h["hang"]) == "oto"]
    ghi_duoc = bool(khoa["bg"]) and khoa["bg"] <= hom_nay
    khoa_cu = bool(khoa["bg"]) and khoa["bg"] < moc
    tim = rules.bo_dau(q)
    cmt_q = _s(q)
    out = []
    for h in tat_ca:
        ts = rules.trang_thai_tot_nghiep(h["tt"], h["ma_bc2"])
        if trang_thai and ts != trang_thai:
            continue
        if tim and not (tim in rules.bo_dau(h["ten"]) or cmt_q in h["cmt"] or cmt_q.casefold() in h["ma_dk"].casefold()):
            continue
        ly = ""
        if not ghi_duoc:
            ly = "Khóa chưa bế giảng — chỉ xem"
        elif ts == "khac":
            ly = f"Đang ở \"{rules.ten_trang_thai(h['tt'], 'oto')}\" — chưa tới bước tốt nghiệp"
        out.append({**h, "trang_thai_tn": ts, "ten_trang_thai": rules.ten_trang_thai(h["tt"], "oto"),
                    "khoa_cu": khoa_cu, "sua_duoc": not ly and ts in ("chua_tot_nghiep", "da_tot_nghiep", "da_vao_bc2"),
                    "ly_do_khoa": ly})
    # điền sẵn: bộ sổ/QĐ/ngày phổ biến nhất của chính khóa (HV nào đã có sổ)
    dem: dict[tuple, int] = {}
    ngay_in_theo: dict[tuple, dict[str, int]] = {}
    for h in tat_ca:
        if h["so_so_tn"]:
            k = (h["so_so_tn"], h["ngay_vao_so"], h["so_quyet_dinh"], h["ngay_ra_qd"])
            dem[k] = dem.get(k, 0) + 1
            if h["ngay_in"]:
                n = ngay_in_theo.setdefault(k, {})
                n[h["ngay_in"]] = n.get(h["ngay_in"], 0) + 1
    so_chung = None
    if dem:
        k = max(dem, key=dem.get)
        ni = ngay_in_theo.get(k) or {}
        so_chung = {"so_so_tn": k[0], "ngay_vao_so": k[1], "so_quyet_dinh": k[2], "ngay_ra_qd": k[3],
                    "ngay_in": max(ni, key=ni.get) if ni else "", "so_hv": dem[k]}
    return {"ma_kh": ma_kh, "ten_kh": khoa["ten_kh"], "ngay_bg": khoa["bg"], "ghi_duoc": ghi_duoc, "khoa_cu": khoa_cu,
            "so_chung": so_chung, "so_giay_ke_tiep": so_giay_ke_tiep_db(cur), "tong": len(tat_ca),
            "dem": {"chua_tot_nghiep": sum(1 for h in tat_ca if h["tt"] == "03" and not h["ma_bc2"]),
                    "da_tot_nghiep": sum(1 for h in tat_ca if h["tt"] == "09" and not h["ma_bc2"]),
                    "da_vao_bc2": sum(1 for h in tat_ca if rules.trang_thai_tot_nghiep(h["tt"], h["ma_bc2"]) == "da_vao_bc2")},
            "hoc_vien": out}


def _chuan_dong_tn(dong: list[dict]) -> list[dict]:
    ds, seen = [], {}
    for d in dong:
        ma = _s(d.get("ma_dk"))
        if not ma:
            continue
        giay = _s(d.get("so_giay"))
        if ma in seen:
            if seen[ma] != giay:
                raise LoiNghiepVu("dong_trung_hoc_vien",
                                  f"Học viên {ma} xuất hiện hai lần với số giấy khác nhau — chỉ giữ một dòng", 400)
            continue
        seen[ma] = giay
        ds.append({"ma_dk": ma, "so_giay": giay})
    vde = rules.kiem_danh_sach_dan([d["ma_dk"] for d in ds])
    if vde:
        raise LoiNghiepVu(vde[0]["ma"], vde[0]["noi_dung"], 400)
    if not ds:
        raise LoiNghiepVu("khong_co_hoc_vien", "Chưa chọn học viên nào", 400)
    return ds


def _phan_tich_lo(cur, ma_kh: str, khoa: dict, ds: list[dict], chung: dict | None, hom_nay: str) -> tuple[list[dict], dict]:
    """Đọc lại HV + số giấy đang thuộc HV khác rồi chạy `phan_tich_dong_tn` cho cả lô. Dùng chung cho
    CHẠY THỬ (`xem_lai_tot_nghiep`) và GHI (`ghi_tot_nghiep`) → hai bên luôn cùng một luật."""
    hvs: dict[str, dict] = {}
    for khoi in _chia([d["ma_dk"] for d in ds], _KHOI_IN):
        cur.execute(_Q_HV_TN_IN.format(ph=",".join(["%s"] * len(khoi))), tuple(khoi))
        for r in cur.fetchall():
            h = _hv_tn(r)
            hvs[h["ma_dk"]] = {**h, "bg": khoa["bg"]}
    dem_lo: dict[str, int] = {}
    for d in ds:
        if d["so_giay"]:
            k = rules.khoa_so_giay(d["so_giay"])
            dem_lo[k] = dem_lo.get(k, 0) + 1
    trung_lo = {k for k, n in dem_lo.items() if n > 1}
    giu: dict[str, set[str]] = {}
    for khoi in _chia(sorted(dem_lo), _KHOI_IN):
        cur.execute(_Q_SO_GIAY_TRUNG.format(ph=",".join(["%s"] * len(khoi))), tuple(khoi))
        for r in cur.fetchall():
            giu.setdefault(rules.khoa_so_giay(r["SoGiayCNTN"]), set()).add(_s(r["MaDK"]))
    khoa_cu = bool(khoa["bg"]) and khoa["bg"] < moc_cua_so_khoa(hom_nay)
    out = []
    for d in ds:
        hv = hvs.get(d["ma_dk"])
        if hv is None:
            kq = {"ma_dk": d["ma_dk"], "ket_qua": rules.KQ_CHAN, "ghi_duoc": False, "hieu_luc": {},
                  "chan": [{"muc": rules.CHAN, "ma": "hv_khong_ton_tai", "noi_dung": "Không còn học viên này"}],
                  "canh_bao": [], "thong_tin": []}
        elif hv["ma_kh"] != ma_kh:
            kq = {"ma_dk": d["ma_dk"], "ket_qua": rules.KQ_CHAN, "ghi_duoc": False, "hieu_luc": {},
                  "chan": [{"muc": rules.CHAN, "ma": "khac_khoa", "noi_dung": "Học viên không thuộc khóa đang chọn"}],
                  "canh_bao": [], "thong_tin": []}
        else:
            k = rules.khoa_so_giay(d["so_giay"]) if d["so_giay"] else ""
            khac = {k} if k and (giu.get(k, set()) - {d["ma_dk"]}) else set()
            kq = rules.phan_tich_dong_tn(hv, d["so_giay"], chung, {"hom_nay": hom_nay, "so_giay_khac": khac,
                                                                    "trung_lo": trung_lo})
            kq["khoa_cu"] = khoa_cu
            if khoa_cu:
                kq["canh_bao"].append({"muc": rules.CANH_BAO, "ma": "khoa_cu", "noi_dung": "Học viên của khóa cũ"})
        out.append(kq)
    return out, hvs


def _tong_hop_canh_bao(ket_qua: list[dict]) -> list[dict]:
    gop: dict[str, dict] = {}
    for kq in ket_qua:
        for w in kq["canh_bao"]:
            c = gop.setdefault(w["ma"], {"ma": w["ma"], "noi_dung": w["noi_dung"], "so_dong": 0})
            c["so_dong"] += 1
    return list(gop.values())


def xem_lai_tot_nghiep(cur, ma_kh: str, dong: list[dict], chung: dict | None = None,
                       hom_nay: str | None = None) -> dict:
    """CHẠY THỬ ghi tốt nghiệp (không ghi): kết quả dự kiến từng dòng, trùng số giấy trong lô và trong DB,
    khoảng số, cảnh báo. `dong` = [{ma_dk, so_giay}]; `chung` = sổ/QĐ/ngày điền chung."""
    hom_nay = hom_nay or hom_nay_iso()
    khoa = _khoa_oto_hoac_loi(cur, ma_kh)
    ds = _chuan_dong_tn(dong)
    ket_qua, _hvs = _phan_tich_lo(cur, ma_kh, khoa, ds, chung, hom_nay)
    dem: dict[str, int] = {}
    so_trong_lo: list[int] = []
    tien_to = ""
    for d, kq in zip(ds, ket_qua):
        dem[kq["ket_qua"]] = dem.get(kq["ket_qua"], 0) + 1
        t = rules.tach_so_giay(d["so_giay"])
        if t and kq["ghi_duoc"]:
            tien_to = tien_to or t[0]
            if t[0] == tien_to:
                so_trong_lo.append(t[1])
    return {
        "ma_kh": ma_kh, "ghi_duoc_khoa": bool(khoa["bg"]) and khoa["bg"] <= hom_nay, "tong": len(ds), "dem": dem,
        "khoang_so": ({"tien_to": tien_to, "tu": min(so_trong_lo), "den": max(so_trong_lo),
                       "so_luong": len(so_trong_lo)} if so_trong_lo else None),
        "co_chan": any(kq["ket_qua"] == rules.KQ_CHAN for kq in ket_qua),
        "canh_bao": _tong_hop_canh_bao(ket_qua), "dong": ket_qua,
    }


def _chon_dong_ghi(ds: list[dict], ket_qua: list[dict], da_xem_canh_bao: bool) -> tuple[list[tuple[dict, dict]], list[dict]]:
    """Từ kết quả phân tích: (các dòng GHI ĐƯỢC, các dòng bỏ qua kèm lý do). Cảnh báo chưa xác nhận → 409
    (không ghi gì); không có dòng nào ghi được → 409."""
    ghi, bo_qua = [], []
    for d, kq in zip(ds, ket_qua):
        if kq["ghi_duoc"]:
            ghi.append((d, kq))
        else:
            ly = (kq["chan"][0] if kq["chan"] else (kq["thong_tin"][0] if kq["thong_tin"] else {}))
            bo_qua.append({"ma_dk": d["ma_dk"], "ma_ly_do": ly.get("ma", kq["ket_qua"]),
                           "ly_do": ly.get("noi_dung", "Không có gì để ghi")})
    if not ghi:
        raise LoiNghiepVu("khong_co_dong_hop_le", "Không có dòng nào ghi được — xem lý do từng dòng", 409,
                          {"bo_qua": bo_qua})
    canh_bao = _tong_hop_canh_bao([kq for _d, kq in ghi])
    if canh_bao and not da_xem_canh_bao:
        raise LoiNghiepVu("can_xac_nhan_canh_bao", canh_bao[0]["noi_dung"], 409, {"canh_bao": canh_bao})
    return ghi, bo_qua


def kiem_truoc_ghi_tn(cur, ma_kh: str, dong: list[dict], chung: dict | None, da_xem_canh_bao: bool,
                      hom_nay: str | None = None) -> None:
    """Kiểm nhanh ĐỒNG BỘ (router gọi trước khi chạy nền): khóa ô tô + đã bế giảng, ít nhất một dòng ghi
    được, cảnh báo đã xác nhận. Không ghi."""
    hom_nay = hom_nay or hom_nay_iso()
    khoa = _khoa_oto_hoac_loi(cur, ma_kh)
    if not khoa["bg"] or khoa["bg"] > hom_nay:
        raise LoiNghiepVu("khoa_chua_be_giang", "Khóa chưa bế giảng — chỉ xem, không ghi được", 409)
    ds = _chuan_dong_tn(dong)
    ket_qua, _ = _phan_tich_lo(cur, ma_kh, khoa, ds, chung, hom_nay)
    _chon_dong_ghi(ds, ket_qua, da_xem_canh_bao)


def _ngay_dt(iso: str | None) -> datetime | None:
    return datetime.strptime(iso, "%Y-%m-%d") if iso else None


def ghi_tot_nghiep(conn, *, lo_id: str, ma_kh: str, dong: list[dict], chung: dict | None, nguoi: str,
                   da_xem_canh_bao: bool = False, hom_nay: str | None = None,
                   bao_tien_do: Callable[[int, int], None] | None = None) -> dict:
    """GHI tốt nghiệp ô tô theo lô (TNB-01): `usp_NguoiLX_HoSo_Update_CNTN` từng HV trong khóa ghi chung.

    Trong khóa: đọc lại + chạy lại CÙNG luật của chạy thử → dòng bị chặn bỏ qua kèm lý do → từng HV: đọc lại
    SÁT trước SP, SP với giá trị hiệu lực (số giấy rỗng truyền `''`, KHÔNG `NULL` — `LEN(NULL)` làm SP rẽ sang
    nhánh hủy 09→03), ghi nhật ký NGAY sau SP, đọc lại sau SP chỉ để cảnh báo. Cùng `lo_id` chạy lại = "Làm
    tiếp": HV đã ghi không bị gọi lại SP. Lỗi DB giữa chừng → trả đã/chưa ghi."""
    hom_nay = hom_nay or hom_nay_iso()
    ds = _chuan_dong_tn(dong)
    with khoa_ghi(conn) as cur:
        khoa = _khoa_oto_hoac_loi(cur, ma_kh)
        if not khoa["bg"] or khoa["bg"] > hom_nay:
            raise LoiNghiepVu("khoa_chua_be_giang", "Khóa chưa bế giảng — chỉ xem, không ghi được", 409)
        nhat_ky.lo_bat_dau(lo_id, nguoi, nhat_ky.LO_TOT_NGHIEP, ma_kh, "", len(ds))
        nk = nhat_ky.bat_dau(nguoi, nhat_ky.TOT_NGHIEP, ma_kh, "", len(ds), f"Tốt nghiệp {len(ds)} HV",
                             {"ma_dk": [d["ma_dk"] for d in ds]}, lo_id=lo_id)
        try:
            return _ghi_tn_trong_khoa(cur, nk=nk, lo_id=lo_id, ma_kh=ma_kh, khoa=khoa, ds=ds, chung=chung,
                                      da_xem_canh_bao=da_xem_canh_bao, hom_nay=hom_nay, bao_tien_do=bao_tien_do)
        except Exception as e:  # noqa: BLE001 — đóng nhật ký rồi ném tiếp
            loi = getattr(e, "noi_dung", None) or str(e)
            nhat_ky.ket_thuc(nk, "that_bai", {"loi": loi[:200]})
            _luu_loi_lo(lo_id, "that_bai", {"loi": loi[:200]})
            raise


def _ghi_tn_trong_khoa(cur, *, nk, lo_id, ma_kh, khoa, ds, chung, da_xem_canh_bao, hom_nay, bao_tien_do) -> dict:
    da_ghi_truoc = {h["ma_dk"] for h in nhat_ky.lo_hv(lo_id) if h["ket_qua"] == "da_ghi"}   # "Làm tiếp"
    moi = [d for d in ds if d["ma_dk"] not in da_ghi_truoc]
    ket_qua, _hvs = _phan_tich_lo(cur, ma_kh, khoa, moi, chung, hom_nay) if moi else ([], {})
    if moi:
        ghi, bo_qua = _chon_dong_ghi(moi, ket_qua, da_xem_canh_bao)
    else:
        ghi, bo_qua = [], []
    for b in bo_qua:
        nhat_ky.lo_ghi_hv(lo_id, b["ma_dk"], "bo_qua", b["ma_ly_do"])
    da_ghi, chua_ghi, canh_bao, loi = [], [], [], None
    for idx, (d, kq) in enumerate(ghi):
        ma_dk = d["ma_dk"]
        hl = kq["hieu_luc"]
        try:
            cur.execute(_Q_HV_TN_IN.format(ph="%s"), (ma_dk,))
            dong_hv = cur.fetchone()
            hien = _hv_tn(dong_hv) if dong_hv else None
            truoc = _hvs.get(ma_dk)
            if (hien is None or truoc is None or hien["tt"] != truoc["tt"] or hien["ma_bc2"] != truoc["ma_bc2"]
                    or hien["so_giay"] != truoc["so_giay"]):
                bo_qua.append({"ma_dk": ma_dk, "ma_ly_do": "doi_giua_chung",
                               "ly_do": "Phần mềm cũ vừa đổi học viên này — không ghi đè"})
                nhat_ky.lo_ghi_hv(lo_id, ma_dk, "bo_qua", "doi_giua_chung")
                continue
            if hl["so_giay"]:   # sát trước SP: số giấy vừa bị người khác dùng?
                k = rules.khoa_so_giay(hl["so_giay"])
                cur.execute(_Q_SO_GIAY_TRUNG.format(ph="%s"), (k,))
                nguoi_giu = {_s(r["MaDK"]) for r in cur.fetchall()
                             if rules.khoa_so_giay(r["SoGiayCNTN"]) == k} - {ma_dk}
                if nguoi_giu and k != rules.khoa_so_giay(hien["so_giay"]):
                    bo_qua.append({"ma_dk": ma_dk, "ma_ly_do": "trung_db",
                                   "ly_do": f"Số giấy {hl['so_giay']} vừa được dùng cho học viên khác"})
                    nhat_ky.lo_ghi_hv(lo_id, ma_dk, "bo_qua", "trung_db")
                    continue
            cur.execute("EXEC usp_NguoiLX_HoSo_Update_CNTN %s,%s,%s,%s,%s,%s,%s,%s",
                        (ma_dk, hien["so_ho_so"], hl["so_so_tn"], _ngay_dt(hl["ngay_vao_so"]), hl["so_quyet_dinh"],
                         _ngay_dt(hl["ngay_ra_qd"]), hl["so_giay"] or "", _ngay_dt(hl["ngay_in"])))
            da_ghi.append({"ma_dk": ma_dk, "ket_qua": kq["ket_qua"]})
            try:
                nhat_ky.lo_ghi_hv(lo_id, ma_dk, "da_ghi", kq["ket_qua"])  # GHI NGAY sau SP thành công
            except Exception:  # noqa: BLE001 — SP đã chạy: vẫn là "đã ghi", chỉ cảnh báo nhật ký
                canh_bao.append({"ma_dk": ma_dk, "ma": "khong_ghi_duoc_nhat_ky",
                                 "noi_dung": "Đã ghi nhưng chưa lưu được nhật ký cho học viên này"})
            try:   # đọc lại SAU SP chỉ để cảnh báo
                cur.execute(_Q_HV_TN_IN.format(ph="%s"), (ma_dk,))
                sau = _hv_tn(cur.fetchone() or {"MaDK": ma_dk})
                mong_doi = "09" if kq["ket_qua"] in (rules.KQ_LEN_09, rules.KQ_GIU_09) else hien["tt"]
                if (sau["tt"] != mong_doi or sau["so_giay"] != (hl["so_giay"] or "")
                        or sau["so_so_tn"] != hl["so_so_tn"] or sau["so_quyet_dinh"] != hl["so_quyet_dinh"]):
                    canh_bao.append({"ma_dk": ma_dk, "ma": "khong_khop_sau_ghi",
                                     "noi_dung": "Sau khi ghi, dữ liệu học viên không như mong đợi — kiểm lại"})
            except Exception:  # noqa: BLE001
                canh_bao.append({"ma_dk": ma_dk, "ma": "khong_doc_lai_duoc",
                                 "noi_dung": "Đã ghi nhưng chưa đọc lại được học viên này — kiểm lại"})
        except Exception as e:  # noqa: BLE001 — lỗi DB: dừng, báo đã/chưa ghi
            loi = {"ma_dk": ma_dk, "noi_dung": str(e)[:200]}
            chua_ghi = [x[0]["ma_dk"] for x in ghi[idx:]]
            for m in chua_ghi:
                nhat_ky.lo_ghi_hv(lo_id, m, "chua_ghi", "loi_db")
            break
        finally:
            if bao_tien_do:
                bao_tien_do(idx + 1, len(ghi))
    bo_cache()
    trang_thai = "loi_giua_chung" if loi else "xong"
    dem: dict[str, int] = {}
    for g in da_ghi:
        dem[g["ket_qua"]] = dem.get(g["ket_qua"], 0) + 1
    kq_tong = {"lo_id": lo_id, "ma_kh": ma_kh, "tong": len(ds), "da_ghi": da_ghi,
               "da_ghi_truoc": sorted(da_ghi_truoc, key=[d["ma_dk"] for d in ds].index),
               "bo_qua": bo_qua, "chua_ghi": chua_ghi, "canh_bao": canh_bao, "dem": dem, "loi": loi,
               "trang_thai": trang_thai}
    nhat_ky.lo_cap_nhat(lo_id, trang_thai=trang_thai, ket_qua={k: v for k, v in kq_tong.items() if k != "lo_id"},
                        luc_xong=datetime.now().isoformat(timespec="seconds"))
    nhat_ky.ket_thuc(nk, trang_thai, {"da_ghi": len(da_ghi), "bo_qua": len(bo_qua), "chua_ghi": len(chua_ghi)})
    return kq_tong


# ══════════════ Hủy tốt nghiệp (TNB-02, task 103) ══════════════
def _phan_loai_huy(cur, ma_kh: str, ds: list[str]) -> tuple[list[dict], list[dict]]:
    """Đọc lại các HV muốn hủy: (hủy được, bỏ qua kèm lý do). Chỉ HV còn `09` và CHƯA gắn BC2."""
    hvs: dict[str, dict] = {}
    for khoi in _chia(ds, _KHOI_IN):
        cur.execute(_Q_HV_TN_IN.format(ph=",".join(["%s"] * len(khoi))), tuple(khoi))
        for r in cur.fetchall():
            h = _hv_tn(r)
            hvs[h["ma_dk"]] = h
    huy_duoc, bo_qua = [], []

    def bq(ma_dk: str, ma: str, ly: str) -> None:
        bo_qua.append({"ma_dk": ma_dk, "ma_ly_do": ma, "ly_do": ly})

    for ma_dk in ds:
        hv = hvs.get(ma_dk)
        if hv is None:
            bq(ma_dk, "hv_khong_ton_tai", "Không còn học viên này")
        elif hv["ma_kh"] != ma_kh:
            bq(ma_dk, "khac_khoa", "Học viên không thuộc khóa đang chọn")
        elif rules.loai_hang(hv["hang"]) != "oto":
            bq(ma_dk, "sai_loai", "Mô tô không có bước tốt nghiệp")
        elif hv["ma_bc2"] or hv["tt"] in rules.TT_VAO_BC2_TRO_DI:
            bq(ma_dk, "da_vao_bc2", "Học viên đã vào BC2 — phải gỡ khỏi BC2 trước khi hủy tốt nghiệp")
        elif hv["tt"] != rules.TT_TOT_NGHIEP:
            bq(ma_dk, "khong_con_o_09",
               f"Đang ở \"{rules.ten_trang_thai(hv['tt'], 'oto')}\" — không có tốt nghiệp để hủy")
        else:
            huy_duoc.append(hv)
    return huy_duoc, bo_qua


def kiem_truoc_huy_tn(cur, ma_kh: str, ds_ma_dk: Iterable[str], hom_nay: str | None = None) -> list[str]:
    """Kiểm nhanh ĐỒNG BỘ trước khi chạy nền: khóa ô tô + đã bế giảng, danh sách hợp lệ, có ít nhất một HV hủy được."""
    hom_nay = hom_nay or hom_nay_iso()
    khoa = _khoa_oto_hoac_loi(cur, ma_kh)
    if not khoa["bg"] or khoa["bg"] > hom_nay:
        raise LoiNghiepVu("khoa_chua_be_giang", "Khóa chưa bế giảng — chỉ xem, không hủy được", 409)
    ds = _chuan_ds(ds_ma_dk)
    vde = rules.kiem_danh_sach_dan(ds)
    if vde:
        raise LoiNghiepVu(vde[0]["ma"], vde[0]["noi_dung"], 400)
    if not ds:
        raise LoiNghiepVu("khong_co_hoc_vien", "Chưa chọn học viên nào để hủy tốt nghiệp", 400)
    huy_duoc, bo_qua = _phan_loai_huy(cur, ma_kh, ds)
    if not huy_duoc:
        raise LoiNghiepVu("khong_co_hoc_vien_huy_duoc", "Không có học viên nào hủy được — xem lý do từng dòng", 409,
                          {"bo_qua": bo_qua})
    return ds


def huy_tot_nghiep(conn, *, lo_id: str, ma_kh: str, ds_ma_dk: Iterable[str], nguoi: str,
                   hom_nay: str | None = None, bao_tien_do: Callable[[int, int], None] | None = None) -> dict:
    """HỦY tốt nghiệp ô tô: HV `09` chưa gắn BC2 → `03`, GIỮ NGUYÊN sổ/quyết định/ngày, chỉ xóa số giấy.

    Dùng `usp_NguoiLX_HoSo_Update_CNTN` với `@sSoCNTN=''` (KHÔNG dùng `Update_HSTotNghiep` — dựa `TT_XuLy_Old`,
    trống ở nhiều HV). SP không kiểm trạng thái → tool tự chặn HV đã vào BC2 / không còn `09`. Đọc lại sát
    trước SP; nhật ký ngay sau SP; "Làm tiếp" cùng `lo_id` không gọi lại SP."""
    hom_nay = hom_nay or hom_nay_iso()
    ds = _chuan_ds(ds_ma_dk)
    vde = rules.kiem_danh_sach_dan(ds)
    if vde:
        raise LoiNghiepVu(vde[0]["ma"], vde[0]["noi_dung"], 400)
    if not ds:
        raise LoiNghiepVu("khong_co_hoc_vien", "Chưa chọn học viên nào để hủy tốt nghiệp", 400)
    with khoa_ghi(conn) as cur:
        khoa = _khoa_oto_hoac_loi(cur, ma_kh)
        if not khoa["bg"] or khoa["bg"] > hom_nay:
            raise LoiNghiepVu("khoa_chua_be_giang", "Khóa chưa bế giảng — chỉ xem, không hủy được", 409)
        nhat_ky.lo_bat_dau(lo_id, nguoi, nhat_ky.LO_HUY_TOT_NGHIEP, ma_kh, "", len(ds))
        nk = nhat_ky.bat_dau(nguoi, nhat_ky.HUY_TOT_NGHIEP, ma_kh, "", len(ds), f"Hủy tốt nghiệp {len(ds)} HV",
                             {"ma_dk": ds}, lo_id=lo_id)
        try:
            return _huy_tn_trong_khoa(cur, nk=nk, lo_id=lo_id, ma_kh=ma_kh, ds=ds, bao_tien_do=bao_tien_do)
        except Exception as e:  # noqa: BLE001 — đóng nhật ký rồi ném tiếp
            loi = getattr(e, "noi_dung", None) or str(e)
            nhat_ky.ket_thuc(nk, "that_bai", {"loi": loi[:200]})
            _luu_loi_lo(lo_id, "that_bai", {"loi": loi[:200]})
            raise


def _huy_tn_trong_khoa(cur, *, nk, lo_id, ma_kh, ds, bao_tien_do) -> dict:
    da_huy_truoc = {h["ma_dk"]: h["ma_ly_do"] for h in nhat_ky.lo_hv(lo_id) if h["ket_qua"] == "da_huy"}   # Làm tiếp
    moi = [m for m in ds if m not in da_huy_truoc]
    huy_duoc, bo_qua = _phan_loai_huy(cur, ma_kh, moi) if moi else ([], [])
    if moi and not huy_duoc:      # cùng cách với ghi: không còn dòng nào hủy được → 409 (danh sách đã hủy được giữ)
        raise LoiNghiepVu("khong_co_hoc_vien_huy_duoc", "Không có học viên nào hủy được — xem lý do từng dòng", 409,
                          {"bo_qua": bo_qua})
    for b in bo_qua:
        nhat_ky.lo_ghi_hv(lo_id, b["ma_dk"], "bo_qua", b["ma_ly_do"])
    da_huy, chua_ghi, canh_bao, loi = [], [], [], None
    for idx, hv in enumerate(huy_duoc):
        ma_dk = hv["ma_dk"]
        try:
            cur.execute(_Q_HV_TN_IN.format(ph="%s"), (ma_dk,))
            dong_hv = cur.fetchone()
            hien = _hv_tn(dong_hv) if dong_hv else None
            if (hien is None or hien["tt"] != hv["tt"] or hien["ma_bc2"] != hv["ma_bc2"]
                    or hien["so_giay"] != hv["so_giay"]):                # đọc lại SÁT trước SP
                bo_qua.append({"ma_dk": ma_dk, "ma_ly_do": "doi_giua_chung",
                               "ly_do": "Phần mềm cũ vừa đổi học viên này — không hủy"})
                nhat_ky.lo_ghi_hv(lo_id, ma_dk, "bo_qua", "doi_giua_chung")
                continue
            # giữ nguyên sổ/quyết định/ngày hiện có; CHỈ số giấy = '' (SP: LEN('')=0 và TT_XuLy='09' → '03')
            cur.execute("EXEC usp_NguoiLX_HoSo_Update_CNTN %s,%s,%s,%s,%s,%s,%s,%s",
                        (ma_dk, hien["so_ho_so"], hien["so_so_tn"], _ngay_dt(hien["ngay_vao_so"]),
                         hien["so_quyet_dinh"], _ngay_dt(hien["ngay_ra_qd"]), "", _ngay_dt(hien["ngay_in"])))
            da_huy.append({"ma_dk": ma_dk, "so_giay_cu": hien["so_giay"]})
            try:
                nhat_ky.lo_ghi_hv(lo_id, ma_dk, "da_huy", hien["so_giay"])     # GHI NGAY sau SP thành công
            except Exception:  # noqa: BLE001
                canh_bao.append({"ma_dk": ma_dk, "ma": "khong_ghi_duoc_nhat_ky",
                                 "noi_dung": "Đã hủy nhưng chưa lưu được nhật ký cho học viên này"})
            try:   # đọc lại SAU SP chỉ để cảnh báo
                cur.execute(_Q_HV_TN_IN.format(ph="%s"), (ma_dk,))
                sau = _hv_tn(cur.fetchone() or {"MaDK": ma_dk})
                if (sau["tt"] != rules.TT_HOC_XONG or sau["so_giay"] != ""
                        or sau["so_so_tn"] != hien["so_so_tn"] or sau["so_quyet_dinh"] != hien["so_quyet_dinh"]):
                    canh_bao.append({"ma_dk": ma_dk, "ma": "khong_khop_sau_huy",
                                     "noi_dung": "Sau khi hủy, dữ liệu học viên không như mong đợi — kiểm lại"})
            except Exception:  # noqa: BLE001
                canh_bao.append({"ma_dk": ma_dk, "ma": "khong_doc_lai_duoc",
                                 "noi_dung": "Đã hủy nhưng chưa đọc lại được học viên này — kiểm lại"})
        except Exception as e:  # noqa: BLE001 — lỗi DB: dừng, báo đã/chưa hủy
            loi = {"ma_dk": ma_dk, "noi_dung": str(e)[:200]}
            chua_ghi = [h["ma_dk"] for h in huy_duoc[idx:]]
            for m in chua_ghi:
                nhat_ky.lo_ghi_hv(lo_id, m, "chua_ghi", "loi_db")
            break
        finally:
            if bao_tien_do:
                bao_tien_do(idx + 1, len(huy_duoc))
    bo_cache()
    trang_thai = "loi_giua_chung" if loi else "xong"
    kq = {"lo_id": lo_id, "ma_kh": ma_kh, "tong": len(ds), "da_huy": da_huy,
          "da_huy_truoc": [{"ma_dk": m, "so_giay_cu": g} for m, g in da_huy_truoc.items()],
          "bo_qua": bo_qua, "chua_ghi": chua_ghi, "canh_bao": canh_bao, "loi": loi, "trang_thai": trang_thai}
    nhat_ky.lo_cap_nhat(lo_id, trang_thai=trang_thai, ket_qua={k: v for k, v in kq.items() if k != "lo_id"},
                        luc_xong=datetime.now().isoformat(timespec="seconds"))
    nhat_ky.ket_thuc(nk, trang_thai, {"da_huy": len(da_huy), "bo_qua": len(bo_qua), "chua_ghi": len(chua_ghi)})
    return kq


# ══════════════ Cứu trạng thái (TNB-06, task 104) ══════════════
CUU_CACHE_GIAY = 60
CUU_TOI_DA_KET_QUA = 50
_Q_HV_CUU_TAT_CA = ("SELECT h.MaDK, h.SoHoSo, n.HoVaTen, n.NgaySinh, n.SoCMT, h.HangGPLX, h.TT_XuLy, h.MaBC2, "
                    "h.MaKhoaHoc, h.SoGiayCNTN, k.TenKH, k.NgayBG "
                    "FROM NguoiLX_HoSo h LEFT JOIN NguoiLX n ON n.MaDK = h.MaDK "
                    "LEFT JOIN KhoaHoc k ON k.MaKH = h.MaKhoaHoc")


def _hv_cuu(r: dict) -> dict:
    return {"ma_dk": _s(r["MaDK"]), "so_ho_so": _s(r.get("SoHoSo")), "ten": _s(r.get("HoVaTen")),
            "ngay_sinh": _ngay_sinh_vn(r.get("NgaySinh")), "cmt": _s(r.get("SoCMT")), "hang": _s(r.get("HangGPLX")),
            "tt": _s(r.get("TT_XuLy")), "ma_bc2": _s(r.get("MaBC2")), "ma_kh": _s(r.get("MaKhoaHoc")),
            "so_giay": _s(r.get("SoGiayCNTN")), "ten_kh": _s(r.get("TenKH")), "bg": _ngay_iso(r.get("NgayBG"))}


def tim_hv_cuu(cur, q: str, loai: str = "", hom_nay: str | None = None,
               now: Callable[[], float] = time.monotonic) -> dict:
    """Tìm HV (tên không dấu / CMT / mã đăng ký) trên TOÀN DB để cứu trạng thái, kèm lý do không có trong danh
    sách ứng viên và các đích cho phép. Danh sách HV giữ trong bộ nhớ ~60 giây."""
    hom_nay = hom_nay or hom_nay_iso()
    tu = _s(q)
    if len(tu) < 2:
        raise LoiNghiepVu("thieu_tu_khoa", "Nhập ít nhất 2 ký tự để tìm", 400)
    with _khoa_cache:
        c = _cuu_cache.get("all")
        tat_ca = c[1] if c and now() - c[0] < CUU_CACHE_GIAY else None
    if tat_ca is None:
        cur.execute(_Q_HV_CUU_TAT_CA)
        tat_ca = [_hv_cuu(r) for r in cur.fetchall()]
        with _khoa_cache:
            _cuu_cache["all"] = (now(), tat_ca)
    k = rules.bo_dau(tu)
    khop = [h for h in tat_ca if k in rules.bo_dau(h["ten"]) or tu in h["cmt"]
            or tu.casefold() in h["ma_dk"].casefold()]
    _b1, bc2_map, _bci, _t = doc_bc(cur)
    out = []
    for h in khop[:CUU_TOI_DA_KET_QUA]:
        loai_hv = rules.loai_hang(h["hang"])
        if loai and loai_hv != loai:
            gt = {"ma": "khac_loai", "noi_dung": "Khác loại hạng với loại đang chọn"}
        else:
            gt = rules.giai_thich_khong_hien(h, loai_hv, {"hom_nay": hom_nay, "ma_kh_chon": h["ma_kh"],
                                                           "bc2_map": bc2_map, "ma_bc2_dang_them": ""})
        dich = rules.dich_cho_phep(h, loai or loai_hv)
        out.append({**h, "loai": loai_hv, "khac_loai": bool(loai) and loai_hv != loai,
                    "ten_trang_thai": rules.ten_trang_thai(h["tt"], loai_hv), "khong_hien": gt,
                    "dich": dich, "cuu_duoc": any(d["cho_phep"] for d in dich)
                    and not (bool(loai) and loai_hv != loai)})
    return {"q": tu, "loai": loai, "tong_khop": len(khop), "hien_toi_da": CUU_TOI_DA_KET_QUA, "hoc_vien": out}


def _doc_hv_cuu_mot(cur, ma_dk: str) -> dict | None:
    cur.execute(_Q_HV_TN_IN.format(ph="%s"), (ma_dk,))
    r = cur.fetchone()
    return _hv_tn(r) if r else None


def _hoan_tat_cuu_do(cur, lo_cu: dict | None, hv: dict, *, lo_id: str, ma_dk: str, dich: str, ly_do: str) -> dict | None:
    """Gửi lại cùng `lo_id` sau khi tool bị ngắt GIỮA lúc cứu: lô còn `dang_chay` nhưng SP đã chạy xong (HV đang
    đúng ở `dich`). Hoàn tất lô từ NHẬT KÝ (ghi trước SP: có `tt_cu`) thay vì từ chối `khong_doi` — để nhân viên
    vẫn có nút Hoàn tác. Trả None nếu không phải ca đó (SP chưa chạy → chạy bình thường)."""
    if lo_cu is None or lo_cu["trang_thai"] != "dang_chay" or lo_cu["loai"] != nhat_ky.LO_CUU:
        return None
    nk_cu = nhat_ky.theo_lo_id(lo_id, nhat_ky.CUU)
    ct = (nk_cu or {}).get("chi_tiet") or {}
    tt_cu = _s(ct.get("tt_cu"))
    if ct.get("ma_dk") != ma_dk or _s(ct.get("tt_moi")) != dich or not tt_cu or tt_cu == dich or hv["tt"] != dich:
        return None
    loai_hv = rules.loai_hang(hv["hang"])
    kq = {"ma_dk": ma_dk, "tt_cu": tt_cu, "tt_moi": dich, "ten_trang_thai_cu": rules.ten_trang_thai(tt_cu, loai_hv),
          "ten_trang_thai_moi": rules.ten_trang_thai(dich, loai_hv), "ly_do": ly_do,
          "canh_bao": [{"ma": "hoan_tat_tu_lan_truoc",
                        "noi_dung": "Lần gửi trước đã chuyển xong nhưng chưa kịp ghi nhận — đã hoàn tất theo nhật ký"}],
          "trang_thai": "xong"}
    try:
        nhat_ky.lo_ghi_hv(lo_id, ma_dk, "da_cuu", f"{tt_cu}>{dich}")
        nhat_ky.lo_cap_nhat(lo_id, trang_thai="xong", ket_qua=kq, luc_xong=datetime.now().isoformat(timespec="seconds"))
        nhat_ky.ket_thuc(nk_cu["id"], "xong", {"tt_cu": tt_cu, "tt_moi": dich, "hoan_tat": True})
    except Exception:  # noqa: BLE001 — chỉ là ghi nhận; HV đã đúng trạng thái đích
        kq["canh_bao"].append({"ma": "khong_ghi_duoc_nhat_ky",
                               "noi_dung": "Đã chuyển nhưng chưa lưu được nhật ký — ghi lại thủ công nếu cần hoàn tác"})
    return {**kq, "lo_id": lo_id, "da_ton_tai": True}


def cuu_chuyen(conn, *, lo_id: str, ma_dk: str, dich: str, ly_do: str, loai: str, nguoi: str) -> dict:
    """Chuyển `TT_XuLy` MỘT HV (cứu HV không tìm thấy khi lập BC2) bằng `usp_NguoiLX_HoSo_UpdateTTXLy`.

    SP không kiểm điều kiện nào và GHI ĐÈ `TT_XuLy_Old` → mọi cổng chặn nằm ở đây (`rules.kiem_cuu`), và
    trạng thái cũ để hoàn tác được lưu trong NHẬT KÝ tool (không dựa vào `TT_XuLy_Old` của DB).
    Idempotent theo `lo_id`."""
    ma_dk, dich, ly_do = _s(ma_dk), _s(dich), _s(ly_do)
    cu = nhat_ky.lo_lay(lo_id)
    if cu is not None and cu["trang_thai"] == "xong":
        kq_cu = cu.get("ket_qua") or {}
        if cu["loai"] != nhat_ky.LO_CUU or kq_cu.get("ma_dk") != ma_dk or kq_cu.get("tt_moi") != dich:
            raise LoiNghiepVu("lo_id_khong_khop", "lo_id này đã dùng cho một thao tác khác — tạo lo_id mới", 409)
        return {**kq_cu, "lo_id": lo_id, "da_ton_tai": True}
    with khoa_ghi(conn) as cur:
        hv = _doc_hv_cuu_mot(cur, ma_dk)
        if hv is None:
            raise LoiNghiepVu("hv_khong_ton_tai", f"Không có học viên {ma_dk}", 404)
        hoan_tat = _hoan_tat_cuu_do(cur, cu, hv, lo_id=lo_id, ma_dk=ma_dk, dich=dich, ly_do=ly_do)
        if hoan_tat is not None:
            return hoan_tat
        vde = rules.kiem_cuu(hv, dich, loai or rules.loai_hang(hv["hang"]), ly_do)
        if vde:
            raise LoiNghiepVu("khong_cuu_duoc", vde[0]["noi_dung"], 409, {"chan": vde})
        nhat_ky.lo_bat_dau(lo_id, nguoi, nhat_ky.LO_CUU, hv["ma_kh"], "", 1)
        nk = nhat_ky.bat_dau(nguoi, nhat_ky.CUU, hv["ma_kh"], "", 1, f"Cứu trạng thái: {_tt_ngoac(hv['tt'], rules.loai_hang(hv['hang']))} → {_tt_ngoac(dich, rules.loai_hang(hv['hang']))}",
                             {"ma_dk": ma_dk, "tt_cu": hv["tt"], "tt_moi": dich, "ly_do": ly_do}, lo_id=lo_id)
        try:
            cur.execute("EXEC usp_NguoiLX_HoSo_UpdateTTXLy %s,%s,%s", (ma_dk, hv["so_ho_so"], dich))
        except Exception as e:  # noqa: BLE001
            nhat_ky.ket_thuc(nk, "that_bai", {"loi": str(e)[:200]})
            nhat_ky.lo_cap_nhat(lo_id, trang_thai="that_bai", ket_qua={"loi": str(e)[:200]})
            raise
        canh_bao = []
        try:   # SP đã chạy: lỗi đọc lại chỉ là cảnh báo
            sau = _doc_hv_cuu_mot(cur, ma_dk)
            if sau is None or sau["tt"] != dich:
                canh_bao.append({"ma": "khong_khop_sau_ghi", "noi_dung": "Sau khi chuyển, trạng thái không như mong đợi — kiểm lại"})
        except Exception:  # noqa: BLE001
            canh_bao.append({"ma": "khong_doc_lai_duoc", "noi_dung": "Đã chuyển nhưng chưa đọc lại được học viên — kiểm lại"})
        bo_cache()
        loai_hv = rules.loai_hang(hv["hang"])
        kq = {"ma_dk": ma_dk, "tt_cu": hv["tt"], "tt_moi": dich, "ten_trang_thai_cu": rules.ten_trang_thai(hv["tt"], loai_hv),
              "ten_trang_thai_moi": rules.ten_trang_thai(dich, loai_hv), "ly_do": ly_do, "canh_bao": canh_bao,
              "trang_thai": "xong"}
        try:   # SP đã chạy: lỗi nhật ký sqlite KHÔNG làm thao tác thành "chưa làm"
            nhat_ky.lo_ghi_hv(lo_id, ma_dk, "da_cuu", f"{hv['tt']}>{dich}")
            nhat_ky.lo_cap_nhat(lo_id, trang_thai="xong", ket_qua=kq,
                                luc_xong=datetime.now().isoformat(timespec="seconds"))
            nhat_ky.ket_thuc(nk, "xong", {"tt_cu": hv["tt"], "tt_moi": dich})
        except Exception:  # noqa: BLE001
            kq["canh_bao"].append({"ma": "khong_ghi_duoc_nhat_ky",
                                   "noi_dung": "Đã chuyển nhưng chưa lưu được nhật ký — ghi lại thủ công nếu cần hoàn tác"})
        return {**kq, "lo_id": lo_id, "da_ton_tai": False}


def cuu_hoan_tac(conn, *, lo_id_cuu: str, lo_id: str, nguoi: str) -> dict:
    """Hoàn tác MỘT lần cứu: về trạng thái cũ ghi trong nhật ký, MIỄN luật đích (về `03` là hợp lệ), chỉ khi HV
    vẫn đang đúng trạng thái vừa cứu (PM cũ chưa đổi tiếp). Idempotent theo `lo_id`."""
    cu = nhat_ky.lo_lay(lo_id)
    if cu is not None and cu["trang_thai"] == "xong":
        if cu["loai"] != nhat_ky.LO_CUU_HOAN_TAC or cu.get("lo_goc") != lo_id_cuu:
            raise LoiNghiepVu("lo_id_khong_khop", "lo_id này đã dùng cho một thao tác khác — tạo lo_id mới", 409)
        return {**(cu.get("ket_qua") or {}), "lo_id": lo_id, "da_ton_tai": True}
    goc = nhat_ky.lo_lay(lo_id_cuu)
    if goc is None or goc["loai"] != nhat_ky.LO_CUU or goc["trang_thai"] != "xong":
        raise LoiNghiepVu("khong_co_lan_cuu", "Không có lần cứu trạng thái này để hoàn tác", 404)
    if goc.get("hoan_tac_boi"):
        raise LoiNghiepVu("da_hoan_tac", "Lần cứu này đã được hoàn tác", 409)
    kq_goc = goc.get("ket_qua") or {}
    ma_dk, tt_cu, tt_moi = _s(kq_goc.get("ma_dk")), _s(kq_goc.get("tt_cu")), _s(kq_goc.get("tt_moi"))
    with khoa_ghi(conn) as cur:
        hv = _doc_hv_cuu_mot(cur, ma_dk)
        if hv is None:
            raise LoiNghiepVu("hv_khong_ton_tai", f"Không có học viên {ma_dk}", 404)
        vde = rules.kiem_hoan_tac_cuu(hv["tt"], tt_moi, tt_cu)
        if vde:
            raise LoiNghiepVu(vde[0]["ma"], vde[0]["noi_dung"], 409, {"chan": vde})
        nhat_ky.lo_bat_dau(lo_id, nguoi, nhat_ky.LO_CUU_HOAN_TAC, hv["ma_kh"], "", 1, lo_goc=lo_id_cuu)
        nk = nhat_ky.bat_dau(nguoi, nhat_ky.CUU, hv["ma_kh"], "", 1, f"Hoàn tác cứu: {_tt_ngoac(tt_moi, rules.loai_hang(hv['hang']))} → {_tt_ngoac(tt_cu, rules.loai_hang(hv['hang']))}",
                             {"ma_dk": ma_dk, "tt_cu": tt_moi, "tt_moi": tt_cu, "lo_goc": lo_id_cuu}, lo_id=lo_id)
        try:
            cur.execute("EXEC usp_NguoiLX_HoSo_UpdateTTXLy %s,%s,%s", (ma_dk, hv["so_ho_so"], tt_cu))
        except Exception as e:  # noqa: BLE001
            nhat_ky.ket_thuc(nk, "that_bai", {"loi": str(e)[:200]})
            nhat_ky.lo_cap_nhat(lo_id, trang_thai="that_bai", ket_qua={"loi": str(e)[:200]})
            raise
        canh_bao = []
        try:   # đọc lại SAU SP chỉ để cảnh báo (đối xứng với cuu_chuyen)
            sau = _doc_hv_cuu_mot(cur, ma_dk)
            if sau is None or sau["tt"] != tt_cu:
                canh_bao.append({"ma": "khong_khop_sau_ghi",
                                 "noi_dung": "Sau khi hoàn tác, trạng thái không như mong đợi — kiểm lại"})
        except Exception:  # noqa: BLE001
            canh_bao.append({"ma": "khong_doc_lai_duoc",
                             "noi_dung": "Đã hoàn tác nhưng chưa đọc lại được học viên — kiểm lại"})
        bo_cache()
        loai_hv = rules.loai_hang(hv["hang"])
        kq = {"ma_dk": ma_dk, "tt_cu": tt_moi, "tt_moi": tt_cu, "lo_goc": lo_id_cuu,
              "ten_trang_thai_moi": rules.ten_trang_thai(tt_cu, loai_hv), "canh_bao": canh_bao, "trang_thai": "xong"}
        try:   # SP đã chạy: lỗi nhật ký sqlite chỉ là cảnh báo
            nhat_ky.lo_cap_nhat(lo_id_cuu, hoan_tac_boi=lo_id)
            nhat_ky.lo_ghi_hv(lo_id, ma_dk, "da_hoan_tac", f"{tt_moi}>{tt_cu}")
            nhat_ky.lo_cap_nhat(lo_id, trang_thai="xong", ket_qua=kq,
                                luc_xong=datetime.now().isoformat(timespec="seconds"))
            nhat_ky.ket_thuc(nk, "xong", {"tt_cu": tt_moi, "tt_moi": tt_cu})
        except Exception:  # noqa: BLE001
            kq["canh_bao"].append({"ma": "khong_ghi_duoc_nhat_ky",
                                   "noi_dung": "Đã hoàn tác nhưng chưa lưu được nhật ký"})
        return {**kq, "lo_id": lo_id, "da_ton_tai": False}


# ══════════════ Danh sách BC1 / BC2 + nhật ký (TNB-07, task 105) — CHỈ ĐỌC ══════════════
_Q_BC1_DS = ("SELECT c.MaBCI, c.SoBaoCao, c.NgayBaoCao, c.MaKH, c.SoHocSinh, k.TenKH, k.HangGPLX, k.NgayBG, "
             "ISNULL(x.so_bc2, 0) AS so_bc2 "
             "FROM BaoCaoI c LEFT JOIN KhoaHoc k ON k.MaKH = c.MaKH "
             "LEFT JOIN (SELECT MaBCI, COUNT(*) AS so_bc2 FROM BaoCaoII GROUP BY MaBCI) x ON x.MaBCI = c.MaBCI "
             "ORDER BY c.NgayBaoCao DESC")
# "HV thực tế" bằng ĐÚNG MỘT GROUP BY cho cả danh sách (NguoiLX_HoSo không có index theo MaBC2: đếm từng BC2 = 455 lần quét)
_Q_BC2_DS = ("SELECT b.MaBCII, b.SoBaoCao, b.NgayBaoCao, b.MaBCI, c.SoBaoCao AS SoBC1, c.MaKH, k.TenKH, k.HangGPLX, "
             "b.TongSoThiSinh, b.TrangThai, b.NguoiTao, b.NgayTao, ISNULL(x.n, 0) AS hv_thuc_te "
             "FROM BaoCaoII b LEFT JOIN BaoCaoI c ON c.MaBCI = b.MaBCI LEFT JOIN KhoaHoc k ON k.MaKH = c.MaKH "
             "LEFT JOIN (SELECT MaBC2, COUNT(*) AS n FROM NguoiLX_HoSo WHERE ISNULL(MaBC2,'') <> '' GROUP BY MaBC2) x "
             "ON x.MaBC2 = b.MaBCII ORDER BY b.NgayBaoCao DESC, b.NgayTao DESC")

TEN_LOAI_NHAT_KY = {
    "tao_bc2": "Tạo BC2", "them_hv": "Thêm học viên vào BC2", "go_hv": "Gỡ học viên khỏi BC2",
    "xoa_bc2": "Xóa BC2", "tot_nghiep": "Cập nhật tốt nghiệp", "huy_tot_nghiep": "Hủy tốt nghiệp",
    "cuu_trang_thai": "Cứu trạng thái",
}
TEN_TRANG_THAI_NHAT_KY = {
    "xong": "Xong", "loi_giua_chung": "Lỗi giữa chừng (một phần đã ghi)", "that_bai": "Thất bại — chưa ghi",
    "bat_dau": "Đang chạy hoặc bị gián đoạn", "da_ton_tai": "Đã có từ trước",
}


def ds_bc1(cur, loai: str = "") -> dict:
    """BC1 (nguồn của BC2) kèm khóa và số BC2 đã có; `loai` suy từ hạng của khóa ('' = tất cả)."""
    cur.execute(_Q_BC1_DS)
    out = []
    for r in cur.fetchall():
        loai_k = rules.loai_hang(r.get("HangGPLX"))
        if loai and loai_k != loai:
            continue
        out.append({"ma_bci": _s(r["MaBCI"]), "so_bao_cao": _s(r.get("SoBaoCao")), "ngay_bao_cao": _ngay_iso(r.get("NgayBaoCao")),
                    "ma_kh": _s(r.get("MaKH")), "ten_kh": _s(r.get("TenKH")), "ngay_bg": _ngay_iso(r.get("NgayBG")),
                    "so_hoc_sinh": r.get("SoHocSinh"), "so_bc2": int(r.get("so_bc2") or 0), "loai": loai_k})
    return {"loai": loai, "tong": len(out), "bc1": out}


def ds_bc2(cur, loai: str = "", dong: str = "") -> dict:
    """Danh sách BC2 (tab Ô tô / Mô tô, lọc đang mở / đã đóng): Tổng ghi, HV thực tế, lệch, người tạo.
    Hoàn toàn chỉ đọc — một truy vấn duy nhất."""
    cur.execute(_Q_BC2_DS)
    out, mo, da_dong, lech = [], 0, 0, 0
    for r in cur.fetchall():
        loai_k = rules.loai_hang(r.get("HangGPLX")) if _s(r.get("HangGPLX")) else ""   # thiếu BC1/khóa: không đoán loại
        if loai and loai_k != loai:
            continue
        la_dong = r.get("TrangThai") in (1, True, "1")
        if (dong == "mo" and la_dong) or (dong == "dong" and not la_dong):
            continue
        tong_ghi = r.get("TongSoThiSinh")
        thuc_te = int(r.get("hv_thuc_te") or 0)
        la_lech = tong_ghi is not None and int(tong_ghi or 0) != thuc_te
        mo += 0 if la_dong else 1
        da_dong += 1 if la_dong else 0
        lech += 1 if la_lech else 0
        out.append({"ma_bc2": _s(r["MaBCII"]), "so_bao_cao": _s(r.get("SoBaoCao")), "ngay_bao_cao": _ngay_iso(r.get("NgayBaoCao")),
                    "ma_bci": _s(r.get("MaBCI")), "so_bc1": _s(r.get("SoBC1")), "ma_kh": _s(r.get("MaKH")),
                    "ten_kh": _s(r.get("TenKH")), "loai": loai_k, "tong_ghi": tong_ghi, "hv_thuc_te": thuc_te,
                    "lech": la_lech, "dong": la_dong, "dang_mo": not la_dong, "nguoi_tao": _s(r.get("NguoiTao")),
                    "ngay_tao": _ngay_iso(r.get("NgayTao"))})
    return {"loai": loai, "dong": dong, "tong": len(out), "dang_mo": mo, "da_dong": da_dong, "lech": lech, "bc2": out}


def _tom_tat_ket_qua(kq: dict) -> dict:
    """Đếm đã/chưa ghi từ kết quả đã lưu của một thao tác (chỉ số lượng, không mã HV/tên/CMT)."""
    def n(k: str) -> int:
        v = kq.get(k)
        return len(v) if isinstance(v, (list, tuple)) else int(v or 0)
    da = n("da_them") + n("da_go") + n("da_ghi") + n("da_huy")
    chua, bo = n("chua_ghi"), n("bo_qua")
    phan = []
    for nhan, k in (("Đã thêm", "da_them"), ("Đã gỡ", "da_go"), ("Đã ghi", "da_ghi"), ("Đã hủy", "da_huy"),
                    ("Bỏ qua", "bo_qua"), ("Chưa ghi", "chua_ghi")):
        if n(k):
            phan.append(f"{nhan} {n(k)}")
    if kq.get("tt_cu") and kq.get("tt_moi"):
        phan.append(f"{_tt_ngoac(kq['tt_cu'])} → {_tt_ngoac(kq['tt_moi'])}")
    return {"da_ghi": da, "chua_ghi": chua, "bo_qua": bo, "tom_tat": " · ".join(phan)}


def ds_nhat_ky(loai: str = "", ma_bc2: str = "", gioi_han: int = 100, db_path=None) -> dict:
    """Nhật ký thao tác phía tool (sqlite): ai · lúc nào · loại · số HV · kết quả đã/chưa ghi."""
    gioi_han = max(1, min(int(gioi_han), 500))
    dang_db = rules.dang_luu_ma_bcii(ma_bc2) if ma_bc2 else None
    out = []
    for r in nhat_ky.gan_day(loai or None, dang_db, gioi_han, db_path):
        kq = r.get("ket_qua") or {}
        out.append({"id": r["id"], "luc": r["luc"], "nguoi": r.get("nguoi") or "", "loai": r["loai"],
                    "ten_loai": TEN_LOAI_NHAT_KY.get(r["loai"], r["loai"]), "ma_kh": r.get("ma_kh") or "",
                    "ma_bc2": r.get("ma_bc2") or "", "lo_id": r.get("lo_id") or "", "so_hv": r.get("so_hv") or 0,
                    "tom_tat_thao_tac": r.get("tom_tat") or "", "trang_thai": r["trang_thai"],
                    "ten_trang_thai": TEN_TRANG_THAI_NHAT_KY.get(r["trang_thai"], r["trang_thai"]),
                    "ket_qua": _tom_tat_ket_qua(kq)})
    return {"loai": loai, "ma_bc2": ma_bc2, "tong": len(out), "nhat_ky": out}
