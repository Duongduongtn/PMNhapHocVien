"""Kết nối PostgreSQL (TDD §3.2).

Engine + session dùng chung. Router auth/hàng đợi (task 14/15) lấy session
qua dependency `get_db`. Schema do `db/init.sql` dựng khi postgres container
khởi tạo lần đầu — module này không tự tạo bảng.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

_settings = get_settings()

engine = create_engine(_settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Lớp gốc cho model SQLAlchemy. Model ánh xạ bảng đã dựng ở db/init.sql;
    id/thời gian có default phía Python để test chạy được trên SQLite in-memory."""


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
