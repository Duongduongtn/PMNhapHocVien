"""Dựng file Excel kết quả học tập của một khóa (KQD-09). Hàm thuần — không DB, không mạng.

Form: 1 sheet `KET_QUA_HOC_TAP` = khối đầu (cơ quan/cơ sở/khóa/ngày lập/người lập/tóm tắt) + bảng chi tiết
22 cột. Bám sổ mẫu `thamkhao/So_theo_doi_ket_qua_hoc_tap_DTLX_TT17.xlsx`: điểm Lý thuyết = TB(Lý thuyết,
Mô phỏng), điểm Thực hành = TB(Sa hình, Chữ chi, Đường trường), làm tròn 1 chữ số; chưa đủ môn thì trống.
Quyết định: TDD §11D.11, TDD-decisions §25.
"""
from __future__ import annotations

import io
import re
from datetime import date, datetime

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app import ketqua_quydoi

TEN_SHEET = "KET_QUA_HOC_TAP"
HOAN_THANH = "Hoàn thành"
CHUA_HOAN_THANH = "Chưa hoàn thành"

# Nhãn trạng thái hồ sơ — khớp TT_LABEL ở CapNhatKQDT.tsx.
TT_NHAN = {
    "03": "Đã đăng ký", "04": "Đã đăng ký",
    "09": "Đã cập nhật · Đạt", "10": "Đã cập nhật · Không đạt",
    "12": "Đã kết xuất gửi Sở", "13": "Hoàn thành",
    "14": "Sở từ chối", "90": "Đang giải trình",
}
MON_NHAN = {
    "ly_thuyet": "Lý thuyết", "mo_phong": "Mô phỏng", "hinh": "Sa hình",
    "tien_lui": "Chữ chi", "duong": "Đường trường",
}
_COT_DIEM = (
    ("ly_thuyet", "DiemKQLyThuyet"), ("mo_phong", "DiemKQMoPhong"), ("hinh", "DiemKQHinh"),
    ("tien_lui", "DiemKQTienLui"), ("duong", "DiemKQThucHanh"),
)

# (tiêu đề, độ rộng) — thứ tự cột của bảng (22 cột).
CAC_COT: list[tuple[str, float]] = [
    ("STT", 5), ("Mã đăng ký", 24), ("Họ và tên", 28), ("Ngày sinh", 12), ("Số CCCD", 15), ("Hạng", 8),
    ("Lý thuyết", 9), ("Mô phỏng", 9), ("Sa hình", 9), ("Chữ chi", 9), ("Đường trường", 10),
    ("Điểm Lý thuyết", 10), ("Điểm Thực hành", 10),
    ("Giờ sân", 8), ("Km sân", 8), ("Giờ đường", 9), ("Km đường", 9),
    ("Kết quả khóa học", 16), ("Ngày xét hoàn thành", 13), ("Trạng thái hồ sơ", 22),
    ("Số giấy HTKH", 22), ("Ghi chú", 38),
]
HANG_TIEU_DE = 9           # hàng tiêu đề bảng; dữ liệu từ hàng 10

_FONT = "Times New Roman"
_VIEN = Side(style="thin", color="999999")
_KHUNG = Border(left=_VIEN, right=_VIEN, top=_VIEN, bottom=_VIEN)


def _so(v, nd: int | None = None) -> float | None:
    """Số từ DB (cột real: 18.399999618…) → float; làm tròn `nd` chữ số nếu có để ô Excel không lộ đuôi."""
    if v is None:
        return None
    return round(float(v), nd) if nd is not None else float(v)


def _tb(*vals: float | None) -> float | None:
    """Trung bình làm tròn 1 chữ số; thiếu bất kỳ môn nào → None (như sổ mẫu)."""
    if any(v is None for v in vals):
        return None
    return round(sum(vals) / len(vals) + 1e-9, 1)


def _ngay_luu(v) -> date | None:
    """'yyyymmdd' (cột NguoiLX.NgaySinh) → date; sai dạng/thiếu → None (ô trống)."""
    so = re.sub(r"\D", "", str(v or ""))
    if len(so) != 8:
        return None
    try:
        return date(int(so[:4]), int(so[4:6]), int(so[6:]))
    except ValueError:
        return None


def _ngay_vn(v: str | None) -> date | None:
    """'dd/mm/yyyy' (CONVERT 103 của SQL Server) → date."""
    m = re.fullmatch(r"\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*", v or "")
    if not m:
        return None
    try:
        return date(int(m[3]), int(m[2]), int(m[1]))
    except ValueError:
        return None


