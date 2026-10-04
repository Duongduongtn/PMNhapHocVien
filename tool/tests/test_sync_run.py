# -*- coding: utf-8 -*-
"""Test chạy đồng bộ (SYNC-01 task 58): validate /run + vòng job (skip/E1/new/
tổng kết) + SSE sentinel. Không chạm SQL thật — mock connection + hàm nghiệp vụ."""
import contextlib
import queue
from datetime import date, datetime

from fastapi.testclient import TestClient

from app.main import app
from app import config_store, sync_helpers, sync_service, sync_history
from app.routers import sync as sync_router

client = TestClient(app)


def _use_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_store, "KEY_FILE", tmp_path / "key.bin")
    monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.enc")


def _target(tmp_path, monkeypatch):
    _use_tmp(tmp_path, monkeypatch)
    config_store.save_sync_config(targets=[{"key": "t", "name": "T", "database": "DBX"}], selected="t")


@contextlib.contextmanager
def _dummy(*a, **k):
    yield object()


def _patch_conns(monkeypatch):
    monkeypatch.setattr(sync_router, "sqlserver_conn", _dummy)
    monkeypatch.setattr(sync_router, "sqlserver_conn_dich", _dummy)


_KHOA = {"ma_csdt": "75032", "ma_so_gtvt": "75", "hang_gplx": "B"}


# --- validate /run ---
def test_run_hang_lech_400(auth_headers, tmp_path, monkeypatch):
    _target(tmp_path, monkeypatch)
    _patch_conns(monkeypatch)
    monkeypatch.setattr(sync_router, "_khoa_hang_nguon", lambda c, m: "A1")
    monkeypatch.setattr(sync_helpers, "get_khoa_info", lambda c, m: dict(_KHOA))
    monkeypatch.setattr(sync_router, "_khoa_ngaykg", lambda c, m: datetime(2026, 10, 5))
    monkeypatch.setattr(sync_router, "_chay_job", lambda *a, **k: None)
    r = client.post("/local/sync/run", headers=auth_headers, json={
        "ma_kh_nguon": "K", "ma_kh_dich": "KD", "ngay_nhap_hs": "2026-10-01", "target_key": "t"})
    assert r.status_code == 400
    assert "Hạng xe không khớp" in r.json()["detail"]


def test_run_ngay_sau_kg_400(auth_headers, tmp_path, monkeypatch):
    from datetime import timedelta
    _target(tmp_path, monkeypatch)
    _patch_conns(monkeypatch)
    monkeypatch.setattr(sync_router, "_khoa_hang_nguon", lambda c, m: "B")
    monkeypatch.setattr(sync_helpers, "get_khoa_info", lambda c, m: dict(_KHOA))
    # KG trong quá khứ; ngày ≤ hôm nay nhưng SAU KG → qua được chặn tương lai, dính chặn KG
    kg = datetime.now().date() - timedelta(days=10)
    monkeypatch.setattr(sync_router, "_khoa_ngaykg", lambda c, m: datetime(kg.year, kg.month, kg.day))
    monkeypatch.setattr(sync_router, "_chay_job", lambda *a, **k: None)
    ngay = (datetime.now().date() - timedelta(days=2)).isoformat()
    r = client.post("/local/sync/run", headers=auth_headers, json={
        "ma_kh_nguon": "K", "ma_kh_dich": "KD", "ngay_nhap_hs": ngay, "target_key": "t"})
    assert r.status_code == 400
    assert "sau NgàyKG" in r.json()["detail"]


