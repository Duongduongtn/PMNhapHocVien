# -*- coding: utf-8 -*-
"""Nghiệp vụ tạo học viên ở CSDL đích cho phân hệ Đồng bộ CDB (SYNC-01).

PORT SÁT `sync_one_hv` của sync_tool v2.0 (`sync_gplx.py`), đổi pyodbc → pymssql:
- `usp_NguoiLX_Insert` tạo NguoiLX (@MaDK OUT; MaCSDT = @DonViNhanHSo = khóa đích)
- INSERT THÔ `NguoiLX_HoSo` với **SoHoSo SỐ** (MAX+1 theo khóa) — khớp 100% dữ liệu
  thật của CSDL đích (kể cả bản phần mềm CDB tạo; KHÔNG dùng CreateNewSoHoso ra B01).
- copy `NguoiLXHS_GiayTo` (MaGT là mã loại giấy tờ, copy từ nguồn) — lỗi copy KHÔNG
  nuốt âm thầm mà trả về cờ (khác `except: pass` của bản cũ).
- Backdate: MaDK tự sinh trước (sync_helpers.sinh_madk_batch) + UPDATE 4 cột ngày
  (SP/DEFAULT hardcode getdate).

Nghiệp vụ CSDL đích: PK NguoiLX_HoSo = MaDK → 1 người = 1 hồ sơ = 1 MaDK. HV đã có
ở đích → caller SKIP (không gọi hàm này).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

logger = logging.getLogger(__name__)

NGUOI_TAO_MAC_DINH = "admin"  # khớp bản ghi phần mềm CDB (verify DB 04/10)

# Cột đọc từ khóa nguồn (GPLX_CSDT) — đúng tập cột sync_tool v2.0 dùng để tạo HV.
_HV_SELECT = """
    SELECT
        A.MaDK, A.HoVaTen, A.SoCMT, A.NgaySinh, A.GioiTinh,
        A.HoDemNLX, A.TenNLX, A.HoVaTenIn, A.MaQuocTich, A.DonViNhanHSo,
        A.NoiTT, A.NoiTT_MaDVHC, A.NoiTT_MaDVQL,
        A.NoiCT, A.NoiCT_MaDVHC, A.NoiCT_MaDVQL,
        A.NgayCapCMT, A.NoiCapCMT, A.GhiChu, A.SO_CMND_CU,
        B.SoHoSo, B.HangGPLX, B.HangDaoTao, B.MaKhoaHoc,
        B.MaLoaiHs, B.MaCSDT, B.MaSoGTVT, B.MaDVNhanHSo,
        B.NgayNhanHSo, B.NguoiNhanHSo, B.NgayHenTra,
        B.DuongDanAnh, B.ChatLuongAnh, B.NgayThuNhanAnh, B.NguoiThuNhanAnh,
        B.SoGPLXDaCo, B.HangGPLXDaCo, B.DonViCapGPLXDaCo, B.NoiCapGPLXDaCo,
        B.NgayCapGPLXDaCo, B.NgayHHGPLXDaCo, B.NgayTTGPLXDaCo,
        B.DonViHocLX, B.NamHocLX, B.SoNamLX, B.SoKmLXAnToan, B.GiayCNSK,
        B.LyDoCapDoi, B.MucDichCapDoi, B.NoiDungSH, B.MaHTCap, B.TT_XuLy
    FROM dbo.NguoiLX A
    JOIN dbo.NguoiLX_HoSo B ON A.MaDK = B.MaDK
    WHERE B.MaKhoaHoc = %s AND A.TrangThai = 1
    ORDER BY A.TenNLX, A.HoDemNLX
