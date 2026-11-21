"""In Báo cáo 2 — luật phần thi (TNB-08, task 164). LUẬT THUẦN, không đụng DB.

Nguồn: TDD §11F.9 (v6.48), PRD TNB-08, CHANGES #103. Bám đúng `usf_BaBT_GetMaNoidungSathach` của phần mềm cũ
(nhóm hạng, miễn lý thuyết mô tô, quá 365 ngày thi lại toàn bộ) + luật mới: **ô tô bỏ phần mô phỏng từ 01/07/2025**.

Phần thi: ô tô L (lý thuyết) · H (sa hình) · Đ (đường) · mô tô LT · TH · A3/A4 LT · TH · Đ.
Một học viên có tập "đã đạt"; phải thi = mọi phần của nhóm − đã đạt; tập phải thi + "đã thi lần nào chưa" → một mục
`DM_NoiDungSH` (tên in ở cột Ghi chú bản in BC2).
"""
from __future__ import annotations

from datetime import date
from typing import Iterable

OTO = "oto"
MOTO = "moto"
BA_BANH = "a3a4"

PHAN = {OTO: ("L", "H", "Đ"), MOTO: ("LT", "TH"), BA_BANH: ("LT", "TH", "Đ")}
TEN_PHAN = {"L": "Lý thuyết", "H": "Sa hình", "Đ": "Đường", "LT": "Lý thuyết", "TH": "Thực hành"}

# Nhóm hạng theo đúng danh sách phần mềm cũ dùng (NguoiLX_HoSo.HangGPLX lưu mã hạng cũ).
_HANG_MOTO = {"A1", "A2", "AM", "A1M", "A11"}
_HANG_BA_BANH = {"A3", "A4"}

# Quá số ngày này kể từ ngày trúng tuyển (NgayQDTT) → thi lại toàn bộ (giữ đúng phần mềm cũ; chờ user chốt mốc).
HAN_BAO_LUU_NGAY = 365

KQ_DA_THI = {"RO", "VA", "RH", "VH", "RD", "VD", "RM", "VM"}

# Tập phần phải thi → mã DM_NoiDungSH, tách theo "đã thi lần nào chưa" khi trùng tập.
# Khóa: (nhóm, frozenset phần thi, đã thi). `None` ở vị trí đã thi = dùng cho cả hai.
_MUC = {
    OTO: {
        (frozenset({"L", "H", "Đ"}), False): 1,   # SH lần đầu
        (frozenset({"L", "H", "Đ"}), True): 4,    # SH lại LT + H + Đ
        (frozenset({"L", "H"}), None): 3,         # SH lại LT + H
        (frozenset({"L", "Đ"}), None): 18,        # SH lại L+Đ
        (frozenset({"H", "Đ"}), None): 5,         # SH lại H + Đ
        (frozenset({"Đ"}), None): 6,              # SH lại Đ
        (frozenset({"L"}), None): 2,              # SH lại LT
        (frozenset({"H"}), None): 8,              # Sát hạch Hình
    },
    MOTO: {
        (frozenset({"LT", "TH"}), False): 1,      # SH lần đầu
        (frozenset({"LT", "TH"}), True): 3,       # SH lại LT + H
        (frozenset({"TH"}), False): 8,            # Sát hạch H (miễn thi lý thuyết) — mã phần mềm cũ trả
        (frozenset({"TH"}), True): 7,             # SH lại TH
        (frozenset({"LT"}), None): 2,             # SH lại LT
    },
    BA_BANH: {
        (frozenset({"LT", "TH", "Đ"}), False): 1,
        (frozenset({"LT", "TH", "Đ"}), True): 4,
        (frozenset({"LT", "TH"}), None): 3,
        (frozenset({"TH", "Đ"}), None): 5,
        (frozenset({"LT", "Đ"}), None): 18,
        (frozenset({"Đ"}), None): 6,
        (frozenset({"LT"}), None): 2,
        (frozenset({"TH"}), None): 7,
    },
}

# Chữ phần mềm cũ in (usf_BaBT_GetNoidungSathach) khác tên danh mục ở mục này — chỉ dùng cho mô tô.
TEN_IN_MOTO_MIEN_LT = "Sát hạch H (Miễn thi lý thuyết)"

