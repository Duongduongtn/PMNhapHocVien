"""DGT-02 — test vòng đời khởi chạy (app/launcher.py): dò cổng, lock-file chống 2 bản,
tự chạy khi bật máy. Phần tray/trình duyệt là side-effect thuần → kiểm tay, không test ở đây."""
from __future__ import annotations

import socket

from app import launcher


# ── Dò cổng ──────────────────────────────────────────────────────────────
def test_cong_trong_va_chon_cong_khi_ban():
    # Chiếm 1 cổng rồi kiểm chon_cong nhảy sang cổng khác.
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    s.listen()
    busy = s.getsockname()[1]
    try:
        assert launcher.cong_trong(busy) is False
        chon = launcher.chon_cong(busy, so_cong_thu=30)
        assert chon != busy
        assert launcher.cong_trong(chon) is True
    finally:
        s.close()


# ── Lock-file chống chạy 2 bản ─────────────────────────────────────────────
def test_lock_ghi_doc_xoa(tmp_path, monkeypatch):
    monkeypatch.setattr(launcher, "LOCK_FILE", tmp_path / "x.lock")
    assert launcher._doc_cong_lock() is None
    launcher.ghi_lock(8123)
    assert launcher._doc_cong_lock() == 8123
    launcher.xoa_lock()
    assert launcher._doc_cong_lock() is None


def test_ban_dang_chay_theo_health(tmp_path, monkeypatch):
    monkeypatch.setattr(launcher, "LOCK_FILE", tmp_path / "x.lock")
    # Không có lock → None.
    assert launcher.ban_dang_chay() is None
    launcher.ghi_lock(8200)
    # Lock có nhưng cổng không sống (lock cũ sau crash) → None (được phép chiếm lại).
    monkeypatch.setattr(launcher, "_health_song", lambda p: False)
    assert launcher.ban_dang_chay() is None
    # Cổng sống → trả đúng cổng để bản mở sau chỉ mở trình duyệt.
    monkeypatch.setattr(launcher, "_health_song", lambda p: True)
    assert launcher.ban_dang_chay() == 8200


def test_lock_hong_khong_sap(tmp_path, monkeypatch):
    f = tmp_path / "x.lock"
    f.write_text("rác không phải json", encoding="utf-8")
    monkeypatch.setattr(launcher, "LOCK_FILE", f)
    assert launcher._doc_cong_lock() is None
    assert launcher.ban_dang_chay() is None


# ── Tự chạy khi bật máy (registry giả, không đụng registry thật) ───────────
class _FakeKey:
    def __init__(self, store):
        self.store = store

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _FakeWinreg:
    HKEY_CURRENT_USER = 1
    KEY_SET_VALUE = 2
    REG_SZ = 1

    def __init__(self):
        self.store: dict[str, str] = {}

    def OpenKey(self, root, key, *a):  # noqa: N802
        return _FakeKey(self.store)

    def SetValueEx(self, k, name, _r, _t, val):  # noqa: N802
        k.store[name] = val

    def QueryValueEx(self, k, name):  # noqa: N802
        if name not in k.store:
            raise FileNotFoundError(name)
        return (k.store[name], self.REG_SZ)

    def DeleteValue(self, k, name):  # noqa: N802
        if name not in k.store:
            raise FileNotFoundError(name)
        del k.store[name]


def test_tu_chay_bat_tat(monkeypatch):
    fake = _FakeWinreg()
    monkeypatch.setattr(launcher, "_winreg", lambda: fake)
    assert launcher.tu_chay_dang_bat() is False
    launcher.dat_tu_chay(True)
    assert launcher.tu_chay_dang_bat() is True
    launcher.dat_tu_chay(False)
    assert launcher.tu_chay_dang_bat() is False
    # Tắt hai lần không lỗi.
    launcher.dat_tu_chay(False)
