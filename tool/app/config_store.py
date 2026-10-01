"""Lưu cấu hình kết nối của tool (SQL Server + VPS) MÃ HÓA cục bộ.

Quyết định (BUILD-PLAN task 4, phương án A):
- Khóa mã hóa Fernet tự sinh lần đầu, cất ở `tool/config/key.bin` (không commit).
- Cấu hình mã hóa ở `tool/config/config.enc`.
- Mất key.bin thì phải nhập lại cấu hình (chấp nhận — tool chạy 1 máy).

Mật khẩu SQL Server + API key VPS KHÔNG bao giờ ghi ra dạng thường và KHÔNG log.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet

# tool/config/ nằm cạnh gói app/ (tool/app/config_store.py -> tool/config/)
CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
KEY_FILE = CONFIG_DIR / "key.bin"
CONFIG_FILE = CONFIG_DIR / "config.enc"

# Trường bí mật — che khi trả ra UI.
SECRET_FIELDS = {"sqlserver_password", "vps_api_key"}
_MASK = "********"


def _fernet() -> Fernet:
    """Lấy Fernet; tự sinh + ghi key.bin nếu chưa có."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not KEY_FILE.exists():
        KEY_FILE.write_bytes(Fernet.generate_key())
    return Fernet(KEY_FILE.read_bytes())


def load_config() -> dict[str, Any]:
    """Đọc + giải mã cấu hình. Chưa có file → trả dict rỗng."""
    if not CONFIG_FILE.exists():
        return {}
    raw = _fernet().decrypt(CONFIG_FILE.read_bytes())
    return json.loads(raw.decode("utf-8"))


def save_config(data: dict[str, Any]) -> None:
    """Mã hóa + ghi cấu hình xuống đĩa."""
    _fernet()  # bảo đảm CONFIG_DIR + key tồn tại
    token = _fernet().encrypt(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    CONFIG_FILE.write_bytes(token)


def masked_config() -> dict[str, Any]:
    """Cấu hình để trả ra UI — che mật khẩu/API key, chỉ báo đã có hay chưa."""
    data = load_config()
    out: dict[str, Any] = {}
    for k, v in data.items():
        if k in SECRET_FIELDS:
            out[k] = _MASK if v else ""
        else:
            out[k] = v
    return out
