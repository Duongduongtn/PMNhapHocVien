"""Test auth HTG-01② (mức 2). Dùng SQLite in-memory, không cần PostgreSQL.

Phủ: băm/verify mật khẩu, JWT roundtrip, đăng nhập đúng/sai, /me,
logout thu hồi phiên (blocklist), chặn 403 theo vai trò, khóa tài khoản có hiệu lực ngay.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import security
from app.auth.security import (
    create_access_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db import Base, get_db
from app.main import app
from app.models.user import RefreshToken, User


@pytest.fixture
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSession()
    db.add_all([
        User(username="admin1", password_hash=hash_password("admin-pass"), ho_ten="Quản trị", vai_tro="admin"),
        User(username="op1", password_hash=hash_password("op-pass"), ho_ten="Nhân viên nạp", vai_tro="operator"),
        User(username="col1", password_hash=hash_password("col-pass"), ho_ten="Nhân viên thu nhận", vai_tro="collector"),
    ])
    db.commit()
    yield db, TestingSession
    db.close()


@pytest.fixture
def client(db_session):
    _db, TestingSession = db_session

    def override_get_db():
        s = TestingSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _login(client: TestClient, username: str, password: str):
    return client.post("/api/auth/login", json={"username": username, "password": password})


# ── Pure (không DB) ──
def test_hash_verify():
    h = hash_password("mat-khau-1")
    assert verify_password("mat-khau-1", h)
    assert not verify_password("sai", h)


def test_jwt_roundtrip():
    from uuid import uuid4
    uid = uuid4()
    token, jti, _exp = create_access_token(sub=uid, username="x", vai_tro="operator")
    payload = decode_token(token)
    assert payload["sub"] == str(uid)
    assert payload["vai_tro"] == "operator"
    assert payload["jti"] == str(jti)


# ── Đăng nhập ──
def test_login_success(client):
    r = _login(client, "admin1", "admin-pass")
    assert r.status_code == 200
    body = r.json()
    assert body["vai_tro"] == "admin"
    assert body["access_token"]
    assert "password_hash" not in body


def test_login_wrong_password(client):
    assert _login(client, "admin1", "sai").status_code == 401


def test_login_unknown_user(client):
    assert _login(client, "khong-co", "x").status_code == 401


def test_me(client):
    token = _login(client, "col1", "col-pass").json()["access_token"]
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "col1"
    assert r.json()["vai_tro"] == "collector"


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code in (401, 403)


# ── Logout thu hồi phiên ──
def test_logout_blocklist(client):
    token = _login(client, "op1", "op-pass").json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/auth/me", headers=h).status_code == 200
    assert client.post("/api/auth/logout", headers=h).status_code == 204
    # token cũ không còn dùng được
    assert client.get("/api/auth/me", headers=h).status_code == 401


# ── Phân quyền 403 (§5.3) ──
def test_collector_cannot_create_user(client):
    token = _login(client, "col1", "col-pass").json()["access_token"]
    r = client.post("/api/admin/users", headers={"Authorization": f"Bearer {token}"},
                    json={"username": "x", "password": "y", "vai_tro": "collector"})
    assert r.status_code == 403


def test_operator_cannot_create_user(client):
    token = _login(client, "op1", "op-pass").json()["access_token"]
    r = client.post("/api/admin/users", headers={"Authorization": f"Bearer {token}"},
                    json={"username": "x", "password": "y", "vai_tro": "collector"})
    assert r.status_code == 403


def test_admin_creates_user_and_dup_conflict(client):
    token = _login(client, "admin1", "admin-pass").json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/admin/users", headers=h, json={"username": "nv-moi", "password": "pw", "vai_tro": "operator"})
    assert r.status_code == 201
    assert r.json()["vai_tro"] == "operator"
    # trùng username
    r2 = client.post("/api/admin/users", headers=h, json={"username": "nv-moi", "password": "pw", "vai_tro": "operator"})
    assert r2.status_code == 409


def test_create_user_invalid_role(client):
    token = _login(client, "admin1", "admin-pass").json()["access_token"]
    r = client.post("/api/admin/users", headers={"Authorization": f"Bearer {token}"},
                    json={"username": "z", "password": "pw", "vai_tro": "sieu-nhan"})
    assert r.status_code == 422


# ── Refresh token — phiên tool vĩnh viễn (DGT-04) ──
def _login_tool(client: TestClient, username: str, password: str):
    """Đăng nhập QUA TOOL (cap_refresh=True) → nhận cả refresh token."""
    return client.post("/api/auth/login",
                       json={"username": username, "password": password, "cap_refresh": True})


def test_login_cap_refresh_tra_refresh_token(client):
    body = _login_tool(client, "op1", "op-pass").json()
    assert body["access_token"]
    assert body["refresh_token"]   # có vì cap_refresh=True


def test_login_web_khong_co_refresh_token(client):
    body = _login(client, "op1", "op-pass").json()   # web, không cap_refresh
    assert body["refresh_token"] is None


def test_refresh_luu_hash_khong_plaintext(client, db_session):
    db, _ = db_session
    rt = _login_tool(client, "op1", "op-pass").json()["refresh_token"]
    row = db.scalar(select(RefreshToken))
    assert row.token_hash != rt                       # không lưu plaintext
    assert row.token_hash == hash_refresh_token(rt)   # lưu đúng sha256 hex
    assert len(row.token_hash) == 64


def test_refresh_xoay_cap_token_moi(client):
    rt = _login_tool(client, "op1", "op-pass").json()["refresh_token"]
    r = client.post("/api/auth/refresh", json={"refresh_token": rt})
    assert r.status_code == 200
    out = r.json()
    assert out["access_token"]
    assert out["refresh_token"] and out["refresh_token"] != rt   # xoay → token mới
    # token mới dùng được tiếp
    assert client.post("/api/auth/refresh", json={"refresh_token": out["refresh_token"]}).status_code == 200


def test_refresh_trong_an_han_retry_mang_ok(client):
    """Gọi lại token vừa xoay NGAY (trong ân hạn) → coi là retry mạng, vẫn cấp token mới."""
    rt = _login_tool(client, "op1", "op-pass").json()["refresh_token"]
    assert client.post("/api/auth/refresh", json={"refresh_token": rt}).status_code == 200
    # rt đã bị đánh dấu dùng, nhưng gọi lại ngay (grace 60s) → vẫn 200
    r2 = client.post("/api/auth/refresh", json={"refresh_token": rt})
    assert r2.status_code == 200


def test_refresh_replay_qua_an_han_thu_hoi_chuoi(client, monkeypatch):
    """Dùng lại token đã xoay SAU ân hạn → replay thật → thu hồi toàn bộ chuỗi."""
    monkeypatch.setattr(security, "REFRESH_GRACE_SECONDS", 0)   # ép quá ân hạn ngay
    rt = _login_tool(client, "op1", "op-pass").json()["refresh_token"]
    moi = client.post("/api/auth/refresh", json={"refresh_token": rt}).json()["refresh_token"]
    # dùng lại token cũ → replay → 401
    assert client.post("/api/auth/refresh", json={"refresh_token": rt}).status_code == 401
    # cả token mới cũng bị thu hồi theo chuỗi
    assert client.post("/api/auth/refresh", json={"refresh_token": moi}).status_code == 401


def test_refresh_token_sai(client):
    assert client.post("/api/auth/refresh", json={"refresh_token": "khong-ton-tai"}).status_code == 401


def test_refresh_tai_khoan_bi_khoa(client, db_session):
    db, _ = db_session
    rt = _login_tool(client, "op1", "op-pass").json()["refresh_token"]
    u = db.scalar(select(User).where(User.username == "op1"))
    u.is_active = False
    db.commit()
    assert client.post("/api/auth/refresh", json={"refresh_token": rt}).status_code == 401


def test_logout_thu_hoi_refresh(client):
    body = _login_tool(client, "op1", "op-pass").json()
    h = {"Authorization": f"Bearer {body['access_token']}"}
    assert client.post("/api/auth/logout", headers=h,
                       json={"refresh_token": body["refresh_token"]}).status_code == 204
    # refresh token của phiên không còn dùng được
    assert client.post("/api/auth/refresh", json={"refresh_token": body["refresh_token"]}).status_code == 401


def test_doi_mat_khau_thu_hoi_toan_bo_refresh(client):
    body = _login_tool(client, "op1", "op-pass").json()
    h = {"Authorization": f"Bearer {body['access_token']}"}
    r = client.post("/api/auth/doi-mat-khau", headers=h,
                    json={"mat_khau_hien_tai": "op-pass", "mat_khau_moi": "op-pass-moi"})
    assert r.status_code == 204
    # đổi mật khẩu → mọi refresh token bị đá
    assert client.post("/api/auth/refresh", json={"refresh_token": body["refresh_token"]}).status_code == 401


# ── Khóa/đổi vai trò có hiệu lực ngay (đọc từ DB, không tin claim) ──
def test_deactivated_user_rejected_immediately(client, db_session):
    db, _ = db_session
    token = _login(client, "op1", "op-pass").json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/auth/me", headers=h).status_code == 200
    # admin khóa tài khoản op1
    u = db.scalar(select(User).where(User.username == "op1"))
    u.is_active = False
    db.commit()
    # token cũ còn hạn nhưng bị từ chối ngay
    assert client.get("/api/auth/me", headers=h).status_code == 401
