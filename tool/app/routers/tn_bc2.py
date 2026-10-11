"""Tốt nghiệp & Báo cáo 2 (TNB) — router tool máy CSDT. TDD §11F.

Task 97: đọc (nguồn ứng viên). Task 98: tạo BC2. Ghi tiếp (thêm/gỡ HV, tốt nghiệp, cứu trạng thái)
ở task 99+. Mọi `POST` ghi cần `xac_nhan_csdl_that: true` (cổng thao tác chống bấm nhầm, KHÔNG phải
kiểm soát an ninh — an ninh = phiên tool + chỉ nghe 127.0.0.1). Mount kèm `require_session` ở main.py (collector không có
session cục bộ → 403). Đọc DB Nạp `GPLX_CSDT` bằng `sqlserver_cursor()` — KHÔNG đụng CDB.
"""
from __future__ import annotations

import re

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


# ── Lập BC2 + thêm HV, hoàn tác (task 99) — chạy nền, idempotent theo `lo_id` ──
_LO_ID = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


def _kiem_lo_id(lo_id: str) -> None:
    if not _LO_ID.match(lo_id or ""):
        raise svc.LoiNghiepVu("lo_id_khong_hop_le", "lo_id phải là chuỗi 8–64 ký tự chữ/số/gạch", 400)


def _cau_xac_nhan(xac_nhan: bool) -> None:
    if not xac_nhan:
        raise HTTPException(status_code=400, detail={
            "ma": "thieu_xac_nhan_csdl_that", "noi_dung": "Cần xác nhận đây là CSDL thật trước khi ghi."})


class LapIn(BaseModel):
    lo_id: str = Field(min_length=1, max_length=80)          # client sinh mỗi lần xác nhận (uuid)
    ma_kh: str = Field(min_length=1, max_length=30)
    ma_bc2: str = Field(default="", max_length=13)           # rỗng = chưa có BC2 → tạo với so_bao_cao
    so_bao_cao: str = Field(default="", max_length=60)
    ngay_bao_cao: str = Field(default="", max_length=10)
    ghi_chu: str = Field(default="", max_length=1000)
    ds_ma_dk: list[str] = Field(default_factory=list, max_length=20000)
    da_xem_canh_bao: bool = False
    xac_nhan_csdl_that: bool = False


@router.post("/bc2/lap")
def lap_bc2(body: LapIn, phien: Phien = Depends(require_session)):
    """"Lập BC2 và thêm N học viên": kiểm nhanh rồi chạy nền; trả ngay `{lo_id, trang_thai, …}`.
    Cùng `lo_id` gọi lại → trả kết quả đang chạy/đã xong, không chạy lần hai (dở dang → "Làm tiếp")."""
    _cau_xac_nhan(body.xac_nhan_csdl_that)
    try:
        _kiem_lo_id(body.lo_id)
        ds = svc._chuan_ds(body.ds_ma_dk)
        vde = rules.kiem_danh_sach_dan(ds)
        if vde:
            raise svc.LoiNghiepVu(vde[0]["ma"], vde[0]["noi_dung"], 400)
        if not ds:
            raise svc.LoiNghiepVu("khong_co_hoc_vien", "Chưa chọn học viên nào để thêm", 400)
        if not svc.trang_thai_lo(body.lo_id):          # lô mới → kiểm nhanh để báo lỗi 4xx ngay, không đợi nền
            with sqlserver_cursor() as cur:
                svc.loai_cua_khoa(cur, body.ma_kh)              # 404 nếu khóa không tồn tại
                bc1_map, bc2_map, bc2_bci, _t = svc.doc_bc(cur)
            svc.kiem_dau_vao({"bc1_theo_khoa": bc1_map, "bc2_map": bc2_map, "bc2_bci": bc2_bci},
                             body.ma_kh, rules.dang_luu_ma_bcii(body.ma_bc2) if body.ma_bc2 else "")
        return svc.khoi_chay(
            body.lo_id, svc.lap_bc2,
            dict(lo_id=body.lo_id, ma_kh=body.ma_kh, ma_bc2=body.ma_bc2, so_bao_cao=body.so_bao_cao,
                 ngay_bao_cao=body.ngay_bao_cao, ghi_chu=body.ghi_chu, ds_ma_dk=ds, nguoi=phien.username,
                 da_xem_canh_bao=body.da_xem_canh_bao),
            sqlserver_conn)
    except Exception as e:  # noqa: BLE001
        raise _loi(e)


@router.get("/bc2/lo/{lo_id}")
def tien_do_lo(lo_id: str):
    """Tiến độ một lô (thêm HV hoặc hoàn tác): `{trang_thai, xu_ly, tong, xong, da_them, bo_qua, …}`."""
    ts = svc.trang_thai_lo(lo_id)
    if ts is None:
        raise HTTPException(status_code=404, detail={"ma": "khong_co_lo", "noi_dung": f"Không có lô {lo_id}"})
    return ts


