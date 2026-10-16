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

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from pydantic import BaseModel, Field

from app import config_store, ketqua_dat, ketqua_quydoi, ketqua_so, ketqua_xuat, paths, sua_sau_gui, sync_helpers
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
    "B.TGThucHanhHinh, B.QDThucHanhHinh, B.TGThucHanhDuong, B.TongQDThucHanh, B.SoGiayCNTN, "
    "B.GiaiTrinh, B.LyDoTuChoiKQDT "
    "FROM dbo.NguoiLX_HoSo B JOIN dbo.NguoiLX A ON A.MaDK = B.MaDK "
    "LEFT JOIN dbo.DM_HangGPLX gp ON gp.MaHang = B.HangGPLX "
    "WHERE B.MaKhoaHoc = %s AND B.TrangThai = 1{loc} "
    "ORDER BY CAST(B.SoHoSo AS INT)"
)


def _diem(v) -> float | None:
    return float(v) if v is not None else None


def _so2(v) -> float | None:
    """Giờ/km đường: cột real của CDB trả 18.399999618… → làm tròn 2 chữ số để hiển thị đúng 18,4."""
    return round(float(v), 2) if v is not None else None


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
            "gio_duong": _so2(r["TGThucHanhDuong"]),
            "km_duong": _so2(r["TongQDThucHanh"]),
            # KQD-04 #77: lý do Sở từ chối + giải trình hiện ngay trên dòng lưới (không phải mở chi tiết)
            "ly_do_tu_choi": ((r.get("LyDoTuChoiKQDT") or "").strip() or None),
            "giai_trinh": ((r.get("GiaiTrinh") or "").strip() or None),
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
            "canh_bao": ketqua_quydoi.canh_bao_duong(
                hv["gio_duong"], hv["km_duong"],
                ketqua_quydoi.phan_loai_hang(r["MaHangMoi"], r["HangGPLX"])),
        })
    return {"ma_kh": ma_kh, "tong": tong, "du": du, "thieu": thieu, "dem": dem, "mo_to_bo_qua": mo_to}


@router.get("/luat")
def luat_kqd() -> dict:
    """Luật dùng chung cho KQD-02 (ô đỏ trên lưới) và KQD-07 (kiểm trước kết xuất): danh sách môn bắt buộc.

    Một nguồn ở backend để hai màn không lệch nhau; UI đọc một lần khi mở màn."""
    return {"mon_bat_buoc": list(ketqua_quydoi.MON)}


# ── KQD-09: xuất Excel kết quả học tập theo khóa (TDD §11D.11) — CHỈ ĐỌC ──
def _doc_khoa_va_hv(ma_kh: str, target_key: str | None) -> tuple[dict, list[dict]]:
    """Thông tin khóa + HV đang hoạt động của khóa (chỉ SELECT). Dùng chung cho các nút xuất file.
    Khóa không tồn tại / không có HV → 404 (không tạo file rỗng)."""
    db = _db_dich(target_key)
    try:
        with sqlserver_conn_dich(db) as conn:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                "SELECT k.MaKH, k.TenKH, k.HangGPLX, "
                "CONVERT(varchar(10), k.NgayKG, 103) AS NgayKG, "
                "CONVERT(varchar(10), k.NgayBG, 103) AS NgayBG, "
                "CONVERT(varchar(10), k.NgayThi, 103) AS NgayThi "
                "FROM dbo.KhoaHoc k WHERE k.MaKH = %s",
                (ma_kh,),
            )
            khoa = cur.fetchone()
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)
    if not khoa:
        raise HTTPException(status_code=404, detail="Không tìm thấy khóa học ở CSDL đích.")
    hv = _doc_hv_khoa(ma_kh, None, target_key)
    if not hv:
        raise HTTPException(status_code=404, detail="Khóa chưa có học viên — không có gì để xuất.")
    return khoa, hv


def _co_so_tu_cau_hinh() -> dict:
    cfg = config_store.load_config()
    return {"co_quan_chu_quan": cfg.get("co_quan_chu_quan", ""),
            "ten_co_so_dao_tao": cfg.get("ten_co_so_dao_tao", "")}


