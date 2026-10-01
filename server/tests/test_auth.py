"""Test auth HTG-01② (mức 2). Dùng SQLite in-memory, không cần PostgreSQL.

Phủ: băm/verify mật khẩu, JWT roundtrip, đăng nhập đúng/sai, /me,
logout thu hồi phiên (blocklist), chặn 403 theo vai trò, khóa tài khoản có hiệu lực ngay.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.security import create_access_token, decode_token, hash_password, verify_password
from app.db import Base, get_db
from app.main import app
from app.models.user import User


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
