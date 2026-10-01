"""Dịch vụ VPS — khung FastAPI (task 12).

Chỉ có health/readiness ở bước này. Router thật thêm sau:
  - task 14: auth JWT + 3 vai trò  → app.routers.auth
  - task 15: hàng đợi ho_so_thu_thap → app.routers.ho_so
  - task 16: job xóa PII 30 ngày    → app.jobs.pii
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import get_settings
from app.db import engine

app = FastAPI(title="Thu nhận hồ sơ — API VPS", version="0.1.0")


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
