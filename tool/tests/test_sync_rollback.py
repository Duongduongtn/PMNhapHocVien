# -*- coding: utf-8 -*-
"""Test Lịch sử & Hủy sync (SYNC-03 task 60): lich-su đọc JSON, rollback/preview
đếm, rollback xóa dual-mode + bắt lỗi BC1 → 409. KHÔNG chạm SQL thật — mock conn
+ cursor; nhật ký ghi vào thư mục tạm."""
import contextlib
from datetime import date, datetime

from fastapi.testclient import TestClient

from app.main import app
from app import config_store, sync_history
from app.routers import sync as sync_router

client = TestClient(app)


def _target(tmp_path, monkeypatch):
    monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_store, "KEY_FILE", tmp_path / "key.bin")
    monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.enc")
    config_store.save_sync_config(
        targets=[{"key": "t", "name": "T", "database": "DBX"}], selected="t",
        options={"tt_xuly_force": "03", "update_tong_so_hv": True},
    )


def _store_with(tmp_path, monkeypatch, batches):
    """Dựng HistoryStore ở thư mục tạm + ghi sẵn các batch; ép endpoint dùng nó."""
    store = sync_history.HistoryStore(base_dir=tmp_path / "hist")
    for b in batches:
        store.save_batch(b)
    monkeypatch.setattr(sync_history, "HistoryStore", lambda *a, **k: store)
    return store


def _batch(khoa_moi, ma_dk_moi, start, khoa_cu="KN"):
    return sync_history.SyncBatch(
        khoa_moi=khoa_moi, khoa_cu=khoa_cu, ngay_nhap_hs_chon=date(2026, 9, 1),
        can_bo="admin", sync_at_start=start, ma_dk_moi=list(ma_dk_moi),
    )


# ---------- list_all_batches (unit) ----------
def test_list_all_batches_sort_moi_nhat_truoc(tmp_path):
    store = sync_history.HistoryStore(base_dir=tmp_path / "h")
    store.save_batch(_batch("KA", ["a1"], datetime(2026, 8, 1, 10, 0, 0)))
    store.save_batch(_batch("KB", ["b1", "b2"], datetime(2026, 8, 3, 9, 0, 0)))
    lst = store.list_all_batches()
    assert [b.khoa_moi for b in lst] == ["KB", "KA"]  # mới nhất lên đầu


# ---------- GET /lich-su ----------
def test_lich_su_tra_danh_sach(auth_headers, tmp_path, monkeypatch):
    _store_with(tmp_path, monkeypatch, [
        _batch("KA", ["a1"], datetime(2026, 8, 1, 10, 0, 0)),
        _batch("KB", ["b1", "b2"], datetime(2026, 8, 3, 9, 0, 0)),
    ])
    r = client.get("/local/sync/lich-su", headers=auth_headers)
    assert r.status_code == 200
    rows = r.json()
    assert [x["khoa_moi"] for x in rows] == ["KB", "KA"]
    assert rows[0]["so_tao"] == 2 and rows[1]["so_tao"] == 1
    assert rows[0]["can_bo"] == "admin"


def test_lich_su_rong(auth_headers, tmp_path, monkeypatch):
    _store_with(tmp_path, monkeypatch, [])
    r = client.get("/local/sync/lich-su", headers=auth_headers)
    assert r.status_code == 200 and r.json() == []


# ---------- Fake DB cho preview + rollback ----------
class _FakeCursor:
    def __init__(self, rules, fetch_seq=None, raise_on=None):
        self.sqls = []
        self._rules = rules          # list[(substr, rowcount)] — khớp đầu tiên thắng
        self._fetch = list(fetch_seq or [])
        self._raise_on = raise_on
        self._rowcount = 0

    def execute(self, sql, params=None):
        self.sqls.append(sql)
        if self._raise_on and self._raise_on in sql:
            raise RuntimeError("DELETE statement conflicted with REFERENCE constraint "
                               '"FK_NguoiLX_HoSo_BaoCaoI" ... table "dbo.BaoCaoI"')
        self._rowcount = 0
        for sub, rc in self._rules:
            if sub in sql:
                self._rowcount = rc
                break

    @property
    def rowcount(self):
        return self._rowcount

    def fetchone(self):
        return self._fetch.pop(0) if self._fetch else (0,)


