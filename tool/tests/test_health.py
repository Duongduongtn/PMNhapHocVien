from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_tra_ve_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
