"""NAP-01 (phần ①) — kéo hàng đợi VPS → staging + nạp lô (mức 2).

Phủ:
- iso_to_yyyymmdd: đổi ngày cấp CCCD ISO → yyyymmdd (SP cần varchar(8)).
- staging keo_ve: upsert dedup theo uuid, danh sách, cập nhật trạng thái.
- /local/nap/keo: gọi VPS (mock) → ghi staging; VPS lỗi → 502.
- /local/nap/keo/{uuid}/anh: proxy ảnh từ VPS (mock); chưa có ảnh → 404.
- /local/nap/nap-lo: lock→nạp→da-nap mỗi HV; 1 HV lỗi không hỏng lô + mở khóa lại.

Mock lớp VPS (app.vps) và lõi nạp (_nap_mot) để không cần VPS/SQL Server thật.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import nap, session
from app import vps as vps_mod
from app.main import app
from app.routers import nap as nap_router
from app.vps import VpsLoi

client = TestClient(app)


# ---- Fixtures ----------------------------------------------------------------
@pytest.fixture
def staging_tmp(tmp_path, monkeypatch):
    """Dời staging.sqlite sang thư mục tạm — không đụng staging thật của máy."""
    monkeypatch.setattr(nap, "ORPHAN_DB", tmp_path / "staging.sqlite")


@pytest.fixture
def op_headers(monkeypatch):
    """Phiên operator có vps_token (khác auth_headers mặc định — cần cho /keo, /nap-lo)."""
    token = "test-keo-token"
    session._phien_theo_token[token] = session.Phien(
        username="op-test", ho_ten="NV Nạp", vai_tro="operator", vps_token="jwt-vps-gia"
    )
    yield {"Authorization": f"Bearer {token}"}
    session._phien_theo_token.pop(token, None)


def _keo_row(uuid: str, **kw) -> dict:
    row = {
        "uuid": uuid, "so_cccd": "012345678901", "so_cmnd_cu": None,
        "ho_ten": "nguyễn văn a", "ngay_sinh": "20000101", "gioi_tinh": "M",
        "noi_tt_raw": "Xã X, Tỉnh Y", "ngay_cap_cccd": "2021-03-10",
        "noi_cap_cccd": "Cục CS", "co_anh": True, "created_at": "2026-10-01T08:00:00+00:00",
    }
    row.update(kw)
    return row


def _nap_item(uuid: str) -> dict:
    """1 HV đã được UI chuẩn bị đủ (payload NapIn)."""
    return {
        "uuid": uuid, "ma_khoa_hoc": "70004K26B010", "ho_ten": "NGUYỄN VĂN A",
        "ngay_sinh": "20000101", "gioi_tinh": "M", "so_cmt": "012345678901",
        "noi_tt_ma_dvhc": "26998", "noi_tt_ma_dvql": "26",
    }


# ---- Hàm thuần ---------------------------------------------------------------
def test_iso_to_yyyymmdd():
    assert nap.iso_to_yyyymmdd("2021-03-10") == "20210310"
    assert nap.iso_to_yyyymmdd("20210310") == "20210310"
    assert nap.iso_to_yyyymmdd(None) == ""
    assert nap.iso_to_yyyymmdd("") == ""
    assert nap.iso_to_yyyymmdd("2021") == ""  # thiếu ngày/tháng → bỏ, không đoán


# ---- staging keo_ve ----------------------------------------------------------
def test_keo_ve_upsert_dedup(staging_tmp):
    n1 = nap.keo_ve_upsert([_keo_row("u1"), _keo_row("u2")])
    assert n1 == 2
    n2 = nap.keo_ve_upsert([_keo_row("u2"), _keo_row("u3")])  # u2 trùng → bỏ qua
    assert n2 == 1
    ds = nap.keo_ve_danh_sach()
    assert {r["uuid"] for r in ds} == {"u1", "u2", "u3"}


def test_keo_ve_upsert_doi_ngay_cap(staging_tmp):
    nap.keo_ve_upsert([_keo_row("u1", ngay_cap_cccd="2021-03-10")])
    r = nap.keo_ve_danh_sach()[0]
    assert r["ngay_cap"] == "20210310"  # đã đổi ISO → yyyymmdd
    assert r["trang_thai"] == "cho"


def test_keo_ve_cap_nhat(staging_tmp):
    nap.keo_ve_upsert([_keo_row("u1")])
    nap.keo_ve_cap_nhat("u1", trang_thai="xong", ma_dk="70004K26B010001", so_ho_so="056")
    r = nap.keo_ve_danh_sach()[0]
    assert r["trang_thai"] == "xong"
    assert r["ma_dk"] == "70004K26B010001"
    assert r["so_ho_so"] == "056"


# ---- /local/nap/keo ----------------------------------------------------------
def test_keo_ghi_staging(staging_tmp, op_headers, monkeypatch):
    goi = {"n": 0}

    def fake_keo(token, limit=200, cursor=None):
        goi["n"] += 1
        return [_keo_row("u1"), _keo_row("u2")] if goi["n"] == 1 else []

    monkeypatch.setattr(vps_mod, "keo", fake_keo)
    r = client.post("/local/nap/keo", headers=op_headers)
    assert r.status_code == 200
    assert r.json() == {"keo_ve": 2, "tong": 2}
    assert len(nap.keo_ve_danh_sach()) == 2


def test_keo_vps_loi_502(staging_tmp, op_headers, monkeypatch):
    def fake_keo(token, limit=200, cursor=None):
        raise VpsLoi("VPS sập", 500)

    monkeypatch.setattr(vps_mod, "keo", fake_keo)
    assert client.post("/local/nap/keo", headers=op_headers).status_code == 502


def test_keo_chua_dang_nhap_401(staging_tmp):
    assert client.post("/local/nap/keo").status_code in (401, 403)


def test_danh_sach(staging_tmp, op_headers):
    nap.keo_ve_upsert([_keo_row("u1")])
    r = client.get("/local/nap/danh-sach", headers=op_headers)
    assert r.status_code == 200
    assert r.json()[0]["uuid"] == "u1"


# ---- /local/nap/keo/{uuid}/anh ----------------------------------------------
def test_tai_anh_proxy(op_headers, monkeypatch):
    monkeypatch.setattr(vps_mod, "tai_anh", lambda token, uuid: b"\xff\xd8\xff\xe0abc")
    r = client.get("/local/nap/keo/u1/anh", headers=op_headers)
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/jpeg"
    assert r.content[:3] == b"\xff\xd8\xff"


def test_tai_anh_chua_co_404(op_headers, monkeypatch):
    monkeypatch.setattr(vps_mod, "tai_anh", lambda token, uuid: None)
    assert client.get("/local/nap/keo/u1/anh", headers=op_headers).status_code == 404


# ---- /local/nap/nap-lo -------------------------------------------------------
def test_nap_lo_thanh_cong(staging_tmp, op_headers, monkeypatch):
    nap.keo_ve_upsert([_keo_row("u1"), _keo_row("u2")])
    monkeypatch.setattr(vps_mod, "lock", lambda t, u: None)
    monkeypatch.setattr(vps_mod, "da_nap", lambda t, u, ma_dk: None)
    monkeypatch.setattr(vps_mod, "unlock", lambda t, u: None)
    monkeypatch.setattr(
        nap_router, "_nap_mot",
        lambda body: {"ma_dk": f"MDK-{body.uuid}", "so_ho_so": "056", "so_giay_to": 3},
    )
    r = client.post("/local/nap/nap-lo", headers=op_headers,
                    json={"items": [_nap_item("u1"), _nap_item("u2")]})
    assert r.status_code == 200
    kq = r.json()
    assert kq["tong"] == 2 and kq["thanh_cong"] == 2 and kq["that_bai"] == 0
    # staging cập nhật 'xong'
    tt = {x["uuid"]: x["trang_thai"] for x in nap.keo_ve_danh_sach()}
    assert tt == {"u1": "xong", "u2": "xong"}


def test_nap_lo_mot_loi_khong_hong_lo(staging_tmp, op_headers, monkeypatch):
    nap.keo_ve_upsert([_keo_row("u1"), _keo_row("u2")])
    mo_khoa = []
    monkeypatch.setattr(vps_mod, "lock", lambda t, u: None)
    monkeypatch.setattr(vps_mod, "da_nap", lambda t, u, ma_dk: None)
    monkeypatch.setattr(vps_mod, "unlock", lambda t, u: mo_khoa.append(u))

    def fake_nap(body):
        if body.uuid == "u1":
            raise ValueError("CCCD/CMND đã có học viên trong khóa")
        return {"ma_dk": "MDK-u2", "so_ho_so": "056", "so_giay_to": 3}

    monkeypatch.setattr(nap_router, "_nap_mot", fake_nap)
    r = client.post("/local/nap/nap-lo", headers=op_headers,
                    json={"items": [_nap_item("u1"), _nap_item("u2")]})
    kq = r.json()
    assert kq["thanh_cong"] == 1 and kq["that_bai"] == 1
    tt = {x["uuid"]: x for x in nap.keo_ve_danh_sach()}
    assert tt["u1"]["trang_thai"] == "loi"
    assert "đã có học viên" in tt["u1"]["loi"]
    assert tt["u2"]["trang_thai"] == "xong"
    assert mo_khoa == ["u1"]  # HV lỗi được mở khóa lại trên VPS


def test_nap_lo_lock_409_ghi_loi(staging_tmp, op_headers, monkeypatch):
    nap.keo_ve_upsert([_keo_row("u1")])
    monkeypatch.setattr(vps_mod, "lock", lambda t, u: (_ for _ in ()).throw(VpsLoi("đang nạp", 409)))
    monkeypatch.setattr(vps_mod, "da_nap", lambda t, u, ma_dk: None)
    unlock_goi = []
    monkeypatch.setattr(vps_mod, "unlock", lambda t, u: unlock_goi.append(u))
    monkeypatch.setattr(nap_router, "_nap_mot", lambda body: {"ma_dk": "X", "so_ho_so": "1", "so_giay_to": 0})
    r = client.post("/local/nap/nap-lo", headers=op_headers, json={"items": [_nap_item("u1")]})
    kq = r.json()
    assert kq["that_bai"] == 1
    assert unlock_goi == []  # lock thất bại → KHÔNG mở khóa (không phải mình khóa)
    assert nap.keo_ve_danh_sach()[0]["trang_thai"] == "loi"
