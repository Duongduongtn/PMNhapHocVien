from app import config_store


def _use_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_store, "KEY_FILE", tmp_path / "key.bin")
    monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.enc")


SAMPLE = {
    "sqlserver_host": "MAY-DB",
    "sqlserver_database": "GPLX_CSDT",
    "sqlserver_user": "gplx_tool",
    "sqlserver_password": "matkhau-bi-mat",
    "vps_url": "https://vps.example/api",
    "vps_api_key": "khoa-may-bi-mat",
}


def test_save_load_roundtrip(tmp_path, monkeypatch):
    _use_tmp(tmp_path, monkeypatch)
    config_store.save_config(SAMPLE)
    assert config_store.load_config() == SAMPLE


def test_file_khong_chua_plaintext_secret(tmp_path, monkeypatch):
    _use_tmp(tmp_path, monkeypatch)
    config_store.save_config(SAMPLE)
    raw = (tmp_path / "config.enc").read_bytes()
    assert b"matkhau-bi-mat" not in raw
    assert b"khoa-may-bi-mat" not in raw


def test_masked_che_secret_giu_phan_con_lai(tmp_path, monkeypatch):
    _use_tmp(tmp_path, monkeypatch)
    config_store.save_config(SAMPLE)
    masked = config_store.masked_config()
    assert masked["sqlserver_password"] == "********"
    assert masked["vps_api_key"] == "********"
    assert masked["sqlserver_host"] == "MAY-DB"
    assert masked["sqlserver_user"] == "gplx_tool"


def test_load_rong_khi_chua_co_file(tmp_path, monkeypatch):
    _use_tmp(tmp_path, monkeypatch)
    assert config_store.load_config() == {}
