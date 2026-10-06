# Tool nạp DB — máy CSDT

Chạy tại máy có SQL Server `GPLX_CSDT`. Pull dữ liệu từ VPS → map địa chỉ → xử lý ảnh → nạp qua stored procedure. Đóng gói PyInstaller (.exe) khi phát hành.

## Chạy dev

Backend (FastAPI, cổng 8000):
```bash
cd tool
python -m venv .venv && . .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000 --reload
# kiểm: GET http://localhost:8000/health → {"status":"ok"}
```

Webui (React + Vite, cổng 3011):
```bash
cd tool/webui
pnpm install
pnpm dev        # http://localhost:3011
pnpm build      # build ra static để nhúng
```

Test backend:
```bash
cd tool && pytest
```

## Đóng gói .exe (DGT-01)

Gói tool thành **một thư mục chạy độc lập** (one-folder) cho máy CSDT không cài Python/Node.

```bash
cd tool
pnpm --dir webui build                      # 1. build giao diện tĩnh (webui/dist)
.venv/Scripts/python.exe -m pip install pyinstaller
.venv/Scripts/python.exe -m PyInstaller tool.spec --noconfirm
# → dist/pmcsdtlx-tool/pmcsdtlx-tool.exe  (+ _internal/ kèm Python, thư viện, model, dữ liệu)
```

Gói sẵn: Python + FastAPI/uvicorn + **pymssql (FreeTDS)** + **rembg/onnxruntime + model u2net** +
`webui/dist` (FastAPI phục vụ UI cùng cổng 8000) + `dvhc_map.sqlite`. Chạy bản gói ghi
config/nháp/ảnh tạm vào `%APPDATA%\pmcsdtlx-tool` (không vào `Program Files`).

**Khởi chạy (DGT-02):** nháy đúp exe → chạy **không cửa sổ console** (windowed), hiện **biểu
tượng khay hệ thống** (menu: Mở giao diện · Tự chạy khi bật máy · Thoát) + **tự mở trình duyệt**
vào đúng trang. Mở lại exe khi đang chạy → chỉ mở thêm tab, **không bật bản thứ hai** (lock-file
`%APPDATA%\pmcsdtlx-tool\pmcsdtlx-tool.lock`). Cổng mặc định 8000 bận → **tự nhảy cổng trống**.
Log chạy ghi ở `%APPDATA%\pmcsdtlx-tool\pmcsdtlx-tool.log`.

**Tự kiểm bản gói trên máy đích** (không cần SQL Server/mạng — chỉ kiểm thư viện C nạp được):
```bash
dist\pmcsdtlx-tool\pmcsdtlx-tool.exe --selftest    # bản windowed: báo kết quả bằng HỘP THOẠI
```
Đổi cổng/host bằng biến môi trường `TOOL_PORT` / `TOOL_HOST`.
Lần đầu máy sạch: Windows SmartScreen cảnh báo exe chưa ký số → bấm "Vẫn chạy".

> Cấu trúc 3 app toàn dự án: xem `docs/TDD.md` §2.4. Thứ tự build: `docs/BUILD-PLAN.md`.
