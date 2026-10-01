"""FastAPI chạy localhost cho tool nạp DB tại máy CSDT.

Tool pull dữ liệu từ VPS về và nạp vào SQL Server GPLX_CSDT qua stored procedure.
File này là KHUNG — các router nghiệp vụ (cấu hình, kéo hàng đợi, map địa chỉ,
xử lý ảnh, nạp) được thêm ở các task sau theo docs/BUILD-PLAN.md.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/health")
def health() -> dict[str, str]:
    """Kiểm tra tiến trình tool còn sống (khung + sau này cho UI/giám sát)."""
    return {"status": "ok"}
