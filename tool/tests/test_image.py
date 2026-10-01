"""NAP-04 — test xử lý ảnh (không rembg, xoa_phong=False): validate + crop 3:4 + .jp2.

rembg (xóa phông) cần model u2net 170MB → kiểm live, không unit test ở đây.
"""
import io

import pytest
from PIL import Image

from app import image


def _img_bytes(w: int, h: int, fmt: str = "JPEG", color=(120, 90, 60)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, format=fmt)
    return buf.getvalue()


# ---- validate --------------------------------------------------------------
def test_validate_qua_lon():
    with pytest.raises(ValueError):
        image.validate_raw(b"\xff\xd8\xff" + b"0" * (image.MAX_BYTES + 1))


def test_validate_sai_dinh_dang():
    with pytest.raises(ValueError):
        image.validate_raw(b"GIF89a....")  # không phải JPEG/PNG


def test_validate_ok():
    image.validate_raw(_img_bytes(10, 10))  # không raise


# ---- crop 3:4 + xuất .jp2 (không phông) ------------------------------------
def _ra_jp2(data, box=None):
    kq = image.xu_ly(data, box=box, xoa_phong=False)
    return kq, Image.open(io.BytesIO(kq["jp2"]))


def test_xuat_dung_kich_thuoc_rgb():
    kq, im = _ra_jp2(_img_bytes(1000, 600))  # ảnh rộng → cắt ngang về 3:4
    assert kq["w"] == 353 and kq["h"] == 471
    im.load()
    assert im.size == (353, 471)
    assert im.mode == "RGB"


def test_crop_tu_anh_vuong():
    _, im = _ra_jp2(_img_bytes(800, 800))  # vuông → ép 3:4
    assert im.size == (353, 471)


def test_crop_theo_box():
    _, im = _ra_jp2(_img_bytes(1200, 1600), box=(100, 100, 600, 800))
    assert im.size == (353, 471)  # box rồi ép 3:4 → vẫn 353×471


def test_jp2_mo_lai_duoc():
    kq, im = _ra_jp2(_img_bytes(600, 900, fmt="PNG"))
    im.load()  # mở + giải mã lại được (JPEG2000 hợp lệ)
    assert kq["jp2"][:4] != b""  # có dữ liệu
