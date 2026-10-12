"""Dựng "Sổ theo dõi kết quả học tập" (mẫu Phụ lục VI, TT17) — KQD-10. Hàm thuần, không DB.

Bám sheet `SO_PHU_LUC_VI` của `thamkhao/So_theo_doi_ket_qua_hoc_tap_DTLX_TT17.xlsx`: A4 dọc, chân trang
`Trang &P/&N`, 2 hàng tiêu đề bảng lặp ở mọi trang, Times New Roman 12, nền tiêu đề `D9EAF7`, viền mỏng.
Khác mẫu CÓ CHỦ ĐÍCH (user yêu cầu): lề thu hẹp (trái 2 · phải 1 · trên/dưới 1,5 cm), cột Họ tên tự giãn
theo tên dài nhất và không xuống dòng, `Người lập` để trống, danh sách xếp theo tên (alphabet tiếng Việt).
Không có bìa, không khối chữ ký (mẫu không có). Quyết định: TDD §11D.12, TDD-decisions §26.
"""
from __future__ import annotations

import io
import math
import unicodedata
from datetime import date, datetime

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from app import ketqua_xuat as kx

TEN_SHEET = "SO_PHU_LUC_VI"
TIEN_TO_FILE = "SoTheoDoiKetQuaHocTap"
HANG_TIEU_DE_1, HANG_TIEU_DE_2 = 10, 11     # 2 hàng tiêu đề bảng (lặp mọi trang); dữ liệu từ hàng 12
HANG_DU_LIEU_DAU = 12

_FONT = "Times New Roman"
_NEN = PatternFill("solid", fgColor="FFD9EAF7")   # ARGB như file mẫu
_VIEN = Side(style="thin", color="FFA6A6A6")   # như file mẫu (viền xám)
_KHUNG = Border(left=_VIEN, right=_VIEN, top=_VIEN, bottom=_VIEN)
_DO = "C00000"

# --- Lề trang (cm → inch): trái 2 · phải 1 · trên/dưới 1,5 (mẫu: 3/2/2/2) ---
_CM = 1 / 2.54
LE_TRAI, LE_PHAI, LE_TREN, LE_DUOI = 2 * _CM, 1 * _CM, 1.5 * _CM, 1.5 * _CM

# --- Độ rộng cột (mẫu: A 4,4 · B 25 · C 9,4 · D–E 7,4 · F 12,4 · G 13,4 · H 12,4) ---
_RONG_B_MIN, _RONG_B_MAX = 25.0, 34.0
_RONG_C_MIN, _RONG_C_MAX = 9.4, 14.0
_RONG_F = 16.5            # đủ cho "Chưa hoàn thành" trên một dòng
_RONG_THUONG = 1.05       # ước lượng độ rộng 1 ký tự thường Times New Roman 12 theo đơn vị cột Excel
_RONG_HOA = 1.6           # chữ HOA rộng hơn nhiều (tên trong DB thường lưu viết hoa)


def _rong_chu(text: str) -> float:
    """Độ rộng ước lượng của chuỗi (đơn vị cột Excel): chữ hoa 1,6 · ký tự khác 1,05 (hơi dư để an toàn)."""
    return sum(_RONG_HOA if c.isupper() else _RONG_THUONG for c in text)


def _so_dong(text: str, rong_o: float) -> int:
    """Số dòng ước lượng khi `text` (có thể nhiều đoạn \n) xuống dòng trong ô rộng `rong_o`."""
    return sum(max(1, math.ceil(_rong_chu(seg) / max(rong_o, 1))) for seg in text.split("\n"))


# =========================== Xếp theo tên tiếng Việt ===========================
_BANG_CHU = "aăâbcdđeêghiklmnoôơpqrstuưvxy"
_HANG_CHU = {c: i for i, c in enumerate(_BANG_CHU)}
_THANH = {"̀": 1, "́": 2, "̉": 3, "̃": 4, "̣": 5}   # huyền, sắc, hỏi, ngã, nặng
_NON, _TRANG, _RAU = "̂", "̆", "̛"                            # ^ , ˘ , râu (ơ ư)


def _khoa_tu(tu: str) -> tuple[tuple[int, ...], int]:
    """(thứ hạng chữ cái, thanh điệu của âm tiết) — chữ cái so TRƯỚC, thanh điệu so SAU
    (a < ă < â < b …; không dấu < huyền < sắc < hỏi < ngã < nặng). Mỗi âm tiết chỉ có MỘT thanh nên
    `Hòa` và `Hoà` (dấu kiểu mới/cũ) cho cùng khóa."""
    chu: list[int] = []
    thanh: list[int] = []
    for ch in unicodedata.normalize("NFC", tu.lower()):
        d = unicodedata.normalize("NFD", ch)
        goc, dau = d[0], d[1:]
        t = max((_THANH.get(m, 0) for m in dau), default=0)
        if goc == "a":
            goc = "ă" if _TRANG in dau else "â" if _NON in dau else "a"
        elif goc == "e" and _NON in dau:
            goc = "ê"
        elif goc == "o":
            goc = "ô" if _NON in dau else "ơ" if _RAU in dau else "o"
        elif goc == "u" and _RAU in dau:
            goc = "ư"
        chu.append(_HANG_CHU.get(goc, 100 + ord(goc[0])))
        thanh.append(t)
    return tuple(chu), max(thanh, default=0)