"""


@dataclass
class KetQuaHV:
    ok: bool
    ma_dk: Optional[str] = None
    so_ho_so: Optional[str] = None
    loi: Optional[str] = None
    giay_to_loi: bool = False  # tạo HV OK nhưng copy giấy tờ lỗi


def load_hoc_vien_nguon(conn_nguon, ma_kh: str) -> list[dict]:
    """Danh sách HV của khóa nguồn (as_dict). Mỗi HV là 1 dict theo _HV_SELECT."""
    cur = conn_nguon.cursor(as_dict=True)
    cur.execute(_HV_SELECT, (ma_kh,))
    return cur.fetchall()


def load_giay_to_nguon(conn_nguon, ma_dk: str, so_ho_so: str) -> list[tuple]:
    """Giấy tờ (MaGT, TenGT, TrangThai) của 1 hồ sơ ở khóa nguồn."""
    cur = conn_nguon.cursor()
    cur.execute(
        "SELECT MaGT, TenGT, TrangThai FROM dbo.NguoiLXHS_GiayTo WHERE MaDK=%s AND SoHoSo=%s",
        (ma_dk, so_ho_so),
    )
    return cur.fetchall()


def next_so_ho_so(conn_dich, ma_khoa_dich: str) -> int:
    """MAX(SoHoSo số) hiện có của khóa đích. Caller +1 cho HV kế tiếp."""
    cur = conn_dich.cursor()
    cur.execute(
        "SELECT ISNULL(MAX(CAST(SoHoSo AS INT)), 0) AS mx FROM dbo.NguoiLX_HoSo "
        "WHERE MaKhoaHoc=%s AND ISNUMERIC(SoHoSo)=1",
        (ma_khoa_dich,),
    )
    row = cur.fetchone()
    return int(row[0]) if row and row[0] is not None else 0


# EXEC usp_NguoiLX_Insert — 24 tham số đúng thứ tự khai báo SP. @MaDK OUT (nếu
# truyền NULL, SP tự sinh qua CreateNewMaDK(@DonViNhanHSo)). @NgayTao/@NgaySua
# bị SP bỏ qua (hardcode getdate) → backdate bằng UPDATE sau.
_EXEC_NGUOILX = """
    SET NOCOUNT ON;
    DECLARE @M varchar(25); SET @M = %s;
    EXEC dbo.usp_NguoiLX_Insert @MaDK=@M OUTPUT,
        @DonViNhanHSo=%s,@HoDemNLX=%s,@TenNLX=%s,@HoVaTen=%s,
        @MaQuocTich=%s,@NgaySinh=%s,@NoiTT=%s,@NoiTT_MaDVHC=%s,@NoiTT_MaDVQL=%s,
        @NoiCT=%s,@NoiCT_MaDVHC=%s,@NoiCT_MaDVQL=%s,@SoCMT=%s,@NgayCapCMT=%s,
        @NoiCapCMT=%s,@GhiChu=%s,@TrangThai=1,@NguoiTao=%s,
        @NguoiSua=%s,@NgayTao=NULL,@NgaySua=NULL,@GioiTinh=%s,@HoVaTenIn=%s;
    SELECT @M AS madk;
"""

_INSERT_HOSO = """
    SET NOCOUNT ON;
    INSERT INTO dbo.NguoiLX_HoSo (
        MaDK, SoHoSo, MaCSDT, MaSoGTVT, MaDVNhanHSo,
        NgayNhanHSo, NguoiNhanHSo, NgayHenTra,
        MaLoaiHs, TT_XuLy,
        DuongDanAnh, ChatLuongAnh, NgayThuNhanAnh, NguoiThuNhanAnh,
        SoGPLXDaCo, HangGPLXDaCo, DonViCapGPLXDaCo, NoiCapGPLXDaCo,
        NgayCapGPLXDaCo, NgayHHGPLXDaCo, NgayTTGPLXDaCo,
        DonViHocLX, NamHocLX,
        HangGPLX, SoNamLX, SoKmLXAnToan, GiayCNSK,
        LyDoCapDoi, MucDichCapDoi,
        NoiDungSH, MaKhoaHoc, HangDaoTao,
        GhiChu, NguoiTao, NguoiSua, NgayTao, NgaySua,
        TrangThai, MaHTCap, Transfer_flag
    ) VALUES (
        %s,%s,%s,%s,%s, %s,%s,%s,
        %s,%s, %s,%s,%s,%s, %s,%s,%s,%s, %s,%s,%s, %s,%s, %s,%s,%s,%s, %s,%s, %s,%s,%s,
        %s,%s,%s, %s,%s, 1,%s,0
    )
