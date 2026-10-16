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


@contextmanager
def sqlserver_conn(autocommit: bool = True):
    """Mở CONNECTION (không phải cursor), tự đóng. Dùng cho nạp HV: applock phải giữ
    trong một connection từ lúc đọc MAX(SoHoSo) tới khi HoSo_Insert xong (TDD §10.1),
    và mỗi usp_* tự BEGIN/COMMIT nên connection để autocommit (không bọc transaction ngoài)."""
    import pymssql  # lazy import

    conn = pymssql.connect(login_timeout=5, charset="UTF-8", autocommit=autocommit, **_params())
    try:
        yield conn
    finally:
        conn.close()


# --- Kết nối CSDL ĐÍCH cho phân hệ Đồng bộ CDB (SYNC, TDD §11B.1) ---------
# Dùng CHUNG host/user/password với cấu hình Nạp, chỉ thay `database`. Tên DB
# đích do caller truyền (từ target đang chọn trong cấu hình Sync).


def _params_dich(database: str) -> dict:
    cfg = load_config()
    need = ("sqlserver_host", "sqlserver_user", "sqlserver_password")
    if any(not cfg.get(k) for k in need):
        raise ConfigChuaDay("Chưa cấu hình kết nối SQL Server — vào màn Cấu hình khai báo trước.")
    if not database or not database.strip():
        raise ConfigChuaDay("Chưa chọn CSDL đích — vào Quản lý CSDL đích để thêm/chọn.")
    return {
        "server": cfg["sqlserver_host"],
        "database": database.strip(),
        "user": cfg["sqlserver_user"],
        "password": cfg["sqlserver_password"],
    }


@contextmanager
def sqlserver_conn_dich(database: str, autocommit: bool = True, timeout: int = 0):
    """Mở CONNECTION tới CSDL đích (database truyền vào). Mỗi usp_* ở CDB tự
    BEGIN/COMMIT nên để autocommit; đồng bộ sinh MaDK + INSERT giữ trong một
    connection giống luồng nạp."""
    import pymssql  # lazy import

    extra = {"timeout": int(timeout)} if timeout and timeout > 0 else {}   # timeout truy vấn (giây); 0 = không giới hạn
    conn = pymssql.connect(login_timeout=5, charset="UTF-8", autocommit=autocommit, **extra, **_params_dich(database))
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def sqlserver_cursor_dich(database: str, as_dict: bool = True):
    """Mở cursor tới CSDL đích, tự đóng. Dùng cho truy vấn đọc (năm/khóa/enrich)."""
    import pymssql  # lazy import

    conn = pymssql.connect(login_timeout=5, charset="UTF-8", **_params_dich(database))
    try:
        yield conn.cursor(as_dict=as_dict)
    finally:
        conn.close()
