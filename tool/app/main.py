"""FastAPI chạy localhost cho tool nạp DB tại máy CSDT.

Tool pull dữ liệu từ VPS về và nạp vào SQL Server GPLX_CSDT qua stored procedure.
File này là KHUNG — các router nghiệp vụ (cấu hình, kéo hàng đợi, map địa chỉ,
xử lý ảnh, nạp) được thêm ở các task sau theo docs/BUILD-PLAN.md.
"""
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os
import threading

from app.session import require_session
from app.routers import auth as auth_router
from app.routers import config as config_router
from app.routers import khoahoc as khoahoc_router
from app.routers import dvhc as dvhc_router
from app.routers import anh as anh_router
from app.routers import nap as nap_router

app = FastAPI(
    title="Tool nạp DB — Thu nhận hồ sơ học viên",
    version="0.1.0",
)

# UI chạy cùng máy (webui Vite ở cổng 3011); chỉ cho phép nguồn cục bộ.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3011",
        "http://127.0.0.1:3011",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Cửa vào — KHÔNG gác token (A1): config là bước mồi (chưa có URL VPS thì không
# đăng nhập được), auth chính là chỗ đăng nhập.
app.include_router(config_router.router)
app.include_router(auth_router.router)

# Nghiệp vụ nạp/tra — buộc session cục bộ (HTG-01③, TDD §4.6).
_gac = [Depends(require_session)]
app.include_router(khoahoc_router.router, dependencies=_gac)
app.include_router(dvhc_router.router, dependencies=_gac)
app.include_router(anh_router.router, dependencies=_gac)
app.include_router(nap_router.router, dependencies=_gac)


@app.on_event("startup")
def _warmup_rembg() -> None:
    """Nạp sẵn model rembg ở thread nền (§9.2) — không chặn khởi động, không gãy nếu lỗi."""
    if os.environ.get("TOOL_SKIP_WARMUP") == "1":
        return
    from app import image

    def _run():
        try:
            image.warmup()
        except Exception:
            pass  # offline/thiếu model → để lần xử lý ảnh đầu tự nạp (chậm hơn)

    threading.Thread(target=_run, daemon=True).start()


@app.get("/health")
def health() -> dict[str, str]:
    """Kiểm tra tiến trình tool còn sống (khung + sau này cho UI/giám sát)."""
    return {"status": "ok"}
