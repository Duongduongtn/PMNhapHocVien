"""NAP-02 — Liệt kê khóa học chưa lập Báo cáo I (BC1) theo loại mô tô / ô tô.

Done khi (PRD NAP-02):
- Mô tô → hạng bắt đầu 'A'; Ô tô → 'B/C/D/E/F'.
- Chỉ khóa TrangThai=1 và chưa có dòng trong BaoCaoI.
- Suy MaLoaiHs (A*→1, còn lại→2), kèm HangGPLX/HangDT/MaSoGTVT theo khóa.
"""
from __future__ import annotations
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator

from app.db import sqlserver_cursor, sqlserver_conn, ConfigChuaDay
from app.session import Phien, require_session

router = APIRouter(prefix="/local/khoa-hoc", tags=["khoa-hoc"])

# Chữ đầu hạng GPLX theo loại xe (TDD §10.2, PRD NAP-02). Hằng cố định — không phải input user.
_CHU_DAU = {"moto": ("A",), "oto": ("B", "C", "D", "E", "F")}


def suy_ma_loai_hs(hang_gplx: str | None) -> int:
    """Hạng bắt đầu 'A' → 1 (mô tô cấp mới); còn lại → 2 (ô tô cấp mới). TDD §10.2."""
    return 1 if (hang_gplx or "").strip().upper().startswith("A") else 2


@router.get("")
def list_khoa_hoc(loai: str = Query(..., pattern="^(moto|oto)$")):
    """Khóa chưa BC1 theo loại. Rỗng → UI báo 'không có khóa nhận HV' (TDD §10.4)."""
    chu_dau = _CHU_DAU[loai]
    placeholders = ",".join(["%s"] * len(chu_dau))
    sql = f"""
        SELECT k.MaKH, k.TenKH, k.HangGPLX, k.HangDT, k.MaSoGTVT
        FROM KhoaHoc k
        WHERE k.TrangThai = 1
          AND LEFT(k.HangGPLX, 1) IN ({placeholders})
          AND NOT EXISTS (SELECT 1 FROM BaoCaoI b WHERE b.MaKH = k.MaKH)
        ORDER BY k.MaKH DESC
    """
    try:
        with sqlserver_cursor() as cur:
            cur.execute(sql, tuple(chu_dau))
            rows = cur.fetchall()
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không truy vấn được SQL Server — kiểm kết nối.")

    return [
        {
            "ma_kh": r["MaKH"],
            "ten_kh": r["TenKH"],
            "hang_gplx": r["HangGPLX"],
            "hang_dt": r["HangDT"],
            "ma_so_gtvt": r["MaSoGTVT"],
            "ma_loai_hs": suy_ma_loai_hs(r["HangGPLX"]),
        }
        for r in rows
    ]


# ---- KHO-01: tạo khóa học ----
# Hằng cố định của CSDT (BR-017): MaCSDT=70004, MaSoGTVT=70, TrangThai=1.
MA_CSDT = "70004"
MA_SO_GTVT = "70"


