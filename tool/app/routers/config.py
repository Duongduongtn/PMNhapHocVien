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
        return {"ok": False, "message": f"Lỗi SQL Server: {e.__class__.__name__}"}


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
