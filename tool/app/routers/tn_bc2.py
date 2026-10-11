"""Tốt nghiệp & Báo cáo 2 (TNB) — router tool máy CSDT. TDD §11F.

Task 97: CHỈ ĐỌC (lập BC2 / thêm HV: nguồn ứng viên). Ghi (tạo BC2, thêm/gỡ HV, tốt nghiệp,
cứu trạng thái) thêm ở task 98+. Mount kèm `require_session` ở main.py (collector không có
session cục bộ → 403). Đọc DB Nạp `GPLX_CSDT` bằng `sqlserver_cursor()` — KHÔNG đụng CDB.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app import tn_bc2_rules as rules
from app import tn_bc2_service as svc
from app.db import ConfigChuaDay, sqlserver_cursor

router = APIRouter(prefix="/local/tnbc2", tags=["tnbc2"])


def _loi(e: Exception) -> HTTPException:
    if isinstance(e, svc.LoiNghiepVu):
        return HTTPException(status_code=e.http, detail={"ma": e.ma, "noi_dung": e.noi_dung})
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