def _luu_file_xuat(data: bytes, ma_kh: str, ngay, tien_to: str, so_hv: int) -> dict:
    """Ghi file vào thư mục output của phần mềm (không ghi đè) → thông tin trả cho UI."""
    try:
        thu_muc = paths.output_dir()
        file = ketqua_xuat.luu_file(thu_muc, ketqua_xuat.ten_file(ma_kh, ngay, tien_to), data)
    except OSError:
        raise HTTPException(status_code=500, detail="Không ghi được file vào thư mục output của phần mềm — kiểm quyền ghi thư mục.")
    return {"ok": True, "ten_file": file.name, "duong_dan": str(file), "thu_muc": str(thu_muc), "so_hoc_vien": so_hv}


@router.post("/xuat-excel")
def xuat_excel(
    ma_kh: str = Query(..., min_length=1),
    target_key: str | None = None,
    phien: Phien = Depends(require_session),
) -> dict:
    """Dựng file `.xlsx` kết quả học tập của ĐÚNG 1 khóa và **lưu vào thư mục `output` của phần mềm**.

    Khối đầu + bảng 22 cột, mọi HV đang hoạt động. Chỉ SELECT DB (không ghi DB); chỉ ghi 1 file ra đĩa.
    Khóa không có HV hoạt động → 404 (không tạo file rỗng). Tên cơ quan/cơ sở lấy từ cấu hình tool
    (trống thì để trống ô); người lập = họ tên người đang đăng nhập tool. Trả đường dẫn để UI báo."""
    khoa, hv = _doc_khoa_va_hv(ma_kh, target_key)
    bay_gio = datetime.now()
    try:
        data = ketqua_xuat.dung_workbook(
            khoa, hv, _co_so_tu_cau_hinh(),
            (phien.ho_ten or phien.username or "").strip(), bay_gio,
            config_store.get_kqd_chuong_trinh(ma_kh),
        )
    except Exception:  # noqa: BLE001 — không lộ chi tiết nội bộ ra response
        raise HTTPException(status_code=500, detail="Không dựng được file Excel — thử lại hoặc báo người hỗ trợ.")
    return _luu_file_xuat(data, ma_kh, bay_gio.date(), "KetQuaHocTap", len(hv))


@router.post("/xuat-so-theo-doi")
def xuat_so_theo_doi(
    ma_kh: str = Query(..., min_length=1),
    target_key: str | None = None,
    phien: Phien = Depends(require_session),
) -> dict:
    """KQD-10 — dựng "Sổ theo dõi kết quả học tập" (mẫu Phụ lục VI, TT17) của ĐÚNG 1 khóa, lưu vào `output`.

    1 sheet A4 dọc: khối đầu + 2 hàng tiêu đề lặp mọi trang + "Trang x/y"; xếp theo TÊN (alphabet tiếng
    Việt); `Người lập` để trống. Chỉ SELECT DB."""
    khoa, hv = _doc_khoa_va_hv(ma_kh, target_key)
    bay_gio = datetime.now()
    try:
        data = ketqua_so.dung_so_theo_doi(khoa, hv, _co_so_tu_cau_hinh(), bay_gio)
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Không dựng được sổ theo dõi — thử lại hoặc báo người hỗ trợ.")
    kq = _luu_file_xuat(data, ma_kh, bay_gio.date(), ketqua_so.TIEN_TO_FILE, len(hv))
    # Giải thích cho người in: HV có kết luận nhưng thiếu điểm → ô kết quả để trống (luật sổ mẫu).
    kq["so_hv_trong_ket_qua"] = ketqua_so.dem_trong_ket_qua(hv)
    return kq


@router.post("/mo-thu-muc-xuat")
def mo_thu_muc_xuat(phien: Phien = Depends(require_session)) -> dict:
    """Mở thư mục `output` của phần mềm bằng File Explorer (đường dẫn cố định, không nhận đầu vào)."""
    import os
    import sys

    thu_muc = paths.output_dir()
    try:
        if sys.platform == "win32":
            os.startfile(str(thu_muc))  # noqa: S606 — đường dẫn do tool tự chọn, không từ người dùng
        else:  # pragma: no cover — tool chỉ chạy Windows
            raise OSError("Chỉ hỗ trợ mở thư mục trên Windows.")
    except OSError:
        raise HTTPException(status_code=500, detail=f"Không mở được thư mục. Đường dẫn: {thu_muc}")
    return {"ok": True, "thu_muc": str(thu_muc)}