def test_run_ngay_tuong_lai_400(auth_headers, tmp_path, monkeypatch):
    _target(tmp_path, monkeypatch)
    _patch_conns(monkeypatch)
    monkeypatch.setattr(sync_router, "_khoa_hang_nguon", lambda c, m: "B")
    monkeypatch.setattr(sync_helpers, "get_khoa_info", lambda c, m: dict(_KHOA))
    monkeypatch.setattr(sync_router, "_khoa_ngaykg", lambda c, m: datetime(2027, 12, 31))  # KG xa
    monkeypatch.setattr(sync_router, "_chay_job", lambda *a, **k: None)
    from datetime import timedelta
    mai = (datetime.now().date() + timedelta(days=1)).isoformat()
    r = client.post("/local/sync/run", headers=auth_headers, json={
        "ma_kh_nguon": "K", "ma_kh_dich": "KD", "ngay_nhap_hs": mai, "target_key": "t"})
    assert r.status_code == 400
    assert "sau hôm nay" in r.json()["detail"]


def test_run_ok_tra_job_id(auth_headers, tmp_path, monkeypatch):
    _target(tmp_path, monkeypatch)
    _patch_conns(monkeypatch)
    monkeypatch.setattr(sync_router, "_khoa_hang_nguon", lambda c, m: "B")
    monkeypatch.setattr(sync_helpers, "get_khoa_info", lambda c, m: dict(_KHOA))
    monkeypatch.setattr(sync_router, "_khoa_ngaykg", lambda c, m: datetime(2099, 10, 5))  # KG tương lai xa
    monkeypatch.setattr(sync_router, "_chay_job", lambda *a, **k: None)
    hom_nay = datetime.now().date().isoformat()
    r = client.post("/local/sync/run", headers=auth_headers, json={
        "ma_kh_nguon": "K", "ma_kh_dich": "KD", "ngay_nhap_hs": hom_nay, "target_key": "t"})
    assert r.status_code == 200
    assert r.json()["job_id"]


# --- vòng job: skip / E1 / new / tổng kết ---
class _FakeStore:
    def save_batch(self, b):
        return None


def test_chay_job_skip_e1_new(monkeypatch):
    _patch_conns(monkeypatch)
    monkeypatch.setattr(sync_history, "HistoryStore", lambda *a, **k: _FakeStore())
    hv = [
        {"HoVaTen": "A", "SoCMT": "001"},   # new
        {"HoVaTen": "B", "SoCMT": "002"},   # skip (đã có)
        {"HoVaTen": "C", "SoCMT": ""},      # E1 thiếu CCCD
    ]
    monkeypatch.setattr(sync_service, "load_hoc_vien_nguon", lambda cn, mk: hv)
    monkeypatch.setattr(sync_helpers, "enrich_from_db_dich",
                        lambda cd, lst: {"002": {"ma_dk": "d1", "ngay_hs_latest": None, "so_hs": 1}})
    monkeypatch.setattr(sync_service, "next_so_ho_so", lambda cd, mk: 0)
    monkeypatch.setattr(sync_service, "sync_one_hv",
                        lambda *a, **k: sync_service.KetQuaHV(ok=True, ma_dk="75032-X-000001", so_ho_so="001"))

    job_id = "testjob"
    sync_router._jobs[job_id] = {"q": queue.Queue(), "done": False, "summary": None}
    body = sync_router.RunIn(ma_kh_nguon="K", ma_kh_dich="KD",
                             ngay_nhap_hs=datetime.now().date(), target_key="t", so_cmt_chon=[])
    tt = {"tt_xuly_force": "03", "update_tong_so_hv": False}
    sync_router._chay_job(job_id, "DBX", body, dict(_KHOA), tt)

    # Rút sự kiện khỏi queue
    q = sync_router._jobs[job_id]["q"]
    evs = []
    while True:
        e = q.get_nowait()
        if e is None:
            break
        evs.append(e)
    maus = [e.get("mau") for e in evs if e["loai"] == "hv"]
    assert maus == ["ok", "skip", "loi"]
    xong = evs[-1]
    assert xong["loai"] == "xong"
    assert (xong["ok"], xong["skip"], xong["loi"]) == (1, 1, 1)


def test_stream_404_job_khong_co(auth_headers):
    r = client.get("/local/sync/stream?job=khongco", headers=auth_headers)
    assert r.status_code == 404
