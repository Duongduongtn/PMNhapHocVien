"""Tốt nghiệp & Báo cáo 2 (TNB, task 96) — LUẬT THUẦN, không đụng DB.

Nguồn: TDD §11F (v6.8), PRD TNB-03/04/06, decisions §23. Ghi vào DB Nạp `GPLX_CSDT`
chỉ qua SP có sẵn (PM cũ dùng chung DB) — module này chỉ NHẬN dữ liệu đã đọc và TRẢ
quyết định (nhóm học viên, vấn đề chặn/cảnh báo, số BC2 gợi ý). Đọc/ghi DB nằm ở
`tn_bc2_service.py` (task 97+).

Hình dạng dữ liệu vào (dict, key viết thường):
  hv   = {ma_dk, ten, hang, ma_kh, ten_kh, tt, ma_bc2, so_giay, bg}
         hang  = NguoiLX_HoSo.HangGPLX · tt = TT_XuLy ('03','09',…) · ma_bc2 = MaBC2 ('' nếu chưa)
         so_giay = SoGiayCNTN ('' nếu chưa) · bg = KhoaHoc.NgayBG 'YYYY-MM-DD' của khóa HV
  ctx  = {hom_nay: 'YYYY-MM-DD', ma_kh_chon: khóa đang chọn (khóa của BC1),
          bc2_map: {ma_bc2: trang_thai 0|1}, ma_bc2_dang_them: BC2 đang thêm vào ('' nếu chưa có)}
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any, Iterable

# ── Mức vấn đề (cùng quy ước phancong_rules) ──
CHAN = "chan"            # ⛔ không ghi được
CANH_BAO = "canh_bao"    # ⚠ ghi được sau khi xác nhận
THONG_TIN = "thong_tin"  # ℹ chỉ báo

# ── Bốn nhóm học viên khi thêm vào BC2 (TDD §11F.4) ──
SAN_SANG = "san_sang"      # ✅ tích sẵn
THI_LAI = "thi_lai"        # 🔁 không tích sẵn
CAN_XEM = "can_xem"        # ⚠ không tích sẵn, có hướng xử lý 1 chạm
KHONG_DUOC = "khong_duoc"  # ⛔ ẩn mặc định, kèm lý do

# Hướng xử lý 1 chạm cho nhóm Cần xem / Không đưa được
GOI_Y_TOT_NGHIEP = "cap_nhat_tot_nghiep"
GOI_Y_CUU = "cuu_trang_thai"
GOI_Y_GO_BC2 = "go_khoi_bc2"

TT_HOC_XONG = "03"    # ô tô: chưa tốt nghiệp · mô tô: chờ lập BC2
TT_TOT_NGHIEP = "09"
TT_DA_VAO_BC2 = "11"
TT_THI_LAI = ("14", "17", "18")
TT_KET_QUA_CUOI = ("13", "16", "19")

# Cứu trạng thái (TNB-06, TDD §11F.5)
NGUON_CUU = ("01", "02", "03", "04", "10", "12", "13")
DICH_CUU = ("09", "14", "17", "18")
CHAN_NGUON_CUU = ("11", "16", "19")

THI_LAI_THANG_MAC_DINH = 12

# Độ dài cột thật (đã verify DB Nạp 11/10/2026) và giới hạn đầu vào (TDD §11F.1/.7)
DO_DAI_COT: dict[str, int] = {
    "so_so_tn": 50, "so_quyet_dinh": 50, "so_giay_cntn": 20, "so_ccn": 20,
    "ma_bcii": 13, "so_bao_cao": 20, "ghi_chu": 255, "nguoi_tao": 30,
}
TOI_DA_DONG_DAN = 5000
TOI_DA_KY_TU_DONG = 40
TOI_DA_LY_DO = 255

_TEN_TRANG_THAI = {
    "01": "Mới nhận hồ sơ", "04": "Nhận hồ sơ từ nơi khác",
    "09": "Đã tốt nghiệp, chờ lập BC2", "11": "Đã vào BC2, chờ kết quả",
    "12": "Đã gửi BC2", "13": "Đã có kết quả cuối", "14": "Chưa đạt BC2 — cần lập lại",
    "16": "Đã có kết quả cuối", "17": "Thi sát hạch chưa đạt", "18": "Vắng sát hạch",
    "19": "Đã có kết quả cuối",
}


# ── Tiện ích ──
def _vd(muc: str, ma: str, noi_dung: str, ref: str = "") -> dict:
    return {"muc": muc, "ma": ma, "ref": ref, "noi_dung": noi_dung}


def _s(v: Any) -> str:
    return (v or "").strip() if isinstance(v, str) or v is None else str(v).strip()


def _dmy(d: str) -> str:
    """'2026-10-11' → '11/10/2026' (hiển thị người dùng)."""
    p = (d or "")[:10].split("-")
    return f"{p[2]}/{p[1]}/{p[0]}" if len(p) == 3 else (d or "")


def loai_hang(hang: str | None) -> str:
    """'moto' nếu hạng chứa `A` hoặc bằng `B1m`, ngược lại 'oto' — đúng điều kiện của
    `usp_NguoiLX_HoSo_ThemHS_BC2` (không dùng startswith('A') như nap.py)."""
    h = _s(hang).upper()
    return "moto" if ("A" in h or h == "B1M") else "oto"


def ten_trang_thai(tt: str | None, loai: str = "oto") -> str:
    """Tên nghiệp vụ của TT_XuLy (giao diện không lộ mã; mã chỉ là chú thích nhỏ)."""
    t = _s(tt)
    if t == TT_HOC_XONG:
        return "Đã học xong, chưa tốt nghiệp" if loai == "oto" else "Đã học xong, chờ lập BC2"
    return _TEN_TRANG_THAI.get(t, f"Trạng thái {t}" if t else "Chưa có trạng thái")


def tuoi_thang(bg: str | None, hom_nay: str) -> int | None:
    """Số tháng từ ngày bế giảng tới hôm nay (theo năm-tháng, như mockup). None nếu thiếu ngày."""
    try:
        a = [int(x) for x in (bg or "")[:10].split("-")]
        b = [int(x) for x in (hom_nay or "")[:10].split("-")]
        return (b[0] - a[0]) * 12 + (b[1] - a[1])
    except (ValueError, IndexError):
        return None


# ── Phân nhóm học viên khi thêm vào BC2 ──
def _bc2_dang_mo(ma_bc2: str, ctx: dict) -> bool:
    return bool(ma_bc2) and (ctx.get("bc2_map") or {}).get(ma_bc2) == 0


def _kq(nhom: str, ma: str, ly_do: str = "", goi_y: str | None = None, tt_ten: str = "",
        tuoi: int | None = None, tich_san: bool = False) -> dict:
    return {"nhom": nhom, "ma_ly_do": ma, "ly_do": ly_do, "goi_y_xu_ly": goi_y,
            "tich_san": tich_san, "tuoi_thang": tuoi, "ten_trang_thai": tt_ten}


def phan_nhom(hv: dict, loai: str, ctx: dict, thi_lai_thang: int = THI_LAI_THANG_MAC_DINH) -> dict | None:
    """Xếp một học viên vào nhóm khi thêm vào BC2 — xét theo thứ tự `khong_duoc` →
    `can_xem` → `thi_lai` → `san_sang`, trúng nhóm đầu thì dừng (TDD §11F.4).

    Trả None khi HV không thuộc danh sách của khóa đang chọn (vd ô tô `09`/mô tô `03` của
    khóa khác — chọn đúng khóa của họ ở bước ①) hoặc đã nằm trong chính BC2 đang thêm.
    `thi_lai_thang` chỉ gắn cờ `trong_nguong` cho nhóm thi lại (nút "Thêm HV thi lại trong N
    tháng" tích theo cờ này); KHÔNG ẩn HV quá hạn (dán danh sách vẫn tới được).
    """
    tt = _s(hv.get("tt"))
    ma_bc2 = _s(hv.get("ma_bc2"))
    ten_tt = ten_trang_thai(tt, loai)
    tuoi = tuoi_thang(hv.get("bg"), ctx.get("hom_nay", ""))
    la_khoa_chon = _s(hv.get("ma_kh")) != "" and _s(hv.get("ma_kh")) == _s(ctx.get("ma_kh_chon"))

    # Đã nằm trong chính BC2 đang thêm → không hiện lại
    dang_them = _s(ctx.get("ma_bc2_dang_them"))
    if dang_them and ma_bc2 == dang_them and tt == TT_DA_VAO_BC2:
        return None

    # 1. Không đưa được
    if loai_hang(hv.get("hang")) != loai:
        return _kq(KHONG_DUOC, "sai_loai", "Khác loại hạng với BC2 đang lập (ô tô và mô tô không trộn)", tt_ten=ten_tt)
    bg = _s(hv.get("bg"))
    if not bg or bg > _s(ctx.get("hom_nay")):
        ngay = f" ({_dmy(bg)})" if bg else ""
        return _kq(KHONG_DUOC, "khoa_chua_be_giang", f"Khóa {_s(hv.get('ten_kh')) or _s(hv.get('ma_kh'))} chưa bế giảng{ngay}",
                   tt_ten=ten_tt)
    if tt == TT_DA_VAO_BC2:
        if _bc2_dang_mo(ma_bc2, ctx):
            return _kq(KHONG_DUOC, "dang_o_bc2_mo", f"Đang ở BC2 số {ma_bc2} — gỡ khỏi BC2 đó trước",
                       GOI_Y_GO_BC2, ten_tt)
        return _kq(KHONG_DUOC, "da_vao_bc2_dong",
                   f"Đang ở BC2 số {ma_bc2 or '(không rõ)'} đã đóng — mở lại ở phần mềm cũ để xử lý", None, ten_tt)
    if tt in TT_KET_QUA_CUOI:
        goi_y = GOI_Y_CUU if tt in NGUON_CUU else None
        return _kq(KHONG_DUOC, "co_ket_qua_cuoi", f"Đã có kết quả cuối ({ten_tt})", goi_y, ten_tt)
    if tt in (TT_HOC_XONG, TT_TOT_NGHIEP) + TT_THI_LAI and _bc2_dang_mo(ma_bc2, ctx):
        return _kq(KHONG_DUOC, "dang_o_bc2_mo", f"Đang ở BC2 số {ma_bc2} — gỡ khỏi BC2 đó trước", GOI_Y_GO_BC2, ten_tt)
    if tt not in (TT_HOC_XONG, TT_TOT_NGHIEP) + TT_THI_LAI:
        if tt in NGUON_CUU:
            return _kq(CAN_XEM, "trang_thai_la", f"Trạng thái \"{ten_tt}\" chưa nằm trong nhóm chờ lập BC2",
                       GOI_Y_CUU, ten_tt) if la_khoa_chon else None
        return _kq(KHONG_DUOC, "trang_thai_ngoai_tap",
                   f"Trạng thái \"{ten_tt}\" chưa nằm trong nhóm chờ lập BC2", None, ten_tt)

    # 2. Thi lại (14/17/18 — bất kể khóa)
    if tt in TT_THI_LAI:
        kq = _kq(THI_LAI, "thi_lai", "", None, ten_tt, tuoi, tich_san=False)
        kq["trong_nguong"] = tuoi is not None and tuoi <= thi_lai_thang
        return kq

    # 3. Chỉ còn 03/09 — thuộc khóa đang chọn mới hiện
    if not la_khoa_chon:
        return None
    if loai == "oto":
        if tt == TT_HOC_XONG:
            return _kq(CAN_XEM, "chua_tot_nghiep", "Chưa tốt nghiệp — cần có giấy chứng nhận trước", GOI_Y_TOT_NGHIEP, ten_tt)
        if not _s(hv.get("so_giay")):
            return _kq(CAN_XEM, "thieu_so_giay", "Đã tốt nghiệp nhưng thiếu số giấy chứng nhận", GOI_Y_TOT_NGHIEP, ten_tt)
        return _kq(SAN_SANG, "", "", None, ten_tt, tich_san=True)
    # mô tô: không có bước tốt nghiệp → chỉ `03` là sẵn sàng; `09` không phải trạng thái của mô tô
    if tt == TT_HOC_XONG:
        return _kq(SAN_SANG, "", "", None, ten_tt, tich_san=True)
    return _kq(CAN_XEM, "trang_thai_la", f"Trạng thái \"{ten_tt}\" chưa nằm trong nhóm chờ lập BC2", None, ten_tt)


def trong_nguong_thi_lai(nhom: dict, thi_lai_thang: int = THI_LAI_THANG_MAC_DINH) -> bool:
    """Nút "Thêm HV thi lại trong N tháng" chỉ tích những HV `tuoi_thang <= N`."""
    t = nhom.get("tuoi_thang")
    return nhom.get("nhom") == THI_LAI and t is not None and t <= thi_lai_thang


def giai_thich_khong_hien(hv: dict, loai: str, ctx: dict) -> dict:
    """Vì sao HV không có trong danh sách để thêm vào BC2 (TNB-06 "Cứu trạng thái")."""
    n = phan_nhom(hv, loai, ctx)
    tt = _s(hv.get("tt"))
    ngoai_tap = tt not in (TT_HOC_XONG, TT_TOT_NGHIEP, TT_DA_VAO_BC2) + TT_THI_LAI + TT_KET_QUA_CUOI
    if ngoai_tap and (n is None or n["ma_ly_do"] in ("trang_thai_la", "trang_thai_ngoai_tap")):
        return {"ma": "trang_thai_ngoai_tap", "goi_y_xu_ly": GOI_Y_CUU if tt in NGUON_CUU else None,
                "noi_dung": f"Trạng thái \"{ten_trang_thai(tt, loai)}\" chưa nằm trong nhóm chờ lập BC2"}
    if n is None:
        if _s(hv.get("tt")) == TT_DA_VAO_BC2 and _s(hv.get("ma_bc2")) == _s(ctx.get("ma_bc2_dang_them")):
            return {"ma": "da_trong_bc2_nay", "noi_dung": "Đã nằm trong BC2 đang xem"}
        return {"ma": "khac_khoa", "noi_dung": "Thuộc khóa khác — chọn đúng khóa của học viên ở bước chọn khóa"}
    if n["nhom"] == KHONG_DUOC or n["nhom"] == CAN_XEM:
        return {"ma": n["ma_ly_do"], "noi_dung": n["ly_do"], "goi_y_xu_ly": n["goi_y_xu_ly"]}
    return {"ma": "dang_hien", "noi_dung": f"Đang có trong danh sách (nhóm {n['nhom']})", "nhom": n["nhom"]}


# ── Cứu trạng thái (TNB-06) ──
def kiem_cuu(hv: dict, dich: str, loai: str, ly_do: str) -> list[dict]:
    """Kiểm một lần chuyển `TT_XuLy`: nguồn ∈ NGUON_CUU, đích ∈ DICH_CUU, đích `09` cần số giấy
    và là ô tô, bắt buộc lý do ≤ 255."""
    vde: list[dict] = []
    tt = _s(hv.get("tt"))
    dich = _s(dich)
    if loai_hang(hv.get("hang")) != loai:
        vde.append(_vd(CHAN, "khac_loai", "Học viên khác loại hạng với loại đang chọn — không đổi trạng thái"))
    if tt in CHAN_NGUON_CUU:
        lydo = {"11": "đang ở BC2 — gỡ khỏi BC2 trước", "16": "đã đạt sát hạch", "19": "đã nhận GPLX"}[tt]
        vde.append(_vd(CHAN, "nguon_bi_chan", f"Không chuyển được vì {lydo}"))
    elif tt not in NGUON_CUU:
        vde.append(_vd(CHAN, "nguon_ngoai_tap", f"Trạng thái hiện tại ({tt or 'trống'}) không nằm trong nhóm được chuyển"))
    if dich not in DICH_CUU:
        vde.append(_vd(CHAN, "dich_khong_hop_le", "Chỉ được chuyển sang: Đã tốt nghiệp, Chưa đạt BC2, "
                       "Thi sát hạch chưa đạt hoặc Vắng sát hạch"))
    elif dich == tt:
        vde.append(_vd(CHAN, "khong_doi", "Trạng thái mới trùng trạng thái hiện tại"))
    if dich == "09":
        if loai != "oto":
            vde.append(_vd(CHAN, "dich_09_chi_o_to", "Mô tô không có bước tốt nghiệp"))
        if not _s(hv.get("so_giay")):
            vde.append(_vd(CHAN, "dich_09_thieu_so_giay", "Đưa về \"Đã tốt nghiệp\" cần có số giấy chứng nhận tốt nghiệp"))
    ld = _s(ly_do)
    if not ld:
        vde.append(_vd(CHAN, "thieu_ly_do", "Cần nhập lý do"))
    elif len(ld) > TOI_DA_LY_DO:
        vde.append(_vd(CHAN, "ly_do_qua_dai", f"Lý do tối đa {TOI_DA_LY_DO} ký tự"))
    return vde


def kiem_hoan_tac_cuu(tt_hien_tai: str, tt_vua_chuyen: str, tt_cu: str) -> list[dict]:
    """Hoàn tác cứu = về trạng thái ngay trước đó, **miễn luật đích** (về `03` là hợp lệ).
    Điều kiện duy nhất: HV vẫn đang đúng trạng thái vừa cứu (PM cũ chưa đổi tiếp)."""
    if not _s(tt_cu):
        return [_vd(CHAN, "khong_co_trang_thai_cu", "Không có trạng thái cũ để hoàn tác")]
    if _s(tt_hien_tai) != _s(tt_vua_chuyen):
        return [_vd(CHAN, "da_bi_doi", "Học viên đã bị đổi trạng thái sau lần chuyển — không hoàn tác được")]
    return []


# ── Đánh số BC2 (TNB-03) ──
def goi_y_so_bc2(loai: str, cac_ma_bcii: Iterable[str], nam: int, so_bc1: str | None = None) -> str:
    """Số BC2 gợi ý (nhân viên sửa được, kiểm trùng riêng).
    Ô tô: `MAX(n)+1` trong các `MaBCII` dạng `n/<năm>`; mô tô: số BC1 bỏ tiền tố `A1A2`."""
    if loai == "moto":
        s = _s(so_bc1)
        return s[4:] if s.upper().startswith("A1A2") else s
    mau = re.compile(rf"^(\d+)/{int(nam)}$")
    cao_nhat = 0
    for ma in cac_ma_bcii:
        m = mau.match(_s(ma))
        if m:
            cao_nhat = max(cao_nhat, int(m.group(1)))
    return f"{cao_nhat + 1}/{int(nam)}"


def khoa_so_bc2(so: str | None) -> str:
    """Khóa so sánh số BC2: không phân biệt hoa/thường và coi `Ð` (U+00D0, dạng đọc ra từ cột
    `MaBCII` varchar, Latin1) = `Đ` (U+0110, dạng nhân viên gõ / cột nvarchar) — cùng một byte 0xD0
    trong DB (collation Latin1_General_CI_AS), nên khóa chính coi chúng là một."""
    return _s(so).replace("Ð", "Đ").replace("ð", "đ").casefold()


def dang_luu_ma_bcii(so: str | None) -> str:
    """Dạng của `MaBCII` (varchar) khi đọc/ghi qua pymssql: `Đ` → `Ð` (như DB trả ra)."""
    return _s(so).replace("Đ", "Ð").replace("đ", "ð")


def kiem_so_bc2(so: str | None, da_co: Iterable[str]) -> list[dict]:
    """Số BC2 (= `MaBCII`): không rỗng, ≤ 13 ký tự (varchar 13), không trùng (không phân biệt
    hoa/thường, `Ð` = `Đ`)."""
    s = _s(so)
    if not s:
        return [_vd(CHAN, "thieu_so", "Cần nhập số báo cáo")]
    vde: list[dict] = []
    if len(s) > DO_DAI_COT["ma_bcii"]:
        vde.append(_vd(CHAN, "so_qua_dai", f"Số báo cáo tối đa {DO_DAI_COT['ma_bcii']} ký tự"))
    if khoa_so_bc2(s) in {khoa_so_bc2(x) for x in da_co}:
        vde.append(_vd(CHAN, "trung_so", f"Số BC2 {s} đã tồn tại — đổi số khác"))
    return vde


# ── Độ dài cột + giới hạn đầu vào (TDD §11F.1/.7) ──
def kiem_do_dai(truong: str, gia_tri: str | None) -> list[dict]:
    """Chặn trước khi gọi SP nếu vượt độ dài cột (SP chỉ báo lỗi cắt chuỗi giữa chừng)."""
    gioi_han = DO_DAI_COT.get(truong)
    if gioi_han is None:
        raise KeyError(truong)
    n = len(_s(gia_tri))
    if n > gioi_han:
        return [_vd(CHAN, "vuot_do_dai", f"Tối đa {gioi_han} ký tự (đang {n})", ref=truong)]
    return []


def kiem_danh_sach_dan(dong: Iterable[str] | None) -> list[dict]:
    """`khop-danh-sach` / `ds_ma_dk[]`: ≤ 5.000 dòng, mỗi dòng ≤ 40 ký tự (sau khi bỏ dòng trống)."""
    ds = [_s(x) for x in (dong or []) if _s(x)]
    if len(ds) > TOI_DA_DONG_DAN:
        return [_vd(CHAN, "qua_nhieu_dong", f"Tối đa {TOI_DA_DONG_DAN} dòng (đang {len(ds)})")]
    dai = next((x for x in ds if len(x) > TOI_DA_KY_TU_DONG), None)
    if dai is not None:
        return [_vd(CHAN, "dong_qua_dai", f"Mỗi dòng tối đa {TOI_DA_KY_TU_DONG} ký tự")]
    return []


def co_chan(vde: Iterable[dict]) -> bool:
    return any(v.get("muc") == CHAN for v in vde)


# ══════════════ Tốt nghiệp ô tô (TNB-01/02, task 101) ══════════════
TT_VAO_BC2_TRO_DI = ("11", "12", "13", "14", "16", "17", "18", "19")
_MAU_SO_GIAY = re.compile(r"^([A-Za-z0-9]+)\|(\d+)$")

# kết quả dự kiến của một dòng ghi tốt nghiệp
KQ_LEN_09 = "se_len_09"                    # 03 + có số giấy → 09
KQ_LUU_SO_TRUOC = "luu_so_truoc"           # 03, chưa có số giấy → chỉ ghi sổ/quyết định, ở lại 03
KQ_GIU_09 = "giu_09_sua_thong_tin"         # 09 + số giấy → sửa thông tin, giữ 09
KQ_DA_VAO_BC2 = "khong_doi_trang_thai_da_vao_bc2"   # ≥ 11, số giấy lần đầu → ghi số giấy, KHÔNG đổi trạng thái
KQ_KHONG_DOI = "khong_doi"                 # nhập y hệt hiện trạng
KQ_BO_QUA = "bo_qua"
KQ_CHAN = "chan"
KQ_GHI_DUOC = (KQ_LEN_09, KQ_LUU_SO_TRUOC, KQ_GIU_09, KQ_DA_VAO_BC2)


def bo_dau(s: str | None) -> str:
    """Chuẩn hóa để tìm không dấu: bỏ dấu, `đ→d`, chữ thường."""
    t = unicodedata.normalize("NFD", _s(s))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return t.replace("đ", "d").replace("Đ", "D").casefold()


def khoa_so_giay(s: str | None) -> str:
    """Khóa so sánh số giấy CNTN: bỏ `|` và khoảng trắng, không phân biệt hoa/thường
    (SP `ThemHS_BC2` trả số giấy đã bỏ `|`; DB lưu `N1|7282`)."""
    return re.sub(r"[|\s]", "", _s(s)).casefold()


def tach_so_giay(s: str | None) -> tuple[str, int] | None:
    """`N1|7282` → ('N1', 7282); không đúng dạng → None."""
    m = _MAU_SO_GIAY.match(_s(s))
    return (m.group(1), int(m.group(2))) if m else None


def so_giay_ke_tiep(cac_so: Iterable[tuple[str, str]]) -> str:
    """Số giấy gợi ý kế tiếp từ các cặp (số giấy, ngày in ISO): lấy tiền tố của số in GẦN NHẤT rồi
    `MAX + 1` trong cùng tiền tố (dữ liệu 11/10/2026: dãy `N1|<n>` chung toàn cơ sở, không đánh lại
    theo năm/khóa; lớn nhất `N1|7328` → `N1|7329`). Không có dữ liệu → ''."""
    ds = [(tach_so_giay(so), ngay) for so, ngay in cac_so]
    ds = [(t, ngay) for t, ngay in ds if t]
    if not ds:
        return ""
    tien_to = max(ds, key=lambda x: (x[1] or "", x[0][1]))[0][0]
    cao = max(t[1] for t, _n in ds if t[0] == tien_to)
    return f"{tien_to}|{cao + 1}"


def trang_thai_tot_nghiep(tt: str | None, ma_bc2: str | None = "") -> str:
    """`chua_tot_nghiep` (03) · `da_tot_nghiep` (09) · `da_vao_bc2` (≥ 11 hoặc có MaBC2) · `khac`."""
    t = _s(tt)
    if t in TT_VAO_BC2_TRO_DI or _s(ma_bc2):
        return "da_vao_bc2"
    return {TT_HOC_XONG: "chua_tot_nghiep", TT_TOT_NGHIEP: "da_tot_nghiep"}.get(t, "khac")


def chuan_ngay(s: str | None) -> str | None:
    """'2026-09-30' hoặc '30/09/2026' → '2026-09-30'; rỗng → ''; sai → None."""
    t = _s(s)
    if not t:
        return ""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(t[:10], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _vd_tn(muc: str, ma: str, noi_dung: str) -> dict:
    return {"muc": muc, "ma": ma, "noi_dung": noi_dung}


def phan_tich_dong_tn(hv: dict, so_giay: str | None, chung: dict | None, ctx: dict) -> dict:
    """Phân tích MỘT dòng ghi tốt nghiệp (chạy thử, không ghi) — TDD §11F.2/§11F.7, PRD TNB-01/02.

    hv   = {ma_dk, hang, ma_kh, tt, ma_bc2, bg, so_giay, so_so_tn, ngay_vao_so, so_quyet_dinh, ngay_ra_qd, ngay_in}
    chung= {so_so_tn, ngay_vao_so, so_quyet_dinh, ngay_ra_qd, ngay_in} — giá trị điền chung ('' = giữ của HV)
    ctx  = {hom_nay, so_giay_khac: set[khoa_so_giay đang thuộc HV KHÁC], trung_lo: set[khoa_so_giay trùng trong lô]}
    Trả {ket_qua, ghi_duoc, hieu_luc, chan[], canh_bao[], thong_tin[]}.
    """
    chung = chung or {}
    chan: list[dict] = []
    canh_bao: list[dict] = []
    thong_tin: list[dict] = []
    tt = _s(hv.get("tt"))
    da_bc2 = tt in TT_VAO_BC2_TRO_DI or bool(_s(hv.get("ma_bc2")))
    giay_cu = _s(hv.get("so_giay"))
    giay = _s(so_giay)

    def hieu_luc(k: str, kieu: str = "s") -> str:
        v = _s(chung.get(k))
        return v if v else _s(hv.get(k))

    # ngày: điền chung ghi đè; sai định dạng → chặn
    ngay: dict[str, str] = {}
    for k in ("ngay_vao_so", "ngay_ra_qd", "ngay_in"):
        raw = hieu_luc(k)
        iso = chuan_ngay(raw)
        if iso is None:
            chan.append(_vd_tn(CHAN, "ngay_khong_hop_le", f"Ngày không hợp lệ ({k})"))
            iso = ""
        ngay[k] = iso
    hl = {"so_so_tn": hieu_luc("so_so_tn"), "so_quyet_dinh": hieu_luc("so_quyet_dinh"), "so_giay": giay, **ngay}

    # luật chung
    if loai_hang(hv.get("hang")) != "oto":
        chan.append(_vd_tn(CHAN, "sai_loai", "Mô tô không có bước tốt nghiệp"))
    bg = _s(hv.get("bg"))
    if not bg or bg > _s(ctx.get("hom_nay")):
        chan.append(_vd_tn(CHAN, "khoa_chua_be_giang", "Khóa chưa bế giảng — chỉ xem, không ghi được"))
    if tt not in (TT_HOC_XONG, TT_TOT_NGHIEP) and not da_bc2:
        chan.append(_vd_tn(CHAN, "trang_thai_khong_hop_le",
                           f"Học viên đang ở \"{ten_trang_thai(tt, 'oto')}\" — chưa tới bước tốt nghiệp"))
    for truong, gia_tri in (("so_giay_cntn", giay), ("so_so_tn", hl["so_so_tn"]), ("so_quyet_dinh", hl["so_quyet_dinh"])):
        chan += [_vd_tn(CHAN, v["ma"], f"{truong}: {v['noi_dung']}") for v in kiem_do_dai(truong, gia_tri)]

    # trùng số giấy: chỉ khi ĐỔI sang số đang thuộc HV khác (DB còn 463 số trùng cũ — không chặn oan)
    if giay:
        k = khoa_so_giay(giay)
        if k in (ctx.get("trung_lo") or set()):
            chan.append(_vd_tn(CHAN, "trung_trong_lo", f"Số giấy {giay} bị trùng trong danh sách đang nhập"))
        if k != khoa_so_giay(giay_cu) and k in (ctx.get("so_giay_khac") or set()):
            chan.append(_vd_tn(CHAN, "trung_db", f"Số giấy {giay} đã thuộc học viên khác"))
        elif k == khoa_so_giay(giay_cu) and k in (ctx.get("so_giay_khac") or set()):
            thong_tin.append(_vd_tn(THONG_TIN, "trung_co_san", "Số giấy này vốn đã trùng với học viên khác từ trước"))

    # dữ liệu bất thường: 03/09 mà đã gắn MaBC2 — SP sẽ đổi 03→09 trong khi báo cáo đã lập → không ghi
    if da_bc2 and tt in (TT_HOC_XONG, TT_TOT_NGHIEP):
        chan.append(_vd_tn(CHAN, "trang_thai_bc2_bat_thuong",
                           f"Học viên đang \"{ten_trang_thai(tt, 'oto')}\" nhưng lại gắn BC2 {_s(hv.get('ma_bc2'))} — "
                           "dữ liệu bất thường, xử lý ở phần mềm cũ"))

    # kết quả dự kiến
    ket_qua = KQ_BO_QUA
    if da_bc2:
        if giay_cu:
            if giay == giay_cu and all(hl[k] == _s(hv.get(k)) or not hl[k] for k in ("so_so_tn", "so_quyet_dinh")):
                ket_qua = KQ_KHONG_DOI
            else:
                chan.append(_vd_tn(CHAN, "da_vao_bc2_khong_sua", "Học viên đã vào BC2 — phải gỡ khỏi BC2 trước khi sửa"))
        elif giay:
            ket_qua = KQ_DA_VAO_BC2
            canh_bao.append(_vd_tn(CANH_BAO, "bao_cao_da_lap_khong_doi_theo",
                                   "Học viên đã vào báo cáo: ghi số giấy nhưng trạng thái và báo cáo đã lập không đổi theo"))
        else:
            thong_tin.append(_vd_tn(THONG_TIN, "khong_co_gi_de_ghi", "Không có số giấy để ghi"))
    elif tt == TT_HOC_XONG:
        if giay:
            if not hl["so_so_tn"] or not hl["so_quyet_dinh"]:
                chan.append(_vd_tn(CHAN, "thieu_so_so_hoac_quyet_dinh",
                                   "Cấp số giấy cần có số sổ tốt nghiệp và số quyết định"))
            else:
                ket_qua = KQ_LEN_09
        elif hl["so_so_tn"] or hl["so_quyet_dinh"]:
            ket_qua = KQ_LUU_SO_TRUOC
        else:
            thong_tin.append(_vd_tn(THONG_TIN, "khong_co_gi_de_ghi", "Chưa có số sổ/quyết định/số giấy để ghi"))
    elif tt == TT_TOT_NGHIEP:
        if giay:
            same = (giay == giay_cu and all(hl[k] == _s(hv.get(k)) for k in ("so_so_tn", "so_quyet_dinh"))
                    and all(ngay[k] == (chuan_ngay(hv.get(k)) or "") for k in ngay))
            ket_qua = KQ_KHONG_DOI if same else KQ_GIU_09
        else:
            thong_tin.append(_vd_tn(THONG_TIN, "dung_huy_tot_nghiep",
                                    "Muốn bỏ tốt nghiệp thì dùng \"Hủy tốt nghiệp\", không để trống số giấy ở đây"))

    if giay and not ngay["ngay_in"]:
        canh_bao.append(_vd_tn(CANH_BAO, "thieu_ngay_in", "Chưa có ngày in giấy chứng nhận"))
    if chan:
        ket_qua = KQ_CHAN
    return {"ma_dk": _s(hv.get("ma_dk")), "ket_qua": ket_qua, "ghi_duoc": ket_qua in KQ_GHI_DUOC,
            "hieu_luc": hl, "chan": chan, "canh_bao": canh_bao, "thong_tin": thong_tin}