# ── KQD-08: nạp giờ/km đường từ PDF DAT (TDD §11D.10) ──
_DAT_TOI_DA = 5 * 1024 * 1024    # PDF DAT 60 dòng chỉ ~vài chục KB; 5 MB là dư


@router.post("/dat/xem-truoc")
def dat_xem_truoc(
    ma_kh: str = Form(..., min_length=1),
    file: UploadFile = File(...),
    target_key: str | None = None,
) -> dict:
    """Đọc PDF DAT → bảng xác nhận (giờ/km cũ → mới) cho ĐÚNG khóa `ma_kh`. KHÔNG ghi DB.

    Mã khóa trong file khác `ma_kh` → 400 (chống nạp nhầm khóa). Khớp HV theo MaDK."""
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Chỉ nhận file PDF báo cáo DAT.")
    data = file.file.read(_DAT_TOI_DA + 1)
    if len(data) > _DAT_TOI_DA:
        raise HTTPException(status_code=413, detail="File quá lớn (tối đa 5 MB).")
    if not data.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="File không phải PDF.")
    try:
        pdf = ketqua_dat.doc_pdf_dat(data)
    except ketqua_dat.LoiDat as e:
        raise HTTPException(status_code=400, detail=str(e))
    if pdf["ma_kh"].strip().upper() != ma_kh.strip().upper():
        raise HTTPException(
            status_code=400,
            detail=f"File thuộc khóa {pdf['ma_kh']}, khác khóa đang chọn ({ma_kh}). Chọn đúng file của khóa này.",
        )
    hv = _doc_hv_khoa(ma_kh, None, target_key)
    kq = ketqua_dat.doi_chieu(pdf["dong"], hv)
    khong_co = [d for d in kq["dong"] if d["tinh_trang"] == ketqua_dat.KHONG_CO_TRONG_KHOA]
    if khong_co:
        theo_ma, theo_ten, chua_tra = _tra_cuu_khong_co(khong_co, target_key)
        ketqua_dat.gan_ly_do_khong_co(khong_co, theo_ma, theo_ten, ma_kh, chua_tra)
    return {"ma_kh": ma_kh, "hang": pdf["hang"], "tong_file": len(pdf["dong"]), **kq}


_TOI_DA_TRA_TEN = 50   # tra theo tên + ngày sinh chạy từng truy vấn → chặn số dòng để không chậm


_TOI_DA_TRA_MA = 500


def _tra_cuu_khong_co(items: list[dict], target_key: str | None) -> tuple[dict | None, dict | None, set]:
    """Tra DB đích (chỉ SELECT) cho các dòng PDF không có trong khóa: theo MaDK ở MỌI khóa, rồi theo
    (họ tên + ngày sinh). Trả (theo_ma, theo_ten, chua_tra): `chua_tra` = mã vượt trần tra cứu (không được
    kết luận "không tìm thấy"). Lỗi kết nối → (None, None, set()) để UI vẫn hiện lý do chung."""
    theo_ma: dict[str, list] = {}
    theo_ten: dict[tuple, list] = {}
    chua_tra: set[str] = set()
    try:
        with sqlserver_conn_dich(_db_dich(target_key)) as conn:
            cur = conn.cursor(as_dict=True)
            ma_het = [d["ma_dk"] for d in items]
            ma = ma_het[:_TOI_DA_TRA_MA]
            chua_tra.update(ma_het[_TOI_DA_TRA_MA:])
            if ma:
                cur.execute(
                    "SELECT hs.MaDK, hs.MaKhoaHoc, hs.TrangThai, kh.TenKH FROM dbo.NguoiLX_HoSo hs "
                    "LEFT JOIN dbo.KhoaHoc kh ON kh.MaKH = hs.MaKhoaHoc WHERE hs.MaDK IN ("
                    + ", ".join(["%s"] * len(ma)) + ")",
                    tuple(ma),
                )
                for r in cur.fetchall():
                    theo_ma.setdefault(r["MaDK"], []).append(r)
            # Chỉ dòng chưa thấy theo mã mới tra theo tên (ưu tiên khớp theo MaDK).
            can_ten_het = [d for d in items if d["ma_dk"] not in theo_ma and d["ma_dk"] not in chua_tra]
            can_ten = can_ten_het[:_TOI_DA_TRA_TEN]
            chua_tra.update(d["ma_dk"] for d in can_ten_het[_TOI_DA_TRA_TEN:])
            for d in can_ten:
                ns = ketqua_dat.ngay_sinh_luu(d.get("ngay_sinh", ""))
                if not ns or not d["ho_ten"].strip():
                    continue
                cur.execute(
                    "SELECT TOP 3 a.MaDK, hs.MaKhoaHoc, hs.TrangThai, kh.TenKH FROM dbo.NguoiLX a "
                    "JOIN dbo.NguoiLX_HoSo hs ON hs.MaDK = a.MaDK "
                    "LEFT JOIN dbo.KhoaHoc kh ON kh.MaKH = hs.MaKhoaHoc "
                    "WHERE a.HoVaTen = %s AND a.NgaySinh = %s",
                    (d["ho_ten"].strip(), ns),
                )
                rows = cur.fetchall()
                if rows:
                    theo_ten[(d["ho_ten"].strip(), ns)] = rows
        return theo_ma, theo_ten, chua_tra
    except Exception:  # noqa: BLE001 — chỉ là phần giải thích thêm, không được làm hỏng xem trước
        return None, None, set()


