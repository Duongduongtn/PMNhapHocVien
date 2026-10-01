"""NAP-02 — test không cần DB thật: suy MaLoaiHs + validate tham số loai.

Truy vấn khóa thật (nối SQL Server) kiểm bằng tay/live, không đưa vào unit test
(cần DB + cấu hình). Ở đây chỉ chốt logic thuần + hợp đồng tham số.
"""
from fastapi.testclient import TestClient

from app.main import app
from app.routers.khoahoc import suy_ma_loai_hs

client = TestClient(app)


def test_suy_ma_loai_hs_moto():
    assert suy_ma_loai_hs("A") == 1
    assert suy_ma_loai_hs("A1") == 1
    assert suy_ma_loai_hs("a2") == 1  # không phân biệt hoa thường


def test_suy_ma_loai_hs_oto():
    for h in ("B", "B1", "C", "D", "E", "F"):
        assert suy_ma_loai_hs(h) == 2


def test_suy_ma_loai_hs_rong():
    assert suy_ma_loai_hs(None) == 2
    assert suy_ma_loai_hs("") == 2


def test_loai_sai_tra_422():
    # Tham số loai ngoài {moto, oto} bị chặn ở tầng validate, không chạm DB.
    r = client.get("/local/khoa-hoc?loai=xe-dap")
    assert r.status_code == 422


def test_thieu_loai_tra_422():
    r = client.get("/local/khoa-hoc")
    assert r.status_code == 422
