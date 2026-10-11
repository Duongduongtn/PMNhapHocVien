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

_Q_BC1 = "SELECT MaBCI, MaKH, MaCSDT, SoBaoCao, SoHocSinh FROM BaoCaoI"
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


def doc_bc(cur) -> tuple[dict, dict, dict, dict]:
    """Đọc BC1 + BC2 hiện có: (bc1_theo_khoa, bc2_map, bc2_bci, bc2_theo_bc1). Không cache."""
    cur.execute(_Q_BC1)
    bc1_theo_khoa = {_s(r["MaKH"]): {"ma_bci": _s(r["MaBCI"]), "ma_csdt": _s(r.get("MaCSDT")),
                                     "so_bao_cao": _s(r["SoBaoCao"]), "so_hoc_sinh": r.get("SoHocSinh")}
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
        "bc1": ({"ma_bci": bc1["ma_bci"], "so_bao_cao": bc1["so_bao_cao"], "so_hoc_sinh": bc1["so_hoc_sinh"]}
                if bc1 else None),
        "bc2_cua_khoa": bc2_theo_bc1.get(bc1["ma_bci"], []) if bc1 else [],
        "trung": rules.khoa_so_bc2(so) in {rules.khoa_so_bc2(m) for m in bc2_map} if so else False,
    }


def _loi_trung_so(e: Exception) -> bool:
    t = str(e)
    return "2627" in t or "PRIMARY KEY" in t.upper() or "duplicate key" in t.lower()


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
            nhat_ky.lo_cap_nhat(lo_id, trang_thai="that_bai", ket_qua={"loi": loi[:200]})
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
            nhat_ky.lo_cap_nhat(lo_id, trang_thai="that_bai", ket_qua={"loi_nghiep_vu": job["loi_nghiep_vu"]})
        except Exception as e:  # noqa: BLE001
            job["loi_nghiep_vu"] = {"ma": "loi_he_thong", "noi_dung": str(e)[:200]}
            job["trang_thai"] = "loi_giua_chung"
            nhat_ky.lo_cap_nhat(lo_id, trang_thai="loi_giua_chung", ket_qua={"loi_nghiep_vu": job["loi_nghiep_vu"]})

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
