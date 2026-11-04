"""NAP-08 — báo hồ sơ CHƯA NẠP vừa được app web cập nhật (mức 2, TDD §10.8).

Phủ: hàm so sánh thuần, ghi nhận khi kéo (không báo lần đầu / không đổi / đã nạp), mốc ảnh `anh_luc`,
dọn khi hồ sơ không còn chờ nạp, cờ "nháp giữ ảnh cũ", Đã xem, bỏ ảnh trong nháp, 3 endpoint.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import nap, session
from app import vps as vps_mod
from app.main import app

client = TestClient(app)


@pytest.fixture
def staging_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(nap, "ORPHAN_DB", tmp_path / "staging.sqlite")


@pytest.fixture
def op_headers():
    token = "test-thaydoi-token"
    session._phien_theo_token[token] = session.Phien(
        username="op-test", ho_ten="NV Nạp", vai_tro="operator", vps_token="jwt-vps-gia"
    )
    yield {"Authorization": f"Bearer {token}"}
    session._phien_theo_token.pop(token, None)


def _row(uuid="u1", **kw) -> dict:
    r = {
        "uuid": uuid, "so_cccd": "012345678901", "so_cmnd_cu": None, "ho_ten": "nguyễn văn a",
        "ngay_sinh": "20000101", "gioi_tinh": "M", "noi_tt_raw": "Xã X, Tỉnh Y",
        "ngay_cap_cccd": "2021-03-10", "noi_cap_cccd": "Cục CS", "co_anh": True,
        "anh_luc": "2026-11-04T02:00:00+00:00", "created_at": "2026-10-01T08:00:00+00:00",
    }
    r.update(kw)
    return r


def _truong(uuid="u1") -> list[str]:
    return next((d["truong"] for d in nap.thay_doi_ds() if d["uuid"] == uuid), [])


# ---- hàm thuần ----
def _bo(**kw):
    b = {"so_cccd": "1", "so_cmnd_cu": "", "ho_ten": "A", "ngay_sinh": "2000", "gioi_tinh": "M",
         "noi_tt_raw": "X", "ngay_cap": "20210310", "noi_cap_cccd": "C", "co_anh": 1,
         "anh_luc": "t1", "gplx_da_co_json": None}
    b.update(kw)
    return b


def test_phat_hien_khong_doi_thi_rong():
    assert nap.phat_hien_thay_doi(_bo(), _bo()) == []


def test_phat_hien_tung_truong_va_khoang_trang():
    assert nap.phat_hien_thay_doi(_bo(), _bo(ho_ten="B")) == ["tt:ho_ten"]
    assert nap.phat_hien_thay_doi(_bo(), _bo(ho_ten="A ")) == []            # khoảng trắng thừa không tính
    assert nap.phat_hien_thay_doi(_bo(so_cmnd_cu=None), _bo(so_cmnd_cu="")) == []  # None ≡ rỗng


def test_phat_hien_gplx_rong_bang_none():
    assert nap.phat_hien_thay_doi(_bo(gplx_da_co_json="[]"), _bo(gplx_da_co_json=None)) == []
    assert nap.phat_hien_thay_doi(_bo(gplx_da_co_json=None), _bo(gplx_da_co_json='[{"hang":"B2"}]')) == ["gplx"]
    # cùng nội dung, khác thứ tự khóa → không đổi
    assert nap.phat_hien_thay_doi(_bo(gplx_da_co_json='[{"a":1,"b":2}]'), _bo(gplx_da_co_json='[{"b":2,"a":1}]')) == []


def test_phat_hien_anh():
    assert nap.phat_hien_thay_doi(_bo(), _bo(anh_luc="t2")) == ["anh"]
    assert nap.phat_hien_thay_doi(_bo(co_anh=0, anh_luc=None), _bo(co_anh=1, anh_luc="t2")) == ["anh"]   # vừa thêm ảnh
    assert nap.phat_hien_thay_doi(_bo(anh_luc=None), _bo(anh_luc="t2")) == []     # chưa có mốc cũ → không kết luận
    assert nap.phat_hien_thay_doi(_bo(), _bo(anh_luc=None)) == []                 # VPS cũ không trả mốc → không báo


# ---- ghi nhận khi kéo ----
def test_lan_dau_khong_bao(staging_tmp):
    nap.keo_ve_upsert([_row()])
    assert nap.thay_doi_ds() == []


def test_keo_lai_khong_doi_khong_bao(staging_tmp):
    nap.keo_ve_upsert([_row()])
    nap.keo_ve_upsert([_row()])
    assert nap.thay_doi_ds() == []


def test_doi_thong_tin_nghi_ten_truong_khong_nghi_gia_tri(staging_tmp):
    nap.keo_ve_upsert([_row()])
    nap.keo_ve_upsert([_row(ho_ten="trần thị b", so_cccd="999999999999")])
    ds = nap.thay_doi_ds()
    assert len(ds) == 1 and set(ds[0]["truong"]) == {"tt:ho_ten", "tt:so_cccd"}
    assert "999999999999" not in repr(ds)          # không lộ giá trị cá nhân (số căn cước)


def test_doi_anh_va_gplx_gop_mot_dong(staging_tmp):
    nap.keo_ve_upsert([_row()])
    nap.keo_ve_upsert([_row(anh_luc="2026-11-04T09:00:00+00:00")])
    nap.keo_ve_upsert([_row(anh_luc="2026-11-04T09:00:00+00:00", gplx_da_co=[{"hang": "B2"}])])
    ds = nap.thay_doi_ds()
    assert len(ds) == 1 and set(ds[0]["truong"]) == {"anh", "gplx"}


def test_nang_cap_chua_co_moc_anh_khong_bao_anh(staging_tmp):
    nap.keo_ve_upsert([_row(anh_luc=None)])                       # máy cũ/VPS cũ: chưa có mốc
    nap.keo_ve_upsert([_row()])                                   # VPS mới trả mốc lần đầu
    assert nap.thay_doi_ds() == []
    nap.keo_ve_upsert([_row(anh_luc="2026-11-05T01:00:00+00:00")])
    assert _truong() == ["anh"]


def test_dia_chi_doi_co_nhap_ghi_dc_reset(staging_tmp):
    nap.keo_ve_upsert([_row()])
    nap.nhap_luu("u1", dia_chi_json='{"x":1}', chi_tiet="s")
    nap.keo_ve_upsert([_row(noi_tt_raw="Xã Z, Tỉnh Q")])
    assert set(_truong()) == {"tt:noi_tt_raw", "dc_reset"}


def test_ho_so_da_nap_khong_ghi(staging_tmp):
    nap.keo_ve_upsert([_row()])
    nap.keo_ve_cap_nhat("u1", trang_thai="xong", ma_dk="K1", so_ho_so="1")
    nap.keo_ve_upsert([_row(ho_ten="đổi sau khi nạp")])
    assert nap.thay_doi_ds() == []


def test_het_cho_nap_thi_tu_bien_mat(staging_tmp):
    nap.keo_ve_upsert([_row()])
    nap.keo_ve_upsert([_row(ho_ten="b")])
    assert len(nap.thay_doi_ds()) == 1
    nap.keo_ve_cap_nhat("u1", trang_thai="xong", ma_dk="K1", so_ho_so="1")
    assert nap.thay_doi_ds() == []


# ---- nháp giữ ảnh cũ ----
def test_nhap_giu_anh_cu(staging_tmp):
    nap.keo_ve_upsert([_row()])
    nap.nhap_luu("u1", jp2_b64="QUJD", anh_preview="UE5H")
    nap.keo_ve_upsert([_row(anh_luc="2026-11-04T09:00:00+00:00")])
    assert nap.thay_doi_ds()[0]["nhap_giu_anh_cu"] is True


def test_khong_co_nhap_anh_thi_khong_canh_bao_dam(staging_tmp):
    nap.keo_ve_upsert([_row()])
    nap.keo_ve_upsert([_row(anh_luc="2026-11-04T09:00:00+00:00")])
    assert nap.thay_doi_ds()[0]["nhap_giu_anh_cu"] is False


def test_bo_anh_nhap_giu_dia_chi_va_go_loai_anh(staging_tmp):
    nap.keo_ve_upsert([_row()])
    nap.nhap_luu("u1", dia_chi_json='{"x":1}', tick_json="[1]", jp2_b64="QUJD", anh_preview="UE5H")
    nap.keo_ve_upsert([_row(ho_ten="b", anh_luc="2026-11-04T09:00:00+00:00")])
    assert nap.nhap_bo_anh("u1") is True
    n = nap.nhap_doc("u1")
    assert n["jp2_b64"] is None and n["anh_preview"] is None
    assert n["dia_chi_json"] == '{"x":1}' and n["tick_json"] == "[1]"
    assert _truong() == ["tt:ho_ten"]                   # chỉ còn loại thông tin
    assert nap.nhap_bo_anh("khong-co") is False


# ---- Đã xem ----
def test_da_xem_tung_ho_so_theo_loai_va_tat_ca(staging_tmp):
    nap.keo_ve_upsert([_row("u1"), _row("u2")])
    nap.keo_ve_upsert([_row("u1", ho_ten="b", anh_luc="2026-11-04T09:00:00+00:00"), _row("u2", ho_ten="c")])
    nap.thay_doi_da_xem(["u1"], loai="anh")
    assert _truong("u1") == ["tt:ho_ten"]
    nap.thay_doi_da_xem(["u1"])
    assert _truong("u1") == [] and _truong("u2") != []
    nap.thay_doi_da_xem(None)                            # tất cả
    assert nap.thay_doi_ds() == []


# ---- endpoint ----
def test_endpoint_keo_dem_thay_doi_va_danh_sach(staging_tmp, op_headers, monkeypatch):
    nap.keo_ve_upsert([_row()])
    monkeypatch.setattr(vps_mod, "keo", lambda t, limit=200, cursor=None: [_row(ho_ten="b")] if cursor is None else [])
    monkeypatch.setattr(vps_mod, "da_xoa", lambda t, since=None: {"uuids": [], "moc": None})
    kq = client.post("/local/nap/keo", headers=op_headers).json()
    assert kq["thay_doi"] == 1
    r = client.get("/local/nap/thay-doi", headers=op_headers)
    assert r.status_code == 200 and r.json()[0]["truong"] == ["tt:ho_ten"]
    assert r.json()[0]["ho_ten"]


def test_endpoint_da_xem_va_bo_anh(staging_tmp, op_headers):
    nap.keo_ve_upsert([_row()])
    nap.nhap_luu("u1", jp2_b64="QUJD", anh_preview="UE5H")
    nap.keo_ve_upsert([_row(anh_luc="2026-11-04T09:00:00+00:00")])
    assert client.post("/local/nap/nhap/u1/bo-anh", headers=op_headers).json()["ok"] is True
    assert client.get("/local/nap/thay-doi", headers=op_headers).json() == []      # loại anh đã gỡ, hết dòng
    nap.keo_ve_upsert([_row(ho_ten="b")])
    r = client.post("/local/nap/thay-doi/da-xem", headers=op_headers, json={"tat_ca": True})
    assert r.status_code == 200
    assert client.get("/local/nap/thay-doi", headers=op_headers).json() == []


def test_endpoint_can_dang_nhap(staging_tmp):
    assert client.get("/local/nap/thay-doi").status_code == 401


# ---- sau review ocr: hai ca biên ----
def test_chi_doi_khoang_trang_noi_tt_van_co_nhan_noi_tt(staging_tmp):
    """Nơi thường trú chỉ thêm khoảng trắng: nháp địa chỉ vẫn bị reset, cảnh báo phải nêu 'Nơi thường trú' (không rỗng)."""
    nap.keo_ve_upsert([_row()])
    nap.nhap_luu("u1", dia_chi_json='{"x":1}', chi_tiet="s")
    nap.keo_ve_upsert([_row(noi_tt_raw="Xã X, Tỉnh Y ")])
    assert set(_truong()) == {"tt:noi_tt_raw", "dc_reset"}


def test_vps_khong_tra_moc_thi_giu_moc_cu(staging_tmp):
    """VPS tạm không trả anh_luc (file ảnh thiếu / bản cũ): giữ mốc đã có, để lần ảnh đổi sau vẫn bắt được."""
    nap.keo_ve_upsert([_row(anh_luc="2026-11-04T02:00:00+00:00")])
    nap.keo_ve_upsert([_row(anh_luc=None)])
    assert nap.thay_doi_ds() == []
    nap.keo_ve_upsert([_row(anh_luc="2026-11-05T01:00:00+00:00")])
    assert _truong() == ["anh"]
