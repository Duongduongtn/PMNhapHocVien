"""Cập nhật kết quả đào tạo — đọc/ghi KQĐT trên CSDL ĐÍCH (GPLX_CDB_CSDT).

Module #3 (KQD). KQD-01 (task 71): CHỈ ĐỌC — băng DB đích, combobox khóa đã BC1
(kèm đếm HV theo trạng thái), lưới HV lọc 4 nhóm trạng thái. Mọi truy vấn qua
`sqlserver_conn_dich(target_key)` — KHÔNG đụng DB Nạp. Ghi (KQD-02/04) thêm ở task 72-75.

Quyết định đọc lưới (TDD §11D.0, user chốt 07/10): **SELECT tự viết** như `sync_tracuu.py`,
lọc thẳng `TT_XuLy` cho đúng 4 nhóm PRD — KHÔNG dùng SP đọc `_CNKQDT` vì tham số
`@TrangThai` của SP gộp "Đã cập nhật" chỉ trả Đạt (09), bỏ sót Không đạt (10).

Mount kèm `require_session` ở main.py (collector không có session cục bộ → 403).
"""
from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app import config_store, ketqua_quydoi, sua_sau_gui, sync_helpers
from app.db import sqlserver_conn_dich, ConfigChuaDay
from app.routers.hoso import ngay_sinh_hien
from app.routers.sync import _db_dich, _loi_db
from app.session import Phien, require_session

router = APIRouter(prefix="/local/ketqua", tags=["ketqua"])

# Nhóm trạng thái KQĐT → tập mã TT_XuLy. "all" không lọc (mọi HV của khóa).
# dangky/capnhat/tuchoi/giaitrinh: lọc lưới KQD-01/02/04. ketxuat: KQD-03 "đã kết xuất" (12).
# "Còn sót kết xuất" của KQD-03 = đã cập nhật chưa kết xuất = dùng lại nhóm "capnhat" (09/10).
_NHOM_TT: dict[str, tuple[str, ...]] = {
    "dangky": ("03", "04"),      # Đã đăng ký khóa học
    "capnhat": ("09", "10"),     # Đã cập nhật KQ (Đạt 09 / Không đạt 10) — cũng là "còn sót kết xuất" (KQD-03)
    "tuchoi": ("14",),           # Sở từ chối
    "giaitrinh": ("90",),        # Đang giải trình
    "ketxuat": ("12",),          # Đã kết xuất gửi Sở (KQD-03 — chỉ xem)
}


@router.get("/db-dich-info")
def db_dich_info(target_key: str | None = None) -> dict:
    """Thông tin CSDL đích cho băng nhắc ở header: tên DB · máy · mã CSĐT · đã kết nối chưa.

    Dùng chung cho mọi phân hệ ghi DB đích (banner ToolLayout). Host đọc từ cấu hình
    (tên máy, KHÔNG phải bí mật); mã CSĐT = QTHT_ThamSoHT.MA_CSDT. Nối lỗi → connected=false
    (banner tự hiện 'chưa kết nối'), KHÔNG ném lỗi để header không vỡ."""
    try:
        db = _db_dich(target_key)
    except HTTPException:
        return {"database": None, "host": None, "ma_csdt": None, "connected": False}
    host = (config_store.load_config().get("sqlserver_host") or "").strip()
    try:
        with sqlserver_conn_dich(db) as conn:
            ma_csdt = sync_helpers.get_ma_csdt_tu_qtht(conn)
        return {"database": db, "host": host, "ma_csdt": ma_csdt, "connected": True}
    except Exception:  # noqa: BLE001 — banner không được vỡ vì nối lỗi
        return {"database": db, "host": host, "ma_csdt": None, "connected": False}


@router.get("/khoa")
def ds_khoa(q: str = "", target_key: str | None = None) -> list[dict]:
    """Combobox khóa (KQD-01): **chỉ khóa đã có Báo cáo 1** (EXISTS BaoCaoI), cùng CSĐT đích.

    Mỗi khóa kèm ngày khai giảng + đếm HV theo 4 nhóm trạng thái (gợi ý chọn khóa)."""
    db = _db_dich(target_key)
    like = f"%{q.strip()}%"

    def _dem(cols: tuple[str, ...]) -> str:
        ds = ", ".join(f"'{c}'" for c in cols)
        return (
            "(SELECT COUNT(*) FROM dbo.NguoiLX_HoSo h WHERE h.MaKhoaHoc = k.MaKH "
            f"AND h.TrangThai = 1 AND h.TT_XuLy IN ({ds}))"
        )

    sql = (
        "SELECT TOP 50 k.MaKH, k.TenKH, k.HangGPLX, "
        "CONVERT(varchar(10), k.NgayKG, 103) AS NgayKG, "
        "CONVERT(varchar(10), k.NgayBG, 103) AS NgayBG, "
        "CONVERT(varchar(10), k.NgayThi, 103) AS NgayThi, "
        + _dem(_NHOM_TT["dangky"]) + " AS dem_dangky, "
        + _dem(_NHOM_TT["capnhat"]) + " AS dem_capnhat, "
        + _dem(_NHOM_TT["tuchoi"]) + " AS dem_tuchoi, "
        + _dem(_NHOM_TT["giaitrinh"]) + " AS dem_giaitrinh, "
        + _dem(_NHOM_TT["ketxuat"]) + " AS dem_ketxuat "
        "FROM dbo.KhoaHoc k "
        "WHERE k.MaCSDT = %s AND k.TrangThai = 1 "
        "AND EXISTS (SELECT 1 FROM dbo.BaoCaoI b WHERE b.MaKH = k.MaKH) "
        "AND (k.MaKH LIKE %s OR k.TenKH LIKE %s) "
        "ORDER BY k.NgayTao DESC"
    )
    try:
        with sqlserver_conn_dich(db) as conn:
            ma_csdt = sync_helpers.get_ma_csdt_tu_qtht(conn)
            if not ma_csdt:
                raise HTTPException(status_code=400, detail="CSDL đích thiếu MA_CSDT trong QTHT_ThamSoHT.")
            cur = conn.cursor(as_dict=True)
            cur.execute(sql, (ma_csdt, like, like))
            rows = cur.fetchall()
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)
    return [
        {
            "ma_kh": r["MaKH"],
            "ten_kh": r["TenKH"],
            "hang_gplx": r["HangGPLX"],
            "ngay_kg": r["NgayKG"],
            "ngay_bg": r["NgayBG"],
            "ngay_thi": r["NgayThi"],
            "dem": {
                "dangky": r["dem_dangky"],
                "capnhat": r["dem_capnhat"],
                "tuchoi": r["dem_tuchoi"],
                "giaitrinh": r["dem_giaitrinh"],
                "ketxuat": r["dem_ketxuat"],
            },
        }
        for r in rows
    ]