def ket_luan(v) -> str | None:
    """KetLuanCSDT (bit/'1'/'0'/NULL) → 'dat' | 'khong_dat' | None."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    return "dat" if int(v) == 1 else "khong_dat"


def dong_hv(h: dict, ngay_thi: date | None) -> dict:
    """1 hàng DB → các giá trị hiển thị của 1 dòng bảng (đã tính điểm TB, kết quả, ghi chú)."""
    diem = {k: _so(h.get(cot), 1) for k, cot in _COT_DIEM}
    kl = ket_luan(h.get("KetLuanCSDT"))
    gio_d, km_d = _so(h.get("TGThucHanhDuong"), 2), _so(h.get("TongQDThucHanh"), 2)
    thieu = [MON_NHAN[k] for k, v in diem.items() if v is None]
    ghi_chu: list[str] = []
    if len(thieu) < len(diem) and thieu:
        ghi_chu.append("Thiếu: " + ", ".join(thieu))
    elif len(thieu) == len(diem):
        ghi_chu.append("Chưa có điểm")
    hang_cat = ketqua_quydoi.phan_loai_hang(h.get("MaHangMoi"), h.get("HangGPLX"))
    for cb in ketqua_quydoi.canh_bao_duong(gio_d, km_d, hang_cat):
        ten = "Giờ đường" if cb["loai"] == "gio_duong" else "Km đường"
        ghi_chu.append(f"{ten} {cb['gia_tri']:g} < {cb['goi_y']}")
    tt = (h.get("TT_XuLy") or "").strip()
    return {
        "ma_dk": h.get("MaDK"), "ho_ten": h.get("HoVaTen"),
        "ngay_sinh": _ngay_luu(h.get("NgaySinh")),
        "cccd": (h.get("SoCMT") or "").strip(),
        "hang": ((h.get("MaHangMoi") or h.get("HangGPLX") or "").strip()),
        "diem": diem,
        "diem_lt": _tb(diem["ly_thuyet"], diem["mo_phong"]),
        "diem_th": _tb(diem["hinh"], diem["tien_lui"], diem["duong"]),
        "gio_san": _so(h.get("TGThucHanhHinh"), 2), "km_san": _so(h.get("QDThucHanhHinh"), 2),
        "gio_duong": gio_d, "km_duong": km_d,
        "ket_qua": {"dat": HOAN_THANH, "khong_dat": CHUA_HOAN_THANH}.get(kl or "", ""),
        "ngay_xet": ngay_thi if kl == "dat" else None,
        "trang_thai": TT_NHAN.get(tt, tt),
        "so_giay": (h.get("SoGiayCNTN") or "").strip(),
        "ghi_chu": "; ".join(ghi_chu),
    }


def _thu_tu(h: dict) -> tuple:
    so = re.sub(r"\D", "", str(h.get("SoHoSo") or ""))
    return (int(so) if so else 10**9, str(h.get("MaDK") or ""))


def ten_file(ma_kh: str, ngay: date) -> str:
    """`KetQuaHocTap_<MaKH>_<dd-mm-yyyy>.xlsx` — chỉ ASCII an toàn cho tên file."""
    ma = re.sub(r"[^A-Za-z0-9_-]", "", ma_kh or "") or "khoa"
    return f"KetQuaHocTap_{ma}_{ngay:%d-%m-%Y}.xlsx"


def dung_workbook(khoa: dict, hv_rows: list[dict], co_so: dict, nguoi_lap: str,
                  ngay_lap: datetime, chuong_trinh: str = "cu") -> bytes:
    """Dựng workbook → bytes .xlsx.

    `khoa`: MaKH, TenKH, HangGPLX, NgayKG/NgayBG/NgayThi ('dd/mm/yyyy').
    `co_so`: {co_quan_chu_quan, ten_co_so_dao_tao} (có thể trống)."""
    ngay_thi = _ngay_vn(khoa.get("NgayThi"))
    dong = [dong_hv(h, ngay_thi) for h in sorted(hv_rows, key=_thu_tu)]
    n_ht = sum(d["ket_qua"] == HOAN_THANH for d in dong)
    n_chua = sum(d["ket_qua"] == CHUA_HOAN_THANH for d in dong)
    n_thieu = len(dong) - n_ht - n_chua

    wb = Workbook()
    ws = wb.active
    ws.title = TEN_SHEET
    so_cot = len(CAC_COT)
    cuoi = get_column_letter(so_cot)

    def khoi(hang: int, text: str, *, dam=False, co=12, can="left") -> None:
        ws.merge_cells(f"A{hang}:{cuoi}{hang}")
        c = ws[f"A{hang}"]
        c.value = text
        c.font = Font(name=_FONT, size=co, bold=dam)
        c.alignment = Alignment(horizontal=can, vertical="center", wrap_text=True)

    ct = "Cũ (TT12/2025)" if chuong_trinh != "moi" else "Mới (TT108/2026)"
    hang_moi = [(h.get("MaHangMoi") or "").strip() for h in hv_rows if (h.get("MaHangMoi") or "").strip()]
    hang_khoa = (max(set(hang_moi), key=hang_moi.count) if hang_moi else (khoa.get("HangGPLX") or "").strip())
    khoi(1, (co_so.get("co_quan_chu_quan") or "").strip(), dam=True)
    khoi(2, (co_so.get("ten_co_so_dao_tao") or "").strip(), dam=True)
    khoi(3, "KẾT QUẢ HỌC TẬP CỦA HỌC VIÊN", dam=True, co=15, can="center")
    khoi(4, f"Khóa học: {(khoa.get('TenKH') or '').strip()} ({khoa.get('MaKH')})"
            f"   ·   Hạng: {hang_khoa}   ·   Chương trình: {ct}")
    khoi(5, f"Khai giảng: {khoa.get('NgayKG') or ''}   ·   Bế giảng: {khoa.get('NgayBG') or ''}"
            f"   ·   Ngày thi: {khoa.get('NgayThi') or ''}")
    khoi(6, f"Ngày lập: {ngay_lap:%d/%m/%Y %H:%M}   ·   Người lập: {nguoi_lap}")
    khoi(7, f"Tổng {len(dong)} học viên   ·   Hoàn thành {n_ht}   ·   Chưa hoàn thành {n_chua}"
            f"   ·   Chưa đủ điểm {n_thieu}", dam=True)
    ws.row_dimensions[3].height = 24

    # --- Tiêu đề bảng
    nen = PatternFill("solid", fgColor="D9E2F3")
    for i, (ten, rong) in enumerate(CAC_COT, start=1):
        c = ws.cell(row=HANG_TIEU_DE, column=i, value=ten)
        c.font = Font(name=_FONT, size=11, bold=True)
        c.fill = nen
        c.border = _KHUNG
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = rong
    ws.row_dimensions[HANG_TIEU_DE].height = 32

    # --- Dữ liệu
    do = Font(name=_FONT, size=11, color="C00000")
    xanh = Font(name=_FONT, size=11, color="1E7B34", bold=True)
    thuong = Font(name=_FONT, size=11)
    giua = Alignment(horizontal="center", vertical="center")
    trai = Alignment(horizontal="left", vertical="center", wrap_text=True)
    for stt, d in enumerate(dong, start=1):
        r = HANG_TIEU_DE + stt
        gia_tri = [
            stt, d["ma_dk"], d["ho_ten"], d["ngay_sinh"], d["cccd"], d["hang"],
            d["diem"]["ly_thuyet"], d["diem"]["mo_phong"], d["diem"]["hinh"],
            d["diem"]["tien_lui"], d["diem"]["duong"], d["diem_lt"], d["diem_th"],
            d["gio_san"], d["km_san"], d["gio_duong"], d["km_duong"],
            d["ket_qua"], d["ngay_xet"], d["trang_thai"], d["so_giay"], d["ghi_chu"],
        ]
        for i, v in enumerate(gia_tri, start=1):
            c = ws.cell(row=r, column=i, value=v if v != "" else None)
            c.font = thuong
            c.border = _KHUNG
            c.alignment = trai if i in (2, 3, 22) else giua
            if i == 5 and v:                      # CCCD: ép chuỗi, không để Excel đổi thành 1.2E+11
                c.number_format = "@"
            elif i in (4, 19):
                c.number_format = "dd/mm/yyyy"
            elif 7 <= i <= 13:
                c.number_format = "0.0"
                if isinstance(v, (int, float)) and v < 5:
                    c.font = do
            elif 14 <= i <= 17:
                c.number_format = "0.##"
            elif i == 18:
                c.font = xanh if v == HOAN_THANH else do if v == CHUA_HOAN_THANH else thuong

    # --- Lọc, đóng băng, in A4 ngang
    cuoi_dl = HANG_TIEU_DE + max(len(dong), 1)
    ws.auto_filter.ref = f"A{HANG_TIEU_DE}:{cuoi}{cuoi_dl}"
    ws.freeze_panes = f"A{HANG_TIEU_DE + 1}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = f"{HANG_TIEU_DE}:{HANG_TIEU_DE}"
    ws.page_margins.left = ws.page_margins.right = 0.5
    ws.page_margins.top = ws.page_margins.bottom = 0.6

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
