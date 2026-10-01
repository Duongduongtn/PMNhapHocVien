"""QLY-01 — Tra cứu hồ sơ: gate đăng nhập + validate tham số (không cần DB thật).

Lưới HV thật (nối SQL Server qua usp_NguoiLX_Select_By_MaKH) kiểm bằng tay/live.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ds_ho_so_chua_dang_nhap_401():
    # Cổng HTG-01③: chưa đăng nhập → chặn trước khi tới DB.
    assert client.get("/local/ho-so?makh=70004K26B010").status_code == 401


def test_thieu_makh_422(auth_headers):
    r = client.get("/local/ho-so", headers=auth_headers)
    assert r.status_code == 422


def test_makh_rong_422(auth_headers):
    # min_length=1 → makh rỗng bị chặn ở validate, không chạm DB.
    r = client.get("/local/ho-so?makh=", headers=auth_headers)
    assert r.status_code == 422