"""


def sync_one_hv(
    conn_dich,
    conn_nguon,
    hv: dict,
    khoa_info: dict,
    ma_khoa_dich: str,
    so_ho_so_num: int,
    tt_xuly: str,
    *,
    ma_dk_pre: Optional[str] = None,
    ngay_nhap_hs: Optional[date] = None,
    nguoi: str = NGUOI_TAO_MAC_DINH,
) -> KetQuaHV:
    """Tạo 1 HV MỚI ở CSDL đích (HV chưa có ở đích). Port sát sync_tool v2.0.

    khoa_info: {ma_csdt, ma_so_gtvt, hang_gplx} của KHÓA ĐÍCH (mã CSDT lấy đúng
    cách từ khóa đích, KHÔNG bê từ bản ghi nguồn).
    so_ho_so_num: số hồ sơ (int) đã cấp cho HV này (caller tăng dần).
    ma_dk_pre: MaDK pre-allocate (backdate). None → SP tự sinh (ngày hôm nay).
    """
    if ngay_nhap_hs is None:
        ngay_nhap_hs = datetime.now().date()
    nguoi = (nguoi or NGUOI_TAO_MAC_DINH).strip() or NGUOI_TAO_MAC_DINH
    ngay_hs_dt = datetime.combine(ngay_nhap_hs, datetime.min.time())

    ma_csdt = khoa_info["ma_csdt"]
    ma_so_gtvt = khoa_info["ma_so_gtvt"]
    so_ho_so = str(so_ho_so_num).zfill(3)
    cur = conn_dich.cursor()
    ma_dk_moi = None

    try:
        cur.execute(
            _EXEC_NGUOILX,
            (
                ma_dk_pre,  # NULL → SP sinh
                ma_csdt, hv["HoDemNLX"], hv["TenNLX"], hv["HoVaTen"],
                hv["MaQuocTich"], hv["NgaySinh"],
                hv["NoiTT"], hv["NoiTT_MaDVHC"], hv["NoiTT_MaDVQL"],
                hv["NoiCT"], hv["NoiCT_MaDVHC"], hv["NoiCT_MaDVQL"],
                hv["SoCMT"], hv["NgayCapCMT"], hv["NoiCapCMT"], hv["GhiChu"],
                nguoi, nguoi, hv["GioiTinh"], hv["HoVaTenIn"],
            ),
        )
        row = cur.fetchone()
        if not row or not row[0]:
            return KetQuaHV(ok=False, loi="SP không trả MaDK")
        ma_dk_moi = row[0]

        # Backdate NgayTao/NgaySua NguoiLX (SP hardcode getdate) — chỉ khi khác hôm nay
        if ngay_nhap_hs != datetime.now().date():
            cur.execute(
                "SET NOCOUNT ON; UPDATE dbo.NguoiLX SET NgayTao=%s, NgaySua=%s WHERE MaDK=%s",
                (ngay_hs_dt, ngay_hs_dt, ma_dk_moi),
            )

        cur.execute(
            _INSERT_HOSO,
            (
                ma_dk_moi, so_ho_so, ma_csdt, ma_so_gtvt, ma_csdt,
                ngay_hs_dt, nguoi, None,
                hv["MaLoaiHs"], tt_xuly,
                hv["DuongDanAnh"], hv["ChatLuongAnh"], hv["NgayThuNhanAnh"], hv["NguoiThuNhanAnh"],
                hv["SoGPLXDaCo"], hv["HangGPLXDaCo"], hv["DonViCapGPLXDaCo"], hv["NoiCapGPLXDaCo"],
                hv["NgayCapGPLXDaCo"], hv["NgayHHGPLXDaCo"], hv["NgayTTGPLXDaCo"],
                hv["DonViHocLX"], hv["NamHocLX"],
                hv["HangGPLX"], hv["SoNamLX"], hv["SoKmLXAnToan"], hv["GiayCNSK"],
                hv["LyDoCapDoi"], hv["MucDichCapDoi"],
                hv["NoiDungSH"], ma_khoa_dich, hv["HangDaoTao"],
                None, nguoi, nguoi, ngay_hs_dt, ngay_hs_dt,
                hv["MaHTCap"],
            ),
        )
        conn_dich.commit()
    except Exception as e:  # noqa: BLE001 — bắt để rollback + trả lỗi cho lô
        try:
            if ma_dk_moi:
                cur.execute("DELETE FROM dbo.NguoiLXHS_GiayTo WHERE MaDK=%s", (ma_dk_moi,))
                cur.execute("DELETE FROM dbo.NguoiLX_HoSo WHERE MaDK=%s", (ma_dk_moi,))
                cur.execute("DELETE FROM dbo.NguoiLX WHERE MaDK=%s", (ma_dk_moi,))
                conn_dich.commit()
        except Exception:  # noqa: BLE001 — cleanup lỗi: để lại orphan, caller biết qua loi
            logger.error("Cleanup rollback MaDK=%s lỗi", ma_dk_moi)
        return KetQuaHV(ok=False, loi=str(e))

    # Copy giấy tờ (best-effort nhưng KHÔNG nuốt im lặng — trả cờ giay_to_loi)
    giay_to_loi = False
    try:
        for gt in load_giay_to_nguon(conn_nguon, hv["MaDK"], hv["SoHoSo"]):
            cur.execute(
                "SET NOCOUNT ON; INSERT INTO dbo.NguoiLXHS_GiayTo (MaGT, MaDK, SoHoSo, TenGT, TrangThai) "
                "VALUES (%s,%s,%s,%s,%s)",
                (gt[0], ma_dk_moi, so_ho_so, gt[1], gt[2]),
            )
        conn_dich.commit()
    except Exception:  # noqa: BLE001
        giay_to_loi = True
        logger.warning("Copy giấy tờ lỗi cho MaDK=%s (HV vẫn tạo thành công)", ma_dk_moi)

    return KetQuaHV(ok=True, ma_dk=ma_dk_moi, so_ho_so=so_ho_so, giay_to_loi=giay_to_loi)
