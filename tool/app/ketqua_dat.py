"""Đọc PDF báo cáo DAT + đối chiếu với học viên của khóa (KQD-08).

PDF "Báo cáo kết quả đào tạo thực hành lái xe trên đường của khóa học" (hệ thống DAT):
đầu file có `Mã khóa học:<mã>`; bảng 7 cột `STT · Mã học viên · Họ và tên · Ngày sinh ·
Tổng thời gian · Tổng quãng đường · Ghi chú`. Giờ dạng `16:19` (có thể ≥ 24), km dạng
`1.008,19`. "Mã học viên" = `NguoiLX.MaDK` (đã đối chiếu DB 12/10/2026).

Luật thuần, không DB. Quyết định: TDD §11D.10, TDD-decisions §24.
"""
from __future__ import annotations

import io
import re

from app import ketqua_quydoi

# Tình trạng dòng ở bảng xác nhận.
KHOP = "khop"
CHUA_CHAY_DAT = "chua_chay_dat"     # giờ trống / km 0 — bỏ tick sẵn
KHONG_CO_TRONG_KHOA = "khong_co_trong_khoa"
DA_KET_XUAT = "da_ket_xuat"          # TT_XuLy 12/13 — không ghi
LOI_DONG = "loi_dong"                # giờ/km sai dạng
TRUNG_DONG = "trung_dong"            # mã HV xuất hiện lại — chỉ lấy dòng đầu

_SAI_LECH = 0.005                    # so "có thay đổi" trên giá trị đã làm tròn 2 chữ số


class LoiDat(ValueError):
    """File không phải báo cáo DAT / không đọc được / giờ-km sai dạng."""


def doc_gio(v) -> float | None:
    """`16:19` → 16.32 (h + m/60, làm tròn 2 chữ số). Trống → None. Số thập phân giữ nguyên.

    Phút ≥ 60, giây ≥ 60 hoặc rác → LoiDat."""
    t = (str(v) if v is not None else "").strip()
    if t == "":
        return None
    m = re.fullmatch(r"(\d{1,3}):(\d{1,2})(?::(\d{1,2}))?", t)
    if m:
        h, ph, gi = int(m[1]), int(m[2]), int(m[3] or 0)
        if ph >= 60 or gi >= 60:
            raise LoiDat(f"Giờ '{t}' sai dạng (phút/giây phải < 60).")
        return round(h + ph / 60 + gi / 3600, 2)
    if re.fullmatch(r"\d+(?:[.,]\d+)?", t):
        return round(float(t.replace(",", ".")), 2)
    raise LoiDat(f"Giờ '{t}' sai dạng.")


def doc_km(v) -> float | None:
    """Số kiểu VN: `725,63` → 725.63 · `1.008,19` → 1008.19 · `0,00` → 0.0. Trống → None."""
    t = (str(v) if v is not None else "").strip()
    if t == "":
        return None
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", t) or re.fullmatch(r"\d+(?:,\d+)?", t):
        return round(float(t.replace(".", "").replace(",", ".")), 2)
    raise LoiDat(f"Quãng đường '{t}' sai dạng.")


def doc_pdf_dat(data: bytes) -> dict:
    """PDF DAT → {ma_kh, hang, dong:[{stt, ma_hv, ho_ten, ngay_sinh, gio, km, ghi_chu, loi}]}.

    Lỗi từng dòng (giờ/km sai dạng) ghi vào `loi`, các dòng khác vẫn đọc. File hỏng / không có
    mã khóa / không có bảng → LoiDat."""
    import pdfplumber  # import trễ: test không cần thư viện, exe gói kèm

    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            if not pdf.pages:
                raise LoiDat("File PDF rỗng.")
            dau = pdf.pages[0].extract_text() or ""
            m_kh = re.search(r"khóa\s*học:\s*(\S+)", dau)
            m_hang = re.search(r"Hạng\s*đào\s*tạo:\s*(\S+)", dau)
            dong: list[dict] = []
            for trang in pdf.pages:
                for bang in trang.extract_tables():
                    for r in bang:
                        if not r or len(r) < 6 or not r[0] or not str(r[0]).strip().isdigit():
                            continue
                        c = [(x or "").strip() for x in r]
                        d = {
                            "stt": int(c[0]), "ma_hv": c[1], "ho_ten": c[2], "ngay_sinh": c[3],
                            "gio": None, "km": None,
                            "ghi_chu": c[6] if len(c) > 6 else "", "loi": None,
                        }
                        try:
                            d["gio"] = doc_gio(c[4])
                            d["km"] = doc_km(c[5])
                        except LoiDat as e:
                            d["loi"] = str(e)
                        dong.append(d)
    except LoiDat:
        raise
    except Exception as e:  # noqa: BLE001 — pdfminer/pdfplumber ném nhiều loại lỗi file hỏng
        raise LoiDat("Không đọc được file PDF — kiểm lại file tải từ hệ thống DAT.") from e
    if not m_kh:
        raise LoiDat("File không phải báo cáo DAT (không thấy 'Mã khóa học').")
    if not dong:
        raise LoiDat("Không thấy bảng học viên trong file.")
    return {"ma_kh": m_kh.group(1), "hang": m_hang.group(1) if m_hang else None, "dong": dong}


