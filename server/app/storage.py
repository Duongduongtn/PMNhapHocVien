"""Lưu + validate ảnh thô CCCD/chân dung trên VPS (TDD §7.4).

Kiểm trước khi lưu, theo đúng thứ tự rẻ→đắt:
  1. Kích thước byte ≤ max_anh_bytes (8 MB) — chặn sớm, chưa đọc nội dung.
  2. Magic-byte đúng JPEG/PNG — KHÔNG tin đuôi tệp hay Content-Type client gửi.
  3. Số điểm ảnh ≤ max_anh_pixels — chặn ảnh "bung nén" (decompression bomb)
     làm treo/sập tool khi rembg/Pillow xử lý sau này.

Không hợp lệ → ném AnhKhongHopLe (router đổi thành 4xx + lý do rõ, PRD ⑦).
"""
from __future__ import annotations

import io
from pathlib import Path
from uuid import UUID

from PIL import Image, UnidentifiedImageError

from app.config import get_settings

# Magic-byte đầu tệp → đuôi chuẩn hóa. Chỉ nhận JPEG/PNG (ảnh CCCD/chân dung).
_MAGIC = (
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
)


class AnhKhongHopLe(ValueError):
    """Ảnh không qua được một bước kiểm — thông điệp đã bằng tiếng Việt cho user."""


def _dinh_dang(data: bytes) -> str | None:
    """Trả 'jpg'/'png' theo magic-byte, hoặc None nếu không khớp định dạng cho phép."""
    for sig, ext in _MAGIC:
        if data.startswith(sig):
            return ext
    return None


def validate_anh(data: bytes) -> str:
    """Kiểm ảnh thô, trả đuôi chuẩn hóa ('jpg'/'png'). Lỗi → ném AnhKhongHopLe."""
    s = get_settings()
    if len(data) == 0:
        raise AnhKhongHopLe("Tệp ảnh rỗng")
    if len(data) > s.max_anh_bytes:
        gioi_han_mb = s.max_anh_bytes // (1024 * 1024)
        raise AnhKhongHopLe(f"Ảnh vượt {gioi_han_mb} MB")

    ext = _dinh_dang(data)
    if ext is None:
        raise AnhKhongHopLe("Chỉ nhận ảnh JPEG hoặc PNG")

    # Đọc kích thước từ header (không decode toàn bộ pixel) để chặn bung nén.
    try:
        with Image.open(io.BytesIO(data)) as im:
            rong, cao = im.size
    except (UnidentifiedImageError, OSError) as exc:
        raise AnhKhongHopLe("Tệp ảnh hỏng hoặc không đọc được") from exc

    if rong * cao > s.max_anh_pixels:
        gioi_han_mp = s.max_anh_pixels // 1_000_000
        raise AnhKhongHopLe(f"Ảnh quá nhiều điểm ảnh (vượt ~{gioi_han_mp} MP)")
    return ext


def luu_anh(uuid: UUID, data: bytes, ext: str) -> str:
    """Ghi ảnh đã validate vào anh_tho_dir/<uuid>.<ext>, trả đường dẫn tuyệt đối (str).

    Mỗi hồ sơ 1 ảnh — ghi đè nếu upload lại cùng uuid (idempotent theo uuid)."""
    thu_muc = Path(get_settings().anh_tho_dir)
    thu_muc.mkdir(parents=True, exist_ok=True)
    duong_dan = thu_muc / f"{uuid}.{ext}"
    duong_dan.write_bytes(data)
    return str(duong_dan)
