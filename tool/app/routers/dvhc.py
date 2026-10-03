"""NAP-03 — endpoint map địa chỉ + danh sách Tỉnh/Xã mới cho chọn tay."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app import dvhc
from app.db import ConfigChuaDay

router = APIRouter(prefix="/local/dvhc", tags=["dvhc"])


class DiaChiCu(BaseModel):
    tinh: str
    huyen: str = ""
    xa: str


def _guard(fn):
    try:
        return fn()
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="Không truy vấn được SQL Server — kiểm kết nối.")


@router.get("/tinh")
def list_tinh():
    """34 tỉnh mới (chọn tay)."""
    return _guard(dvhc.ds_tinh)


@router.get("/xa")
def list_xa(tinh: str = Query(..., min_length=1, max_length=10)):
    """Xã/phường mới theo mã tỉnh (MaDVQL)."""
    return _guard(lambda: dvhc.ds_xa(tinh))


@router.get("/so-gtvt")
def list_so_gtvt():
    """Danh sách Sở GTVT cho combobox 'Nơi cấp' (mã=MaDVQL, tên=TenDV) — BUG-10."""
    return _guard(dvhc.ds_so_gtvt)


@router.post("/map")
def map_dia_chi(dc: DiaChiCu):
    """Tra địa chỉ cũ → xã mới. Không khớp hoặc xã chia → UI cho chọn tay (TDD §8)."""
    kq = dvhc.tra_map(dc.tinh, dc.huyen, dc.xa)
    if kq is None:
        return {"matched": False, "divided": False}
    return kq
