"""Dịch vụ VPS — khung FastAPI (task 12).

Chỉ có health/readiness ở bước này. Router thật thêm sau:
  - task 14: auth JWT + 3 vai trò  → app.routers.auth
  - task 15: hàng đợi ho_so_thu_thap → app.routers.ho_so
  - task 16: job xóa PII 30 ngày    → app.jobs.pii
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import get_settings
from app.db import engine
from app.jobs.scheduler import tao_scheduler
from app.routers import admin, admin_users, auth, ho_so, nap


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Bật scheduler job xóa PII khi khởi động, tắt khi dừng (TDD §7.3)."""
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
