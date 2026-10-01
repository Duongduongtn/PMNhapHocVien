import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.security import hash_password
from app.db import Base, get_db
from app.main import app
from app.models import ho_so as _ho_so  # noqa: F401 — nạp bảng ho_so_thu_thap/audit_log vào Base.metadata
from app.models.user import User


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def db_setup():
    """SQLite in-memory + seed 3 vai trò — không cần PostgreSQL (mẫu task 14)."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSession()
    db.add_all([
        User(username="admin1", password_hash=hash_password("admin-pass"), ho_ten="Quản trị", vai_tro="admin"),
        User(username="op1", password_hash=hash_password("op-pass"), ho_ten="Nhân viên nạp", vai_tro="operator"),
        User(username="col1", password_hash=hash_password("col-pass"), ho_ten="Thu nhận 1", vai_tro="collector"),
        User(username="col2", password_hash=hash_password("col-pass"), ho_ten="Thu nhận 2", vai_tro="collector"),
    ])
    db.commit()
    yield db, TestingSession
    db.close()


@pytest.fixture
def api(db_setup):
    _db, TestingSession = db_setup

    def override_get_db():
        s = TestingSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