class DatDongIn(BaseModel):
    ma_dk: str
    gio_duong: float = Field(ge=0, le=999)
    km_duong: float = Field(ge=0, le=99999)


class DatLuuIn(BaseModel):
    ma_kh: str
    dong: list[DatDongIn] = Field(min_length=1, max_length=1000)


@router.post("/dat/luu")
def dat_luu(body: DatLuuIn, target_key: str | None = None,
            phien: Phien = Depends(require_session)) -> dict:
    """Ghi giờ đường + km đường cho các HV đã tick — MỘT transaction, chỉ 2 cột này.

    KHÔNG gọi SP `_CapNhat` (SP ghi đè điểm/kết luận/trạng thái). Chỉ HV thuộc `ma_kh` và chưa
    `12`/`13`; dòng không đủ điều kiện → `bo_qua` kèm lý do. Hỏng giữa chừng → rollback cả lô."""
    db = _db_dich(target_key)
    da_luu = 0
    bo_qua: list[dict] = []
    try:
        with sqlserver_conn_dich(db, autocommit=False) as conn:
            cur = conn.cursor(as_dict=True)
            try:
                for d in body.dong:
                    cur.execute(
                        "UPDATE dbo.NguoiLX_HoSo SET TGThucHanhDuong=%s, TongQDThucHanh=%s, NgaySua=GETDATE() "
                        "WHERE MaDK=%s AND MaKhoaHoc=%s AND TrangThai = 1 AND ISNULL(TT_XuLy,'') NOT IN ('12','13')",
                        (d.gio_duong, d.km_duong, d.ma_dk, body.ma_kh),
                    )
                    if cur.rowcount == 1:
                        da_luu += 1
                    else:
                        bo_qua.append({"ma_dk": d.ma_dk,
                                       "ly_do": "Không thuộc khóa này, không còn hoạt động, hoặc đã kết xuất/hoàn thành (12/13)."})
                conn.commit()
            except Exception:
                conn.rollback()
                raise
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=502, detail="Không ghi được giờ/km — kiểm kết nối rồi thử lại, chưa có dòng nào được lưu.")
    return {"ok": True, "da_luu": da_luu, "bo_qua": bo_qua}


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
    giai_trinh: str | None = None        # KQD-04: None = không đụng cột GiaiTrinh; '' = xóa (khi không có chung); chuỗi = ghi
    giai_trinh_chung: str | None = None  # KQD-04 #77: giải trình chung của khóa — chỉ dùng khi riêng rỗng VÀ cột đang trống


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


