"""Ghi đè ảnh .jp2 TẠI CHỖ — dùng chung cho thay ảnh CDB (TCB-02) và đổi nền cả khóa (QLY-07).

Ảnh là file VẬT LÝ dùng chung 2 DB (Nạp + đích; sync sao chép `DuongDanAnh` nguyên văn) nên ghi
đè đúng đường dẫn đang có — không tạo file ở thư mục khác, không đổi đường dẫn.
"""
from __future__ import annotations

import shutil
from pathlib import Path


def ghi_de_tai_cho(duong_dan: str, jp2_bytes: bytes, sao_luu: bool = True) -> str:
    """Ghi đè ĐÚNG file .jp2 cũ (giữ nguyên tên + đường dẫn).

    `sao_luu`: trước khi đè, sao lưu `<stem>_BACKUP.jp2` CÙNG thư mục — CHỈ nếu chưa có (chạy lần 2
    không đè mất bản gốc). Ghi atomic (temp → replace) để crash giữa chừng không để lại .jp2 cụt.

    File không còn → FileNotFoundError. File bị phần mềm CDB khóa → PermissionError (caller → 409).
    """
    p = Path(duong_dan)
    if not p.exists():
        raise FileNotFoundError(duong_dan)
    if sao_luu:
        backup = p.with_name(f"{p.stem}_BACKUP{p.suffix}")
        if not backup.exists():
            shutil.copy2(p, backup)  # giữ bản gốc đầu tiên (copy2 giữ cả metadata)
    tmp = p.with_name(f"{p.name}.tmp")
    tmp.write_bytes(jp2_bytes)
    try:
        tmp.replace(p)  # nguyên tử; app CDB còn khóa file → PermissionError
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return str(p)
