"""DGT-03 (task 68) — endpoint kiểm môi trường cho wizard (mức 2).

Monkeypatch load_config để kiểm 3 trạng thái khởi động mà không đụng config thật.
"""
from fastapi.testclient import TestClient

from app.main import app
from app.routers import config as cfgmod

client = TestClient(app)


def test_moi_truong_da_cau_hinh(monkeypatch):
    monkeypatch.setattr(cfgmod.config_store, "load_config",
                        lambda: {k: "x" for k in cfgmod._REQUIRED_CAU_HINH})
    r = client.get("/local/config/moi-truong")
    assert r.status_code == 200
    b = r.json()
    assert b["da_cau_hinh"] is True
    assert "thu_muc_ghi_duoc" in b and "duong_dan" in b


def test_moi_truong_may_sach_thieu_cau_hinh(monkeypatch):
    monkeypatch.setattr(cfgmod.config_store, "load_config", lambda: {"sqlserver_host": "x"})
    assert client.get("/local/config/moi-truong").json()["da_cau_hinh"] is False


def test_moi_truong_key_hong_coi_la_may_sach(monkeypatch):
    # TDD §11C.5 ca (c): key.bin có nhưng giải mã lỗi → endpoint KHÔNG 500, coi máy sạch → wizard.
    def _loi():
        raise ValueError("InvalidToken giả lập")

    monkeypatch.setattr(cfgmod.config_store, "load_config", _loi)
    r = client.get("/local/config/moi-truong")
    assert r.status_code == 200
    assert r.json()["da_cau_hinh"] is False
