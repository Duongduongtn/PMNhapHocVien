"""FastAPI chạy localhost cho tool nạp DB tại máy CSDT.

Tool pull dữ liệu từ VPS về và nạp vào SQL Server GPLX_CSDT qua stored procedure.
File này là KHUNG — các router nghiệp vụ (cấu hình, kéo hàng đợi, map địa chỉ,
xử lý ảnh, nạp) được thêm ở các task sau theo docs/BUILD-PLAN.md.
"""
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import os
import threading

from app import paths
from app.session import require_session
from app.routers import auth as auth_router
from app.routers import config as config_router
from app.routers import khoahoc as khoahoc_router
from app.routers import hoso as hoso_router
from app.routers import dvhc as dvhc_router
from app.routers import anh as anh_router
from app.routers import nap as nap_router
from app.routers import doinen as doinen_router
from app.routers import sync as sync_router
from app.routers import sync_tracuu as sync_tracuu_router
from app.routers import doisoat as doisoat_router

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
# đăng nhập được), auth chính là chỗ đăng nhập. DGT-03: cấu hình CSDL đích (sync
# targets) cũng là bước mồi cho wizard lần đầu — mount TRƯỚC khi gác.
app.include_router(config_router.router)
app.include_router(auth_router.router)
app.include_router(sync_router.targets_router)

# Nghiệp vụ nạp/tra — buộc session cục bộ (HTG-01③, TDD §4.6).
_gac = [Depends(require_session)]
app.include_router(khoahoc_router.router, dependencies=_gac)
app.include_router(hoso_router.router, dependencies=_gac)
app.include_router(dvhc_router.router, dependencies=_gac)
app.include_router(anh_router.router, dependencies=_gac)
app.include_router(nap_router.router, dependencies=_gac)
app.include_router(doinen_router.router, dependencies=_gac)
app.include_router(doisoat_router.router, dependencies=_gac)
app.include_router(sync_router.router, dependencies=_gac)
app.include_router(sync_tracuu_router.router, dependencies=_gac)


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


@app.on_event("startup")
def _nap_phien_va_heartbeat() -> None:
    """DGT-04 — khởi động: nạp phiên từ đĩa (mở lại vào thẳng) + heartbeat làm mới
    vps_token ngầm (đổi refresh token) để nạp từ VPS không chết sau 8h."""
    from app import session

    session.nap_phien_tu_dia()
    if os.environ.get("TOOL_SKIP_HEARTBEAT") == "1":
        return

    def _loop():
        import time

        while True:
            # Làm mới ngay vòng đầu (vps_token trên đĩa có thể đã hết 8h), rồi mỗi N giờ.
            for tok in list(session._phien_theo_token.keys()):
                try:
                    session.lam_moi_phien(tok)
                except Exception:
                    pass
            time.sleep(session.HEARTBEAT_SECONDS)

    threading.Thread(target=_loop, daemon=True).start()


@app.get("/health")
def health() -> dict[str, str]:
    """Kiểm tra tiến trình tool còn sống (khung + sau này cho UI/giám sát)."""
    return {"status": "ok"}


# ── DGT-01: FastAPI phục vụ giao diện tĩnh (webui/dist) cùng cổng với API ──
# Chỉ bật khi có bản build (bản .exe luôn có; chạy dev dùng cổng vite 3011 riêng nên
# thường KHÔNG có dist → bỏ qua, không ảnh hưởng dev). Đăng ký SAU mọi router + /health
# để các route API (/local/*, /health) khớp trước; catch-all chỉ nhận phần còn lại.
_DIST = paths.BUNDLE_DIR / "webui" / "dist"
if _DIST.is_dir():
    _ASSETS = _DIST / "assets"
    if _ASSETS.is_dir():
        # StaticFiles tự đặt đúng Content-Type cho .js/.css (quan trọng cho ES module).
        app.mount("/assets", StaticFiles(directory=_ASSETS), name="assets")

    @app.get("/")
    def _spa_index() -> FileResponse:
        return FileResponse(_DIST / "index.html")

    @app.get("/{full_path:path}")
    def _spa_fallback(full_path: str) -> FileResponse:
        """SPA (BrowserRouter): path là file tĩnh thật → trả file; còn lại → index.html
        để React Router tự định tuyến (vd /tool/thiet-lap khi F5 / mở link sâu)."""
        f = (_DIST / full_path).resolve()
        # Chặn đi ra ngoài thư mục dist (path traversal); phải là file thật mới trả.
        if f.is_file() and str(f).startswith(str(_DIST.resolve())):
            return FileResponse(f)
        return FileResponse(_DIST / "index.html")