def khoa_sap_xep(ho_ten: str) -> tuple:
    """Khóa xếp danh sách theo TÊN rồi họ đệm: tên (từ cuối) → họ (từ đầu) → các tên đệm.
    Tên trống xếp cuối. Không dùng `locale` (kết quả không ổn định giữa các máy)."""
    tu = (ho_ten or "").split()
    if not tu:
        return ((10**6,), 0, (), 0, ())
    ten = _khoa_tu(tu[-1])
    ho = _khoa_tu(tu[0]) if len(tu) > 1 else ((), 0)
    dem = tuple(_khoa_tu(w) for w in tu[1:-1])
    return (ten[0], ten[1], ho[0], ho[1], dem)


# =========================== Dựng sổ ===========================
def _dong_so(h: dict, ngay_thi: date | None) -> dict:
    d = kx.dong_hv(h, ngay_thi)
    du5 = all(v is not None for v in d["diem"].values())
    # Luật sổ mẫu: chưa đủ 5 nội dung thì để trống (kể cả khi PM cũ đã lưu kết luận).
    d["ket_qua_so"] = d["ket_qua"] if du5 else ""
    d["ngay_xet_so"] = ngay_thi if d["ket_qua_so"] == kx.HOAN_THANH else None
    return d


def dem_trong_ket_qua(hv_rows: list[dict]) -> int:
    """Số HV ĐÃ có kết luận (Đạt/Không đạt) nhưng thiếu điểm nên ô kết quả trong sổ để trống —
    để UI giải thích (dữ liệu PM cũ hay lưu kết luận mà thiếu điểm môn)."""
    n = 0
    for h in hv_rows:
        d = kx.dong_hv(h, None)
        du5 = all(v is not None for v in d["diem"].values())
        if d["ket_qua"] and not du5:
            n += 1
    return n


