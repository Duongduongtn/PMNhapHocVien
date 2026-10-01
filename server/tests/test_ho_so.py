"""Test HTG-02 (1/2) — endpoint collector: gửi/sửa/ảnh (mức 2, SQLite in-memory).

Phủ: gửi hồ sơ, idempotent theo uuid, chặn vai trò, quyền sở hữu (IDOR),
sửa khi pending, validate ảnh (magic-byte, kích thước, số điểm ảnh).
"""
import io
from uuid import UUID, uuid4

import pytest
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.config import get_settings
from app.models.ho_so import HoSoThuThap


@pytest.fixture(autouse=True)
def _anh_tmp_dir(tmp_path, monkeypatch):
    """Ghi ảnh thô vào thư mục tạm của test, không đụng anh_tho_dir thật."""
    monkeypatch.setattr(get_settings(), "anh_tho_dir", str(tmp_path / "anh-tho"))


def _login(api: TestClient, username: str, password: str = None) -> dict:
    pw = password or ("admin-pass" if username == "admin1" else ("op-pass" if username == "op1" else "col-pass"))
    token = api.post("/api/auth/login", json={"username": username, "password": pw}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _anh_bytes(fmt: str = "JPEG", size=(20, 20)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (200, 180, 160)).save(buf, fmt)
    return buf.getvalue()


# ── Gửi hồ sơ + idempotent ──
def test_collector_gui_ho_so(api):
    h = _login(api, "col1")
    u = str(uuid4())
    r = api.post("/api/ho-so", headers=h, json={"uuid": u, "ho_ten": "Nguyễn Văn A", "so_cccd": "012345678901"})
    assert r.status_code == 201  # tạo mới (TDD §4.7)
    assert r.json()["trang_thai"] == "pending"
    assert r.json()["ho_ten"] == "Nguyễn Văn A"
    assert r.json()["co_anh"] is False


def test_gui_idempotent_cung_uuid(api, db_setup):
    db, _ = db_setup
    h = _login(api, "col1")
    u = str(uuid4())
    r1 = api.post("/api/ho-so", headers=h, json={"uuid": u, "ho_ten": "A"})
    r2 = api.post("/api/ho-so", headers=h, json={"uuid": u, "ho_ten": "A"})  # gửi lại (mất mạng → thử lại)
    assert r1.status_code == 201  # tạo mới
    assert r2.status_code == 200  # gửi lại cùng uuid → 200, không tạo trùng (TDD §4.7)
    assert db.scalar(select(func.count()).select_from(HoSoThuThap)) == 1  # không nhân đôi


def test_uuid_nguoi_khac_dung_409(api):
    u = str(uuid4())
    api.post("/api/ho-so", headers=_login(api, "col1"), json={"uuid": u, "ho_ten": "A"})
    r = api.post("/api/ho-so", headers=_login(api, "col2"), json={"uuid": u, "ho_ten": "B"})
    assert r.status_code == 409


def test_operator_khong_gui_duoc(api):
    r = api.post("/api/ho-so", headers=_login(api, "op1"), json={"uuid": str(uuid4()), "ho_ten": "A"})
    assert r.status_code == 403


def test_gioi_tinh_sai_422(api):
    r = api.post("/api/ho-so", headers=_login(api, "col1"), json={"uuid": str(uuid4()), "gioi_tinh": "X"})
    assert r.status_code == 422


# ── Xem của mình ──
def test_cua_toi_chi_thay_cua_minh(api):
    api.post("/api/ho-so", headers=_login(api, "col1"), json={"uuid": str(uuid4()), "ho_ten": "A1"})
    api.post("/api/ho-so", headers=_login(api, "col2"), json={"uuid": str(uuid4()), "ho_ten": "B1"})
    r = api.get("/api/ho-so/cua-toi", headers=_login(api, "col1"))
    assert r.status_code == 200
    assert [x["ho_ten"] for x in r.json()] == ["A1"]


# ── Sửa khi pending + quyền sở hữu ──
def test_sua_pending(api):
    h = _login(api, "col1")
    u = str(uuid4())
    api.post("/api/ho-so", headers=h, json={"uuid": u, "ho_ten": "A"})
    r = api.put(f"/api/ho-so/{u}", headers=h, json={"ho_ten": "Nguyễn Thị B"})
    assert r.status_code == 200
    assert r.json()["ho_ten"] == "Nguyễn Thị B"


def test_sua_ho_so_nguoi_khac_404(api):
    u = str(uuid4())
    api.post("/api/ho-so", headers=_login(api, "col1"), json={"uuid": u, "ho_ten": "A"})
    r = api.put(f"/api/ho-so/{u}", headers=_login(api, "col2"), json={"ho_ten": "X"})
    assert r.status_code == 404  # không lộ hồ sơ của người khác


def test_sua_khi_da_importing_409(api, db_setup):
    db, _ = db_setup
    h = _login(api, "col1")
    u = str(uuid4())
    api.post("/api/ho-so", headers=h, json={"uuid": u, "ho_ten": "A"})
    hs = db.get(HoSoThuThap, UUID(u))
    hs.trang_thai = "importing"
    db.commit()
    r = api.put(f"/api/ho-so/{u}", headers=h, json={"ho_ten": "X"})
    assert r.status_code == 409


# ── Upload ảnh (TDD §7.4) ──
def test_upload_anh_jpeg_ok(api):
    h = _login(api, "col1")
    u = str(uuid4())
    api.post("/api/ho-so", headers=h, json={"uuid": u, "ho_ten": "A"})
    r = api.post(f"/api/ho-so/{u}/anh", headers=h, files={"file": ("a.jpg", _anh_bytes("JPEG"), "image/jpeg")})
    assert r.status_code == 200
    assert r.json()["co_anh"] is True


def test_upload_khong_phai_anh_400(api):
    h = _login(api, "col1")
    u = str(uuid4())
    api.post("/api/ho-so", headers=h, json={"uuid": u, "ho_ten": "A"})
    # gửi nội dung PDF nhưng đặt tên .jpg — magic-byte phải bắt
    r = api.post(f"/api/ho-so/{u}/anh", headers=h, files={"file": ("a.jpg", b"%PDF-1.4 fake", "image/jpeg")})
    assert r.status_code == 400


def test_upload_vuot_kich_thuoc_400(api, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_anh_bytes", 10)  # hạ giới hạn để test
    h = _login(api, "col1")
    u = str(uuid4())
    api.post("/api/ho-so", headers=h, json={"uuid": u, "ho_ten": "A"})
    r = api.post(f"/api/ho-so/{u}/anh", headers=h, files={"file": ("a.jpg", _anh_bytes("JPEG"), "image/jpeg")})
    assert r.status_code == 400


def test_upload_qua_nhieu_diem_anh_400(api, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_anh_pixels", 1)  # ảnh 20x20 vượt ngay → chặn bung nén
    h = _login(api, "col1")
    u = str(uuid4())
    api.post("/api/ho-so", headers=h, json={"uuid": u, "ho_ten": "A"})
    r = api.post(f"/api/ho-so/{u}/anh", headers=h, files={"file": ("a.png", _anh_bytes("PNG"), "image/png")})
    assert r.status_code == 400


def test_upload_ho_so_nguoi_khac_404(api):
    u = str(uuid4())
    api.post("/api/ho-so", headers=_login(api, "col1"), json={"uuid": u, "ho_ten": "A"})
    r = api.post(f"/api/ho-so/{u}/anh", headers=_login(api, "col2"), files={"file": ("a.jpg", _anh_bytes(), "image/jpeg")})
    assert r.status_code == 404
