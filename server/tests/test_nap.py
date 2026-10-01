"""Test HTG-02 (1/2) — endpoint operator /api/nap/* (mức 2, SQLite in-memory).

Phủ: X-Tool-Key bắt buộc, chặn vai trò, kéo pending, lock CAS nguyên tử
(hai lần lock → lần sau 409), da-nap + ma_dk, unlock, imported không kéo lại.
"""
import io
from uuid import uuid4

import pytest
from PIL import Image
from fastapi.testclient import TestClient

from app.config import get_settings

TOOL_KEY = get_settings().tool_api_key


@pytest.fixture(autouse=True)
def _anh_tmp_dir(tmp_path, monkeypatch):
    """Ghi ảnh thô vào thư mục tạm của test, không đụng anh_tho_dir thật."""
    monkeypatch.setattr(get_settings(), "anh_tho_dir", str(tmp_path / "anh-tho"))


def _anh_bytes(fmt: str = "JPEG", size=(20, 20)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (200, 180, 160)).save(buf, fmt)
    return buf.getvalue()


def _login(api: TestClient, username: str) -> dict:
    pw = {"admin1": "admin-pass", "op1": "op-pass", "col1": "col-pass"}[username]
    token = api.post("/api/auth/login", json={"username": username, "password": pw}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _op_headers(api: TestClient) -> dict:
    return {**_login(api, "op1"), "X-Tool-Key": TOOL_KEY}


def _gui_pending(api: TestClient, ho_ten: str = "A") -> str:
    """Collector gửi 1 hồ sơ pending, trả uuid."""
    u = str(uuid4())
    api.post("/api/ho-so", headers=_login(api, "col1"), json={"uuid": u, "ho_ten": ho_ten})
    return u


# ── X-Tool-Key ──
def test_thieu_tool_key_401(api):
    r = api.get("/api/nap/keo", headers=_login(api, "op1"))  # không có X-Tool-Key
    assert r.status_code == 401


def test_sai_tool_key_401(api):
    r = api.get("/api/nap/keo", headers={**_login(api, "op1"), "X-Tool-Key": "sai-key"})
    assert r.status_code == 401


def test_collector_khong_nap_duoc_403(api):
    # có X-Tool-Key đúng nhưng vai trò collector → 403
    r = api.get("/api/nap/keo", headers={**_login(api, "col1"), "X-Tool-Key": TOOL_KEY})
    assert r.status_code == 403


# ── Kéo ──
def test_keo_chi_pending(api):
    _gui_pending(api, "A")
    _gui_pending(api, "B")
    r = api.get("/api/nap/keo", headers=_op_headers(api))
    assert r.status_code == 200
    assert len(r.json()) == 2
    assert {x["ho_ten"] for x in r.json()} == {"A", "B"}


# ── Lock CAS ──
def test_lock_pending_thanh_importing(api):
    u = _gui_pending(api)
    r = api.post(f"/api/nap/{u}/lock", headers=_op_headers(api))
    assert r.status_code == 200
    assert r.json()["trang_thai"] == "importing"


def test_lock_lan_hai_409(api):
    u = _gui_pending(api)
    assert api.post(f"/api/nap/{u}/lock", headers=_op_headers(api)).status_code == 200
    r2 = api.post(f"/api/nap/{u}/lock", headers=_op_headers(api))  # đã bị khóa
    assert r2.status_code == 409


def test_lock_khong_ton_tai_404(api):
    r = api.post(f"/api/nap/{uuid4()}/lock", headers=_op_headers(api))
    assert r.status_code == 404


def test_da_lock_khong_con_trong_keo(api):
    u = _gui_pending(api)
    api.post(f"/api/nap/{u}/lock", headers=_op_headers(api))
    r = api.get("/api/nap/keo", headers=_op_headers(api))
    assert all(x["uuid"] != u for x in r.json())  # đang importing → không kéo


# ── Đã nạp ──
def test_da_nap_tu_importing(api):
    u = _gui_pending(api)
    api.post(f"/api/nap/{u}/lock", headers=_op_headers(api))
    r = api.post(f"/api/nap/{u}/da-nap", headers=_op_headers(api), json={"ma_dk": "70004K26B010001"})
    assert r.status_code == 200
    assert r.json()["trang_thai"] == "imported"
    assert r.json()["ma_dk"] == "70004K26B010001"


def test_da_nap_khi_chua_lock_409(api):
    u = _gui_pending(api)  # còn pending, chưa importing
    r = api.post(f"/api/nap/{u}/da-nap", headers=_op_headers(api), json={"ma_dk": "X"})
    assert r.status_code == 409


def test_imported_khong_keo_lai(api):
    u = _gui_pending(api)
    api.post(f"/api/nap/{u}/lock", headers=_op_headers(api))
    api.post(f"/api/nap/{u}/da-nap", headers=_op_headers(api), json={"ma_dk": "M1"})
    r = api.get("/api/nap/keo", headers=_op_headers(api))
    assert all(x["uuid"] != u for x in r.json())


# ── Mở khóa khi lỗi ──
def test_unlock_tu_importing_ve_pending(api):
    u = _gui_pending(api)
    api.post(f"/api/nap/{u}/lock", headers=_op_headers(api))
    r = api.post(f"/api/nap/{u}/unlock", headers=_op_headers(api))
    assert r.status_code == 200
    assert r.json()["trang_thai"] == "pending"
    # sau unlock, lock lại được
    assert api.post(f"/api/nap/{u}/lock", headers=_op_headers(api)).status_code == 200


def test_unlock_khi_pending_409(api):
    u = _gui_pending(api)  # chưa importing
    r = api.post(f"/api/nap/{u}/unlock", headers=_op_headers(api))
    assert r.status_code == 409


# ── Kéo trả ngày cấp CCCD (NAP-01: SP cần @p_NgayCap) ──
def test_keo_tra_ngay_cap_cccd(api):
    u = str(uuid4())
    api.post("/api/ho-so", headers=_login(api, "col1"),
             json={"uuid": u, "ho_ten": "A", "ngay_cap_cccd": "2021-03-10"})
    r = api.get("/api/nap/keo", headers=_op_headers(api))
    dong = next(x for x in r.json() if x["uuid"] == u)
    assert dong["ngay_cap_cccd"] == "2021-03-10"  # ISO; tool đổi sang yyyymmdd khi nạp


# ── Tải ảnh thô (NAP-01: tool cần ảnh để hiển thị + xử lý .jp2) ──
def test_tai_anh_khi_co_anh(api):
    u = _gui_pending(api)
    api.post(f"/api/ho-so/{u}/anh", headers=_login(api, "col1"),
             files={"file": ("a.jpg", _anh_bytes("JPEG"), "image/jpeg")})
    r = api.get(f"/api/nap/{u}/anh", headers=_op_headers(api))
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")
    assert r.content[:3] == b"\xff\xd8\xff"  # đúng JPEG đã lưu


def test_tai_anh_chua_co_404(api):
    u = _gui_pending(api)  # chưa upload ảnh
    assert api.get(f"/api/nap/{u}/anh", headers=_op_headers(api)).status_code == 404


def test_tai_anh_khong_ton_tai_404(api):
    assert api.get(f"/api/nap/{uuid4()}/anh", headers=_op_headers(api)).status_code == 404


def test_tai_anh_thieu_tool_key_401(api):
    u = _gui_pending(api)
    assert api.get(f"/api/nap/{u}/anh", headers=_login(api, "op1")).status_code == 401


def test_tai_anh_collector_403(api):
    u = _gui_pending(api)
    r = api.get(f"/api/nap/{u}/anh", headers={**_login(api, "col1"), "X-Tool-Key": TOOL_KEY})
    assert r.status_code == 403
