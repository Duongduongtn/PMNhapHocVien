"""Lưu cấu hình kết nối của tool (SQL Server + VPS) MÃ HÓA cục bộ.

Quyết định (BUILD-PLAN task 4, phương án A):
- Khóa mã hóa Fernet tự sinh lần đầu, cất ở `tool/config/key.bin` (không commit).
- Cấu hình mã hóa ở `tool/config/config.enc`.
- Mất key.bin thì phải nhập lại cấu hình (chấp nhận — tool chạy 1 máy).

Mật khẩu SQL Server + API key VPS KHÔNG bao giờ ghi ra dạng thường và KHÔNG log.
"""
from __future__ import annotations

import json
import os
import threading
from typing import Any

from cryptography.fernet import Fernet

from app import paths

# config/ nằm trong thư mục GHI ĐƯỢC: dev là tool/config, bản .exe là %APPDATA%\pmcsdtlx-tool\config (DGT-01).
CONFIG_DIR = paths.DATA_DIR / "config"
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


# KQD-04 #77 (TDD §11D.13): ghi cấu hình có KHÓA + ghi file tạm rồi thay (`os.replace`) để hai thao tác lưu
# trùng giờ (vd lưu mẫu giải trình lúc tích CŨ/MỚI) không làm mất thay đổi của nhau hay để lại file cụt.
_LOCK = threading.RLock()


def save_config(data: dict[str, Any]) -> None:
    """Mã hóa + ghi cấu hình xuống đĩa (nguyên tử: file tạm → os.replace)."""
    with _LOCK:
        _fernet()  # bảo đảm CONFIG_DIR + key tồn tại
        token = _fernet().encrypt(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        tam = CONFIG_FILE.with_name(CONFIG_FILE.name + ".tmp")
        tam.write_bytes(token)
        os.replace(tam, CONFIG_FILE)


def sua_config(ham) -> Any:
    """Đọc → `ham(data)` sửa tại chỗ → ghi, TRONG một khóa (tránh mất cập nhật khi hai luồng cùng sửa)."""
    with _LOCK:
        data = load_config()
        kq = ham(data)
        save_config(data)
        return kq


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
    def _sua(data: dict) -> None:
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
    sua_config(_sua)   # đọc-sửa-ghi TRONG khóa (KQD-04 #77)
    return get_sync_config()


# --- Cờ chương trình đào tạo CŨ/MỚI theo từng khóa (KQD-02) --------------
# Map MaKH → 'cu' (TT12/2025) | 'moi' (TT108/2026), lưu PHÍA TOOL (không đụng schema
# CDB) — quyết định tích theo TỪNG KHÓA, không nhảy theo ngày (TDD-decisions §17).
# Mặc định 'cu' khi khóa chưa tích.
def get_kqd_chuong_trinh(ma_kh: str) -> str:
    data = load_config()
    m = data.get("kqd_chuong_trinh") or {}
    v = m.get((ma_kh or "").strip())
    return "moi" if v == "moi" else "cu"


def set_kqd_chuong_trinh(ma_kh: str, ct: str) -> str:
    def _sua(data: dict) -> None:
        m = dict(data.get("kqd_chuong_trinh") or {})
        m[(ma_kh or "").strip()] = "moi" if ct == "moi" else "cu"
        data["kqd_chuong_trinh"] = m
    sua_config(_sua)
    return get_kqd_chuong_trinh(ma_kh)


# --- Mẫu giải trình (KQD-04 #77) — lưu THEO CƠ SỞ ĐÍCH (target_key), phía tool ---------------
MAU_TOI_DA = 20
MAU_DO_DAI_TOI_DA = 1000


class MauDaDoi(Exception):
    """`phien_ban` client gửi lệch bản đang lưu — người khác vừa lưu mẫu."""


def chuan_hoa_mau(mau: list[str]) -> list[str]:
    """Bỏ mẫu rỗng/trùng (giữ thứ tự), cắt khoảng trắng. Quá 20 mẫu hoặc 1 mẫu > 1000 ký tự → ValueError
    (từ chối rõ ràng, KHÔNG cắt âm thầm)."""
    out: list[str] = []
    for m in mau or []:
        t = (m or "").strip()
        if not t:
            continue
        if len(t) > MAU_DO_DAI_TOI_DA:
            raise ValueError(f"Mẫu giải trình tối đa {MAU_DO_DAI_TOI_DA} ký tự.")
        if t not in out:
            out.append(t)
    if len(out) > MAU_TOI_DA:
        raise ValueError(f"Tối đa {MAU_TOI_DA} mẫu giải trình — xóa bớt rồi lưu lại.")
    return out


def get_mau_giai_trinh(target_key: str) -> dict[str, Any]:
    d = (load_config().get("mau_giai_trinh") or {}).get((target_key or "").strip()) or {}
    return {"mau": list(d.get("mau") or []), "phien_ban": int(d.get("phien_ban") or 0)}


def set_mau_giai_trinh(target_key: str, mau: list[str], phien_ban: int | None) -> dict[str, Any]:
    ds = chuan_hoa_mau(mau)
    k = (target_key or "").strip()

    def _sua(data: dict) -> None:
        tat_ca = dict(data.get("mau_giai_trinh") or {})
        cu = tat_ca.get(k) or {}
        pb_cu = int(cu.get("phien_ban") or 0)
        if phien_ban is not None and int(phien_ban) != pb_cu:
            raise MauDaDoi()
        tat_ca[k] = {"mau": ds, "phien_ban": pb_cu + 1}
        data["mau_giai_trinh"] = tat_ca
    sua_config(_sua)
    return get_mau_giai_trinh(k)


def get_sync_target(key: str | None = None) -> dict[str, Any] | None:
    """Trả target theo key, hoặc target đang chọn nếu không truyền key."""
    cfg = get_sync_config()
    k = (key or cfg["selected"]).strip()
    for t in cfg["targets"]:
        if t["key"] == k:
            return t
    return None
