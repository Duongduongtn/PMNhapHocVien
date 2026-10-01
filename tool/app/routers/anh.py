"""NAP-04 — endpoint xử lý ảnh: crop 3:4 + rembg nền trắng + xuất .jp2."""
from __future__ import annotations
import base64

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app import image

router = APIRouter(prefix="/local/anh", tags=["anh"])


def _parse_box(box: str) -> tuple | None:
    if not box:
        return None
    try:
        parts = [int(round(float(x))) for x in box.split(",")]
    except ValueError:
        return None
    return tuple(parts) if len(parts) == 4 else None


@router.post("/xu-ly")
async def xu_ly(
    file: UploadFile = File(...),
    box: str = Form(""),            # "left,top,w,h" px gốc; rỗng → crop giữa
    xoa_phong: bool = Form(True),
):
    data = await file.read()
    try:
        kq = image.xu_ly(data, _parse_box(box), xoa_phong)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Xử lý ảnh thất bại — thử ảnh khác.")
    return {
        "preview": "data:image/png;base64," + base64.b64encode(kq["png"]).decode(),
        "jp2_b64": base64.b64encode(kq["jp2"]).decode(),  # NAP-05 dùng để ghi file
        "w": kq["w"],
        "h": kq["h"],
    }
