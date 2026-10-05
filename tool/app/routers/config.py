"""Cấu hình kết nối tool (HTG-01①): GET/PUT /local/config, POST /local/config/test.

Lưu ý: guard token operator cho /local/* được gắn ở Phase 2 (task 17) khi có đăng nhập.
"""
from __future__ import annotations

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from app import config_store

router = APIRouter(prefix="/local/config", tags=["config"])

_MASK = "********"


class ConfigIn(BaseModel):
    sqlserver_host: str = ""
    sqlserver_database: str = ""
    sqlserver_user: str = ""
    sqlserver_password: str = ""
    vps_url: str = ""
    vps_api_key: str = ""


def _resolve_secrets(data: dict) -> dict:
    """UI gửi lại giá trị che (********) cho secret không đổi → giữ secret đã lưu."""
    saved = config_store.load_config()
    out = dict(data)
    for field in config_store.SECRET_FIELDS:
        if out.get(field) in ("", _MASK):
            out[field] = saved.get(field, "")
    return out


@router.get("")
def get_config() -> dict:
    """Đọc cấu hình hiện tại (mật khẩu/API key đã che)."""
    return config_store.masked_config()


@router.put("")
def put_config(cfg: ConfigIn) -> dict:
    """Lưu cấu hình (mã hóa cục bộ). Trả bản đã che."""
    config_store.save_config(_resolve_secrets(cfg.model_dump()))
    return config_store.masked_config()


@router.post("/test")
def test_config(cfg: ConfigIn) -> dict:
    """Thử nối SQL Server + ping VPS với giá trị đang nhập (chưa cần lưu)."""
    data = _resolve_secrets(cfg.model_dump())
    return {
        "sqlserver": _test_sqlserver(data),
        "vps": _test_vps(data),
    }


_REQUIRED_CAU_HINH = (
    "sqlserver_host", "sqlserver_database", "sqlserver_user",
    "sqlserver_password", "vps_url", "vps_api_key",
)


def _thu_muc_ghi_duoc() -> bool:
    """Thử tạo thư mục cấu hình + ghi file thăm dò rồi xóa — bắt lỗi Program Files chỉ-đọc."""
    try:
        config_store.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        probe = config_store.CONFIG_DIR / ".ghi_thu"
        probe.write_bytes(b"x")
        probe.unlink(missing_ok=True)
        return True
    except Exception:  # noqa: BLE001
        return False


@router.get("/moi-truong")
def kiem_moi_truong() -> dict:
    """DGT-03 — kiểm môi trường cho wizard lần đầu (KHÔNG gác token — bước mồi).

    `thu_muc_ghi_duoc`: thư mục ghi cấu hình/nháp/ảnh có ghi được không (đặt trong
    Program Files sẽ không ghi được). `da_cau_hinh`: đã khai đủ 6 trường kết nối chưa
    (dùng để nhận 'máy sạch' → vào wizard thay vì màn đăng nhập)."""
    try:
        cfg = config_store.load_config()
    except Exception:  # noqa: BLE001 — key.bin hỏng / giải mã lỗi (TDD §11C.5 ca c)
        cfg = {}       # → coi như máy sạch → vào wizard, không kẹt màn đăng nhập
    return {
        "thu_muc_ghi_duoc": _thu_muc_ghi_duoc(),
        "duong_dan": str(config_store.CONFIG_DIR),
        "da_cau_hinh": all(cfg.get(k) for k in _REQUIRED_CAU_HINH),
    }


def _test_sqlserver(data: dict) -> dict:
    host = data.get("sqlserver_host", "")
    if not host:
        return {"ok": False, "message": "Chưa nhập Server"}
    try:
        import pymssql  # import trễ: chỉ cần khi thật sự test

        conn = pymssql.connect(
            server=host,
            user=data.get("sqlserver_user", ""),
            password=data.get("sqlserver_password", ""),
            database=data.get("sqlserver_database", ""),
            login_timeout=5,
            timeout=5,
        )
        conn.close()
        return {"ok": True, "message": "Kết nối SQL Server thành công"}
    except Exception as e:  # noqa: BLE001 — gói mọi lỗi nối thành thông báo cho UI
        # Giữ nguyên văn lỗi pymssql (str(e)) để phân biệt sai mật khẩu / không thấy máy /
        # sai tên DB (EC DGT-03) — không rút gọn còn tên class chung chung.
        chi_tiet = str(e).strip() or e.__class__.__name__
        return {"ok": False, "message": f"Lỗi SQL Server: {chi_tiet}"}


def _test_vps(data: dict) -> dict:
    url = data.get("vps_url", "")
    if not url:
        return {"ok": False, "message": "Chưa nhập URL VPS"}
    try:
        # Bất kỳ phản hồi HTTP nào = VPS tới được (kể cả 401/404).
        httpx.get(url, timeout=5.0)
        return {"ok": True, "message": "VPS tới được"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "message": f"Không tới được VPS: {e.__class__.__name__}"}
