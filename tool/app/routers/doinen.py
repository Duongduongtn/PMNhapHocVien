"""QLY-07 (task 39) — endpoint đổi nền trắng cả khóa + theo dõi tiến độ.

- POST /local/khoa/{ma_kh}/doi-nen : bắt đầu job nền (applock theo khóa → 409 nếu đang chạy).
- GET  /local/khoa/{ma_kh}/doi-nen : tiến độ (N/tổng, bỏ qua, lỗi, danh sách lỗi).

Session đã được gác ở tầng app (main.include_router(..., dependencies=[require_session])).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app import doinen
from app.session import Phien, require_session

router = APIRouter(prefix="/local/khoa", tags=["doi-nen"])


class DoiNenIn(BaseModel):
    pham_vi: str = "chua_trang"   # 'chua_trang' (mặc định) | 'tat_ca'
    sao_luu: bool = True          # sao lưu _BACKUP trước khi ghi đè (mặc định bật)


@router.post("/{ma_kh}/doi-nen")
def bat_dau_doi_nen(ma_kh: str, body: DoiNenIn, phien: Phien = Depends(require_session)):
    """Khởi động đổi nền cả khóa (chạy nền). Khóa đang chạy → 409."""
    if body.pham_vi not in ("chua_trang", "tat_ca"):
        raise HTTPException(status_code=422, detail="Phạm vi không hợp lệ.")
    nguoi = (phien.ho_ten or phien.username or "tool")[:60]
    try:
        doinen.bat_dau(ma_kh, body.pham_vi, body.sao_luu, nguoi)
    except RuntimeError:
        raise HTTPException(status_code=409, detail="Khóa này đang đổi nền — chờ xong rồi chạy lại.")
    return {"ok": True, "ma_kh": ma_kh}


@router.get("/{ma_kh}/doi-nen")
def tien_do_doi_nen(ma_kh: str, phien: Phien = Depends(require_session)):
    """Tiến độ job đổi nền của khóa. Chưa có job → 404."""
    td = doinen.tien_do(ma_kh)
    if td is None:
        raise HTTPException(status_code=404, detail="Chưa có tiến trình đổi nền cho khóa này.")
    return {
        "tong": td.tong,
        "xong": td.xong,
        "bo_qua": td.bo_qua,
        "loi": td.loi,
        "ds_loi": td.ds_loi,
        "dang_chay": td.dang_chay,
        "xong_het": td.xong_het,
        "thong_bao": td.thong_bao,
    }