# Lưới HV của 1 khóa đích. Hạng hiển thị lấy MaHangMoi (LEFT JOIN DM_HangGPLX) — fallback HangGPLX.
# Điểm quy đổi 5 môn + KetLuanCSDT để lưới hiện "điểm (nếu có)" + cột Kết luận (KQD-01/02).
_SQL_HV = (
    "SELECT A.MaDK, A.HoVaTen, A.NgaySinh, A.SoCMT, B.SoHoSo, "
    "B.HangGPLX, gp.MaHangMoi, B.TT_XuLy, B.KetLuanCSDT, "
    "B.DiemKQLyThuyet, B.DiemKQMoPhong, B.DiemKQHinh, B.DiemKQTienLui, B.DiemKQThucHanh, "
    "B.TGThucHanhHinh, B.QDThucHanhHinh, B.TGThucHanhDuong, B.TongQDThucHanh "
    "FROM dbo.NguoiLX_HoSo B JOIN dbo.NguoiLX A ON A.MaDK = B.MaDK "
    "LEFT JOIN dbo.DM_HangGPLX gp ON gp.MaHang = B.HangGPLX "
    "WHERE B.MaKhoaHoc = %s AND B.TrangThai = 1{loc} "
    "ORDER BY CAST(B.SoHoSo AS INT)"
)


def _diem(v) -> float | None:
    return float(v) if v is not None else None


