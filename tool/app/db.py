"""Kết nối SQL Server GPLX_CSDT từ cấu hình đã lưu (mã hóa cục bộ).

Dùng chung cho mọi endpoint /local/* cần query DB đích. CHỈ đọc/ghi qua SP theo TDD —
file này chỉ lo mở kết nối, không chứa SQL nghiệp vụ.
"""
from __future__ import annotations
from contextlib import contextmanager

from app.config_store import load_config

_REQUIRED = ("sqlserver_host", "sqlserver_database", "sqlserver_user", "sqlserver_password")


class ConfigChuaDay(RuntimeError):
    """Chưa khai báo đủ cấu hình kết nối SQL Server (màn Cấu hình)."""


def _params() -> dict:
    cfg = load_config()
    if any(not cfg.get(k) for k in _REQUIRED):
        raise ConfigChuaDay("Chưa cấu hình kết nối SQL Server — vào màn Cấu hình khai báo trước.")
    return {
        "server": cfg["sqlserver_host"],
        "database": cfg["sqlserver_database"],
        "user": cfg["sqlserver_user"],
        "password": cfg["sqlserver_password"],
    }


@contextmanager
def sqlserver_cursor(as_dict: bool = True):
    """Mở kết nối + cursor, tự đóng. pymssql import trễ để test không cần driver."""
    import pymssql  # lazy import

    conn = pymssql.connect(login_timeout=5, charset="UTF-8", **_params())
    try:
        yield conn.cursor(as_dict=as_dict)
    finally:
        conn.close()