# KQD-04 (#77, TDD §11D.13): HV Sở từ chối (14) đã Đạt + có giải trình → "Đang giải trình" (90).
# SP `_CapNhat` GIỮ nguyên 14/90/13 và không thủ tục nào đặt 90, nên tool tự UPDATE; guard nằm TRONG SQL
# (không tin cờ client). Dùng chung cho `/cap-nhat` và (task 137) `/giai-trinh-lo`.
_SQL_14_SANG_90 = (
    "UPDATE dbo.NguoiLX_HoSo SET TT_XuLy='90', NgaySua=GETDATE() "
    "WHERE MaDK=%s AND MaKhoaHoc=%s AND TT_XuLy='14' AND KetLuanCSDT=1 AND LTRIM(RTRIM(ISNULL(GiaiTrinh,'')))<>''"
)
_SQL_DOC_LAI_TT = "SELECT TT_XuLy, ISNULL(GiaiTrinh,'') AS GiaiTrinh FROM dbo.NguoiLX_HoSo WHERE MaDK=%s"


def chuyen_14_sang_90(cur, ma_dk: str, ma_kh: str) -> None:
    """UPDATE 14→90 cho 1 HV, guard trong SQL. Không dựa rowcount — người gọi SELECT lại trạng thái."""
    cur.execute(_SQL_14_SANG_90, (ma_dk, ma_kh))


def giai_trinh_hieu_luc(rieng: str | None, chung: str | None, hien_co: str) -> tuple[bool, str | None]:
    """(co_ghi, gia_tri). Riêng có chữ → ghi riêng · riêng '' và KHÔNG có chung → xóa ·
    chung có chữ mà cột đang trống → ghi chung (chung KHÔNG BAO GIỜ đè giải trình đã có) · còn lại giữ nguyên."""
    r = (rieng or "").strip() if rieng is not None else None
    c = (chung or "").strip()
    if r:
        return True, r
    if rieng is not None and chung is None:      # '' tường minh, không có chung → xóa
        return True, None
    if c and not (hien_co or "").strip():
        return True, c
    return False, None


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
                "SELECT hs.MaKhoaHoc, hs.TT_XuLy, hs.HangGPLX, gp.MaHangMoi, hs.MaCSDT, "
                "ISNULL(hs.GiaiTrinh,'') AS GiaiTrinh, "
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
            # KQD-04 #77: HV phải thuộc cơ sở của máy (máy dùng chung nhiều CSĐT). Máy thiếu MA_CSDT → không chặn.
            ma_may = sync_helpers.get_ma_csdt_tu_qtht(conn)
            ma_hv = (hv.get("MaCSDT") or "").strip()
            if ma_may and ma_hv and ma_may != ma_hv:
                raise HTTPException(status_code=403, detail="Học viên không thuộc cơ sở của máy này.")
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
            #    điểm/trạng thái (HV giữ 14/90, báo lỗi sạch). Hiệu lực: riêng → chung (chỉ khi cột
            #    đang trống) → giữ nguyên. Guard `TT_XuLy NOT IN ('12','13')` chống đua với kết xuất lại.
            for cho in (body.giai_trinh, body.giai_trinh_chung):
                if cho is not None and len(cho.strip()) > 1000:
                    raise HTTPException(status_code=400, detail="Giải trình tối đa 1000 ký tự.")
            co_ghi, gt_ghi = giai_trinh_hieu_luc(body.giai_trinh, body.giai_trinh_chung, hv.get("GiaiTrinh") or "")
            if co_ghi:
                cur.execute(
                    "UPDATE dbo.NguoiLX_HoSo SET GiaiTrinh=%s WHERE MaDK=%s AND MaKhoaHoc=%s "
                    "AND ISNULL(TT_XuLy,'') NOT IN ('12','13')",
                    (gt_ghi, body.ma_dk, ma_kh),
                )
            # 6b) Đọc lại trạng thái NGAY TRƯỚC SP: phần mềm CDB có thể vừa kết xuất lại (→12) và SP
            #     không bảo vệ 12 (sẽ kéo lùi 12→09). Khe hở nhỏ còn lại ghi ở TDD §11D.13 (d).
            cur.execute(_SQL_DOC_LAI_TT, (body.ma_dk,))
            dl = cur.fetchone()
            if dl is None or (dl["TT_XuLy"] or "").strip() != tt:
                raise HTTPException(status_code=409, detail={"loi": "trang_thai_da_doi",
                                                            "thong_bao": "Trạng thái học viên vừa đổi — tải lại danh sách rồi thử lại."})

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
            # 7) KQD-04 #77: HV `14` vừa Đạt + có giải trình → 90. Lỗi ở đây KHÔNG được báo 502 (điểm đã ghi):
            #    trả 200 + cảnh báo để UI hiện nút "Chuyển lại".
            canh_bao = None
            if tt == "14" and kq.ket_luan_csdt:
                try:
                    chuyen_14_sang_90(cur, body.ma_dk, ma_kh)
                except Exception:
                    canh_bao = "chua_chuyen_90"
            # Suy sẵn kết quả theo quy tắc để nếu SELECT đọc lại lỗi thì KHÔNG báo sai (vd HV đã sang 90).
            gt_db = ((gt_ghi if co_ghi else hv.get("GiaiTrinh")) or "").strip()
            tt_db = tt
            if tt == "14" and kq.ket_luan_csdt and gt_db and canh_bao is None:
                tt_db = "90"
            try:
                cur.execute(_SQL_DOC_LAI_TT, (body.ma_dk,))
                dl2 = cur.fetchone()
                if dl2:
                    tt_db, gt_db = (dl2["TT_XuLy"] or "").strip(), (dl2["GiaiTrinh"] or "").strip()
            except Exception:
                pass
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không ghi được kết quả — kiểm kết nối rồi thử lại.")
    # tt_moi đọc lại từ DB (SP giữ nguyên 90/13/14; riêng 14→90 do tool — KQD-04 #77). Không đọc lại
    # được thì suy từ quy tắc cũ. thieu_giai_trinh: HV 14 Đạt mà chưa có giải trình → CHƯA kết xuất được.
    if tt_db == tt and tt not in ("90", "13", "14"):
        tt_db = "09" if kq.ket_luan_csdt else "10"
    return {
        "ok": True,
        "ma_dk": body.ma_dk,
        "ket_luan": "dat" if kq.ket_luan_csdt else "khong_dat",
        "tt_moi": tt_db,
        "thieu_giai_trinh": bool(tt_db == "14" and kq.ket_luan_csdt and not gt_db),
        "canh_bao": canh_bao,
        "so_giay": so_giay,
        "quy_doi": kq.quy_doi_tron,
        "ct": ct,
    }


