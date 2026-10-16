# -*- coding: utf-8 -*-
"""Ô "Chọn in GPLX" (NguoiLX_HoSo.CHON_IN_GPLX) — mặc định theo HẠNG khi nạp vào DB Nạp + chép sang DB đích (Sync).

1 = ghép (có TH + không TH) · 2 = có thời hạn (ô tô) · 3 = không thời hạn (mô tô). Dữ liệu thật ở DB Nạp:
ô tô → 2 (~15.000 HV), mô tô → 3 (~17.000 HV). Không chạm SQL Server: hàm thuần + connection giả + sqlite tạm.
"""
import sqlite3
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app import nap, sync_service
from app.main import app

client = TestClient(app)

_HV = {"ho_ten": "NGUYỄN VĂN AN", "ngay_sinh": "20000101", "gioi_tinh": "M", "so_cmt": "079200000001",
       "noi_tt_ma_dvhc": "00097"}
_TEN = {"HoVaTen": "NGUYỄN VĂN AN", "HoVaTenIn": "NGUYỄN VĂN AN"}


def _khoa(hang):
    return {"ma_kh": "K1", "hang_gplx": hang, "hang_dt": hang, "ma_so_gtvt": "70"}


def _p(hv, hang):
    return dict(nap.build_params_sp_gop(hv, _khoa(hang), "001", _TEN, "1,2,3,", "op"))["p_CHON_IN_GPLX"]


# ── mặc định theo hạng ──
@pytest.mark.parametrize("hang", ["A1", "A1m", "A2", "A3", "A01", "a1", " A1 "])
def test_mo_to_mac_dinh_khong_thoi_han(hang):
    assert nap.chon_in_gplx_mac_dinh(hang) == nap.IN_GPLX_KHONG_THOI_HAN == 3


@pytest.mark.parametrize("hang", ["B1", "B11", "B2", "C", "C1", "D", "E", "FC", "B.01"])
def test_o_to_mac_dinh_co_thoi_han(hang):
    assert nap.chon_in_gplx_mac_dinh(hang) == nap.IN_GPLX_CO_THOI_HAN == 2


@pytest.mark.parametrize("hang", [None, "", "  "])
def test_hang_trong_giu_nhu_cu_co_thoi_han(hang):
    assert nap.chon_in_gplx_mac_dinh(hang) == 2


def test_build_params_khoa_mo_to_la_3_khoa_o_to_la_2():
    assert _p(dict(_HV), "A1") == 3
    assert _p(dict(_HV), "A2") == 3
    assert _p(dict(_HV), "B1") == 2
    assert _p(dict(_HV), "C1") == 2


@pytest.mark.parametrize("chon", [1, 2, 3])
def test_nhan_vien_chon_tay_thang_mac_dinh(chon):
    assert _p({**_HV, "chon_in_gplx": chon}, "A1") == chon      # kể cả khóa mô tô
    assert _p({**_HV, "chon_in_gplx": chon}, "B2") == chon      # kể cả khóa ô tô


def test_build_params_khong_doi_so_tham_so():
    assert len(nap.build_params_sp_gop(dict(_HV), _khoa("B1"), "001", _TEN, "1,2,3,", "op")) == 30


# ── API: kiểm hợp lệ ──
def _body(**kw):
    return {"uuid": "u1", "ma_khoa_hoc": "K1", "ho_ten": "NGUYỄN VĂN AN", "ngay_sinh": "20000101", "gioi_tinh": "M",
            "so_cmt": "079200000001", "noi_tt_ma_dvhc": "00097", "noi_tt_ma_dvql": "00097", **kw}


@pytest.mark.parametrize("v", [0, 4, -1, 99])
def test_nap_chon_in_gplx_ngoai_tap_422(auth_headers, v):
    r = client.post("/local/nap", headers=auth_headers, json=_body(chon_in_gplx=v))
    assert r.status_code == 422


def test_nhap_chon_in_gplx_ngoai_tap_422(auth_headers):
    r = client.put("/local/nap/nhap/u1", headers=auth_headers, json={"chon_in_gplx": 7})
    assert r.status_code == 422


# ── nháp bền ──
@pytest.fixture
def staging_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(nap, "ORPHAN_DB", tmp_path / "staging.sqlite")
    return tmp_path / "staging.sqlite"


def test_nhap_luu_doc_chon_in_gplx(staging_tmp):
    nap.nhap_luu("u1", chon_in_gplx=3)
    assert nap.nhap_doc("u1")["chon_in_gplx"] == 3


def test_nhap_khong_chon_la_none_de_theo_mac_dinh_cua_hang(staging_tmp):
    nap.nhap_luu("u2", chi_tiet="x")
    assert nap.nhap_doc("u2")["chon_in_gplx"] is None