def _so2(v) -> float | None:
    return round(float(v), 2) if v is not None else None


def doi_chieu(dong: list[dict], hv_khoa: list[dict]) -> dict:
    """Khớp dòng file với HV của khóa (theo MaDK) → bảng xác nhận. KHÔNG ghi gì.

    `hv_khoa`: hàng đọc từ CDB (MaDK, HoVaTen, SoCMT, TT_XuLy, MaHangMoi, HangGPLX,
    TGThucHanhDuong, TongQDThucHanh). Trả {dong:[…], vang_trong_file:[…]}."""
    theo_ma = {h["MaDK"]: h for h in hv_khoa}
    thay: set[str] = set()
    out: list[dict] = []
    for d in dong:
        h = theo_ma.get(d["ma_hv"])
        item = {
            "stt": d["stt"], "ma_dk": d["ma_hv"],
            "ho_ten": (h["HoVaTen"] if h else d["ho_ten"]),
            "gio_cu": _so2(h["TGThucHanhDuong"]) if h else None,
            "km_cu": _so2(h["TongQDThucHanh"]) if h else None,
            "gio_moi": d["gio"], "km_moi": d["km"],
            "tinh_trang": KHOP, "canh_bao": [], "co_thay_doi": False,
            "chon_duoc": False, "tick_san": False, "ghi_chu": d["loi"],
        }
        out.append(item)
        if h is None:
            item["tinh_trang"] = KHONG_CO_TRONG_KHOA
            continue
        if d["ma_hv"] in thay:
            item["tinh_trang"] = TRUNG_DONG
            item["ghi_chu"] = "Mã học viên xuất hiện lại trong file — chỉ lấy dòng đầu."
            continue
        thay.add(d["ma_hv"])
        if (h["TT_XuLy"] or "").strip() in ("12", "13"):
            item["tinh_trang"] = DA_KET_XUAT
            continue
        if d["loi"]:
            item["tinh_trang"] = LOI_DONG
            continue
        gio, km = d["gio"], d["km"]
        if (gio is None or gio == 0) and (km is None or km == 0):
            item["tinh_trang"] = CHUA_CHAY_DAT
            item["chon_duoc"] = True          # ai cần ghi 0 thì tự tick
            continue
        if gio is None or km is None:
            item["tinh_trang"] = LOI_DONG
            item["ghi_chu"] = "Thiếu giờ hoặc quãng đường."
            continue
        item["chon_duoc"] = True
        item["canh_bao"] = ketqua_quydoi.canh_bao_duong(
            gio, km, ketqua_quydoi.phan_loai_hang(h["MaHangMoi"], h["HangGPLX"]))
        cu_g, cu_k = item["gio_cu"], item["km_cu"]
        item["co_thay_doi"] = (
            cu_g is None or cu_k is None
            or abs(cu_g - gio) > _SAI_LECH or abs(cu_k - km) > _SAI_LECH
        )
        item["tick_san"] = item["co_thay_doi"]
    co_trong_file = {d["ma_hv"] for d in dong}
    vang = [
        {"ma_dk": h["MaDK"], "ho_ten": h["HoVaTen"], "so_cccd": h.get("SoCMT")}
        for h in hv_khoa if h["MaDK"] not in co_trong_file
    ]
    return {"dong": out, "vang_trong_file": vang}
