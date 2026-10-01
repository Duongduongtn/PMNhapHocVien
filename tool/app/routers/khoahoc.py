"""NAP-02 — Liệt kê khóa học chưa lập Báo cáo I (BC1) theo loại mô tô / ô tô.

Done khi (PRD NAP-02):
- Mô tô → hạng bắt đầu 'A'; Ô tô → 'B/C/D/E/F'.
- Chỉ khóa TrangThai=1 và chưa có dòng trong BaoCaoI.
- Suy MaLoaiHs (A*→1, còn lại→2), kèm HangGPLX/HangDT/MaSoGTVT theo khóa.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query

from app.db import sqlserver_cursor, ConfigChuaDay

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