def _ket_luan(v) -> str | None:
    """KetLuanCSDT (bit) → 'dat' | 'khong_dat' | None (chưa có kết luận)."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    return "dat" if int(v) == 1 else "khong_dat"


def _doc_hv_khoa(ma_kh: str, nhom: tuple[str, ...] | None, target_key: str | None) -> list[dict]:
    """Đọc HV của 1 khóa ở DB đích, lọc theo tập TT_XuLy (None = tất cả). Dùng chung /hoc-vien + /kiem-truoc."""
    db = _db_dich(target_key)
    params: list = [ma_kh]
    loc = ""
    if nhom:
        loc = " AND B.TT_XuLy IN (" + ", ".join(["%s"] * len(nhom)) + ")"
        params.extend(nhom)
    try:
        with sqlserver_conn_dich(db) as conn:
            cur = conn.cursor(as_dict=True)
            cur.execute(_SQL_HV.format(loc=loc), tuple(params))
            return cur.fetchall()
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)


@router.get("/hoc-vien")
def ds_hoc_vien(
    ma_kh: str = Query(..., min_length=1),
    trang_thai: str = "all",
    target_key: str | None = None,
) -> list[dict]:
    """Lưới HV 1 khóa, lọc theo nhóm trạng thái (all | dangky | capnhat | tuchoi | giaitrinh).

    Tìm nhanh tên/CCCD lọc phía client (như TraCuuCDB). Trả về cả HV đã kết xuất/hoàn thành
    (12/13) khi 'all' để lưới hiện dòng chỉ-đọc (KQD-02 khóa sửa)."""
    rows = _doc_hv_khoa(ma_kh, _NHOM_TT.get(trang_thai), target_key)
    return [
        {
            "ma_dk": r["MaDK"],
            "ho_ten": r["HoVaTen"],
            "ngay_sinh": ngay_sinh_hien(r["NgaySinh"]),
            "so_cccd": r["SoCMT"],
            "so_ho_so": r["SoHoSo"],
            "hang": (r["MaHangMoi"] or r["HangGPLX"] or "").strip() or None,
            "ma_hang_moi": (r["MaHangMoi"] or "").strip() or None,
            "ma_hang": (r["HangGPLX"] or "").strip() or None,
            "tt_xuly": (r["TT_XuLy"] or "").strip() or None,
            "ket_luan": _ket_luan(r["KetLuanCSDT"]),
            "diem": {
                "ly_thuyet": _diem(r["DiemKQLyThuyet"]),
                "mo_phong": _diem(r["DiemKQMoPhong"]),
                "hinh": _diem(r["DiemKQHinh"]),
                "tien_lui": _diem(r["DiemKQTienLui"]),
                "duong": _diem(r["DiemKQThucHanh"]),
            },
        }
        for r in rows
    ]


@router.get("/kiem-truoc")
def kiem_truoc(ma_kh: str = Query(..., min_length=1), target_key: str | None = None) -> dict:
    """KQD-07 — kiểm trước kết xuất cho ĐÚNG 1 khóa (chỉ đọc, chỉ nhắc, không chặn).

    Chỉ HV TT_XuLy 03/04/09/10 (12/13/14/90 không xét). Hạng mô tô không nhập KQĐT → không xét,
    đếm riêng ở `mo_to_bo_qua`. Luật ở `ketqua_quydoi.hv_chua_du` (một nguồn với KQD-02)."""
    rows = _doc_hv_khoa(ma_kh, _NHOM_TT["dangky"] + _NHOM_TT["capnhat"], target_key)
    thieu: list[dict] = []
    dem = {k: 0 for k in (ketqua_quydoi.LY_DO_CHUA_CO_DIEM, ketqua_quydoi.LY_DO_THIEU_MON,
                          ketqua_quydoi.LY_DO_THIEU_GIO_KM, ketqua_quydoi.LY_DO_THIEU_KET_LUAN)}
    tong = du = mo_to = 0
    for r in rows:
        if ketqua_quydoi.la_mo_to(r["MaHangMoi"], r["HangGPLX"]):
            mo_to += 1
            continue
        tong += 1
        hv = {
            "tt_xuly": (r["TT_XuLy"] or "").strip() or None,
            "ket_luan": _ket_luan(r["KetLuanCSDT"]),
            "diem": {
                "ly_thuyet": _diem(r["DiemKQLyThuyet"]), "mo_phong": _diem(r["DiemKQMoPhong"]),
                "hinh": _diem(r["DiemKQHinh"]), "tien_lui": _diem(r["DiemKQTienLui"]),
                "duong": _diem(r["DiemKQThucHanh"]),
            },
            "gio_san": r["TGThucHanhHinh"], "km_san": r["QDThucHanhHinh"],
            "gio_duong": r["TGThucHanhDuong"], "km_duong": r["TongQDThucHanh"],
        }
        kq = ketqua_quydoi.hv_chua_du(hv)
        if not kq["ly_do"]:
            du += 1
            continue
        for ld in kq["ly_do"]:
            dem[ld] += 1
        thieu.append({
            "ma_dk": r["MaDK"], "ho_ten": r["HoVaTen"], "so_cccd": r["SoCMT"],
            "tt_xuly": hv["tt_xuly"], "ly_do": kq["ly_do"], "mon_thieu": kq["mon_thieu"],
        })
    return {"ma_kh": ma_kh, "tong": tong, "du": du, "thieu": thieu, "dem": dem, "mo_to_bo_qua": mo_to}


# ── KQD-02: cờ chương trình CŨ/MỚI theo khóa (lưu phía tool) ──
class ChuongTrinhIn(BaseModel):
    ma_kh: str
    ct: str  # 'cu' | 'moi'


@router.get("/chuong-trinh")
def get_chuong_trinh(ma_kh: str = Query(..., min_length=1)) -> dict:
    return {"ma_kh": ma_kh, "ct": config_store.get_kqd_chuong_trinh(ma_kh)}


@router.post("/chuong-trinh")
def set_chuong_trinh(body: ChuongTrinhIn) -> dict:
    ct = config_store.set_kqd_chuong_trinh(body.ma_kh, body.ct)
    return {"ma_kh": body.ma_kh, "ct": ct}


@router.get("/giai-trinh")
def get_giai_trinh(ma_dk: str = Query(..., min_length=1), target_key: str | None = None) -> dict:
    """KQD-04 — lý do Sở từ chối (chỉ đọc, do Sở ghi) + giải trình hiện có của HV.

    `LyDoTuChoiKQDT` KHÔNG được SP đọc trả về (verify 07/10) → SELECT riêng."""
    db = _db_dich(target_key)
    try:
        with sqlserver_conn_dich(db) as conn:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                "SELECT LyDoTuChoiKQDT, GiaiTrinh FROM dbo.NguoiLX_HoSo WHERE MaDK=%s",
                (ma_dk,),
            )
            r = cur.fetchone()
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ học viên ở CSDL đích.")
    return {
        "ma_dk": ma_dk,
        "ly_do_tu_choi": (r["LyDoTuChoiKQDT"] or "").strip() or None,
        "giai_trinh": (r["GiaiTrinh"] or "").strip() or None,
    }


# ── KQD-02: ghi kết quả đào tạo vào CDB đích (nhập điểm gốc → quy đổi → SP) ──
class CapNhatIn(BaseModel):
    ma_dk: str
    diem_goc: dict[str, float]           # điểm GỐC các môn NHẬP (KQD-02: đủ 5; KQD-06 sửa lẻ: chỉ môn sửa)
    giu_quydoi: dict[str, float] | None = None  # KQD-06 sửa lẻ: {mon: quy đổi /10 đã lưu} cho môn GIỮ nguyên
    km_san: float | None = None          # km sân (điền sẵn sửa được); None → mặc định theo hạng
    gio_duong: float | None = None       # giờ đường (nhập tay)
    km_duong: float | None = None        # km đường (nhập tay)
    ngay_ra_qdtn: str = ""               # ngày cấp HTKH 'dd/mm/yyyy' | '' = hôm nay
    tg_bat_dau: str = ""                 # 'dd/mm/yyyy' | '' = NgayBG khóa
    tg_ket_thuc: str = ""                # 'dd/mm/yyyy' | '' = NgayThi khóa
    giai_trinh: str | None = None        # KQD-04: None = không đụng cột GiaiTrinh; '' = xóa; chuỗi = ghi


def _ymd(v: str) -> str:
    """'dd/mm/yyyy' → 'yyyymmdd' (varchar8 cho TGBatDau/TGKetThuc). Rỗng → ''."""
    import re
    m = re.match(r"^\s*(\d{2})/(\d{2})/(\d{4})\s*$", v or "")
    return f"{m[3]}{m[2]}{m[1]}" if m else ""


def _ngay(v: str):
    """'dd/mm/yyyy' → datetime (NgayRaQDTN). Rỗng/sai → hôm nay."""
    try:
        return datetime.strptime((v or "").strip(), "%d/%m/%Y")
    except ValueError:
        return datetime.now()


_SP_CAPNHAT = (
    "EXEC dbo.usp_NguoiLX_KetQuaDaoTao_CSDT_CapNhat "
    "@MaDK=%s, @MaKH=%s, @KQLyThuyet=%s, @KQThucHanh=%s, @TGBatDau=%s, @TGKetThuc=%s, "
    "@KetLuanCSDT=%s, @DiemKQLyThuyet=%s, @DiemKQThucHanh=%s, @DiemKQMoPhong=%s, "
    "@DiemKQHinh=%s, @DiemKQTienLui=%s, @TGThucHanhDuong=%s, @TGThucHanhHinh=%s, "
    "@TongQDThucHanh=%s, @QDThucHanhHinh=%s, @SoGiayCNTN=%s, @NgayRaQDTN=%s"
)


@router.post("/cap-nhat")
def cap_nhat(body: CapNhatIn, target_key: str | None = None,
             phien: Phien = Depends(require_session)) -> dict:
    """Ghi KQĐT 1 HV vào CDB đích. Quy đổi điểm gốc → 5 điểm /10 + 3 cờ Đạt (per-môn ≥5,
    điểm thô) → gọi SP `_CapNhat` (18 tham số). Cờ CŨ/MỚI đọc theo khóa (phía tool).

    **CHẶN HV `TT_XuLy` 12/13** (đã kết xuất/hoàn thành) — SP KHÔNG bảo vệ 12 (gọi vào sẽ
    kéo lùi 12→09). Hạng lấy TỪ DB (không tin client). SoGiayCNTN tự sinh khi Đạt."""
    db = _db_dich(target_key)
    try:
        with sqlserver_conn_dich(db, autocommit=True) as conn:
            cur = conn.cursor(as_dict=True)
            # 1) Đọc HV: khóa, trạng thái, hạng, ngày khóa — từ DB (không tin client)
            cur.execute(
                "SELECT hs.MaKhoaHoc, hs.TT_XuLy, hs.HangGPLX, gp.MaHangMoi, "
                "CONVERT(varchar(8), kh.NgayBG, 112) AS NgayBG, "
                "CONVERT(varchar(8), kh.NgayThi, 112) AS NgayThi "
                "FROM dbo.NguoiLX_HoSo hs JOIN dbo.KhoaHoc kh ON kh.MaKH = hs.MaKhoaHoc "
                "LEFT JOIN dbo.DM_HangGPLX gp ON gp.MaHang = hs.HangGPLX "
                "WHERE hs.MaDK = %s",
                (body.ma_dk,),
            )
            hv = cur.fetchone()
            if not hv:
                raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ học viên ở CSDL đích.")
            tt = (hv["TT_XuLy"] or "").strip()
            if tt in ("12", "13"):
                raise HTTPException(
                    status_code=409,
                    detail="Học viên đã kết xuất gửi Sở / hoàn thành (TT_XuLy 12/13) — không sửa kết quả qua tool.",
                )
            ma_kh = hv["MaKhoaHoc"]
            ct = config_store.get_kqd_chuong_trinh(ma_kh)
            hang_cat = ketqua_quydoi.phan_loai_hang(hv["MaHangMoi"], hv["HangGPLX"])
            ma_hang_moi = (hv["MaHangMoi"] or "").strip()

            # 2) Quy đổi + tính Đạt (vượt khung → 400). KQD-06 sửa lẻ: môn giữ lấy quy-đổi đã lưu.
            try:
                if body.giu_quydoi:
                    kq = ketqua_quydoi.ket_qua_hon_hop(body.diem_goc, body.giu_quydoi, hang_cat, ct)
                else:
                    kq = ketqua_quydoi.tinh_ket_qua(body.diem_goc, hang_cat, ct)
            except ketqua_quydoi.LoiDiem as e:
                raise HTTPException(status_code=400, detail=str(e))

            # 3) Giờ/km: giờ sân khóa cứng theo hạng; km sân mặc định theo hạng (cho sửa);
            #    giờ/km đường nhập tay (None → NULL). Hạng không xác định → không khóa cứng.
            gk = ketqua_quydoi.gio_km(hang_cat)
            gio_san = gk.gio_san if gk else None
            km_san = body.km_san if body.km_san is not None else (gk.km_san if gk else None)

            # 4) Số giấy HTKH tự sinh khi Đạt (MaDK + '-' + MaHangMoi)
            so_giay = (f"{body.ma_dk}-{ma_hang_moi}" if (kq.ket_luan_csdt and ma_hang_moi) else None)

            # 5) Ngày: UI gửi (cho sửa) hoặc mặc định từ khóa
            tg_bd = _ymd(body.tg_bat_dau) or (hv["NgayBG"] or "")
            tg_kt = _ymd(body.tg_ket_thuc) or (hv["NgayThi"] or "")
            ngay_qd = _ngay(body.ngay_ra_qdtn)

            # 6) KQD-04: ghi giải trình TRƯỚC khi gọi SP (quyết định ④-A) — UPDATE tham số hóa
            #    riêng cột GiaiTrinh (SP _CapNhat không có tham số này). Lỗi ở đây thì chưa đụng
            #    điểm/trạng thái (HV giữ 14/90, báo lỗi sạch). None = không đụng cột.
            if body.giai_trinh is not None:
                gt = body.giai_trinh.strip()
                if len(gt) > 1000:
                    raise HTTPException(status_code=400, detail="Giải trình tối đa 1000 ký tự.")
                cur.execute(
                    "UPDATE dbo.NguoiLX_HoSo SET GiaiTrinh=%s WHERE MaDK=%s AND MaKhoaHoc=%s",
                    (gt or None, body.ma_dk, ma_kh),
                )

            cot = kq.quy_doi_tron
            cur.execute(_SP_CAPNHAT, (
                body.ma_dk, ma_kh,
                "1" if kq.kq_ly_thuyet else "0",
                "1" if kq.kq_thuc_hanh else "0",
                tg_bd, tg_kt,
                "1" if kq.ket_luan_csdt else "0",
                cot["ly_thuyet"], cot["duong"], cot["mo_phong"], cot["hinh"], cot["tien_lui"],
                body.gio_duong, gio_san, body.km_duong, km_san,
                so_giay, ngay_qd,
            ))
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không ghi được kết quả — kiểm kết nối rồi thử lại.")
    # tt_moi phản ánh đúng SP: giữ nguyên 90/13/14, else 09 (đạt) / 10 (không đạt).
    tt_moi = tt if tt in ("90", "13", "14") else ("09" if kq.ket_luan_csdt else "10")
    return {
        "ok": True,
        "ma_dk": body.ma_dk,
        "ket_luan": "dat" if kq.ket_luan_csdt else "khong_dat",
        "tt_moi": tt_moi,
        "so_giay": so_giay,
        "quy_doi": kq.quy_doi_tron,
        "ct": ct,
    }


# ── KQD-06: Xóa điểm (reset HV về chưa có điểm) — chỉ HV chưa kết xuất (09/10) ──
# SP _CapNhat chỉ đặt 09/10, KHÔNG lùi được 03 → UPDATE trực tiếp tham số hóa (verify DB 07/10).
class XoaDiemIn(BaseModel):
    ma_dk: str


_SQL_XOA_DIEM = (
    "UPDATE dbo.NguoiLX_HoSo SET "
    "DiemKQLyThuyet=NULL, DiemKQMoPhong=NULL, DiemKQHinh=NULL, DiemKQTienLui=NULL, DiemKQThucHanh=NULL, "
    "KQLyThuyet=NULL, KQThucHanh=NULL, KetLuanCSDT=NULL, SoGiayCNTN=NULL, "
    "TT_XuLy='03', NgaySua=GETDATE() "
    "WHERE MaDK=%s AND TT_XuLy IN ('09','10')"
)


@router.post("/xoa-diem")
def xoa_diem(body: XoaDiemIn, target_key: str | None = None) -> dict:
    """KQD-06: xóa điểm đã lưu, đưa HV về chưa có điểm (TT_XuLy='03').

    CHỈ HV `TT_XuLy` 09/10 (đã cập nhật, CHƯA gửi Sở). HV 12 phải mở khóa (KQD-05) trước;
    13 khóa tuyệt đối; 14/90 sửa qua KQD-04. Kiểm trạng thái bằng SELECT TRƯỚC rồi mới UPDATE:
    không ở 09/10 → 409; không tìm thấy → 404. KHÔNG dùng `rowcount` để quyết (pymssql có thể
    trả -1 khi bảng có trigger/NOCOUNT → báo nhầm thất bại dù điểm đã xóa).
    NULL 5 điểm + 3 cờ + SoGiayCNTN; reset TT về '03'. UI phải xác nhận trước khi gọi."""
    db = _db_dich(target_key)
    try:
        with sqlserver_conn_dich(db, autocommit=True) as conn:
            cur = conn.cursor(as_dict=True)
            # 1) Kiểm trạng thái TRƯỚC (không tin rowcount pymssql)
            cur.execute("SELECT TT_XuLy FROM dbo.NguoiLX_HoSo WHERE MaDK = %s", (body.ma_dk,))
            hv = cur.fetchone()
            if not hv:
                raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ học viên ở CSDL đích.")
            if (hv["TT_XuLy"] or "").strip() not in ("09", "10"):
                raise HTTPException(
                    status_code=409,
                    detail="Chỉ xóa được điểm của HV đang 'Đã cập nhật' (09/10, chưa kết xuất). "
                           "HV đã kết xuất phải Mở khóa trước; hoàn thành/giải trình không xóa ở đây.",
                )
            # 2) UPDATE — giữ ràng buộc 09/10 trong WHERE làm lưới chống đua (TOCTOU)
            cur.execute(_SQL_XOA_DIEM, (body.ma_dk,))
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không xóa được điểm — kiểm kết nối rồi thử lại.")
    return {"ok": True, "ma_dk": body.ma_dk, "tt_moi": "03"}


# ── KQD-05 (task 76): Mở khóa để sửa sau kết xuất — gỡ chặn 12 có kiểm soát, MỨC CƠ SỞ ──
# Nghiệp vụ + lý do (DB KHÔNG nối HV↔gói, tên gói chỉ timestamp): TDD §11D.7 · TDD-decisions §19.
# Thao tác MỨC CƠ SỞ (mọi khóa của CSĐT) vì xóa gói buộc quét cả CSĐT — gói lọc theo
# NoiGui=<mã CSĐT> (không parse tên file), nên HV lùi cũng phải cả cơ sở, tránh HV khóa khác
# treo "12 không gói". Verify cột live 07/10: TrangThai varchar(1) '0'/'1', Id varchar(36),
# SP usp_TRANS_CLI_HangDoiGui_Delete(@Id). require_session gác sẵn ở cấp router (main.py _gac).

_SQL_GOI_KQDT = (
    "SELECT Id, DuongDan, TrangThai, KickThuocFile, "
    "CONVERT(varchar(10), NgayTao, 103) + ' ' + CONVERT(varchar(5), NgayTao, 108) AS NgayTao "
    "FROM dbo.TRANS_CLI_HangDoiGui "
    "WHERE KieuDuLieu = 'KET_QUA_DAO_TAO' AND NoiGui = %s "
    "ORDER BY NgayTao DESC"
)

# Đếm HV TT_XuLy=12 của cơ sở: se_lui = CÓ kết luận (sẽ về 09/10); bo_qua = KetLuanCSDT NULL
# (bất thường, đã kết xuất ắt có kết luận → KHÔNG ép '10' oan, chỉ bỏ qua + báo); so_khoa trong nhóm sẽ lùi.
_SQL_DEM_HV12 = (
    "SELECT "
    "SUM(CASE WHEN KetLuanCSDT IS NOT NULL THEN 1 ELSE 0 END) AS se_lui, "
    "SUM(CASE WHEN KetLuanCSDT IS NULL THEN 1 ELSE 0 END) AS bo_qua, "
    "COUNT(DISTINCT CASE WHEN KetLuanCSDT IS NOT NULL THEN MaKhoaHoc END) AS so_khoa "
    "FROM dbo.NguoiLX_HoSo WHERE MaCSDT = %s AND TT_XuLy = '12'"
)

# UPDATE lùi MỌI HV 12 CÓ kết luận của cơ sở về 09/10 (review #1: mức cơ sở, không theo khóa).
# Guard KetLuanCSDT IS NOT NULL (review #3): HV 12 chưa kết luận → bỏ qua, không ép '10' oan.
# {gt} = ", GiaiTrinh = %s" khi UI gửi lý do (ghi cho mọi HV được lùi), rỗng khi không.
_SQL_LUI_HV12 = (
    "UPDATE dbo.NguoiLX_HoSo "
    "SET TT_XuLy = CASE WHEN KetLuanCSDT = 1 THEN '09' WHEN KetLuanCSDT = 0 THEN '10' END, "
    "NgaySua = GETDATE(){gt} "
    "WHERE MaCSDT = %s AND TT_XuLy = '12' AND KetLuanCSDT IS NOT NULL"
)


def _goi_row(r: dict) -> dict:
    """1 gói hàng đợi → dict cho UI. ten_file = tên tệp cuối đường dẫn (DuongDan có cả 'C:\\…')."""
    duong_dan = (r["DuongDan"] or "").strip()
    ten = duong_dan.replace("/", "\\").rstrip("\\").split("\\")[-1] or duong_dan
    return {
        "id": r["Id"],
        "ten_file": ten,
        "duong_dan": duong_dan,
        "ngay_tao": (r["NgayTao"] or "").strip() or None,
        "kich_thuoc": r["KickThuocFile"],
    }


def _ma_csdt_hoac_loi(conn) -> str:
    ma = sync_helpers.get_ma_csdt_tu_qtht(conn)
    if not ma:
        raise HTTPException(status_code=400, detail="CSDL đích thiếu MA_CSDT trong QTHT_ThamSoHT.")
    return ma


@router.get("/mo-khoa")
def mo_khoa_trang_thai(target_key: str | None = None) -> dict:
    """KQD-05 cổng B-1 (CHỈ ĐỌC): cơ sở còn gói KQĐT chưa gửi không → bật/tắt nút + nội dung modal.

    Trả danh sách gói chưa gửi (sẽ xóa) + đã gửi (ca khóa cứng M1) + số HV 12 sẽ lùi / bỏ qua
    + số khóa ảnh hưởng. KHÔNG đổi gì."""
    db = _db_dich(target_key)
    try:
        with sqlserver_conn_dich(db) as conn:
            ma = _ma_csdt_hoac_loi(conn)
            cur = conn.cursor(as_dict=True)
            cur.execute(_SQL_GOI_KQDT, (ma,))
            goi = cur.fetchall()
            cur.execute(_SQL_DEM_HV12, (ma,))
            dem = cur.fetchone() or {}
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)
    chua = [_goi_row(r) for r in goi if (r["TrangThai"] or "").strip() == "0"]
    da = [_goi_row(r) for r in goi if (r["TrangThai"] or "").strip() == "1"]
    return {
        "ma_csdt": ma,
        "mo_duoc": bool(chua),                        # cổng B-1: còn gói chưa gửi → mở được
        "goi_chua_gui": chua,
        "goi_da_gui": da,
        "so_hv_mo": int(dem.get("se_lui") or 0),      # HV 12 sẽ lùi (có kết luận)
        "so_hv_bo_qua": int(dem.get("bo_qua") or 0),  # HV 12 KetLuanCSDT NULL → bỏ qua
        "so_khoa": int(dem.get("so_khoa") or 0),
    }


class MoKhoaIn(BaseModel):
    ma_kh: str | None = None            # chỉ ghi log/ngữ cảnh (gói KHÔNG nối khóa — thao tác cả cơ sở)
    giai_trinh: str | None = None       # None = không đụng GiaiTrinh; chuỗi = ghi cho mọi HV được lùi


@router.post("/mo-khoa")
def mo_khoa(body: MoKhoaIn, target_key: str | None = None) -> dict:
    """KQD-05: mở khóa để sửa điểm sau kết xuất — MỨC CƠ SỞ, gỡ chặn 12 có kiểm soát.

    Chỉ mở khi cơ sở còn gói KQĐT chưa gửi (cổng B-1); hết gói chưa gửi → 409 (M1), KHÔNG đổi gì.
    Lùi MỌI HV 12 CÓ kết luận của cơ sở về 09/10 **TRƯỚC**, rồi mới xóa gói qua SP — nếu xóa gói
    lỗi giữa chừng thì HV đã về 09/10 sửa được + cổng còn mở để chạy lại (khớp edge PRD KQD-05),
    tránh kẹt "12 không gói". `13` tuyệt đối không mở. HV 12 KetLuanCSDT NULL → bỏ qua, không ép '10'."""
    db = _db_dich(target_key)
    gt = None
    if body.giai_trinh is not None:
        gt = body.giai_trinh.strip()
        if len(gt) > 1000:
            raise HTTPException(status_code=400, detail="Lý do mở khóa tối đa 1000 ký tự.")
    try:
        with sqlserver_conn_dich(db, autocommit=True) as conn:
            ma = _ma_csdt_hoac_loi(conn)
            cur = conn.cursor(as_dict=True)
            cur.execute(_SQL_GOI_KQDT, (ma,))
            goi = cur.fetchall()
            chua = [r for r in goi if (r["TrangThai"] or "").strip() == "0"]
            # Cổng B-1: không còn gói chưa gửi → khóa cứng (M1), KHÔNG đổi gì.
            if not chua:
                da = [_goi_row(r) for r in goi if (r["TrangThai"] or "").strip() == "1"]
                raise HTTPException(status_code=409, detail={
                    "loi": "da_gui_het",
                    "thong_bao": "Mọi gói kết quả của cơ sở đã gửi đi Sở — không xóa gói để mở khóa được. "
                                 "Dùng \"Sửa sau gửi\": tích chọn từng học viên ở tab Cập nhật KQĐT rồi bấm Mở sửa điểm.",
                    "goi_da_gui": da,
                })
            # Đếm trước khi lùi (sau khi lùi, nhóm có-kết-luận về 09/10 nên đếm lại = 0).
            cur.execute(_SQL_DEM_HV12, (ma,))
            dem = cur.fetchone() or {}
            so_khoa = int(dem.get("so_khoa") or 0)
            so_hv_bo_qua = int(dem.get("bo_qua") or 0)
            # 1) Lùi HV TRƯỚC (an toàn khi xóa gói lỗi giữa chừng).
            sql_lui = _SQL_LUI_HV12.format(gt=(", GiaiTrinh = %s" if gt is not None else ""))
            params = ((gt or None, ma) if gt is not None else (ma,))
            cur.execute(sql_lui, params)
            rc = cur.rowcount
            so_hv_mo = rc if (rc is not None and rc >= 0) else int(dem.get("se_lui") or 0)
            # 2) Xóa mọi gói chưa gửi của cơ sở qua SP (quét cả CSĐT — gói không lọc được theo khóa).
            so_goi_xoa = 0
            for r in chua:
                cur.execute("EXEC dbo.usp_TRANS_CLI_HangDoiGui_Delete @Id=%s", (r["Id"],))
                so_goi_xoa += 1
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không mở khóa được — kiểm kết nối rồi thử lại.")
    return {
        "ok": True,
        "ma_csdt": ma,
        "so_hv_mo": so_hv_mo,          # HV 12 đã lùi về 09/10
        "so_goi_xoa": so_goi_xoa,      # gói chưa gửi đã xóa
        "so_hv_bo_qua": so_hv_bo_qua,  # HV 12 KetLuanCSDT NULL → bỏ qua (cảnh báo)
        "so_khoa": so_khoa,            # số khóa có HV được lùi
    }


# ── KQD-05 mở rộng (task 83, CHANGES #53): "Sửa sau gửi" — chọn từng HV, KHÔNG xóa gói ──
# Dùng khi cơ sở HẾT gói chưa gửi (còn gói chưa gửi → lối mở khóa ở trên, xóa gói để không
# gửi điểm cũ). Phản hồi Sở (usp_CSDT_PheDuyetKQDT_TiepNhan) chỉ nhận HV đang '12' → HV mở
# sửa phải được kết xuất lại sớm; khối đỏ ở KQD-03 nhắc việc đó. TDD §11D.7b · decisions §21.

class MoSuaSauGuiIn(BaseModel):
    ma_dk: list[str] = Field(..., min_length=1, max_length=sua_sau_gui.SO_HV_TOI_DA)
    ly_do: str          # kiểm rỗng / ≤1000 SAU khi strip (xem handler)


_SQL_HV_SSG = (
    "SELECT B.MaDK, B.MaKhoaHoc, B.TT_XuLy, B.KetLuanCSDT, A.HoVaTen, "
    "B.DiemKQLyThuyet, B.DiemKQMoPhong, B.DiemKQHinh, B.DiemKQTienLui, B.DiemKQThucHanh "
    "FROM dbo.NguoiLX_HoSo B JOIN dbo.NguoiLX A ON A.MaDK = B.MaDK "
    "WHERE B.MaCSDT = %s AND B.MaDK IN ({ph})"
)

# Lùi ĐÚNG 1 HV theo MaDK (không theo cơ sở như _SQL_LUI_HV12). Guard '12' + có kết luận.
_SQL_LUI_MOT_HV = (
    "UPDATE dbo.NguoiLX_HoSo "
    "SET TT_XuLy = CASE WHEN KetLuanCSDT = 1 THEN '09' WHEN KetLuanCSDT = 0 THEN '10' END, "
    "GiaiTrinh = %s, NgaySua = GETDATE() "
    "WHERE MaDK = %s AND MaCSDT = %s AND TT_XuLy = '12' AND KetLuanCSDT IS NOT NULL"
)

_SQL_TT_HIEN_TAI = "SELECT MaDK, TT_XuLy FROM dbo.NguoiLX_HoSo WHERE MaCSDT = %s AND MaDK IN ({ph})"


def _chunks(xs: list, n: int = 200):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def _tt_hien_tai(cur, ma: str, ma_dks: list[str]) -> dict[str, str]:
    """{MaDK: TT_XuLy} hiện tại ở đích — SELECT lại thay vì tin rowcount (pymssql có thể -1)."""
    out: dict[str, str] = {}
    for ch in _chunks(ma_dks):
        cur.execute(_SQL_TT_HIEN_TAI.format(ph=", ".join(["%s"] * len(ch))), (ma, *ch))
        for r in cur.fetchall():
            out[str(r["MaDK"]).strip()] = (r["TT_XuLy"] or "").strip()
    return out


@router.post("/mo-sua-sau-gui")
def mo_sua_sau_gui(body: MoSuaSauGuiIn, target_key: str | None = None,
                   phien: Phien = Depends(require_session)) -> dict:
    """KQD-05 #53: mở sửa điểm cho các HV `12` được chọn khi gói đã gửi Sở (KHÔNG xóa gói).

    Thứ tự an toàn: (1) cổng — còn gói chưa gửi → 409 `con_goi_chua_gui`; (2) có HV `13` →
    409 `co_hv_13` (không đổi gì); (3) ghi nhật ký sqlite TRƯỚC (lỗi → chưa đụng DB đích);
    (4) UPDATE từng MaDK; (5) SELECT lại để biết HV nào thật sự lùi, dòng nhật ký HV không
    lùi được → 'huy'. HV `12` thiếu kết luận → bỏ qua, không ép '10'."""
    ly_do = body.ly_do.strip()
    if not ly_do:
        raise HTTPException(status_code=400, detail="Cần nhập lý do sửa sau khi đã gửi Sở.")
    if len(ly_do) > sua_sau_gui.LY_DO_TOI_DA:
        raise HTTPException(status_code=400, detail=f"Lý do tối đa {sua_sau_gui.LY_DO_TOI_DA} ký tự.")
    ma_dks = list(dict.fromkeys(m.strip() for m in body.ma_dk if m and m.strip()))
    if not ma_dks:
        raise HTTPException(status_code=400, detail="Chưa chọn học viên nào.")
    db = _db_dich(target_key)
    mo: list[dict] = []
    bo_qua: list[dict] = []
    try:
        with sqlserver_conn_dich(db, autocommit=True) as conn:
            ma = _ma_csdt_hoac_loi(conn)
            cur = conn.cursor(as_dict=True)
            # 1) Cổng: còn gói chưa gửi → dùng "Mở khóa" (xóa gói chưa gửi), không dùng lối này.
            cur.execute(_SQL_GOI_KQDT, (ma,))
            chua = [r for r in cur.fetchall() if (r["TrangThai"] or "").strip() == "0"]
            if chua:
                raise HTTPException(status_code=409, detail={
                    "loi": "con_goi_chua_gui",
                    "thong_bao": "Cơ sở còn gói kết quả chưa gửi Sở — dùng \"Mở khóa để sửa\" "
                                 "(xóa gói chưa gửi) thay vì sửa sau gửi.",
                    "goi_chua_gui": [_goi_row(r) for r in chua],
                })
            # 2) Đọc HV được chọn (ràng MaCSDT) rồi phân loại.
            rows: list[dict] = []
            for ch in _chunks(ma_dks):
                cur.execute(_SQL_HV_SSG.format(ph=", ".join(["%s"] * len(ch))), (ma, *ch))
                rows.extend(cur.fetchall())
            pl = sua_sau_gui.phan_loai(rows, ma_dks)
            if pl["bi_13"]:
                raise HTTPException(status_code=409, detail={
                    "loi": "co_hv_13",
                    "thong_bao": "Có học viên đã hoàn thành (13, Sở đã duyệt) — không mở sửa được. "
                                 "Bỏ họ khỏi lựa chọn rồi thử lại.",
                    "ma_dk": pl["bi_13"],
                })
            bo_qua = list(pl["bo_qua"])
            hop_le = pl["hop_le"]
            if hop_le:
                # 3) Nhật ký TRƯỚC — lỗi thì chưa đụng DB đích.
                try:
                    ids = sua_sau_gui.ghi(hop_le, ly_do, phien.username)
                except Exception:  # noqa: BLE001
                    raise HTTPException(
                        status_code=500,
                        detail="Không ghi được nhật ký sửa sau gửi — chưa đổi gì ở CSDL đích.",
                    )
                ma_hl = [str(r["MaDK"]).strip() for r in hop_le]
                try:
                    # 4) UPDATE từng HV.
                    for r in hop_le:
                        cur.execute(_SQL_LUI_MOT_HV, (ly_do, str(r["MaDK"]).strip(), ma))
                finally:
                    # 5) Đối chiếu thật: HV nào đã về 09/10; không lùi được → hủy dòng nhật ký.
                    tt_moi = _tt_hien_tai(cur, ma, ma_hl)
                    huy: list[int] = []
                    for r in hop_le:
                        ma_dk = str(r["MaDK"]).strip()
                        tt = tt_moi.get(ma_dk)
                        if tt in ("09", "10"):
                            mo.append({"ma_dk": ma_dk, "ho_ten": (r.get("HoVaTen") or "").strip(), "tt_moi": tt})
                        else:
                            huy.append(ids[ma_dk])
                            bo_qua.append({"ma_dk": ma_dk, "ly_do": "Trạng thái đổi giữa chừng — chưa mở được, thử lại."})
                    sua_sau_gui.doi_trang_thai(huy, sua_sau_gui.HUY)
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=502, detail="Không mở sửa được — kiểm kết nối rồi thử lại.")
    return {"ok": True, "so_mo": len(mo), "mo": mo, "bo_qua": bo_qua}


def _luc_hien(iso: str | None) -> str | None:
    """'2026-10-10T14:05:00' → '10/10/2026 14:05' (hiển thị VN)."""
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y %H:%M") if iso else None
    except ValueError:
        return iso


@router.get("/sua-sau-gui")
def ds_sua_sau_gui(target_key: str | None = None) -> list[dict]:
    """KQD-03 khối đỏ: HV đã mở "sửa sau gửi" mà chưa kết xuất lại (nhật ký ∩ trạng thái hiện tại).

    HV đã về `12` (hoặc xa hơn 13/14/90) → phần mềm CDB đã kết xuất lại → đánh 'da_kx', rời
    khối đỏ. HV không còn trong CSDL → 'huy'. Chỉ đọc CDB đích; ghi duy nhất vào nhật ký."""
    cho = sua_sau_gui.cho_kx()
    if not cho:
        return []
    db = _db_dich(target_key)
    ma_dks = list(dict.fromkeys(c["ma_dk"] for c in cho))
    hien: dict[str, dict] = {}
    try:
        with sqlserver_conn_dich(db) as conn:
            ma = _ma_csdt_hoac_loi(conn)
            cur = conn.cursor(as_dict=True)
            for ch in _chunks(ma_dks):
                cur.execute(_SQL_HV_SSG.format(ph=", ".join(["%s"] * len(ch))), (ma, *ch))
                for r in cur.fetchall():
                    hien[str(r["MaDK"]).strip()] = r
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)
    da_kx: list[int] = []
    huy: list[int] = []
    out: list[dict] = []
    for c in cho:
        r = hien.get(c["ma_dk"])
        if r is None:
            huy.append(c["id"])
            continue
        tt = (r["TT_XuLy"] or "").strip()
        if tt in sua_sau_gui.TT_DA_KX:
            da_kx.append(c["id"])
            continue
        try:
            truoc = json.loads(c["diem_truoc_json"] or "{}")
        except ValueError:
            truoc = {}
        out.append({
            "id": c["id"],
            "ma_dk": c["ma_dk"],
            "ma_kh": c["ma_kh"],
            "ho_ten": c["ho_ten"],
            "nguoi": c["nguoi"],
            "luc_mo": _luc_hien(c["luc_mo"]),
            "ly_do": c["ly_do"],
            "tt_xuly": tt or None,
            "diem_truoc": truoc,
            "diem_hien": {
                "ly_thuyet": _diem(r["DiemKQLyThuyet"]),
                "mo_phong": _diem(r["DiemKQMoPhong"]),
                "hinh": _diem(r["DiemKQHinh"]),
                "tien_lui": _diem(r["DiemKQTienLui"]),
                "duong": _diem(r["DiemKQThucHanh"]),
                "ket_luan": _ket_luan(r["KetLuanCSDT"]),
            },
        })
    sua_sau_gui.doi_trang_thai(da_kx, sua_sau_gui.DA_KX)
    sua_sau_gui.doi_trang_thai(huy, sua_sau_gui.HUY)
    return out
