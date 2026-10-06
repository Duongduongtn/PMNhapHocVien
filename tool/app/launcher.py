"""DGT-02 — khởi chạy tool như một phần mềm thường (TDD §11C.2).

Thuần vòng đời tiến trình, KHÔNG chạm nghiệp vụ Nạp/Sync/TCB:
- dò cổng trống (độc lập với chống-2-bản);
- chống chạy 2 bản bằng lock-file (ghi cổng bản đang chạy để mở lại đúng URL);
- khay hệ thống (pystray) thay cửa sổ console đen;
- tự chạy khi bật máy (registry Run, mặc định TẮT).

Hàm thuần (dò cổng, đọc/ghi lock, bật/tắt tự-chạy) tách khỏi phần side-effect
(tray, trình duyệt) để unit test được mà không cần màn hình.
"""
from __future__ import annotations

import json
import os
import socket
import sys
from pathlib import Path

from app import paths

# Lock-file nằm trong thư mục ghi được (dev: tool/; .exe: %APPDATA%\pmcsdtlx-tool).
LOCK_FILE: Path = paths.DATA_DIR / "pmcsdtlx-tool.lock"

# Tên giá trị trong registry Run (tự chạy khi bật máy).
_RUN_APP_NAME = "PMCSDTLX-Tool"
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


# ── Dò cổng ────────────────────────────────────────────────────────────────
def cong_trong(port: int) -> bool:
    """Cổng 127.0.0.1:`port` có bind được (còn trống) không."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def chon_cong(uu_tien: int, so_cong_thu: int = 20) -> int:
    """Trả cổng trống: ưu tiên `uu_tien`, bận thì dò lần lượt tới `so_cong_thu` cổng kế.
    Hết dải vẫn bận → nhờ OS cấp cổng trống bất kỳ."""
    for p in range(uu_tien, uu_tien + so_cong_thu):
        if cong_trong(p):
            return p
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# ── Lock-file chống chạy 2 bản ──────────────────────────────────────────────
def ghi_lock(port: int) -> None:
    """Đánh dấu bản này đang chạy + cổng của nó (để bản mở sau biết mở trình duyệt vào đâu)."""
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOCK_FILE.write_text(json.dumps({"port": port, "pid": os.getpid()}), encoding="utf-8")


def xoa_lock() -> None:
    """Xóa lock khi thoát gọn (best-effort)."""
    try:
        LOCK_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def _doc_cong_lock() -> int | None:
    """Đọc cổng ghi trong lock-file; không có / hỏng → None."""
    try:
        return int(json.loads(LOCK_FILE.read_text(encoding="utf-8"))["port"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _health_song(port: int) -> bool:
    """Cổng này có đúng là tool mình đang sống không (phân biệt lock cũ sau crash)."""
    import httpx

    try:
        r = httpx.get(f"http://127.0.0.1:{port}/health", timeout=1.5)
        return r.status_code == 200 and r.json().get("status") == "ok"
    except Exception:
        return False


def ban_dang_chay() -> int | None:
    """Đã có bản tool đang chạy → trả cổng của nó; chưa có hoặc lock cũ (đã crash) → None."""
    port = _doc_cong_lock()
    if port is None:
        return None
    return port if _health_song(port) else None


# ── Tự chạy khi bật máy (Windows registry Run; mặc định TẮT) ────────────────
def _winreg():
    if sys.platform != "win32":
        return None
    import winreg

    return winreg


def tu_chay_dang_bat() -> bool:
    reg = _winreg()
    if reg is None:
        return False
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, _RUN_KEY) as k:
            reg.QueryValueEx(k, _RUN_APP_NAME)
            return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def dat_tu_chay(bat: bool) -> None:
    """Bật/tắt tự chạy khi đăng nhập Windows. Trỏ thẳng tới exe hiện tại (sys.executable)."""
    reg = _winreg()
    if reg is None:
        return
    with reg.OpenKey(reg.HKEY_CURRENT_USER, _RUN_KEY, 0, reg.KEY_SET_VALUE) as k:
        if bat:
            reg.SetValueEx(k, _RUN_APP_NAME, 0, reg.REG_SZ, f'"{sys.executable}"')
        else:
            try:
                reg.DeleteValue(k, _RUN_APP_NAME)
            except FileNotFoundError:
                pass


# ── Side-effect: chờ server, mở trình duyệt, icon, khay ─────────────────────
def cho_san_sang(port: int, giay: float = 20.0) -> bool:
    """Chờ tới khi /health của cổng này trả 200 (hoặc hết `giay`)."""
    import time

    het = time.monotonic() + giay
    while time.monotonic() < het:
        if _health_song(port):
            return True
        time.sleep(0.2)
    return False


def mo_trinh_duyet(url: str) -> bool:
    """Mở trình duyệt hệ thống tới `url`; không mở được → False (để báo địa chỉ cho user gõ tay)."""
    import webbrowser

    try:
        return webbrowser.open(url)
    except Exception:
        return False


def _icon_image():
    """Sinh icon khay đơn giản bằng PIL (không phụ thuộc file SVG)."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (64, 64), (16, 94, 164))  # xanh nước
    d = ImageDraw.Draw(img)
    d.rectangle([14, 16, 50, 48], outline="white", width=3)
    d.text((22, 24), "HV", fill="white")
    return img


def chay_khay(url: str, on_quit) -> None:
    """Hiện khay hệ thống (chặn luồng chính). Menu: Mở giao diện · Tự chạy khi bật máy · Thoát.
    'Thoát' gọi `on_quit()` (dừng server + xóa lock) rồi tắt icon."""
    import pystray
    from pystray import Menu, MenuItem

    def _mo(icon, item):  # noqa: ARG001
        mo_trinh_duyet(url)

    def _toggle_tu_chay(icon, item):  # noqa: ARG001
        dat_tu_chay(not tu_chay_dang_bat())

    def _thoat(icon, item):  # noqa: ARG001
        on_quit()
        icon.stop()

    menu = Menu(
        MenuItem("Mở giao diện", _mo, default=True),
        MenuItem("Tự chạy khi bật máy", _toggle_tu_chay, checked=lambda i: tu_chay_dang_bat()),
        MenuItem("Thoát", _thoat),
    )
    pystray.Icon("pmcsdtlx-tool", _icon_image(), "Tool nạp hồ sơ học viên", menu).run()