# ── KQD-04 đổi (#77, task 137): giải trình + chuyển 14→90 HÀNG LOẠT, mẫu giải trình ──
LO_TOI_DA = 200
NOI_DUNG_TOI_DA = 1000

_SQL_LO_DOC = (
    "SELECT B.MaDK, B.MaKhoaHoc, B.MaCSDT, B.TT_XuLy, B.KetLuanCSDT, ISNULL(B.GiaiTrinh,'') AS GiaiTrinh, "
    "B.HangGPLX, gp.MaHangMoi, B.DiemKQLyThuyet, B.DiemKQMoPhong, B.DiemKQHinh, B.DiemKQTienLui, "
    "B.DiemKQThucHanh, B.TGThucHanhHinh, B.QDThucHanhHinh, B.TGThucHanhDuong, B.TongQDThucHanh, B.SoGiayCNTN "
    "FROM dbo.NguoiLX_HoSo B LEFT JOIN dbo.DM_HangGPLX gp ON gp.MaHang = B.HangGPLX "
    "WHERE B.TrangThai = 1 AND B.MaDK IN ({ph})"
)
# Giải trình riêng được GIỮ (chỉ ghi chung cho người cột đang trống) trừ khi tham số đầu = 1 (ghi_de_rieng).
# Guard trong SQL: đúng HV 14 + Đạt — người nào đổi trạng thái giữa chừng thì không khớp, không bị ghi đè.
_SQL_LO_GHI = (
    "UPDATE dbo.NguoiLX_HoSo SET "
    "GiaiTrinh = CASE WHEN %s = 1 OR LTRIM(RTRIM(ISNULL(GiaiTrinh,''))) = '' THEN %s ELSE GiaiTrinh END, "
    "TT_XuLy = '90', NgaySua = GETDATE() "
    "WHERE MaDK IN ({ph}) AND TT_XuLy = '14' AND KetLuanCSDT = 1"
)
_SQL_LO_DOC_LAI = "SELECT MaDK, TT_XuLy FROM dbo.NguoiLX_HoSo WHERE MaDK IN ({ph})"
_KHONG_RO = {"ketqua": "khong_ro", "thong_bao": "Không rõ kết quả — kiểm tra lại danh sách trước khi gửi lại."}