def dung_so_theo_doi(khoa: dict, hv_rows: list[dict], co_so: dict, ngay_lap: datetime) -> bytes:
    """Dựng sổ → bytes .xlsx. `khoa`: MaKH, TenKH, NgayThi ('dd/mm/yyyy'). `co_so`: {co_quan_chu_quan,
    ten_co_so_dao_tao} (có thể trống). `Người lập` luôn để trống (ký/ghi tay sau khi in)."""
    ngay_thi = kx._ngay_vn(khoa.get("NgayThi"))
    ds = sorted(hv_rows, key=lambda h: (khoa_sap_xep(h.get("HoVaTen") or ""), str(h.get("MaDK") or "")))
    dong = [_dong_so(h, ngay_thi) for h in ds]
    ten_khoa = kx._sach(khoa.get("TenKH") or khoa.get("MaKH") or "").strip()

    wb = Workbook()
    ws = wb.active
    ws.title = TEN_SHEET
    ws.sheet_view.showGridLines = False

    # --- độ rộng cột
    rong_b = min(max(_RONG_B_MIN, round(max((_rong_chu(d["ho_ten"]) for d in dong), default=0) + 2, 1)), _RONG_B_MAX)
    rong_c = min(max(_RONG_C_MIN, round(_rong_chu(ten_khoa) + 2, 1)), _RONG_C_MAX)
    for cot, rong in (("A", 4.4), ("B", rong_b), ("C", rong_c), ("D", 7.4), ("E", 7.4),
                      ("F", _RONG_F), ("G", 13.4), ("H", 12.4)):
        ws.column_dimensions[cot].width = rong

    def khoi(rng: str, text: str, *, dam=False, co=12, can="left", wrap=False) -> None:
        ws.merge_cells(rng)
        c = ws[rng.split(":")[0]]
        kx._ghi_chu(c, kx._sach(text))
        c.font = Font(name=_FONT, size=co, bold=dam)
        c.alignment = Alignment(horizontal=can, vertical="center", wrap_text=wrap, indent=0)

    # --- khối đầu: cơ quan/cơ sở (trái) · quốc hiệu (phải) · tiêu đề · 3 dòng thông tin
    co_quan = (co_so.get("co_quan_chu_quan") or "").strip()
    ten_cs = (co_so.get("ten_co_so_dao_tao") or "").strip()
    khoi("A1:D2", "\n".join(x for x in (co_quan, ten_cs) if x), dam=True, can="center", wrap=True)
    khoi("E1:H2", "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nĐộc lập - Tự do - Hạnh phúc", dam=True, can="center", wrap=True)
    khoi("A4:H4", "SỔ THEO DÕI KẾT QUẢ HỌC TẬP", dam=True, co=14, can="center")
    khoi("A6:H6", f"Khóa học: {ten_khoa}")
    khoi("A7:H7", f"Ngày lập: {ngay_lap:%d/%m/%Y}")
    khoi("A8:H8", "Người lập:")
    for r, h in ((1, 32.1), (2, 21.95), (3, 15.75), (4, 26.1), (5, 15.75), (6, 20.1), (7, 20.1), (8, 20.1),
                 (9, 15.75), (HANG_TIEU_DE_1, 38.1), (HANG_TIEU_DE_2, 30.0)):
        ws.row_dimensions[r].height = h
    # Khối cơ quan/cơ sở (A1:D2, 54 pt ≈ 3 dòng chữ đậm 12): tên dài xuống > 3 dòng thì tăng hàng 2 cho khỏi cắt chữ.
    rong_ad = 4.4 + rong_b + rong_c + 7.4
    so_dong_cs = _so_dong("\n".join(x for x in (co_quan, ten_cs) if x), rong_ad - 2) if (co_quan or ten_cs) else 0
    if so_dong_cs > 3:
        ws.row_dimensions[2].height = 21.95 + 15.5 * (so_dong_cs - 3)

    # --- 2 hàng tiêu đề bảng
    tieu_de = {
        "A": "Số\nTT", "B": "Họ tên\nhọc viên", "C": "Khóa\nhọc", "F": "Kết quả\nkhóa học",
        "G": "Ngày xét hoàn thành\nkhóa học", "H": "Xác nhận của\ncơ sở đào tạo",
    }
    for cot, text in tieu_de.items():
        ws.merge_cells(f"{cot}{HANG_TIEU_DE_1}:{cot}{HANG_TIEU_DE_2}")
        ws[f"{cot}{HANG_TIEU_DE_1}"].value = text
    ws.merge_cells(f"D{HANG_TIEU_DE_1}:E{HANG_TIEU_DE_1}")
    ws[f"D{HANG_TIEU_DE_1}"].value = "Kết quả học tập"
    ws[f"D{HANG_TIEU_DE_2}"].value = "Lý thuyết"
    ws[f"E{HANG_TIEU_DE_2}"].value = "Thực hành"
    for hang in (HANG_TIEU_DE_1, HANG_TIEU_DE_2):
        for cot in "ABCDEFGH":
            c = ws[f"{cot}{hang}"]
            c.font = Font(name=_FONT, size=12, bold=True)
            c.fill = _NEN
            c.border = _KHUNG
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # --- dữ liệu
    thuong = Font(name=_FONT, size=12)
    do = Font(name=_FONT, size=12, color=_DO)
    for stt, d in enumerate(dong, start=1):
        r = HANG_DU_LIEU_DAU + stt - 1
        ws.row_dimensions[r].height = 21.95
        gia_tri = {
            "A": stt, "B": d["ho_ten"], "C": ten_khoa, "D": d["diem_lt"], "E": d["diem_th"],
            "F": d["ket_qua_so"] or None, "G": d["ngay_xet_so"], "H": None,
        }
        for cot, v in gia_tri.items():
            c = ws[f"{cot}{r}"]
            kx._ghi_chu(c, v)
            c.font = thuong
            c.border = _KHUNG
            can = "left" if cot == "B" else "center"
            # Họ tên: KHÔNG xuống dòng; tên vượt độ rộng trần thì thu nhỏ chữ vừa ô (shrinkToFit).
            c.alignment = Alignment(horizontal=can, vertical="center", wrap_text=False, indent=0,
                                    shrink_to_fit=(cot in ("B", "C")))
            if cot in ("D", "E"):
                c.number_format = "0.0"
            elif cot == "G":
                c.number_format = "dd/mm/yyyy"
            elif cot == "F" and v == kx.CHUA_HOAN_THANH:
                c.font = do

    # --- in: A4 dọc, lề hẹp, lặp 2 hàng tiêu đề, "Trang x/y" ở chân trang
    ws.page_setup.orientation = "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_options.horizontalCentered = True
    ws.page_margins.left, ws.page_margins.right = LE_TRAI, LE_PHAI
    ws.page_margins.top, ws.page_margins.bottom = LE_TREN, LE_DUOI
    ws.page_margins.header, ws.page_margins.footer = 0.3, 0.3   # footer 0,3: không đè dòng cuối (lề dưới 1,5 cm)
    ws.print_title_rows = f"{HANG_TIEU_DE_1}:{HANG_TIEU_DE_2}"
    for pie in (ws.oddFooter, ws.evenFooter):
        pie.center.text = "Trang &P/&N"
        pie.center.size = 10          # như file mẫu
        pie.center.font = f"{_FONT},Regular"

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