# Mã phần mềm cũ có thể trả → (tập phần, đã thi). Ô tô có M: bỏ M (luật 01/07/2025). Dùng cho dòng "PM cũ: …"
# và làm phương án cuối khi không suy được từ dữ liệu.
_MA_CU_OTO = {
    1: ({"L", "H", "Đ"}, False), 11: ({"L", "H", "Đ"}, False),
    4: ({"L", "H", "Đ"}, True), 12: ({"L", "H", "Đ"}, True),
    3: ({"L", "H"}, True), 20: ({"L", "H"}, True),
    18: ({"L", "Đ"}, True), 19: ({"L", "Đ"}, True),
    5: ({"H", "Đ"}, True), 13: ({"H", "Đ"}, True),
    6: ({"Đ"}, True), 15: ({"Đ"}, True),
    2: ({"L"}, True), 14: ({"L"}, True),
    8: ({"H"}, True), 9: ({"H"}, True), 17: ({"H"}, True), 7: ({"H"}, True),
    16: (set(), True),  # SH lại M — bỏ M thì không còn phần nào
}
_MA_CU_MOTO = {
    1: ({"LT", "TH"}, False), 11: ({"LT", "TH"}, False),
    3: ({"LT", "TH"}, True), 4: ({"LT", "TH"}, True), 12: ({"LT", "TH"}, True),
    8: ({"TH"}, False), 9: ({"TH"}, False),
    7: ({"TH"}, True), 5: ({"TH"}, True),
    2: ({"LT"}, True),
}


def nhom_hang(hang: str | None) -> str:
    h = (hang or "").strip().upper().replace(".", "")
    if h in _HANG_MOTO:
        return MOTO
    if h in _HANG_BA_BANH:
        return BA_BANH
    return OTO


def thu_tu(nhom: str, phan: Iterable[str]) -> list[str]:
    s = set(phan)
    return [p for p in PHAN[nhom] if p in s]


def muc_tu_phan(nhom: str, phai_thi: Iterable[str], da_thi: bool) -> int | None:
    """Tập phần phải thi → mã DM_NoiDungSH. Rỗng → None (dòng "Phải bật ít nhất 1 phần")."""
    tap = frozenset(phai_thi)
    if not tap:
        return None
    bang = _MUC[nhom]
    return bang.get((tap, da_thi), bang.get((tap, None)))


def ten_in(nhom: str, ma: int, ten_dm: str) -> str:
    """Chữ in ở cột Ghi chú: tên danh mục, riêng mô tô miễn lý thuyết in đúng chữ phần mềm cũ."""
    if nhom == MOTO and ma == 8:
        return TEN_IN_MOTO_MIEN_LT
    return ten_dm


def phan_tu_ma_cu(nhom: str, ma: int | None) -> tuple[set[str], bool] | None:
    """Mã phần mềm cũ tính → (tập phần phải thi đã bỏ M, đã thi). Không biết mã → None."""
    if ma is None:
        return None
    bang = _MA_CU_MOTO if nhom == MOTO else _MA_CU_OTO
    kq = bang.get(int(ma))
    if kq is None:
        return None
    phan, da_thi = kq
    if nhom == BA_BANH:  # A3/A4: phần mềm cũ dùng cùng bộ mã với ô tô, đổi L/H → LT/TH
        phan = {{"L": "LT", "H": "TH"}.get(p, p) for p in phan}
    return set(phan), da_thi


def _qua_han(ngay_qdtt: date | None, hom_nay: date) -> bool:
    return ngay_qdtt is not None and (hom_nay - ngay_qdtt).days > HAN_BAO_LUU_NGAY


def mien_ly_thuyet_moto(hang: str | None, hang_gplx_da_co: str | None) -> bool:
    """Mô tô A1/Am/A1m có GPLX ô tô → miễn lý thuyết. Dò chuỗi đúng như phần mềm cũ (CHARINDEX)."""
    if (hang or "").strip().upper() not in {"A1", "AM", "A1M"}:
        return False
    s = hang_gplx_da_co or ""
    return any(k in s for k in ("B1", "B2", "C", "D", "E", "FB2", "FC", "FD", "FE"))


def dat_tu_ket_qua(nhom: str, ket_qua_sh: str | None, diem: dict | None = None,
                   nguong: dict | None = None, phan_da_thi: Iterable[str] | None = None) -> set[str]:
    """Phần đạt trong MỘT kỳ: suy theo thứ tự thi L → H → Đ từ `KetQuaSH`, cộng phần có điểm ≥ ngưỡng.

    `diem` = {"L": .., "H": .., "Đ": ..} (mô tô dùng khóa "LT"/"TH"); `nguong` cùng khóa; `phan_da_thi` giới hạn
    trong các phần thật sự thi kỳ đó (không biết → mọi phần)."""
    kq = (ket_qua_sh or "").strip().upper()
    if kq not in KQ_DA_THI:
        return set()
    p = PHAN[nhom]
    dat: set[str] = set()
    if kq in ("RH", "VH"):
        dat = {p[0]}                       # rớt/vắng hình ⇒ lý thuyết đã qua
    elif kq in ("RD", "VD") and len(p) == 3:
        dat = {p[0], p[1]}                 # rớt/vắng đường ⇒ lý thuyết + hình đã qua
    elif kq in ("RM", "VM"):
        dat = {p[0]}                       # (luật cũ) rớt mô phỏng ⇒ lý thuyết đã qua
    for k, v in (diem or {}).items():
        tt = (nguong or {}).get(k)
        if k in p and v is not None and tt is not None and v >= tt:
            dat.add(k)
    if phan_da_thi is not None:
        dat &= set(phan_da_thi)
    return dat


