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

> Cấu trúc 3 app toàn dự án: xem `docs/TDD.md` §2.4. Thứ tự build: `docs/BUILD-PLAN.md`.
