# server/ — Dịch vụ VPS (FastAPI + PostgreSQL)

Backend hệ thu nhận hồ sơ: auth, hàng đợi hồ sơ chờ nạp, lưu ảnh thô, job xóa PII.
Xem TDD §2.1–§2.4, §3.2, §15.

> Task 12 mới dựng **khung** (health/readiness + kết nối DB + schema + docker-compose).
> Auth (task 14), hàng đợi (task 15), job PII (task 16) thêm sau.

## Cấu trúc

```
server/
├── app/
│   ├── main.py        FastAPI app + /api/health, /api/ready, /api/version
│   ├── config.py      đọc env (pydantic-settings)
│   ├── db.py          engine + session PostgreSQL + get_db
│   ├── routers/       (task 14/15)
│   ├── models/        (task 14/15)
│   └── jobs/          (task 16)
├── db/init.sql        schema §3.2 (postgres nạp lần đầu)
├── tests/             pytest (smoke: health/version/ready)
├── requirements.txt
└── Dockerfile
```

## Chạy bằng docker-compose (giống VPS) — từ gốc repo

```bash
cp .env.example .env          # rồi điền POSTGRES_PASSWORD, JWT_SECRET, TOOL_API_KEY
docker compose up -d --build
curl http://localhost/api/health   # {"status":"ok"}
curl http://localhost/api/ready    # {"status":"ok","db":true}
```

## Chạy cục bộ không qua docker (dev)

```bash
cd server
python -m venv .venv && . .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# cần PostgreSQL local + đặt DATABASE_URL trong .env (xem .env.example)
uvicorn app.main:app --reload --port 8000
```

## Test

```bash
cd server
pip install -r requirements.txt
pytest               # smoke test, không cần PostgreSQL
```