class HoanTacIn(BaseModel):
    lo_id: str = Field(min_length=1, max_length=80)          # lô hoàn tác (client sinh)
    xac_nhan_csdl_that: bool = False


@router.post("/bc2/{ma:path}/hoan-tac")
def hoan_tac(ma: str, body: HoanTacIn, phien: Phien = Depends(require_session)):
    """Hoàn tác lần thêm gần nhất của BC2 `ma` (số có dấu `/` nên dùng `{ma:path}`), một lần, chạy nền."""
    _cau_xac_nhan(body.xac_nhan_csdl_that)
    try:
        _kiem_lo_id(body.lo_id)
        if not svc.trang_thai_lo(body.lo_id):
            with sqlserver_cursor() as cur:
                _b1, bc2_map, _bci, _t = svc.doc_bc(cur)
            dang_db = rules.dang_luu_ma_bcii(ma)
            tt = bc2_map.get(dang_db, bc2_map.get(ma))
            if tt is None:
                raise svc.LoiNghiepVu("bc2_khong_ton_tai", f"Không có BC2 số {ma}", 404)
            if tt != 0:
                raise svc.LoiNghiepVu("bc2_da_dong", f"BC2 số {ma} đã đóng — không gỡ được", 409)
            from app import tn_bc2_nhat_ky as nk
            goc = nk.lo_lap_gan_nhat_cua_bc2(dang_db)
            if goc is None:
                raise svc.LoiNghiepVu("khong_co_lo", "Không có lần thêm nào của BC2 này để hoàn tác", 404)
            if goc.get("hoan_tac_boi"):
                raise svc.LoiNghiepVu("da_hoan_tac", "Lần thêm gần nhất của BC2 này đã được hoàn tác", 409)
        return svc.khoi_chay(body.lo_id, svc.hoan_tac, dict(ma_bc2=ma, lo_id=body.lo_id, nguoi=phien.username),
                             sqlserver_conn)
    except Exception as e:  # noqa: BLE001
        raise _loi(e)


# ── Tốt nghiệp ô tô: đọc + xem lại (TNB-01, task 101). Đường cố định, đặt TRƯỚC `/bc2/{ma:path}`. ──
@router.get("/khoa")
def khoa_tot_nghiep(loai: str = Query("oto", pattern="^(moto|oto)$"),
                    cu: bool = Query(False, description="Hiện cả khóa bế giảng trước mốc 'hôm nay − 1 tháng − 1 năm'")):
    """Khóa cho màn Tốt nghiệp + số giấy kế tiếp gợi ý. Mô tô không có bước tốt nghiệp nên chỉ `oto`."""
    try:
        if loai != "oto":
            raise svc.LoiNghiepVu("chi_o_to", "Mô tô không có bước tốt nghiệp", 400)
        with sqlserver_cursor() as cur:
            return svc.khoa_tot_nghiep(cur, loai, cu)
    except Exception as e:  # noqa: BLE001
        raise _loi(e)


@router.get("/tot-nghiep/hv")
def hv_tot_nghiep(ma_kh: str = Query(..., min_length=1, max_length=30), q: str = Query("", max_length=100),
                  trang_thai: str = Query("", pattern="^(|chua_tot_nghiep|da_tot_nghiep|da_vao_bc2)$")):
    """HV ô tô của khóa kèm sổ/quyết định/số giấy; tìm không dấu theo tên, CMT, mã đăng ký."""
    try:
        with sqlserver_cursor() as cur:
            return svc.hv_tot_nghiep(cur, ma_kh, q, trang_thai)
    except Exception as e:  # noqa: BLE001
        raise _loi(e)


class DongTnIn(BaseModel):
    # Trần pydantic chỉ để chống rác; giới hạn nghiệp vụ (số giấy ≤ 20…) do luật báo `vuot_do_dai` kèm lý do (không 422)
    ma_dk: str = Field(min_length=1, max_length=200)
    so_giay: str = Field(default="", max_length=500)    # rỗng = chưa cấp


class ChungTnIn(BaseModel):
    so_so_tn: str = Field(default="", max_length=500)
    ngay_vao_so: str = Field(default="", max_length=40)
    so_quyet_dinh: str = Field(default="", max_length=500)
    ngay_ra_qd: str = Field(default="", max_length=40)
    ngay_in: str = Field(default="", max_length=40)


class XemLaiTnIn(BaseModel):
    ma_kh: str = Field(min_length=1, max_length=30)
    dong: list[DongTnIn] = Field(default_factory=list, max_length=20000)
    chung: ChungTnIn = Field(default_factory=ChungTnIn)


