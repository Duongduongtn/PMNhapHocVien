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


# ---- PUT /local/config gộp, không làm rơi khóa khác (sửa 12/10/2026) -----------------------------
def test_put_config_giu_nguyen_khoa_khac_va_secret_da_che(monkeypatch, tmp_path, auth_headers):
    from fastapi.testclient import TestClient

    from app import config_store
    from app.main import app

    monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_store, "KEY_FILE", tmp_path / "key.bin")
    monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.enc")
    config_store.save_config({
        "sqlserver_host": "H", "sqlserver_database": "D", "sqlserver_user": "u", "sqlserver_password": "bi-mat",
        "vps_url": "https://v", "vps_api_key": "khoa-vps",
        "kqd_chuong_trinh": {"75032K260003": "moi"}, "sync_targets": [{"key": "t1", "database": "GPLX_CDB_CSDT"}],
        "co_quan_chu_quan": "CÔNG TY A",
    })
    r = TestClient(app).put("/local/config", headers=auth_headers, json={
        "sqlserver_host": "H2", "sqlserver_database": "D", "sqlserver_user": "u", "sqlserver_password": "********",
        "vps_url": "https://v", "vps_api_key": "********", "co_quan_chu_quan": "CÔNG TY A", "ten_co_so_dao_tao": "TT B"})
    assert r.status_code == 200
    luu = config_store.load_config()
    assert luu["sqlserver_host"] == "H2"                                   # trường kết nối được ghi
    assert luu["sqlserver_password"] == "bi-mat" and luu["vps_api_key"] == "khoa-vps"   # secret che → giữ nguyên
    assert luu["kqd_chuong_trinh"] == {"75032K260003": "moi"}              # KHÔNG bị rơi
    assert luu["sync_targets"] == [{"key": "t1", "database": "GPLX_CDB_CSDT"}]
    assert luu["ten_co_so_dao_tao"] == "TT B"
    assert r.json()["sqlserver_password"] == "********"                     # trả ra vẫn che

