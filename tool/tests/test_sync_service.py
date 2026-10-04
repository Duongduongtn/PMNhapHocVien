# -*- coding: utf-8 -*-
"""Test tạo HV ở CSDL đích (SYNC-01 task 57): sync_one_hv (port sync_tool) +
endpoint hoc-vien (E1 thiếu CCCD / E2 trùng CCCD nguồn). Connection giả."""
import contextlib
from datetime import date, datetime

from fastapi.testclient import TestClient

from app.main import app
from app import config_store, sync_helpers, sync_service
from app.routers import sync as sync_router

client = TestClient(app)


def _use_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_store, "KEY_FILE", tmp_path / "key.bin")
    monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.enc")


# --- connection giả cho sync_one_hv ---
class _Cur:
    def __init__(self, madk):
        self.madk = madk
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return (self.madk,)

    def fetchall(self):
        return []


class _Conn:
    def __init__(self, madk="75032-20260803-000006"):
        self._cur = _Cur(madk)
        self.commits = 0

    def cursor(self, as_dict=False):
        return self._cur

    def commit(self):
        self.commits += 1


def _hv(**over):
    base = {k: None for k in [
        "HoDemNLX", "TenNLX", "HoVaTen", "MaQuocTich", "NgaySinh", "NoiTT",
        "NoiTT_MaDVHC", "NoiTT_MaDVQL", "NoiCT", "NoiCT_MaDVHC", "NoiCT_MaDVQL",
        "SoCMT", "NgayCapCMT", "NoiCapCMT", "GhiChu", "GioiTinh", "HoVaTenIn",
        "MaLoaiHs", "DuongDanAnh", "ChatLuongAnh", "NgayThuNhanAnh", "NguoiThuNhanAnh",
        "SoGPLXDaCo", "HangGPLXDaCo", "DonViCapGPLXDaCo", "NoiCapGPLXDaCo",
        "NgayCapGPLXDaCo", "NgayHHGPLXDaCo", "NgayTTGPLXDaCo", "DonViHocLX", "NamHocLX",
        "HangGPLX", "SoNamLX", "SoKmLXAnToan", "GiayCNSK", "LyDoCapDoi", "MucDichCapDoi",
        "NoiDungSH", "HangDaoTao", "MaHTCap", "MaDK", "SoHoSo",
    ]}
    base.update({"HoVaTen": "Nguyễn Văn A", "SoCMT": "079201001234", "HangGPLX": "B",
                 "GioiTinh": "M", "MaLoaiHs": 2, "MaDK": "n1", "SoHoSo": "001"})
    base.update(over)
    return base


_KHOA = {"ma_csdt": "75032", "ma_so_gtvt": "75", "hang_gplx": "B"}


def test_sync_one_hv_thanh_cong():
    cd, cn = _Conn("75032-20260803-000006"), _Conn()
    kq = sync_service.sync_one_hv(cd, cn, _hv(), _KHOA, "75032K260101", 5, "03",
                                  ngay_nhap_hs=datetime.now().date())
    assert kq.ok is True
    assert kq.ma_dk == "75032-20260803-000006"
    assert kq.so_ho_so == "005"  # zero-pad 3
    assert kq.giay_to_loi is False
    # NguoiTao mặc định 'admin' truyền vào EXEC
    exec_call = cd._cur.calls[0]
    assert "admin" in exec_call[1]


def test_sync_one_hv_backdate_co_update_ngay():
    cd, cn = _Conn(), _Conn()
    sync_service.sync_one_hv(cd, cn, _hv(), _KHOA, "K", 1, "03",
                             ngay_nhap_hs=date(2025, 9, 18))
    sqls = " ".join(c[0] for c in cd._cur.calls)
    assert "UPDATE dbo.NguoiLX SET NgayTao" in sqls  # backdate


def test_sync_one_hv_khong_backdate_khi_hom_nay():
    cd, cn = _Conn(), _Conn()
    sync_service.sync_one_hv(cd, cn, _hv(), _KHOA, "K", 1, "03",
                             ngay_nhap_hs=datetime.now().date())
    sqls = " ".join(c[0] for c in cd._cur.calls)
    assert "UPDATE dbo.NguoiLX SET NgayTao" not in sqls


def test_sync_one_hv_sp_khong_tra_madk():
    cd, cn = _Conn(madk=None), _Conn()
    kq = sync_service.sync_one_hv(cd, cn, _hv(), _KHOA, "K", 1, "03")
    assert kq.ok is False
    assert "MaDK" in kq.loi


def test_next_so_ho_so():
    assert sync_service.next_so_ho_so(_Conn(madk=3), "K") == 3


def test_load_hoc_vien_nguon():
    class _C:
        def cursor(self, as_dict=False):
            class X:
                def execute(self, s, p=None): pass
                def fetchall(self): return [{"HoVaTen": "A"}]
            return X()
    assert sync_service.load_hoc_vien_nguon(_C(), "K")[0]["HoVaTen"] == "A"


# --- endpoint hoc-vien: E1/E2 + skip ---
def test_hoc_vien_e1_e2_skip(auth_headers, tmp_path, monkeypatch):
    _use_tmp(tmp_path, monkeypatch)
    config_store.save_sync_config(
        targets=[{"key": "t", "name": "T", "database": "DBX"}], selected="t",
    )

    @contextlib.contextmanager
    def _src():
        yield object()

    @contextlib.contextmanager
    def _dst(db):
        yield object()

    monkeypatch.setattr(sync_router, "sqlserver_conn", _src)
    monkeypatch.setattr(sync_router, "sqlserver_conn_dich", _dst)
    hv = [
        {"HoVaTen": "A", "SoCMT": "001", "HangGPLX": "B", "MaDK": "n1", "NgayNhanHSo": None},
        {"HoVaTen": "B", "SoCMT": "001", "HangGPLX": "B", "MaDK": "n2", "NgayNhanHSo": None},  # E2
        {"HoVaTen": "C", "SoCMT": "", "HangGPLX": "B", "MaDK": "n3", "NgayNhanHSo": None},     # E1
        {"HoVaTen": "D", "SoCMT": "002", "HangGPLX": "B", "MaDK": "n4", "NgayNhanHSo": None},  # đã có đích
    ]
    monkeypatch.setattr(sync_service, "load_hoc_vien_nguon", lambda cn, mk: hv)
    monkeypatch.setattr(
        sync_helpers, "enrich_from_db_dich",
        lambda cd, lst: {"002": {"ma_dk": "d1", "ngay_hs_latest": None, "so_hs": 1}},
    )
    d = client.post("/local/sync/hoc-vien", json={"ma_kh_nguon": "K", "target_key": "t"},
                    headers=auth_headers).json()
    assert d["tong"] == 4
    assert d["da_co_dich"] == 1
    assert d["se_tao_moi"] == 3
    assert d["thieu_cccd"] == 1
    assert d["trung_cccd_nguon"] == 2  # cả 2 dòng "001"
    # dòng D đã có đích
    row_d = next(r for r in d["hoc_vien"] if r["ho_ten"] == "D")
    assert row_d["da_co_dich"] is True and row_d["ma_dk_dich"] == "d1"


def test_hoc_vien_can_target(auth_headers, tmp_path, monkeypatch):
    _use_tmp(tmp_path, monkeypatch)  # chưa có target → 400
    r = client.post("/local/sync/hoc-vien", json={"ma_kh_nguon": "K"}, headers=auth_headers)
    assert r.status_code == 400