class GiaiTrinhLoIn(BaseModel):
    ma_dk: list[str]
    noi_dung: str
    ghi_de_rieng: bool = False


def phan_loai_lo(ma_dk: list[str], rows: dict[str, dict], ma_may: str | None) -> tuple[list[str], list[dict]]:
    """THUẦN (không DB): tách lô thành (đủ điều kiện, bỏ qua kèm lý do). Một nguồn luật `hv_chua_du` với KQD-07."""
    du: list[str] = []
    bo: list[dict] = []
    for ma in ma_dk:
        r = rows.get(ma)
        if r is None:
            bo.append({"ma_dk": ma, "ly_do": "khong_tim_thay"})
            continue
        ma_hv = (r.get("MaCSDT") or "").strip()
        if ma_may and ma_hv and ma_may != ma_hv:
            bo.append({"ma_dk": ma, "ly_do": "khong_thuoc_co_so"})
            continue
        tt = (r.get("TT_XuLy") or "").strip()
        if tt in ("12", "13"):
            bo.append({"ma_dk": ma, "ly_do": "da_gui_hoac_hoan_thanh"})
            continue
        if tt == "90":
            bo.append({"ma_dk": ma, "ly_do": "da_o_dang_giai_trinh"})     # gọi lại an toàn — không phải lỗi
            continue
        if tt != "14":
            bo.append({"ma_dk": ma, "ly_do": "khong_con_o_so_tu_choi"})
            continue
        if _ket_luan(r.get("KetLuanCSDT")) != "dat":
            bo.append({"ma_dk": ma, "ly_do": "khong_dat"})
            continue
        hv = {
            "tt_xuly": tt, "ket_luan": "dat",
            "diem": {"ly_thuyet": _diem(r.get("DiemKQLyThuyet")), "mo_phong": _diem(r.get("DiemKQMoPhong")),
                     "hinh": _diem(r.get("DiemKQHinh")), "tien_lui": _diem(r.get("DiemKQTienLui")),
                     "duong": _diem(r.get("DiemKQThucHanh"))},
            "gio_san": r.get("TGThucHanhHinh"), "km_san": r.get("QDThucHanhHinh"),
            "gio_duong": r.get("TGThucHanhDuong"), "km_duong": r.get("TongQDThucHanh"),
        }
        kq = ketqua_quydoi.hv_chua_du(hv)
        ly_do = list(kq["ly_do"])
        if not (r.get("SoGiayCNTN") or "").strip():
            ly_do.append("thieu_so_giay")
        if ly_do:
            bo.append({"ma_dk": ma, "ly_do": "chua_du_diem", "chi_tiet": {"ly_do": ly_do, "mon_thieu": kq["mon_thieu"]}})
            continue
        du.append(ma)
    return du, bo


