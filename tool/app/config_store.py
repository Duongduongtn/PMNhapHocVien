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


# --- Cấu hình phân hệ Đồng bộ CDB (SYNC) ---------------------------------
# Lưu CHUNG trong config.enc nhưng tách khối riêng, KHÔNG trộn khóa cấu hình
# Nạp. DB đích dùng chung host/user/pass với Nạp (chỉ khác tên database) nên
# target chỉ giữ tên hiển thị + tên database — không có secret riêng.
SYNC_TT_XULY_MAC_DINH = "03"  # Đã nhận ảnh chân dung — sẵn sàng Kết xuất DKKH


def get_sync_config() -> dict[str, Any]:
    """Đọc cấu hình Sync: danh sách DB đích, DB đang chọn, tùy chọn đồng bộ.

    Trả cấu trúc ổn định kể cả khi chưa khai báo lần nào (list rỗng)."""
    data = load_config()
    targets = data.get("sync_targets") or []
    selected = (data.get("sync_selected") or "").strip()
    opts = data.get("sync_options") or {}
    # Chốt selected về target còn tồn tại (phòng khi key cũ đã xóa)
    keys = {t.get("key") for t in targets}
    if selected not in keys:
        selected = targets[0]["key"] if targets else ""
    return {
        "targets": targets,
        "selected": selected,
        "options": {
            "tt_xuly_force": (opts.get("tt_xuly_force") or SYNC_TT_XULY_MAC_DINH),
            "update_tong_so_hv": bool(opts.get("update_tong_so_hv", True)),
        },
    }


def save_sync_config(
    targets: list[dict[str, Any]],
    selected: str,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Ghi cấu hình Sync vào config.enc (giữ nguyên các khóa cấu hình Nạp).

    targets: list dict {key, name, database}. Trả về cấu hình Sync đã lưu."""
    data = load_config()
    data["sync_targets"] = [
        {
            "key": str(t["key"]).strip(),
            "name": str(t.get("name", t["key"])).strip(),
            "database": str(t.get("database", "")).strip(),
        }
        for t in targets
    ]
    keys = {t["key"] for t in data["sync_targets"]}
    data["sync_selected"] = selected if selected in keys else (
        data["sync_targets"][0]["key"] if data["sync_targets"] else ""
    )
    opts = options or {}
    data["sync_options"] = {
        "tt_xuly_force": (opts.get("tt_xuly_force") or SYNC_TT_XULY_MAC_DINH),
        "update_tong_so_hv": bool(opts.get("update_tong_so_hv", True)),
    }
    save_config(data)
    return get_sync_config()


def get_sync_target(key: str | None = None) -> dict[str, Any] | None:
    """Trả target theo key, hoặc target đang chọn nếu không truyền key."""
    cfg = get_sync_config()
    k = (key or cfg["selected"]).strip()
    for t in cfg["targets"]:
        if t["key"] == k:
            return t
    return None
