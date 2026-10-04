# -*- coding: utf-8 -*-
"""Test API Quản lý CSDL đích (SYNC-02, task 56): CRUD targets + test kết nối.
Gác session (auth_headers). Kho cấu hình mã hóa thật trong tmp (isolated)."""
import contextlib

from fastapi.testclient import TestClient

from app.main import app
from app import config_store
from app.routers import sync as sync_router

client = TestClient(app)


def _use_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_store, "KEY_FILE", tmp_path / "key.bin")
    monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.enc")


def test_can_session(tmp_path, monkeypatch):
    _use_tmp(tmp_path, monkeypatch)
    # Không có Bearer → bị gác (401/403)
    assert client.get("/local/sync/targets").status_code in (401, 403)


def test_targets_rong(auth_headers, tmp_path, monkeypatch):
    _use_tmp(tmp_path, monkeypatch)
    d = client.get("/local/sync/targets", headers=auth_headers).json()
    assert d["targets"] == []
    assert d["selected"] == ""
    assert d["options"]["tt_xuly_force"] == "03"
    assert d["options"]["update_tong_so_hv"] is True
    assert any(o["ma"] == "03" for o in d["tt_xuly_options"])


def test_luu_va_doc_lai(auth_headers, tmp_path, monkeypatch):
    _use_tmp(tmp_path, monkeypatch)
    body = {
        "targets": [
            {"name": "CDB chính", "database": "GPLX_CDB_CSDT"},
            {"key": "", "name": "CDB mô tô", "database": "GPLX_CDB_CSDT_MOTO"},
        ],
        "selected": "",
        "options": {"tt_xuly_force": "03", "update_tong_so_hv": False},
    }
    d = client.put("/local/sync/targets", json=body, headers=auth_headers).json()
    assert len(d["targets"]) == 2
    assert d["targets"][0]["key"]  # tự sinh từ tên
    assert d["targets"][0]["database"] == "GPLX_CDB_CSDT"
    assert d["selected"] == d["targets"][0]["key"]  # mặc định về target đầu
    assert d["options"]["update_tong_so_hv"] is False
    # Đọc lại: còn nguyên
    d2 = client.get("/local/sync/targets", headers=auth_headers).json()
    assert len(d2["targets"]) == 2
    assert d2["targets"][1]["database"] == "GPLX_CDB_CSDT_MOTO"


def test_key_trung_duoc_sinh_lai(auth_headers, tmp_path, monkeypatch):
    _use_tmp(tmp_path, monkeypatch)
    body = {
        "targets": [
            {"name": "CDB", "database": "DB1"},
            {"name": "CDB", "database": "DB2"},  # cùng tên → key phải khác nhau
        ],
        "selected": "",
    }
    d = client.put("/local/sync/targets", json=body, headers=auth_headers).json()
    keys = [t["key"] for t in d["targets"]]
    assert len(set(keys)) == 2


def test_tt_xuly_khong_hop_le_ve_mac_dinh(auth_headers, tmp_path, monkeypatch):
    _use_tmp(tmp_path, monkeypatch)
    body = {"targets": [], "selected": "", "options": {"tt_xuly_force": "99", "update_tong_so_hv": True}}
    d = client.put("/local/sync/targets", json=body, headers=auth_headers).json()
    assert d["options"]["tt_xuly_force"] == "03"


def test_test_ket_noi_ok(auth_headers, tmp_path, monkeypatch):
    _use_tmp(tmp_path, monkeypatch)

    class _Cur:
        def execute(self, sql):
            pass

        def fetchone(self):
            return {"n": 12550}

    @contextlib.contextmanager
    def _fake(database, as_dict=True):
        yield _Cur()

    monkeypatch.setattr(sync_router, "sqlserver_cursor_dich", _fake)
    d = client.post("/local/sync/targets/test", json={"database": "GPLX_CDB_CSDT"}, headers=auth_headers).json()
    assert d["ok"] is True
    assert d["count"] == 12550
    assert "12.550" in d["message"]  # phân cách nghìn VN


def test_test_ket_noi_loi(auth_headers, tmp_path, monkeypatch):
    _use_tmp(tmp_path, monkeypatch)

    @contextlib.contextmanager
    def _fake(database, as_dict=True):
        raise RuntimeError("không nối được")
        yield  # pragma: no cover

    monkeypatch.setattr(sync_router, "sqlserver_cursor_dich", _fake)
    d = client.post("/local/sync/targets/test", json={"database": "X"}, headers=auth_headers).json()
    assert d["ok"] is False
    assert d["count"] == 0


def test_test_ket_noi_thieu_database(auth_headers, tmp_path, monkeypatch):
    _use_tmp(tmp_path, monkeypatch)
    r = client.post("/local/sync/targets/test", json={"database": "  "}, headers=auth_headers)
    assert r.status_code == 422  # validate rỗng