@router.post("/giai-trinh-lo")
def giai_trinh_lo(body: GiaiTrinhLoIn, target_key: str | None = None,
                  phien: Phien = Depends(require_session)) -> dict:
    """Giải trình + chuyển HV Sở từ chối `14` → `90` HÀNG LOẠT (TDD §11D.13). Một giao dịch thật:
    lỗi thì KHÔNG chuyển ai (502 `lo_loi`); mất kết nối đúng lúc COMMIT → 502 `khong_ro`. Gọi lại an toàn."""
    ma_dk = list(dict.fromkeys(m.strip() for m in body.ma_dk if m and m.strip()))
    if not ma_dk:
        raise HTTPException(status_code=422, detail="Chưa chọn học viên nào.")
    if len(ma_dk) > LO_TOI_DA:
        raise HTTPException(status_code=422, detail=f"Tối đa {LO_TOI_DA} học viên một lượt.")
    noi_dung = (body.noi_dung or "").strip()
    if not noi_dung:
        raise HTTPException(status_code=422, detail="Phải có nội dung giải trình mới chuyển được.")
    if len(noi_dung) > NOI_DUNG_TOI_DA:
        raise HTTPException(status_code=422, detail=f"Giải trình tối đa {NOI_DUNG_TOI_DA} ký tự.")

    db = _db_dich(target_key)
    ph = ", ".join(["%s"] * len(ma_dk))
    da_chuyen: list[str] = []
    giu = 0
    try:
        with sqlserver_conn_dich(db, autocommit=False, timeout=30) as conn:
            cur = conn.cursor(as_dict=True)
            cur.execute(_SQL_LO_DOC.format(ph=ph), tuple(ma_dk))
            rows = {str(r["MaDK"]).strip(): r for r in cur.fetchall()}
            ma_may = sync_helpers.get_ma_csdt_tu_qtht(conn)
            du, bo_qua = phan_loai_lo(ma_dk, rows, ma_may)
            if du:
                ph_du = ", ".join(["%s"] * len(du))
                try:
                    cur.execute(_SQL_LO_GHI.format(ph=ph_du), (1 if body.ghi_de_rieng else 0, noi_dung, *du))
                except Exception:
                    conn.rollback()
                    raise HTTPException(status_code=502, detail={
                        "loi": "lo_loi", "da_chuyen": [],
                        "thong_bao": "Không chuyển được — chưa chuyển học viên nào. Thử lại."})
                try:
                    conn.commit()
                except Exception:
                    raise HTTPException(status_code=502, detail=_KHONG_RO)
                # đọc lại trạng thái thật (không tin rowcount)
                try:
                    cur.execute(_SQL_LO_DOC_LAI.format(ph=ph_du), tuple(du))
                    sau = {str(r["MaDK"]).strip(): (r["TT_XuLy"] or "").strip() for r in cur.fetchall()}
                except Exception:
                    raise HTTPException(status_code=502, detail=_KHONG_RO)
                for m in du:
                    if sau.get(m) == "90":
                        da_chuyen.append(m)
                    else:
                        bo_qua.append({"ma_dk": m, "ly_do": "khong_con_o_so_tu_choi"})   # đổi trạng thái giữa chừng
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail={
            "loi": "lo_loi", "da_chuyen": [],
            "thong_bao": "Không kết nối được CSDL đích — chưa chuyển học viên nào."})
    # giu_rieng: số người ĐÃ CHUYỂN mà giải trình riêng được giữ (đếm sau khi đọc lại trạng thái)
    if not body.ghi_de_rieng:
        giu = sum(1 for m in da_chuyen if (rows[m].get("GiaiTrinh") or "").strip())
    return {"ok": True, "da_chuyen": da_chuyen, "bo_qua": bo_qua, "giu_rieng": giu}


class MauGiaiTrinhIn(BaseModel):
    mau: list[str]
    phien_ban: int | None = None


def _khoa_co_so(target_key: str | None) -> str:
    """Khóa lưu mẫu theo cơ sở đích: target_key, thiếu thì target đang chọn."""
    return (target_key or config_store.get_sync_config().get("selected") or "mac_dinh").strip()


@router.get("/mau-giai-trinh")
def doc_mau_giai_trinh(target_key: str | None = None) -> dict:
    """Mẫu giải trình của cơ sở đích + `phien_ban` (PUT gửi lại để phát hiện người khác vừa lưu)."""
    return config_store.get_mau_giai_trinh(_khoa_co_so(target_key))


@router.put("/mau-giai-trinh")
def luu_mau_giai_trinh(body: MauGiaiTrinhIn, target_key: str | None = None) -> dict:
    """Thay TOÀN BỘ danh sách mẫu (sửa/xóa/thêm gom một lần). Rỗng/trùng bị loại; >20 mẫu hoặc >1000 ký tự →
    422 nêu rõ; `phien_ban` lệch → 409 `mau_da_doi`."""
    try:
        return config_store.set_mau_giai_trinh(_khoa_co_so(target_key), body.mau, body.phien_ban)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except config_store.MauDaDoi:
        raise HTTPException(status_code=409, detail={
            "loi": "mau_da_doi", "thong_bao": "Mẫu vừa được người khác cập nhật — tải lại danh sách."})


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