@router.post("/tot-nghiep/xem-lai")
def xem_lai_tot_nghiep(body: XemLaiTnIn):
    """CHẠY THỬ (không ghi, không cần cổng xác nhận): kết quả dự kiến từng dòng, trùng số giấy trong lô/DB,
    khoảng số, cảnh báo — dùng cho "kiểm trùng ngay khi gõ" và hộp "Xem lại"."""
    try:
        with sqlserver_cursor() as cur:
            return svc.xem_lai_tot_nghiep(cur, body.ma_kh, [d.model_dump() for d in body.dong],
                                          body.chung.model_dump())
    except Exception as e:  # noqa: BLE001
        raise _loi(e)


class GhiTnIn(BaseModel):
    lo_id: str = Field(min_length=1, max_length=80)          # client sinh mỗi lần xác nhận (uuid)
    ma_kh: str = Field(min_length=1, max_length=30)
    dong: list[DongTnIn] = Field(default_factory=list, max_length=20000)
    chung: ChungTnIn = Field(default_factory=ChungTnIn)
    da_xem_canh_bao: bool = False
    xac_nhan_csdl_that: bool = False


@router.post("/tot-nghiep/ghi")
def ghi_tot_nghiep(body: GhiTnIn, phien: Phien = Depends(require_session)):
    """GHI tốt nghiệp ô tô theo lô: kiểm nhanh đồng bộ (4xx/409 ngay) rồi chạy nền theo `lo_id`;
    theo dõi bằng `GET /bc2/lo/{lo_id}`. Cùng `lo_id` gọi lại → không chạy lần hai (dở dang → "Làm tiếp")."""
    _cau_xac_nhan(body.xac_nhan_csdl_that)
    try:
        _kiem_lo_id(body.lo_id)
        dong = [d.model_dump() for d in body.dong]
        chung = body.chung.model_dump()
        if not svc.trang_thai_lo(body.lo_id):
            with sqlserver_cursor() as cur:
                svc.kiem_truoc_ghi_tn(cur, body.ma_kh, dong, chung, body.da_xem_canh_bao)
        return svc.khoi_chay(
            body.lo_id, svc.ghi_tot_nghiep,
            dict(lo_id=body.lo_id, ma_kh=body.ma_kh, dong=dong, chung=chung, nguoi=phien.username,
                 da_xem_canh_bao=body.da_xem_canh_bao),
            sqlserver_conn)
    except Exception as e:  # noqa: BLE001
        raise _loi(e)


# ── Xem / gỡ / xóa BC2 (task 100). Đặt CUỐI file: `{ma:path}` sẽ nuốt `/goi-y-so`, `/ung-vien`, `/lo/…`
#    nếu khai báo trước các route cố định. Số BC2 có dấu `/` nên dùng `:path`. ──
@router.get("/bc2/{ma:path}")
def chi_tiet_bc2(ma: str):
    """Chi tiết một BC2 + học viên (màn xem/gỡ): `go_duoc`, `ly_do_khoa`, `xoa_duoc`."""
    try:
        with sqlserver_cursor() as cur:
            return svc.chi_tiet_bc2(cur, ma)
    except Exception as e:  # noqa: BLE001
        raise _loi(e)


class GoIn(BaseModel):
    lo_id: str = Field(min_length=1, max_length=80)
    ds_ma_dk: list[str] = Field(default_factory=list, max_length=20000)
    da_xem_canh_bao: bool = False
    xac_nhan_csdl_that: bool = False


@router.post("/bc2/{ma:path}/go")
def go_hv(ma: str, body: GoIn, phien: Phien = Depends(require_session)):
    """Gỡ HV đã chọn khỏi BC2 đang mở; chạy nền theo `lo_id` (cùng cách theo dõi với lập/hoàn tác)."""
    _cau_xac_nhan(body.xac_nhan_csdl_that)
    try:
        _kiem_lo_id(body.lo_id)
        if not svc.trang_thai_lo(body.lo_id):      # lô mới → kiểm nhanh để báo 4xx/409 ngay, không đợi nền
            with sqlserver_cursor() as cur:
                svc.kiem_truoc_go(cur, ma, body.ds_ma_dk, body.da_xem_canh_bao)
        return svc.khoi_chay(
            body.lo_id, svc.go_hv,
            dict(ma_bc2=ma, lo_id=body.lo_id, ds_ma_dk=svc._chuan_ds(body.ds_ma_dk), nguoi=phien.username,
                 da_xem_canh_bao=body.da_xem_canh_bao),
            sqlserver_conn)
    except Exception as e:  # noqa: BLE001
        raise _loi(e)


@router.delete("/bc2/{ma:path}")
def xoa_bc2(ma: str, xac_nhan_csdl_that: bool = Query(False), phien: Phien = Depends(require_session)):
    """Xóa BC2 rỗng còn mở (đếm `MaBC2` mọi `TT_XuLy` ở máy chủ); BC2 đã đóng không xóa."""
    _cau_xac_nhan(xac_nhan_csdl_that)
    try:
        with sqlserver_conn() as conn:
            return svc.xoa_bc2(conn, ma, phien.username)
    except Exception as e:  # noqa: BLE001
        raise _loi(e)