def cong_don(dat_cu: Iterable[str], dat_moi: Iterable[str]) -> set[str]:
    """Cộng phần vừa đạt vào phần đã đạt; không xóa phần đạt cũ."""
    return set(dat_cu) | set(dat_moi)


def mac_dinh(*, hang: str | None, ket_qua_sh: str | None = None, diem: dict | None = None,
             nguong: dict | None = None, hang_gplx_da_co: str | None = None, ngay_qdtt: date | None = None,
             hom_nay: date, so: dict | None = None, ma_pm_cu: int | None = None) -> dict:
    """Phần đã đạt + mục điền sẵn cho một học viên.

    Thứ tự: (1) sổ phần thi của tool `so={"dat": [...], "da_thi": bool, "nguon": "so"|"sua"}`; (2) suy từ DB Nạp;
    (3) mã phần mềm cũ (đã bỏ M) khi không suy được. Quá hạn bảo lưu → đã đạt rỗng (thi lại toàn bộ).
    Trả {nhom, dat, phai_thi, da_thi, ma, nguon}; `ma` None = chưa có phần nào để thi."""
    nhom = nhom_hang(hang)
    kq = (ket_qua_sh or "").strip().upper()
    if so is not None:
        dat, da_thi, nguon = set(so.get("dat") or []), bool(so.get("da_thi")), so.get("nguon") or "so"
    elif kq in KQ_DA_THI:
        dat, da_thi, nguon = dat_tu_ket_qua(nhom, kq, diem, nguong), True, "suy"
        if nhom == MOTO and mien_ly_thuyet_moto(hang, hang_gplx_da_co):
            dat.add("LT")  # miễn lý thuyết vẫn giữ khi đã thi (phần mềm cũ: "SH lại TH")
    elif nhom == MOTO and mien_ly_thuyet_moto(hang, hang_gplx_da_co):
        dat, da_thi, nguon = {"LT"}, False, "suy"
    else:
        cu = phan_tu_ma_cu(nhom, ma_pm_cu)
        if cu is not None and kq not in ("", "1", "DA"):
            phai, da_thi = cu
            dat, nguon = set(PHAN[nhom]) - phai, "pm_cu"
        else:
            dat, da_thi, nguon = set(), False, "chua_thi"
    if da_thi and _qua_han(ngay_qdtt, hom_nay):
        dat, nguon = set(), "qua_han"
        if nhom == MOTO and mien_ly_thuyet_moto(hang, hang_gplx_da_co):
            dat = {"LT"}               # phần mềm cũ xét miễn lý thuyết sau luật quá hạn (usf_BaBT_GetMaNoidungSathach)
    dat &= set(PHAN[nhom])
    phai = [p for p in PHAN[nhom] if p not in dat]
    return {"nhom": nhom, "dat": thu_tu(nhom, dat), "phai_thi": phai, "da_thi": da_thi,
            "ma": muc_tu_phan(nhom, phai, da_thi), "nguon": nguon}


def nguong_theo_hang(dong_dm: Iterable[dict], hang: str | None) -> dict:
    """Ngưỡng đạt từ `DM_DiemSatHach` theo mã hạng. Hạng có nhiều dòng (B, C1) → lấy ngưỡng CAO nhất, để không
    đánh dấu đạt nhầm (user sửa được). Trả khóa theo phần của nhóm hạng."""
    h = (hang or "").strip().upper().replace(".", "")
    dong = [r for r in dong_dm if (r.get("Hang") or "").strip().upper().replace(".", "") == h]

    def cao_nhat(cot: str):
        vals = [r[cot] for r in dong if r.get(cot) is not None]
        return max(vals) if vals else None

    lt, hi, dd = cao_nhat("LtDiemToiThieu"), cao_nhat("HiDiemToiThieu"), cao_nhat("DdDiemToiThieu")
    nhom = nhom_hang(hang)
    if nhom == OTO:
        return {k: v for k, v in (("L", lt), ("H", hi), ("Đ", dd)) if v is not None}
    if nhom == MOTO:
        return {k: v for k, v in (("LT", lt), ("TH", hi)) if v is not None}
    return {k: v for k, v in (("LT", lt), ("TH", hi), ("Đ", dd)) if v is not None}


def diem_theo_nhom(nhom: str, diem_lt, diem_hinh, diem_duong) -> dict:
    """3 cột điểm `KetQua_LyThuyet/Hinh/Duong` → khóa phần của nhóm."""
    if nhom == OTO:
        return {"L": diem_lt, "H": diem_hinh, "Đ": diem_duong}
    if nhom == MOTO:
        return {"LT": diem_lt, "TH": diem_hinh}
    return {"LT": diem_lt, "TH": diem_hinh, "Đ": diem_duong}