def test_nhap_migrate_bang_cu_chua_co_cot(staging_tmp):
    """Máy đã có nhap_chuan_bi theo bản cũ (không có chon_in_gplx) → tự thêm cột, không vỡ lưu nháp."""
    c = sqlite3.connect(str(staging_tmp))
    c.execute("CREATE TABLE nhap_chuan_bi (uuid TEXT PRIMARY KEY, dia_chi_json TEXT, chi_tiet TEXT, noi_cap TEXT, "
              "ngay_cap TEXT, tick_json TEXT, jp2_b64 TEXT, anh_preview TEXT, updated_at TEXT)")
    c.execute("INSERT INTO nhap_chuan_bi (uuid, chi_tiet) VALUES ('cu', 'nháp cũ')")
    c.commit()
    c.close()
    assert nap.nhap_doc("cu")["chi_tiet"] == "nháp cũ"              # đọc nháp cũ vẫn được
    assert nap.nhap_doc("cu")["chon_in_gplx"] is None
    nap.nhap_luu("moi", chon_in_gplx=2)
    assert nap.nhap_doc("moi")["chon_in_gplx"] == 2


def test_api_nhap_round_trip(auth_headers, staging_tmp):
    assert client.put("/local/nap/nhap/u9", headers=auth_headers, json={"chon_in_gplx": 3}).status_code == 200
    assert client.get("/local/nap/nhap/u9", headers=auth_headers).json()["chon_in_gplx"] == 3
    assert client.get("/local/nap/nhap/chua-co", headers=auth_headers).json()["chon_in_gplx"] is None


# ── Sync CDB: chép nguyên sang DB đích ──
class _Cur:
    def __init__(self):
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return ("75032-20260803-000006",)

    def fetchall(self):
        return []


class _Conn:
    def __init__(self):
        self._cur = _Cur()

    def cursor(self, as_dict=False):
        return self._cur

    def commit(self):
        pass


def _hv_nguon(**over):
    base = {k: None for k in [
        "HoDemNLX", "TenNLX", "HoVaTen", "MaQuocTich", "NgaySinh", "NoiTT", "NoiTT_MaDVHC", "NoiTT_MaDVQL", "NoiCT",
        "NoiCT_MaDVHC", "NoiCT_MaDVQL", "SoCMT", "NgayCapCMT", "NoiCapCMT", "GhiChu", "GioiTinh", "HoVaTenIn",
        "MaLoaiHs", "DuongDanAnh", "ChatLuongAnh", "NgayThuNhanAnh", "NguoiThuNhanAnh", "SoGPLXDaCo", "HangGPLXDaCo",
        "DonViCapGPLXDaCo", "NoiCapGPLXDaCo", "NgayCapGPLXDaCo", "NgayHHGPLXDaCo", "NgayTTGPLXDaCo", "DonViHocLX",
        "NamHocLX", "HangGPLX", "SoNamLX", "SoKmLXAnToan", "GiayCNSK", "LyDoCapDoi", "MucDichCapDoi", "NoiDungSH",
        "HangDaoTao", "MaHTCap", "MaDK", "SoHoSo"]}
    base.update({"HoVaTen": "Nguyễn Văn A", "SoCMT": "079201001234", "HangGPLX": "A1", "GioiTinh": "M",
                 "MaLoaiHs": 1, "MaDK": "n1", "SoHoSo": "001"})
    base.update(over)
    return base


def _insert_hoso(cd):
    return [(s, p) for s, p in cd._cur.calls if "INSERT INTO dbo.NguoiLX_HoSo" in s][0]


def _sync(hv):
    cd, cn = _Conn(), _Conn()
    kq = sync_service.sync_one_hv(cd, cn, hv, {"ma_csdt": "75032", "ma_so_gtvt": "75", "hang_gplx": hv["HangGPLX"]},
                                  "75032K260101", 5, "03", ngay_nhap_hs=datetime.now().date())
    assert kq.ok is True
    return _insert_hoso(cd)


@pytest.mark.parametrize("gia_tri", [1, 2, 3])
def test_sync_chep_nguyen_gia_tri_tu_nguon(gia_tri):
    sql, p = _sync(_hv_nguon(CHON_IN_GPLX=gia_tri))
    assert "CHON_IN_GPLX" in sql
    assert p[-1] == gia_tri
    assert sql.count("%s") == len(p)                      # số cột = số tham số (không lệch khi thêm cột)


def test_sync_nguon_null_hoac_thieu_thi_ghi_0_nhu_mac_dinh_cot():
    assert _sync(_hv_nguon(CHON_IN_GPLX=None))[1][-1] == 0
    assert _sync(_hv_nguon())[1][-1] == 0                  # nguồn cũ không có cột trong dict


def test_sync_select_nguon_doc_cot_in_gplx():
    assert "B.CHON_IN_GPLX" in sync_service._HV_SELECT
