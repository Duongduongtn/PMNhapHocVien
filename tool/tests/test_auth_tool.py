"""HTG-01③ — Đăng nhập tool qua VPS + session cục bộ (mức 2, mock httpx).

Tool không tự verify JWT: gọi VPS /api/auth/login thay mặt (option A) rồi phát
session token cục bộ cho /local/*. Chỉ operator/admin dùng được tool (collector 403).
Test mock httpx để không cần VPS thật. Chỉ assert status code + trường dữ liệu,
KHÔNG assert chuỗi thông báo (tránh gãy khi sửa text).
"""
import httpx
import pytest
from fastapi.testclient import TestClient

from app import session
from app.main import app

client = TestClient(app)


class FakeResp:
    def __init__(self, status: int, payload: dict | None = None):
        self.status_code = status
        self._payload = payload or {}

    def json(self):
        return self._payload


@pytest.fixture
def mock_vps(monkeypatch):
    """Trả về hàm cấu hình phản hồi VPS giả cho một test."""

    def _setup(*, status=200, payload=None, vps_url="http://vps.test", raise_net=False):
        monkeypatch.setattr(
            session.config_store, "load_config", lambda: ({"vps_url": vps_url} if vps_url else {})
        )

        def fake_post(url, json=None, timeout=None):
            if raise_net:
                raise httpx.ConnectError("không tới được")
            return FakeResp(status, payload)

        monkeypatch.setattr(session.httpx, "post", fake_post)

    return _setup


def _login(username="op1", password="x"):
    return client.post("/local/auth/login", json={"username": username, "password": password})


# ── Đăng nhập theo vai trò ──
def test_operator_dang_nhap(mock_vps):
    mock_vps(status=200, payload={"username": "op1", "ho_ten": "NV Nạp", "vai_tro": "operator"})
    r = _login()
    assert r.status_code == 200
    assert r.json()["session_token"]
    assert r.json()["vai_tro"] == "operator"


def test_admin_dang_nhap(mock_vps):
    mock_vps(status=200, payload={"username": "ad1", "ho_ten": "Quản trị", "vai_tro": "admin"})
    r = _login("ad1")
    assert r.status_code == 200
    assert r.json()["session_token"]
    assert r.json()["vai_tro"] == "admin"


def test_collector_bi_chan_403(mock_vps):
    # VPS xác thực OK nhưng vai trò collector → tool chặn (không nạp DB).
    mock_vps(status=200, payload={"username": "col1", "ho_ten": "Thu nhận", "vai_tro": "collector"})
    assert _login("col1").status_code == 403


# ── Lỗi đăng nhập ──
def test_sai_mat_khau_401(mock_vps):
    mock_vps(status=401)
    assert _login().status_code == 401


def test_chua_cau_hinh_vps_400(mock_vps):
    mock_vps(vps_url="")  # vps_url rỗng → chặn trước khi gọi VPS
    assert _login().status_code == 400


def test_vps_khong_toi_duoc_502(mock_vps):
    mock_vps(raise_net=True)
    assert _login().status_code == 502


def test_vps_tra_500_thanh_502(mock_vps):
    # VPS maintenance/nginx lỗi (status ngoài {200,401}) → tool coi là 502.
    mock_vps(status=500)
    assert _login().status_code == 502


# ── Session dùng được / thu hồi ──
def test_me_voi_session_hop_le(mock_vps):
    mock_vps(status=200, payload={"username": "op1", "ho_ten": "NV Nạp", "vai_tro": "operator"})
    tok = _login().json()["session_token"]
    r = client.get("/local/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    assert r.json()["username"] == "op1"
    assert r.json()["vai_tro"] == "operator"
    assert "ho_ten" in r.json()


def test_me_thieu_header_bi_chan():
    # Thiếu Authorization → HTTPBearer(auto_error=True) chặn (phiên bản này trả 401;
    # bản khác có thể 403). Điều cần đảm bảo: KHÔNG vào được, không phải con số chính xác.
    assert client.get("/local/auth/me").status_code in (401, 403)


def test_logout_thu_hoi_session(mock_vps):
    mock_vps(status=200, payload={"username": "op1", "ho_ten": None, "vai_tro": "operator"})
    tok = _login().json()["session_token"]
    h = {"Authorization": f"Bearer {tok}"}
    assert client.get("/local/auth/me", headers=h).status_code == 200
    assert client.post("/local/auth/logout", headers=h).status_code == 204
    assert client.get("/local/auth/me", headers=h).status_code == 401  # token cũ hết hiệu lực
