"""Gốc đường dẫn dữ liệu của tool — tách bản chạy-dev và bản đóng gói .exe (DGT-01, TDD §11C.1).

- `BUNDLE_DIR`: dữ liệu CHỈ ĐỌC gói kèm (webui/dist, dvhc_map.sqlite). Bản đóng gói
  PyInstaller nằm ở `sys._MEIPASS`; chạy dev là gốc repo `tool/`.
- `DATA_DIR`: dữ liệu GHI ĐƯỢC (config/key.bin, session.bin, staging.sqlite, ảnh tạm).
  Bản đóng gói ghi vào `%APPDATA%\\pmcsdtlx-tool` (Program Files không ghi được);
  chạy dev giữ nguyên gốc repo `tool/` để KHÔNG đổi hành vi đang chạy.

Chuyển bản chạy-dev → .exe KHÔNG di cư dữ liệu tự động (config/nháp cũ ở chỗ cũ);
máy cài exe coi như thiết lập lại — vào wizard, không phải bug (TDD §11C.1).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# True khi chạy trong bản đóng gói PyInstaller.
FROZEN = bool(getattr(sys, "frozen", False))

# Gốc repo tool/ khi chạy dev (…/tool/app/paths.py → …/tool).
_REPO_ROOT = Path(__file__).resolve().parent.parent

if FROZEN:
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", _REPO_ROOT))
    _appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or str(Path.home())
    DATA_DIR = Path(_appdata) / "pmcsdtlx-tool"
    # rembg tìm model ở U2NET_HOME (mặc định ~/.u2net). Gói kèm u2net.onnx (xóa phông ảnh,
    # DGT-01) để máy sạch chạy offline, không phải tải 167MB lần đầu. Chỉ set khi máy chưa đặt.
    os.environ.setdefault("U2NET_HOME", str(BUNDLE_DIR / "models"))
else:
    BUNDLE_DIR = _REPO_ROOT
    DATA_DIR = _REPO_ROOT

# Thư mục ghi-được phải tồn tại (bản đóng gói tạo %APPDATA%\pmcsdtlx-tool lần đầu).
DATA_DIR.mkdir(parents=True, exist_ok=True)


def output_dir() -> Path:
    """Thư mục `output` của phần mềm — nơi lưu file xuất ra (vd Excel kết quả học tập, KQD-09).

    Bản đóng gói: cạnh `pmcsdtlx-tool.exe` (dễ thấy, người dùng mở thẳng từ thư mục cài). Nếu thư mục cài
    không ghi được (vd Program Files) thì lùi về `%APPDATA%\\pmcsdtlx-tool\\output`. Chạy dev: `tool/output`."""
    ung_vien = [Path(sys.executable).resolve().parent / "output"] if FROZEN else [_REPO_ROOT / "output"]
    ung_vien.append(DATA_DIR / "output")
    for d in ung_vien:
        try:
            d.mkdir(parents=True, exist_ok=True)
            probe = d / ".ghi_thu"
            probe.write_bytes(b"")
            probe.unlink()
            return d
        except OSError:
            continue
    raise OSError("Không tạo/ghi được thư mục output của phần mềm.")

