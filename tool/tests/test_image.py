"""QLY-01 (task 34) — transcode ảnh .jp2 → PNG + thumbnail cho màn Tra cứu DB.

Mức 2, không cần SQL Server: kiểm hàm thuần `jp2_sang_png` / `thumb_jp2` của app.image.
"""
import io

import pytest
from PIL import Image

from app import image


def _jp2(w: int = 353, h: int = 471) -> bytes:
    b = io.BytesIO()
    Image.new("RGB", (w, h), "white").save(b, format="JPEG2000")
    return b.getvalue()


def test_jp2_sang_png_giai_ma_ok():
    png = image.jp2_sang_png(_jp2())
    assert png[:8] == b"\x89PNG\r\n\x1a\n"            # magic PNG (trình duyệt xem được)
    with Image.open(io.BytesIO(png)) as im:
        assert im.size == (353, 471)


def test_jp2_sang_png_thumbnail_giu_ty_le():
    png = image.jp2_sang_png(_jp2(353, 471), max_canh=96)
    with Image.open(io.BytesIO(png)) as im:
        assert max(im.size) == 96                     # cạnh dài = 96
        assert im.width < im.height                   # giữ chiều dọc 3:4


def test_jp2_sang_png_file_hong_raise():
    with pytest.raises(ValueError):
        image.jp2_sang_png(b"day-khong-phai-anh-jp2")


def test_thumb_jp2_cache_hit(tmp_path):
    f = tmp_path / "a.jp2"
    f.write_bytes(_jp2())
    png1 = image.thumb_jp2(str(f))
    assert max(Image.open(io.BytesIO(png1)).size) == 96
    assert image.thumb_jp2(str(f)) == png1            # cache hit (cùng mtime) trả cùng bytes
