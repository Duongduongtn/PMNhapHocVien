"""Khung smoke test (task 12). Test auth/queue/pii-job thêm ở task 14/15/16."""


def test_health_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_version(client):
    r = client.get("/api/version")
    assert r.status_code == 200
    body = r.json()
    assert body["version"] == "0.1.0"
    assert "ten" in body


def test_ready_reports_db(client):
    """Không có PostgreSQL khi test đơn → /api/ready trả 503, không 500.

    Xác nhận lỗi nối DB được gói thành readiness âm, không làm sập app.
    """
    r = client.get("/api/ready")
    assert r.status_code in (200, 503)
    assert "db" in r.json()
