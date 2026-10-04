"""TCB-02 (task 64) — thay ảnh HV ở CDB: ghi đè đúng file + sao lưu _BACKUP cùng thư mục.

Chỉ test hàm filesystem thuần `thay_anh_ghi_de` (không cần SQL Server/rembg). Phần UPDATE cột ảnh
đích + các mã lỗi HTTP (404/409) kiểm tay/live ở Checkpoint 14.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.routers.sync_tracuu import thay_anh_ghi_de


def test_ghi_de_giu_nguyen_ten_va_duong_dan(tmp_path):
    # Tên file gốc trỏ path nguồn (dùng chung 2 DB) — phải GIỮ NGUYÊN sau khi thay.
    f = tmp_path / "70004-2026K1.jp2"
    f.write_bytes(b"ANH-CU")
    kq = thay_anh_ghi_de(str(f), b"ANH-MOI")
    assert kq == str(f)                 # đường dẫn không đổi
    assert f.read_bytes() == b"ANH-MOI"  # đã ghi đè đúng file


def test_backup_canh_file_chi_neu_chua_co(tmp_path):
    f = tmp_path / "70004-2026K1.jp2"
    f.write_bytes(b"ANH-GOC")
    thay_anh_ghi_de(str(f), b"ANH-MOI-1")
    backup = tmp_path / "70004-2026K1_BACKUP.jp2"
    assert backup.exists()                      # backup nằm CÙNG thư mục
    assert backup.read_bytes() == b"ANH-GOC"    # giữ bản gốc đầu tiên
    # Thay lần 2 → KHÔNG đè backup (vẫn là bản gốc đầu tiên, không phải ANH-MOI-1)
    thay_anh_ghi_de(str(f), b"ANH-MOI-2")
    assert backup.read_bytes() == b"ANH-GOC"
    assert f.read_bytes() == b"ANH-MOI-2"


def test_khong_tao_file_anh_thu_2(tmp_path):
    # ❌ PRD: không tạo file ảnh thứ 2 — sau thay chỉ có file gốc + 1 backup, không thêm .jp2 khác.
    f = tmp_path / "70004-2026K1.jp2"
    f.write_bytes(b"ANH-GOC")
    thay_anh_ghi_de(str(f), b"ANH-MOI")
    jp2s = sorted(p.name for p in tmp_path.glob("*.jp2"))
    assert jp2s == ["70004-2026K1.jp2", "70004-2026K1_BACKUP.jp2"]
    # không để lại file .tmp cụt
    assert list(tmp_path.glob("*.tmp")) == []


def test_file_khong_con_raise(tmp_path):
    with pytest.raises(FileNotFoundError):
        thay_anh_ghi_de(str(tmp_path / "khong-ton-tai.jp2"), b"X")
