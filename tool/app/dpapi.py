"""Mã hóa dữ liệu nhạy cảm bằng Windows DPAPI (CryptProtectData, phạm vi CurrentUser).

Dùng cho PHIÊN đăng nhập lưu đĩa (DGT-04). Khác `config_store` (Fernet + `key.bin`):
`key.bin` nằm cùng thư mục cấu hình nên copy cả thư mục sang máy/user khác là giải mã
được. DPAPI ràng dữ liệu vào đúng **máy + tài khoản Windows** — copy đi nơi khác KHÔNG
mở được. Phiên = vào thẳng sửa/xóa GPLX + xem căn cước mà không cần mật khẩu, nên cần
lớp ràng chặt hơn config (TDD §11C.4, /reviewtdd 05/10).

Ngoài Windows (chạy test/CI trên Linux/Mac) không có DPAPI → fallback Fernet bằng
`key.bin`. Fallback CHỈ để test chạy được; máy thật ở CSDT là Windows nên luôn dùng DPAPI.
"""
from __future__ import annotations

import sys


def co_dpapi() -> bool:
    return sys.platform == "win32"


# ── DPAPI qua ctypes (không thêm thư viện pip) ──
if co_dpapi():
    import ctypes
    from ctypes import wintypes

    class _DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    _CRYPTPROTECT_UI_FORBIDDEN = 0x01  # không bật hộp thoại UI (chạy nền/khay)

    def _doc_blob(blob: "_DATA_BLOB") -> bytes:
        try:
            return ctypes.string_at(blob.pbData, blob.cbData)
        finally:
            ctypes.windll.kernel32.LocalFree(blob.pbData)

    def _protect(data: bytes) -> bytes:
        buf = ctypes.create_string_buffer(bytes(data), len(data))  # giữ ref tới khi call xong
        blob_in = _DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
        blob_out = _DATA_BLOB()
        ok = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(blob_in), None, None, None, None,
            _CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(blob_out))
        if not ok:
            raise OSError("CryptProtectData thất bại")
        return _doc_blob(blob_out)

    def _unprotect(blob: bytes) -> bytes:
        buf = ctypes.create_string_buffer(bytes(blob), len(blob))
        blob_in = _DATA_BLOB(len(blob), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
        blob_out = _DATA_BLOB()
        ok = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(blob_in), None, None, None, None,
            _CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(blob_out))
        if not ok:
            raise OSError("CryptUnprotectData thất bại")
        return _doc_blob(blob_out)


def bao_ve(data: bytes) -> bytes:
    """Mã hóa `data` → blob ràng vào máy+user (Windows), hoặc Fernet (ngoài Windows)."""
    if co_dpapi():
        return _protect(data)
    from app import config_store
    return config_store._fernet().encrypt(data)


def giai_ma(blob: bytes) -> bytes:
    """Giải mã blob. Ném OSError/InvalidToken nếu không phải của máy+user này / hỏng."""
    if co_dpapi():
        return _unprotect(blob)
    from app import config_store
    return config_store._fernet().decrypt(blob)
