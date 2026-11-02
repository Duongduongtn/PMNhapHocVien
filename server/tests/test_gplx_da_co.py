"""GPLX đã có trên VPS (THU-07, TDD §10.6): kiểm dữ liệu, sửa không mất, kéo về, dọn cùng dữ liệu cá nhân."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.jobs.pii import xoa_pii_qua_han
from app.models.ho_so import HoSoThuThap
from tests.test_ho_so import _anh_tmp_dir, _login  # noqa: F401
from tests.test_nap import TOOL_KEY, _login as _login_nap

B2 = {"nhom": "cu", "hang": "B2", "so": "790000000123", "ngay_tt": "20120815", "ngay_cap": "20180427",
      "ngay_hh": "20280427", "don_vi": "70"}
A1 = {"nhom": "moi", "hang": "A1m", "so": "790000000456", "ngay_tt": "", "ngay_cap": "", "ngay_hh": "", "don_vi": ""}


def _gui(api: TestClient, **kw):
    u = str(uuid4())
    r = api.post("/api/ho-so", headers=_login(api, "col1"), json={"uuid": u, "ho_ten": "A", **kw})
    return u, r


def test_gui_va_doc_lai_o_cua_toi(api):
    u, r = _gui(api, gplx_da_co=[B2, A1])
    assert r.status_code == 201
    assert [b["hang"] for b in r.json()["gplx_da_co"]] == ["B2", "A1m"]
    ds = api.get("/api/ho-so/cua-toi", headers=_login(api, "col1")).json()
    assert next(x for x in ds if x["uuid"] == u)["gplx_da_co"][0]["so"] == "790000000123"


def test_khong_gui_la_null(api):
    _, r = _gui(api)
    assert r.json()["gplx_da_co"] is None


@pytest.mark.parametrize("sua", [
    {"hang": "Z9"}, {"hang": ""}, {"so": ""}, {"so": "1" * 21}, {"so": "12|3"},
    {"don_vi": "700"}, {"ngay_cap": "20181332"}, {"ngay_tt": "15/08/2012"}, {"nhom": "khac"},
])
def test_du_lieu_sai_422_ngay_luc_gui(api, sua):
    _, r = _gui(api, gplx_da_co=[{**B2, **sua}])
    assert r.status_code == 422


def test_qua_8_bang_hoac_vuot_100_ky_tu_422(api):
    assert _gui(api, gplx_da_co=[B2] * 9)[1].status_code == 422
    assert _gui(api, gplx_da_co=[{**B2, "so": "1" * 20}] * 8)[1].status_code == 422


def test_loi_422_khong_chep_so_gplx_vao_phan_hoi(api):
    _, r = _gui(api, gplx_da_co=[{**B2, "hang": "Z9"}])
    assert "790000000123" not in r.text


def test_sua_truong_khac_khong_lam_mat_gplx(api):
    u, _ = _gui(api, gplx_da_co=[B2])
    r = api.put(f"/api/ho-so/{u}", headers=_login(api, "col1"), json={"ho_ten": "B"})
    assert r.status_code == 200
    assert r.json()["gplx_da_co"][0]["hang"] == "B2"


def test_sua_gplx_va_xoa_het(api):
    u, _ = _gui(api, gplx_da_co=[B2])
    h = _login(api, "col1")
    assert api.put(f"/api/ho-so/{u}", headers=h, json={"gplx_da_co": [A1]}).json()["gplx_da_co"][0]["hang"] == "A1m"
    assert api.put(f"/api/ho-so/{u}", headers=h, json={"gplx_da_co": []}).json()["gplx_da_co"] in (None, [])


def test_keo_tra_kem(api):
    u, _ = _gui(api, gplx_da_co=[B2])
    ds = api.get("/api/nap/keo", headers={**_login_nap(api, "op1"), "X-Tool-Key": TOOL_KEY}).json()
    assert next(x for x in ds if x["uuid"] == u)["gplx_da_co"][0]["hang"] == "B2"


def test_xoa_mem_xoa_luon_gplx(api, db_setup):
    db, _ = db_setup
    u, _ = _gui(api, gplx_da_co=[B2])
    assert api.delete(f"/api/ho-so/{u}", headers=_login(api, "col1")).status_code == 204
    db.expire_all()
    hs = db.scalar(select(HoSoThuThap).where(HoSoThuThap.uuid == __import__("uuid").UUID(u)))
    assert hs.trang_thai == "deleted"
    assert hs.gplx_da_co is None


def test_job_30_ngay_don_ca_gplx(api, db_setup):
    db, _ = db_setup
    u, _ = _gui(api, gplx_da_co=[B2])
    uid = __import__("uuid").UUID(u)
    hs = db.scalar(select(HoSoThuThap).where(HoSoThuThap.uuid == uid))
    hs.updated_at = datetime.now(timezone.utc) - timedelta(days=40)
    hs.created_at = hs.updated_at
    db.commit()
    assert xoa_pii_qua_han(db, retention_days=30) >= 1
    db.commit()
    assert db.scalar(select(HoSoThuThap).where(HoSoThuThap.uuid == uid)) is None