class KhoaHocTao(BaseModel):
    """Input tạo khóa (KHO-01). 5 bắt buộc + 4 tùy chọn (BR-017)."""
    hang_dt: str            # DM_HangDT.MaHangDT (hạng mới, vd 'B', 'B.01', 'C1')
    ten_kh: str
    ngay_kg: date
    ngay_bg: date
    tong_so_hv: int
    so_qd: str | None = None
    ngay_qd: date | None = None
    ngay_thi: date | None = None
    ghi_chu: str | None = None

    @field_validator("hang_dt", "ten_kh")
    @classmethod
    def _khong_rong(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Không được để trống")
        return v.strip()

    @field_validator("ten_kh")
    @classmethod
    def _ten_do_dai(cls, v: str) -> str:
        if len(v) > 50:  # KhoaHoc.TenKH nvarchar(50)
            raise ValueError("Tên khóa tối đa 50 ký tự")
        return v

    @field_validator("tong_so_hv")
    @classmethod
    def _hv_duong(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Tổng số học viên phải lớn hơn 0")
        return v


def dung_tham_so_insert(body: KhoaHocTao, hang_gplx: str, thoi_gian_dt: int | None, nguoi: str) -> tuple:
    """Dựng 27 tham số cho usp_KhoaHoc_Insert, đúng thứ tự khai báo SP.

    @MaKH bị SP bỏ qua (tự sinh qua CreateNewMaKhoaHoc); @NgayTao/@NgaySua SP dùng getdate().
    HangGPLX = DM_HangGPLX.MaHang suy từ hạng ĐT (tra ở handler). Đếm HV mới = 0.
    """
    return (
        "",                       # @MaKH (SP tự sinh)
        MA_CSDT,                  # @MaCSDT
        MA_SO_GTVT,               # @MaSoGTVT
        body.ten_kh,              # @TenKH
        hang_gplx,                # @HangGPLX
        body.hang_dt,             # @HangDT
        body.so_qd or None,       # @SoQD_KhaiGiang
        body.ngay_qd,             # @NgayQD_KhaiGiang
        body.ngay_kg,             # @NgayKG
        body.ngay_bg,             # @NgayBG
        None,                     # @MucTieuDT
        body.ngay_thi,            # @NgayThi
        None,                     # @NgaySH
        body.tong_so_hv,          # @TongSoHV
        0,                        # @SoHVTotNghiep
        0,                        # @SoHVDuocCapGPLX
        thoi_gian_dt,             # @ThoiGianDT
        0,                        # @SoNgayOnKT
        0,                        # @SoNgayThucHoc
        0,                        # @SoNgayNghiLe
        0,                        # @TongSoNgay
        body.ghi_chu or None,     # @GhiChu
        1,                        # @TrangThai
        nguoi,                    # @NguoiTao
        nguoi,                    # @NguoiSua
        None,                     # @NgayTao (SP getdate())
        None,                     # @NgaySua (SP getdate())
    )


_EXEC_INSERT = (
    "EXEC dbo.usp_KhoaHoc_Insert @MaKH=%s,@MaCSDT=%s,@MaSoGTVT=%s,@TenKH=%s,@HangGPLX=%s,"
    "@HangDT=%s,@SoQD_KhaiGiang=%s,@NgayQD_KhaiGiang=%s,@NgayKG=%s,@NgayBG=%s,@MucTieuDT=%s,"
    "@NgayThi=%s,@NgaySH=%s,@TongSoHV=%s,@SoHVTotNghiep=%s,@SoHVDuocCapGPLX=%s,@ThoiGianDT=%s,"
    "@SoNgayOnKT=%s,@SoNgayThucHoc=%s,@SoNgayNghiLe=%s,@TongSoNgay=%s,@GhiChu=%s,@TrangThai=%s,"
    "@NguoiTao=%s,@NguoiSua=%s,@NgayTao=%s,@NgaySua=%s"
)


@router.get("/hang-dt")
def list_hang_dt():
    """DS hạng đào tạo CẤP MỚI cho dropdown tạo khóa (KHO-01).

    `DM_HangDT` active, loại hạng nâng-hạng ghép (MaHangDT chứa '-'). Mỗi hạng kèm
    HangGPLX suy ra (`DM_HangGPLX.MaHang` where `MaHangMoi` = hạng ĐT) + tuổi tối thiểu +
    thời gian ĐT. Bỏ hạng không suy được HangGPLX (không tạo khóa được)."""
    sql = (
        "SELECT dt.MaHangDT, dt.TenHangDT, dt.TuoiHV, dt.ThoiGianDaoTao, "
        "(SELECT TOP 1 gp.MaHang FROM DM_HangGPLX gp WHERE gp.MaHangMoi = dt.MaHangDT "
        "AND gp.TrangThai = 1 ORDER BY gp.MaHang) AS HangGPLX "
        "FROM DM_HangDT dt WHERE dt.TrangThai = 1 AND dt.MaHangDT NOT LIKE %s "
        "ORDER BY dt.MaHangDT"
    )
    try:
        with sqlserver_cursor() as cur:
            cur.execute(sql, ("%-%",))
            rows = cur.fetchall()
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không truy vấn được SQL Server — kiểm kết nối.")

    return [
        {
            "ma_hang_dt": r["MaHangDT"],
            "ten": r["TenHangDT"],
            "tuoi_hv": r["TuoiHV"],
            "thoi_gian_dt": r["ThoiGianDaoTao"],
            "hang_gplx": r["HangGPLX"],
        }
        for r in rows
        if r["HangGPLX"]
    ]


@router.get("/tra-cuu")
def tra_cuu_khoa(q: str = ""):
    """QLY-01 — tìm khóa theo tên/mã, MỌI khóa (kể cả đã BC1), kèm cờ bc1.

    Khác dropdown nạp (NAP-02 ẩn khóa BC1): chế độ Tra cứu hiện mọi khóa để xem HV,
    khóa đã BC1 chỉ xem (chặn sửa, BR-012)."""
    like = f"%{q.strip()}%"
    sql = (
        "SELECT TOP 50 k.MaKH, k.TenKH, k.HangGPLX, k.HangDT, "
        "CASE WHEN EXISTS (SELECT 1 FROM BaoCaoI b WHERE b.MaKH = k.MaKH) THEN 1 ELSE 0 END AS bc1 "
        "FROM KhoaHoc k WHERE k.MaCSDT = %s AND k.TrangThai = 1 "
        "AND (k.MaKH LIKE %s OR k.TenKH LIKE %s) ORDER BY k.NgayTao DESC"
    )
    try:
        with sqlserver_cursor() as cur:
            cur.execute(sql, (MA_CSDT, like, like))
            rows = cur.fetchall()
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không truy vấn được SQL Server — kiểm kết nối.")
    return [
        {
            "ma_kh": r["MaKH"],
            "ten_kh": r["TenKH"],
            "hang_gplx": r["HangGPLX"],
            "hang_dt": r["HangDT"],
            "bc1": bool(r["bc1"]),
        }
        for r in rows
    ]


@router.post("/tao")
def tao_khoa(body: KhoaHocTao, phien: Phien = Depends(require_session)):
    """Tạo khóa học qua usp_KhoaHoc_Insert (KHO-01, GHI DB). Mã tự sinh → đọc lại trả về.

    Suy HangGPLX + ThoiGianDT từ hạng ĐT; hằng MaCSDT/MaSoGTVT/TrangThai theo BR-017.
    """
    if body.ngay_bg < body.ngay_kg:
        raise HTTPException(status_code=400, detail="Ngày bế giảng không được trước ngày khai giảng.")
    nguoi = (phien.ho_ten or phien.username or "tool")[:30]
    try:
        with sqlserver_conn(autocommit=True) as conn:
            cur = conn.cursor(as_dict=True)
            cur.execute(
                "SELECT TOP 1 dt.ThoiGianDaoTao, "
                "(SELECT TOP 1 gp.MaHang FROM DM_HangGPLX gp WHERE gp.MaHangMoi = dt.MaHangDT "
                "AND gp.TrangThai = 1 ORDER BY gp.MaHang) AS HangGPLX "
                "FROM DM_HangDT dt WHERE dt.MaHangDT = %s AND dt.TrangThai = 1",
                (body.hang_dt,),
            )
            dt = cur.fetchone()
            if not dt:
                raise HTTPException(status_code=400, detail="Hạng đào tạo không hợp lệ hoặc đã ngừng.")
            hang_gplx = dt["HangGPLX"]
            if not hang_gplx:
                raise HTTPException(status_code=400, detail="Hạng này chưa map được HangGPLX — không tạo khóa được.")

            cur.execute(_EXEC_INSERT, dung_tham_so_insert(body, hang_gplx, dt["ThoiGianDaoTao"], nguoi))
            # SP không trả MaKH → đọc lại bản vừa tạo (mới nhất khớp CSDT + HangGPLX + tên).
            cur.execute(
                "SELECT TOP 1 MaKH, TenKH, HangGPLX, HangDT FROM KhoaHoc "
                "WHERE MaCSDT = %s AND HangGPLX = %s AND TenKH = %s ORDER BY NgayTao DESC",
                (MA_CSDT, hang_gplx, body.ten_kh),
            )
            moi = cur.fetchone()
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không tạo được khóa trên SQL Server — kiểm kết nối rồi thử lại.")

    if not moi:
        raise HTTPException(status_code=500, detail="Đã gọi tạo khóa nhưng không đọc lại được mã — kiểm trong app cũ.")
    return {"ma_kh": moi["MaKH"], "ten_kh": moi["TenKH"], "hang_gplx": moi["HangGPLX"], "hang_dt": moi["HangDT"]}
