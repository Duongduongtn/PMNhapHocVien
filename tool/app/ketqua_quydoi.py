"""Quy đổi điểm + tính Đạt + tham số giờ/km thực hành cho module KQĐT (KQD-02).

Nguồn: "Sổ theo dõi KQ học tập TT17" (quy đổi) + TT 17/2026/TT-BXD (giờ/km).
Quyết định: TDD §11D.2-4, TDD-decisions §17 (user chốt 06-07/10).

Nguyên tắc chốt:
- Quy đổi 2 đoạn tuyến tính, ngưỡng quy đổi = 5,0.
- **Xét Đạt trên điểm THÔ chưa làm tròn**; chỉ làm tròn 1 chữ số khi hiển thị/ghi DiemKQ*.
- Đạt = TỪNG MÔN ≥5 (bỏ điểm liệt, bỏ loại trực tiếp).
- Tham số Lý thuyết theo hạng × cờ chương trình CŨ (TT12/2025) / MỚI (TT108/2026).
"""
from __future__ import annotations

from dataclasses import dataclass

# 5 môn (khóa nội bộ) ↔ cột DB (DiemKQ*).
MON = ("ly_thuyet", "mo_phong", "hinh", "tien_lui", "duong")
COT_DIEM = {
    "ly_thuyet": "DiemKQLyThuyet",
    "mo_phong": "DiemKQMoPhong",
    "hinh": "DiemKQHinh",
    "tien_lui": "DiemKQTienLui",
    "duong": "DiemKQThucHanh",
}

# Tham số Lý thuyết (ngưỡng, tối đa = tổng câu) theo nhóm hạng × chương trình.
# Nhóm LT: B (gồm B.01 số tự động + B sàn) · C1.  Căn cứ TT12/2025/TT-BCA (cũ), TT108/2026/TT-BCA (mới).
_LT = {
    ("B", "cu"): (27, 30),
    ("B", "moi"): (45, 50),
    ("C1", "cu"): (32, 35),
    ("C1", "moi"): (54, 60),
}
# Môn nhập thẳng /10 (ngưỡng 5, tối đa 10) hoặc /100 (ngưỡng 80, tối đa 100).
_NG_MAX = {
    "mo_phong": (5, 10),
    "hinh": (80, 100),
    "tien_lui": (5, 10),
    "duong": (80, 100),
}

# Giờ/km thực hành theo nhóm hạng thực hành (TT 17/2026/TT-BXD).
# gio_san + km_san: điền sẵn (giờ sân khóa cứng, km sân sửa được). goi_y_*: ngưỡng gợi ý đường.
@dataclass(frozen=True)
class GioKm:
    gio_san: int
    km_san: int
    goi_y_gio_duong: int
    goi_y_km_duong: int


_GIO_KM = {
    "B01": GioKm(34, 240, 12, 710),   # B số tự động
    "B": GioKm(34, 240, 20, 810),     # B số sàn
    "C1": GioKm(35, 225, 24, 825),
}


def phan_loai_hang(ma_hang_moi: str | None, ma_hang: str | None) -> str | None:
    """Phân loại hạng thực hành: 'B01' (B số tự động) | 'B' (B số sàn) | 'C1'.

    None = không xác định được từ dữ liệu (dữ liệu cũ MaHangMoi rỗng) → UI không khóa
    cứng giờ/km, cảnh báo (TDD §11D.3). Phân biệt theo MaHangMoi + MaHang."""
    m = (ma_hang_moi or "").strip().upper()
    h = (ma_hang or "").strip().upper()
    if m == "B.01" or h == "B11":
        return "B01"
    if m == "C1" or h in ("C1",):
        return "C1"
    if m == "B" or h in ("B1", "B2"):
        return "B"
    return None


def _nhom_lt(hang_cat: str | None) -> str | None:
    """Nhóm tham số Lý thuyết: B01/B → 'B'; C1 → 'C1'."""
    if hang_cat in ("B01", "B"):
        return "B"
    if hang_cat == "C1":
        return "C1"
    return None


def lt_param(hang_cat: str | None, ct: str) -> tuple[int, int] | None:
    """(ngưỡng, tổng câu) Lý thuyết theo hạng × chương trình. None nếu không xác định."""
    nhom = _nhom_lt(hang_cat)
    if nhom is None:
        return None
    return _LT.get((nhom, "moi" if ct == "moi" else "cu"))


def gio_km(hang_cat: str | None) -> GioKm | None:
    return _GIO_KM.get(hang_cat or "")


