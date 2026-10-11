"""Tốt nghiệp & Báo cáo 2 (TNB) — router tool máy CSDT. TDD §11F.

Task 97: đọc (nguồn ứng viên). Task 98: tạo BC2. Ghi tiếp (thêm/gỡ HV, tốt nghiệp, cứu trạng thái)
ở task 99+. Mọi `POST` ghi cần `xac_nhan_csdl_that: true` (cổng thao tác chống bấm nhầm, KHÔNG phải
kiểm soát an ninh — an ninh = phiên tool + chỉ nghe 127.0.0.1). Mount kèm `require_session` ở main.py (collector không có
session cục bộ → 403). Đọc DB Nạp `GPLX_CSDT` bằng `sqlserver_cursor()` — KHÔNG đụng CDB.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app import tn_bc2_rules as rules
from app import tn_bc2_service as svc
from app.db import ConfigChuaDay, sqlserver_conn, sqlserver_cursor
from app.session import Phien, require_session

router = APIRouter(prefix="/local/tnbc2", tags=["tnbc2"])


def _loi(e: Exception) -> HTTPException:
    if isinstance(e, svc.LoiNghiepVu):
        d = {"ma": e.ma, "noi_dung": e.noi_dung}
        if e.du_lieu:
            d.update(e.du_lieu)
        return HTTPException(status_code=e.http, detail=d)
    if isinstance(e, ConfigChuaDay):
        return HTTPException(status_code=400, detail={"ma": "chua_cau_hinh_db", "noi_dung": str(e)})
    return HTTPException(status_code=502, detail={
        "ma": "khong_truy_van_duoc", "noi_dung": "Không truy vấn được SQL Server — kiểm kết nối."})


@router.get("/bc2/khoa-san-sang")
def khoa_san_sang(loai: str = Query(..., pattern="^(moto|oto)$"),
                  cu: bool = Query(False, description="Hiện cả khóa bế giảng trước mốc 'hôm nay − 1 tháng − 1 năm'"),
                  thi_lai_thang: int = Query(rules.THI_LAI_THANG_MAC_DINH, ge=0, le=240),
                  lam_tuoi: bool = Query(False, description="Bỏ cache, đọc lại DB")):
    """Bước ①: khóa đã bế giảng + đếm Sẵn sàng / Thi lại / Cần xem (từ một lần đọc cả CSĐT)."""
    try:
        tap = svc.lay_tap(sqlserver_cursor, loai, lam_tuoi=lam_tuoi)
        return svc.khoa_san_sang(tap, loai, cu, thi_lai_thang)
    except Exception as e:  # noqa: BLE001
        raise _loi(e)


def _khoa_va_tap(ma_kh: str, lam_tuoi: bool):
    with sqlserver_cursor() as cur:
        khoa = svc.loai_cua_khoa(cur, ma_kh)
    tap = svc.lay_tap(sqlserver_cursor, khoa["loai"], lam_tuoi=lam_tuoi)
    return khoa, tap


@router.get("/bc2/ung-vien")
def ung_vien(ma_kh: str = Query(..., min_length=1, max_length=30),
             ma_bc2: str = Query("", max_length=13),
             thi_lai_thang: int = Query(rules.THI_LAI_THANG_MAC_DINH, ge=0, le=240),
             lam_tuoi: bool = False):
    """Bước ②: bốn nhóm học viên cho khóa; `ma_bc2` rỗng = chưa có BC2 (sẽ lập ở bước ③)."""
    try:
        khoa, tap = _khoa_va_tap(ma_kh, lam_tuoi)
        svc.kiem_dau_vao(tap, ma_kh, ma_bc2)
        with sqlserver_cursor() as cur:
            ngoai_tap = svc.doc_ngoai_tap_cua_khoa(cur, ma_kh)
        return svc.ung_vien(tap, khoa, ma_bc2, thi_lai_thang, ngoai_tap)
    except Exception as e:  # noqa: BLE001
        raise _loi(e)


class KhopIn(BaseModel):
    ma_kh: str = Field(min_length=1, max_length=30)
    ma_bc2: str = Field(default="", max_length=13)
    dong: list[str] = Field(default_factory=list, max_length=20000)


@router.post("/bc2/khop-danh-sach")
def khop_danh_sach(body: KhopIn):
    """Dán danh sách CMT / mã đăng ký → học viên khớp (chỉ `san_sang`/`thi_lai` được tích)."""
    try:
        khoa, tap = _khoa_va_tap(body.ma_kh, False)
        svc.kiem_dau_vao(tap, body.ma_kh, body.ma_bc2)
        with sqlserver_cursor() as cur:
            ngoai_tap = svc.doc_ngoai_tap_cua_khoa(cur, body.ma_kh)
        return svc.khop_danh_sach(tap, khoa, body.dong, body.ma_bc2, ngoai_tap)
    except Exception as e:  # noqa: BLE001
        raise _loi(e)


@router.get("/bc2/goi-y-so")
def goi_y_so(ma_kh: str = Query(..., min_length=1, max_length=30)):
    """Số BC2 gợi ý (nhân viên sửa được) + BC1 của khóa + BC2 đã có của BC1 đó."""
    try:
        with sqlserver_cursor() as cur:
            return svc.goi_y_so(cur, ma_kh)
    except Exception as e:  # noqa: BLE001
        raise _loi(e)


class TaoBc2In(BaseModel):
    ma_kh: str = Field(min_length=1, max_length=30)
    so_bao_cao: str = Field(min_length=1, max_length=60)      # kiểm ≤ 13 ký tự ở luật (MaBCII varchar 13)
    ngay_bao_cao: str = Field(default="", max_length=10)       # YYYY-MM-DD; rỗng = hôm nay
    ghi_chu: str = Field(default="", max_length=1000)
    da_xem_canh_bao: bool = False
    thu_lai: bool = False            # True = gửi lại sau khi không biết kết quả lần trước (mất kết nối)
    xac_nhan_csdl_that: bool = False


@router.post("/bc2")
def tao_bc2(body: TaoBc2In, phien: Phien = Depends(require_session)):
    """Tạo BC2 rỗng (hoặc dùng lại cho `/bc2/lap`): `usp_BaoCaoII_Insert`, `TrangThai=0`."""
    if not body.xac_nhan_csdl_that:
        raise HTTPException(status_code=400, detail={
            "ma": "thieu_xac_nhan_csdl_that", "noi_dung": "Cần xác nhận đây là CSDL thật trước khi ghi."})
    try:
        with sqlserver_conn() as conn:
            return svc.tao_bc2(conn, body.ma_kh, body.so_bao_cao, body.ngay_bao_cao, body.ghi_chu,
                               phien.username, da_xem_canh_bao=body.da_xem_canh_bao, thu_lai=body.thu_lai)
    except Exception as e:  # noqa: BLE001
        raise _loi(e)
