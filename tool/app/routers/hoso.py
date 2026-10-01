"""QLY-01 — Tra cứu hồ sơ đã có trong DB đích (chế độ "Tra cứu DB").

Lát 1 (đọc): lưới học viên theo khóa qua usp_NguoiLX_Select_By_MaKH. Sửa/đổi khóa/xóa
(QLY-01 sửa, QLY-02, QLY-03) thêm sau. Mọi SQL parameterized (TDD §12).
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query

from app.db import sqlserver_cursor, ConfigChuaDay

router = APIRouter(prefix="/local/ho-so", tags=["ho-so"])


@router.get("")
def ds_ho_so(makh: str = Query(..., min_length=1)):
    """Lưới học viên theo khóa (usp_NguoiLX_Select_By_MaKH). Tìm trong lưới = lọc phía
    client trên kết quả này (bỏ dấu tên / CCCD) như NAP-01/THU-02."""
    try:
        with sqlserver_cursor() as cur:
            cur.execute("EXEC dbo.usp_NguoiLX_Select_By_MaKH @MaKH=%s", (makh,))
            rows = cur.fetchall()
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không truy vấn được SQL Server — kiểm kết nối.")

    return [
        {
            "ma_dk": r["MaDK"],
            "ho_ten": r["HoVaTen"],
            "ngay_sinh": r["NgaySinh"],
            "gioi_tinh": r["GioiTinh"],
            "so_cccd": r["SoCMT"],
            "so_cmnd_cu": r["SO_CMND_CU"],
            "so_ho_so": r["SoHoSo"],
            "noi_tt": r["NoiTT"],
            "co_anh": bool((r["DuongDanAnh"] or "").strip()),
            "ma_loai_hs": r["MaLoaiHs"],
        }
        for r in rows
    ]
