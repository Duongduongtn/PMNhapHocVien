"""QLY-09 — đối soát VPS↔CSDT (mức 2, không cần DB/VPS thật).

Mock `sqlserver_cursor` (đọc CSDT) + lớp `vps` (gọi máy chủ). Phủ: ca ② theo khóa,
ca ①③ quét lạc, 3 action, phân quyền admin, và phòng tuyến 2 (nap_fn bỏ da_nap vé cũ).
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app import session as _session
from app import nap as nap_mod
from app import vps as vps_mod
from app.main import app
from app.routers import doisoat as ds

client = TestClient(app)


class _FakeCur:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, sql, params=None):
        pass

    def fetchall(self):
        return self._rows


class _FakeCM:
    def __init__(self, rows):
        self._cur = _FakeCur(rows)

    def __enter__(self):
        return self._cur

    def __exit__(self, *a):
        return False


def _headers(vai_tro: str):
    token = f"test-ds-{vai_tro}"
    _session._phien_theo_token[token] = _session.Phien(
        username=f"{vai_tro}-test", ho_ten="NV", vai_tro=vai_tro, vps_token="jwt-vps"
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def op_h():
    h = _headers("operator")
    yield h
    _session._phien_theo_token.clear()


@pytest.fixture
def admin_h():
    h = _headers("admin")
    yield h
    _session._phien_theo_token.clear()


# ---- Gác phiên / quyền --------------------------------------------------------
def test_doi_soat_chua_dang_nhap_401():
    assert client.get("/local/doi-soat/khoa?ma_kh=K1").status_code == 401
    assert client.get("/local/doi-soat/lac").status_code == 401


def test_quet_lac_operator_bi_chan_403(op_h):
    assert client.get("/local/doi-soat/lac", headers=op_h).status_code == 403


def test_tra_ve_mo_khoa_operator_bi_chan_403(op_h):
    assert client.post("/local/doi-soat/tra-ve?uuid=u1", headers=op_h).status_code == 403
    assert client.post("/local/doi-soat/mo-khoa?uuid=u1", headers=op_h).status_code == 403


# ---- Ca ② theo khóa -----------------------------------------------------------
def test_ca2_theo_khoa(op_h, monkeypatch):
    # CSDT khóa K1 có 3 HV: M1 (uuid u1, VPS imported → KHỚP), M2 (uuid u2, VPS importing → ca ②),
    # M3 (không tra được uuid → khong_tra_duoc).
    monkeypatch.setattr(ds, "sqlserver_cursor",
                        lambda *a, **k: _FakeCM([{"ma_dk": "M1", "ho_ten": "A"},
                                                 {"ma_dk": "M2", "ho_ten": "B"},
                                                 {"ma_dk": "M3", "ho_ten": "C"}]))
    monkeypatch.setattr(nap_mod, "lay_uuid_theo_ma_dk",
                        lambda ma_dk: {"M1": "u1", "M2": "u2"}.get(ma_dk))
    monkeypatch.setattr(vps_mod, "trang_thai_nhieu", lambda token, uuids: {
        "u1": {"uuid": "u1", "trang_thai": "imported", "ma_dk": "M1"},
        "u2": {"uuid": "u2", "trang_thai": "importing", "ma_dk": "M2"},
    })
    r = client.get("/local/doi-soat/khoa?ma_kh=K1", headers=op_h)
    assert r.status_code == 200
    d = r.json()
    assert [x["ma_dk"] for x in d["ca2"]] == ["M2"]       # chỉ M2 lệch (chưa imported)
    assert d["ca2"][0]["hanh_dong"] == "da_nap"
    assert {x["ma_dk"] for x in d["khong_tra_duoc"]} == {"M3"}  # M3 thiếu uuid


def test_ca2_vps_khong_con_ban_ghi_vao_khong_tra_duoc(op_h, monkeypatch):
    # Có uuid nhưng VPS đã dọn PII (trang_thai_nhieu không trả) → khong_tra_duoc, KHÔNG báo ca ②.
    monkeypatch.setattr(ds, "sqlserver_cursor",
                        lambda *a, **k: _FakeCM([{"ma_dk": "M1", "ho_ten": "A"}]))
    monkeypatch.setattr(nap_mod, "lay_uuid_theo_ma_dk", lambda ma_dk: "u1")
    monkeypatch.setattr(vps_mod, "trang_thai_nhieu", lambda token, uuids: {})  # VPS rỗng
    d = client.get("/local/doi-soat/khoa?ma_kh=K1", headers=op_h).json()
    assert d["ca2"] == []
    assert d["khong_tra_duoc"][0]["ma_dk"] == "M1"


# ---- Ca ①③ quét lạc -----------------------------------------------------------
def test_quet_lac_phantom_va_treo(admin_h, monkeypatch):
    cu = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()   # treo
    moi = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()   # đang nạp thật
    def fake_admin(token, trang_thai=None, limit=500, offset=0):
        if trang_thai == "imported":
            return {"items": [{"uuid": "p1", "ma_dk": "MX", "ho_ten": "Phantom"},   # CSDT KHÔNG có
                              {"uuid": "ok", "ma_dk": "MOK", "ho_ten": "That"}],      # CSDT CÓ
                    "total": 2}
        return {"items": [{"uuid": "t1", "locked_at": cu, "ho_ten": "Treo"},          # quá ngưỡng
                          {"uuid": "t2", "locked_at": moi, "ho_ten": "DangNap"}],      # mới → bỏ qua
                "total": 2}
    monkeypatch.setattr(vps_mod, "admin_ho_so", fake_admin)
    monkeypatch.setattr(ds, "sqlserver_cursor", lambda *a, **k: _FakeCM([{"MaDK": "MOK"}]))  # chỉ MOK có thật
    d = client.get("/local/doi-soat/lac", headers=admin_h).json()
    assert [x["uuid"] for x in d["phantom"]] == ["p1"]   # MX không có trong CSDT = phantom
    assert [x["uuid"] for x in d["treo"]] == ["t1"]      # chỉ dòng importing quá 15'


# ---- 3 action -----------------------------------------------------------------
def test_action_da_nap(op_h, monkeypatch):
    goi = {}
    monkeypatch.setattr(vps_mod, "da_nap", lambda token, uuid, ma_dk: goi.update(uuid=uuid, ma_dk=ma_dk))
    r = client.post("/local/doi-soat/da-nap?uuid=u1&ma_dk=M1", headers=op_h)
    assert r.status_code == 200 and goi == {"uuid": "u1", "ma_dk": "M1"}


def test_action_tra_ve_goi_vps_va_staging(admin_h, monkeypatch):
    goi = []
    monkeypatch.setattr(vps_mod, "tra_ve_cho_nap", lambda token, uuid: goi.append(("vps", uuid)))
    monkeypatch.setattr(nap_mod, "keo_ve_ve_cho", lambda uuid: goi.append(("staging", uuid)))
    r = client.post("/local/doi-soat/tra-ve?uuid=p1", headers=admin_h)
    assert r.status_code == 200
    assert ("vps", "p1") in goi and ("staging", "p1") in goi  # cả VPS lẫn staging


def test_action_mo_khoa(admin_h, monkeypatch):
    goi = {}
    monkeypatch.setattr(vps_mod, "unlock", lambda token, uuid: goi.update(uuid=uuid))
    r = client.post("/local/doi-soat/mo-khoa?uuid=t1", headers=admin_h)
    assert r.status_code == 200 and goi == {"uuid": "t1"}


# ---- Hàm thuần: ngưỡng treo ---------------------------------------------------
def test_qua_nguong():
    assert ds._qua_nguong((datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()) is True
    assert ds._qua_nguong((datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()) is False
    assert ds._qua_nguong(None) is False
    assert ds._qua_nguong("rác-không-parse-được") is False
