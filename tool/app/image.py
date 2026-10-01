"""NAP-04 — xử lý ảnh chân dung: validate + crop 3:4 + rembg nền trắng + xuất .jp2 353×471.

Chỉ XỬ LÝ ảnh (trả .jp2 bytes + preview). Ghi file ra IMG_PATH + lưu DuongDanAnh/ChatLuongAnh
thuộc NAP-05 (cần MaDK do SP trả). rembg import trễ để test phần không-phông không cần model.
"""
from __future__ import annotations
import io
from functools import lru_cache

from PIL import Image

MAX_BYTES = 8 * 1024 * 1024            # ≤ 8 MB (TDD §7.4)
Image.MAX_IMAGE_PIXELS = 40_000_000    # chặn decompression bomb (§7.4)
OUT_W, OUT_H = 353, 471                 # 3:4, chuẩn app cũ (§9.2)
_JP2_RATE = 10                          # tỷ lệ nén JPEG2000 → ~48 KB

# magic-byte, không tin đuôi/Content-Type (§7.4)
_MAGIC = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n")


def validate_raw(data: bytes) -> None:
    if len(data) > MAX_BYTES:
        raise ValueError("Ảnh vượt 8 MB.")
    if not any(data.startswith(m) for m in _MAGIC):
        raise ValueError("Chỉ nhận ảnh JPEG hoặc PNG.")


@lru_cache(maxsize=1)
def _session():
    from rembg import new_session  # lazy
    return new_session("u2net")


def warmup() -> None:
    """Nạp sẵn model rembg (u2net ~170MB) — gọi lúc khởi động tool (§9.2)."""
    _session()


def _crop_3_4(img: Image.Image, box: tuple | None) -> Image.Image:
    """Crop theo box (left, top, w, h) px gốc nếu có, rồi ép đúng tỷ lệ 3:4 (giữ giữa)."""
    if box:
        l, t, w, h = box
        l = max(0, l); t = max(0, t)
        img = img.crop((l, t, min(l + w, img.width), min(t + h, img.height)))
    w, h = img.size
    if w * 4 > h * 3:                       # quá rộng → cắt ngang
        nw = round(h * 3 / 4)
        off = (w - nw) // 2
        img = img.crop((off, 0, off + nw, h))
    elif w * 4 < h * 3:                     # quá cao → cắt dọc
        nh = round(w * 4 / 3)
        off = (h - nh) // 2
        img = img.crop((0, off, w, off + nh))
    return img


def _nen_trang(img: Image.Image) -> Image.Image:
    """rembg xóa phông → ghép nền TRẮNG, trả RGB."""
    from rembg import remove  # lazy
    cut = remove(img, session=_session())            # RGBA, nền trong suốt
    bg = Image.new("RGBA", cut.size, (255, 255, 255, 255))
    bg.alpha_composite(cut.convert("RGBA"))
    return bg.convert("RGB")


def xu_ly(data: bytes, box: tuple | None = None, xoa_phong: bool = True) -> dict:
    """Validate → crop 3:4 → (rembg nền trắng) → resize 353×471 → .jp2 + preview PNG."""
    validate_raw(data)
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img = _crop_3_4(img, box)
    if xoa_phong:
        img = _nen_trang(img)
    img = img.resize((OUT_W, OUT_H), Image.LANCZOS)

    jp2 = io.BytesIO()
    img.save(jp2, format="JPEG2000", quality_mode="rates", quality_layers=[_JP2_RATE])
    png = io.BytesIO()
    img.save(png, format="PNG")
    return {"jp2": jp2.getvalue(), "png": png.getvalue(), "w": OUT_W, "h": OUT_H}