class _FakeConn:
    def __init__(self, cursor):
        self._c = cursor
        self.committed = False

    def cursor(self):
        return self._c

    def commit(self):
        self.committed = True


def _patch_dich(monkeypatch, conn):
    @contextlib.contextmanager
    def _cm(db, autocommit=True):
        yield conn
    monkeypatch.setattr(sync_router, "sqlserver_conn_dich", _cm)


# ---------- GET /rollback/preview ----------
def test_rollback_preview_dem(auth_headers, tmp_path, monkeypatch):
    _target(tmp_path, monkeypatch)
    _store_with(tmp_path, monkeypatch, [_batch("KA", ["d1", "d2"], datetime(2026, 8, 1))])
    # fetchone: lần 1 = COUNT MaDK IN(...) còn ở đích = 2; lần 2 = COUNT NguoiTao='SYNC' = 3
    cur = _FakeCursor(rules=[], fetch_seq=[(2,), (3,)])
    _patch_dich(monkeypatch, _FakeConn(cur))
    r = client.get("/local/sync/rollback/preview?ma_kh=KA", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {"log_count": 2, "log_con_dich": 2, "sync_group": 3, "tong": 5}


# ---------- POST /rollback ----------
_RULES_DELETE = [
    ("NguoiLX_HoSo WHERE MaDK=%s AND MaKhoaHoc", 1),            # per-MaDK: HoSo
    ("NOT EXISTS (SELECT 1 FROM dbo.NguoiLX_HoSo", 1),          # per-MaDK: NguoiLX
    ("NguoiLX_HoSo WHERE MaKhoaHoc=%s AND NguoiTao", 3),        # nhóm SYNC: HoSo
    ("NOT IN (SELECT MaDK FROM dbo.NguoiLX_HoSo)", 3),          # nhóm SYNC: NguoiLX
]


def test_rollback_xoa_va_commit(auth_headers, tmp_path, monkeypatch):
    _target(tmp_path, monkeypatch)
    _store_with(tmp_path, monkeypatch, [_batch("KA", ["d1"], datetime(2026, 8, 1))])
    cur = _FakeCursor(rules=_RULES_DELETE, fetch_seq=[(42,)])  # (42,) = TongSoHV sau cập nhật
    conn = _FakeConn(cur)
    _patch_dich(monkeypatch, conn)
    r = client.post("/local/sync/rollback", headers=auth_headers, json={"ma_kh": "KA", "target_key": "t"})
    assert r.status_code == 200
    d = r.json()
    assert d["hs_del"] == 1 + 3          # HoSo: per-MaDK 1 + nhóm SYNC 3
    assert d["nlx_del"] == 1 + 3         # NguoiLX: per-MaDK 1 + nhóm SYNC 3
    assert d["tong_so_hv"] == 42
    assert conn.committed is True
    assert any("NguoiTao='SYNC'" in s for s in cur.sqls)  # có chạy nhánh tương thích cũ


def test_rollback_bc1_chan_409_khong_commit(auth_headers, tmp_path, monkeypatch):
    _target(tmp_path, monkeypatch)
    _store_with(tmp_path, monkeypatch, [_batch("KA", ["d1"], datetime(2026, 8, 1))])
    cur = _FakeCursor(rules=[], raise_on="DELETE FROM dbo.NguoiLX_HoSo WHERE MaDK")
    conn = _FakeConn(cur)
    _patch_dich(monkeypatch, conn)
    r = client.post("/local/sync/rollback", headers=auth_headers, json={"ma_kh": "KA", "target_key": "t"})
    assert r.status_code == 409
    assert "Báo cáo 1" in r.json()["detail"]
    assert conn.committed is False  # không commit → DB tự rollback khi đóng


def test_rollback_thieu_ma_kh_422(auth_headers, tmp_path, monkeypatch):
    _target(tmp_path, monkeypatch)
    r = client.post("/local/sync/rollback", headers=auth_headers, json={"ma_kh": "  ", "target_key": "t"})
    assert r.status_code == 422
