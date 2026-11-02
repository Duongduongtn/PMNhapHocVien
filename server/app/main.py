"""Dịch vụ VPS — FastAPI.

Router: auth (JWT + 3 vai trò) · admin / admin_users (quản trị, tài khoản) · ho_so (hàng đợi thu thập) ·
nap (tool kéo/nạp qua X-Tool-Key). Job nền: xóa PII sau PII_RETENTION_DAYS ngày (app.jobs). Có health/ready/version.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import get_settings
from app.db import engine
from app.jobs.scheduler import tao_scheduler
from app.routers import admin, admin_users, auth, ho_so, nap


def dam_bao_cot_moi() -> None:
    """init.sql chỉ chạy cho DB mới nên DB đang chạy phải tự thêm cột, trước khi nhận truy vấn (TDD §10.6)."""
    if engine.dialect.name != "postgresql":
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE ho_so_thu_thap ADD COLUMN IF NOT EXISTS gplx_da_co JSONB"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Bật scheduler job xóa PII khi khởi động, tắt khi dừng (TDD §7.3)."""
    dam_bao_cot_moi()
    scheduler = None
    if get_settings().enable_scheduler:
        scheduler = tao_scheduler()
        scheduler.start()
    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)


app = FastAPI(title="Thu nhận hồ sơ — API VPS", version="0.1.0", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(admin_users.router)
app.include_router(ho_so.router)
app.include_router(nap.router)


@app.get("/api/health")
def health() -> dict:
    """Liveness — app còn sống. Luôn 200, không phụ thuộc DB."""
    return {"status": "ok"}


@app.get("/api/ready")
def ready() -> JSONResponse:
    """Readiness — sẵn sàng nhận việc: kiểm nối được PostgreSQL chưa."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return JSONResponse({"status": "ok", "db": True})
    except Exception as exc:  # noqa: BLE001 — health check: gói mọi lỗi nối DB thành 503
        return JSONResponse({"status": "unavailable", "db": False, "chi_tiet": str(exc)}, status_code=503)


@app.get("/api/version")
def version() -> dict:
    s = get_settings()
    return {"ten": app.title, "version": app.version, "domain": s.app_domain}