def quy_doi(goc: float, nguong: float, toi_da: float) -> float:
    """Quy đổi 1 môn về thang 10 (2 đoạn tuyến tính, ngưỡng quy đổi = 5,0). Giá trị THÔ."""
    if goc >= nguong:
        return 5 + (goc - nguong) / (toi_da - nguong) * 5
    return goc / nguong * 5


def lam_tron(x: float) -> float:
    """Làm tròn 1 chữ số để hiển thị/ghi DiemKQ* (xét Đạt vẫn dùng giá trị thô)."""
    return round(x + 1e-9, 1)


class LoiDiem(ValueError):
    """Điểm gốc vượt khung cho phép (câu > tổng, /100 > 100, âm)."""


def _nguong_max_mon(mon: str, hang_cat: str | None, ct: str) -> tuple[int, int]:
    if mon == "ly_thuyet":
        p = lt_param(hang_cat, ct)
        if p is None:
            raise LoiDiem("Không xác định được hạng để lấy thang điểm Lý thuyết.")
        return p
    return _NG_MAX[mon]


@dataclass
class KetQua:
    quy_doi_tho: dict[str, float]      # 5 môn, giá trị thô (xét Đạt)
    quy_doi_tron: dict[str, float]     # 5 môn, làm tròn 1 chữ số (ghi DB/hiển thị)
    ket_luan_csdt: bool                # cả 5 môn ≥5
    kq_ly_thuyet: bool                 # LT≥5 và Mô phỏng≥5
    kq_thuc_hanh: bool                 # Sa hình≥5 và Chữ chi≥5 và Đường≥5


def tinh_ket_qua(diem_goc: dict[str, float], hang_cat: str | None, ct: str) -> KetQua:
    """Nhập điểm GỐC 5 môn → quy đổi + 3 cờ Đạt (per-môn ≥5, trên điểm thô).

    diem_goc: {ly_thuyet, mo_phong, hinh, tien_lui, duong}. Vượt khung → LoiDiem."""
    tho: dict[str, float] = {}
    for mon in MON:
        if mon not in diem_goc or diem_goc[mon] is None:
            raise LoiDiem(f"Thiếu điểm môn {mon}.")
        goc = float(diem_goc[mon])
        ng, mx = _nguong_max_mon(mon, hang_cat, ct)
        if goc < 0 or goc > mx:
            raise LoiDiem(f"Điểm môn {mon} ({goc}) ngoài khung 0–{mx}.")
        tho[mon] = quy_doi(goc, ng, mx)
    return _tu_tho(tho)


def _tu_tho(tho: dict[str, float]) -> KetQua:
    """Dựng KetQua từ 5 quy-đổi thô (xét Đạt per-môn ≥5)."""
    dat = {m: tho[m] >= 5 for m in MON}
    return KetQua(
        quy_doi_tho=tho,
        quy_doi_tron={m: lam_tron(tho[m]) for m in MON},
        ket_luan_csdt=all(dat.values()),
        kq_ly_thuyet=dat["ly_thuyet"] and dat["mo_phong"],
        kq_thuc_hanh=dat["hinh"] and dat["tien_lui"] and dat["duong"],
    )


def ket_qua_hon_hop(
    diem_goc_moi: dict[str, float],
    giu_quydoi: dict[str, float],
    hang_cat: str | None,
    ct: str,
) -> KetQua:
    """KQD-06 sửa lẻ: môn vừa sửa lấy GỐC (quy đổi) · môn giữ lấy QUY ĐỔI đã lưu.

    diem_goc_moi: {mon: điểm gốc} cho môn sửa lại. giu_quydoi: {mon: điểm quy đổi /10 đã lưu}
    cho môn giữ nguyên. Môn không có ở cả hai → LoiDiem (thiếu). Vượt khung → LoiDiem.
    Lưu ý: môn giữ dùng quy-đổi ĐÃ LÀM TRÒN (DB chỉ lưu quy đổi, không lưu gốc) → xét Đạt
    trên giá trị đã tròn; ca ranh giới 4,95→5,0 đã quyết lúc lưu lần đầu, không tính lại từ gốc."""
    tho: dict[str, float] = {}
    for mon in MON:
        g = diem_goc_moi.get(mon)
        if g is not None:
            goc = float(g)
            ng, mx = _nguong_max_mon(mon, hang_cat, ct)
            if goc < 0 or goc > mx:
                raise LoiDiem(f"Điểm môn {mon} ({goc}) ngoài khung 0–{mx}.")
            tho[mon] = quy_doi(goc, ng, mx)
        elif giu_quydoi.get(mon) is not None:
            tho[mon] = float(giu_quydoi[mon])
        else:
            raise LoiDiem(f"Thiếu điểm môn {mon} (chưa nhập và không có điểm đã lưu).")
    return _tu_tho(tho)
