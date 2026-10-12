# -*- coding: utf-8 -*-
"""Unit test nền phân hệ Đồng bộ CDB (task 55): sinh MaDK, enrich, khóa,
nhật ký JSON, cấu hình Sync. Không cần SQL Server — dùng connection giả."""
from datetime import date, datetime

import pytest

from app import sync_helpers as sh
from app import sync_history as hist
from app import config_store as cs


# --- Connection giả: cursor(as_dict=True) trả dict rows đã nạp sẵn ---------
class _FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, sql, params=None):
        self.sql = sql
        self.params = params

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class _FakeConn:
    def __init__(self, rows):
        self._rows = rows

    def cursor(self, as_dict=False):
        return _FakeCursor(self._rows)


# --- sinh_madk_batch ------------------------------------------------------
def test_sinh_madk_batch_dinh_dang_va_so_thu_tu():
    conn = _FakeConn([{"maxseq": 5}])
    out = sh.sinh_madk_batch(conn, "75032", date(2026, 8, 3), 3)
    assert out == [
        "75032-20260803-000006",
        "75032-20260803-000007",
        "75032-20260803-000008",
    ]
    assert all(len(m) == 21 for m in out)


def test_sinh_madk_batch_tu_khong_khi_chua_co():
    conn = _FakeConn([{"maxseq": 0}])
    out = sh.sinh_madk_batch(conn, "70004", date(2026, 1, 15), 1)
    assert out == ["70004-20260115-000001"]


def test_sinh_madk_batch_guard_so_luong():
    with pytest.raises(ValueError):
        sh.sinh_madk_batch(_FakeConn([]), "75032", date(2026, 8, 3), 0)


@pytest.mark.parametrize("ma_csdt", ["7503", "750321", "", "   "])
def test_sinh_madk_batch_guard_macsdt_khac_5(ma_csdt):
    with pytest.raises(ValueError):
        sh.sinh_madk_batch(_FakeConn([{"maxseq": 0}]), ma_csdt, date(2026, 8, 3), 1)


# --- kiem_tra_madk_ton_tai ------------------------------------------------
def test_kiem_tra_madk_ton_tai():
    assert sh.kiem_tra_madk_ton_tai(_FakeConn([{"x": 1}]), "75032-20260803-000001") is True
    assert sh.kiem_tra_madk_ton_tai(_FakeConn([]), "75032-20260803-000099") is False


# --- enrich_from_db_dich --------------------------------------------------
def test_enrich_tra_ve_theo_socmt():
    rows = [
        {"SoCMT": "012345678901", "MaDK": "75032-20260701-000015",
         "NgayHSMax": date(2026, 7, 1), "SoHS": 1},
    ]
    out = sh.enrich_from_db_dich(_FakeConn(rows), ["012345678901", "999", ""])
    assert out["012345678901"]["ma_dk"] == "75032-20260701-000015"
    assert out["012345678901"]["so_hs"] == 1
    assert "999" not in out  # không có ở đích → không xuất hiện


def test_enrich_rong():
    assert sh.enrich_from_db_dich(_FakeConn([]), []) == {}
    assert sh.enrich_from_db_dich(_FakeConn([]), ["", "  "]) == {}


# --- load khóa / năm ------------------------------------------------------
def test_load_khoa_map_truong_va_bc1():
    rows = [{"MaKH": "75032K260101", "TenKH": "B2 K01", "HangGPLX": "B",
             "NgayKG": datetime(2026, 10, 5), "SoHV": 12, "bc1": 1}]
    out = sh.load_khoa_hoc_by_year(_FakeConn(rows), 2026, with_bc1=True)
    assert out[0]["ma_kh"] == "75032K260101"
    assert out[0]["so_hv"] == 12
    assert out[0]["bc1"] is True


def test_load_years_fallback_nam_nay():
    assert sh.load_years_from_khoa(_FakeConn([])) == [datetime.now().year]
    assert sh.load_years_from_khoa(_FakeConn([{"Nam": 2026}, {"Nam": 2025}])) == [2026, 2025]


def test_get_ma_csdt():
    assert sh.get_ma_csdt_tu_qtht(_FakeConn([{"GiaTriTS": "75032 "}])) == "75032"
    assert sh.get_khoa_info(_FakeConn([{"MaCSDT": "75032", "MaSoGTVT": "75", "HangGPLX": "B"}]), "x")[
        "ma_so_gtvt"
    ] == "75"


# --- sync_history ---------------------------------------------------------
def test_history_round_trip(tmp_path):
    store = hist.HistoryStore(base_dir=tmp_path)
    batch = hist.SyncBatch(
        khoa_moi="75032K260101", khoa_cu="75032K250918",
        ngay_nhap_hs_chon=date(2026, 8, 3), can_bo="admin",
        sync_at_start=datetime(2026, 8, 5, 14, 22, 11),
        ma_dk_moi=["75032-20260803-000001", "75032-20260803-000002"],
    )
    store.save_batch(batch)
    loaded = store.load_batches_for_khoa("75032K260101")
    assert len(loaded) == 1
    assert loaded[0].ma_dk_moi == batch.ma_dk_moi
    assert loaded[0].can_bo == "admin"
    assert store.get_all_ma_dk_for_khoa("75032K260101") == set(batch.ma_dk_moi)


def test_history_bo_qua_file_hong(tmp_path):
    store = hist.HistoryStore(base_dir=tmp_path)
    (store.history_dir / "75032K260101_20260101_000000.json").write_text("{ hỏng", encoding="utf-8")
    assert store.load_batches_for_khoa("75032K260101") == []


# --- config_store Sync (monkeypatch kho cấu hình trong RAM) ---------------
def test_sync_config_round_trip(monkeypatch):
    store: dict = {}
    monkeypatch.setattr(cs, "load_config", lambda: dict(store))
    monkeypatch.setattr(cs, "save_config", lambda d: store.update(d))

    cs.save_sync_config(
        targets=[
            {"key": "cdb_chinh", "name": "CDB chính", "database": "GPLX_CDB_CSDT"},
            {"key": "cdb_moto", "name": "CDB mô tô", "database": "GPLX_CDB_CSDT_MOTO"},
        ],
        selected="cdb_chinh",
        options={"tt_xuly_force": "03", "update_tong_so_hv": False},
    )
    cfg = cs.get_sync_config()
    assert len(cfg["targets"]) == 2
    assert cfg["selected"] == "cdb_chinh"
    assert cfg["options"]["tt_xuly_force"] == "03"
    assert cfg["options"]["update_tong_so_hv"] is False
    assert cs.get_sync_target()["database"] == "GPLX_CDB_CSDT"
    assert cs.get_sync_target("cdb_moto")["database"] == "GPLX_CDB_CSDT_MOTO"


def test_sync_config_selected_ve_target_con_lai(monkeypatch):
    store: dict = {}
    monkeypatch.setattr(cs, "load_config", lambda: dict(store))
    monkeypatch.setattr(cs, "save_config", lambda d: store.update(d))
    # selected trỏ key không tồn tại → tự về target đầu
    cs.save_sync_config(
        targets=[{"key": "a", "name": "A", "database": "DB_A"}],
        selected="khong_co",
    )
    assert cs.get_sync_config()["selected"] == "a"


def test_sync_config_mac_dinh_khi_trong(monkeypatch):
    monkeypatch.setattr(cs, "load_config", lambda: {})
    cfg = cs.get_sync_config()
    assert cfg["targets"] == []
    assert cfg["selected"] == ""
    assert cfg["options"]["tt_xuly_force"] == "03"
    assert cfg["options"]["update_tong_so_hv"] is True
