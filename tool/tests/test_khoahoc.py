"""NAP-02 — test không cần DB thật: suy MaLoaiHs + validate tham số loai.

Truy vấn khóa thật (nối SQL Server) kiểm bằng tay/live, không đưa vào unit test
(cần DB + cấu hình). Ở đây chỉ chốt logic thuần + hợp đồng tham số.
"""
from datetime import date

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.routers.khoahoc import KhoaHocTao, dung_tham_so_insert, suy_ma_loai_hs, MA_CSDT, MA_SO_GTVT

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


def test_loai_sai_tra_422(auth_headers):
    # Tham số loai ngoài {moto, oto} bị chặn ở tầng validate, không chạm DB.
    # (Đã đăng nhập để qua cổng HTG-01③, mới tới được tầng validate.)
    r = client.get("/local/khoa-hoc?loai=xe-dap", headers=auth_headers)
    assert r.status_code == 422


def test_thieu_loai_tra_422(auth_headers):
    r = client.get("/local/khoa-hoc", headers=auth_headers)
    assert r.status_code == 422


def test_khoa_hoc_chua_dang_nhap_401():
    # Cổng HTG-01③: chưa đăng nhập → chặn trước khi tới DB.
    assert client.get("/local/khoa-hoc?loai=moto").status_code == 401


# ---- KHO-01: tạo khóa (logic thuần + validate + gate; không chạm DB) ----
def _body(**kw):
    d = dict(hang_dt="B", ten_kh="B-K150", ngay_kg=date(2026, 10, 15), ngay_bg=date(2027, 1, 15), tong_so_hv=50)
    d.update(kw)
    return KhoaHocTao(**d)


def test_dung_tham_so_insert_thu_tu_hang_va_hang_so():
    p = dung_tham_so_insert(_body(), "B1", 90, "NV Nạp")
    assert len(p) == 27
    assert p[0] == ""                       # @MaKH — SP tự sinh, bỏ qua
    assert (p[1], p[2]) == (MA_CSDT, MA_SO_GTVT)
    assert p[3] == "B-K150" and p[4] == "B1" and p[5] == "B"  # Ten, HangGPLX, HangDT
    assert p[8] == date(2026, 10, 15) and p[9] == date(2027, 1, 15)  # NgayKG, NgayBG
    assert p[13] == 50                      # TongSoHV
    assert p[14] == 0 and p[15] == 0        # tốt nghiệp / cấp GPLX = 0
    assert p[16] == 90                      # ThoiGianDT
    assert p[22] == 1                       # TrangThai
    assert p[23] == "NV Nạp" and p[24] == "NV Nạp"
    assert p[25] is None and p[26] is None  # NgayTao/NgaySua — SP getdate()


def test_tham_so_tuy_chon_mac_dinh_none():
    p = dung_tham_so_insert(_body(so_qd=None, ghi_chu=None), "B1", 90, "x")
    assert p[6] is None and p[11] is None and p[21] is None  # SoQD, NgayThi, GhiChu


def test_validate_ten_rong():
    with pytest.raises(ValidationError):
        _body(ten_kh="   ")


def test_validate_ten_qua_dai():
    with pytest.raises(ValidationError):
        _body(ten_kh="x" * 51)


def test_validate_tong_hv_khong_duong():
    with pytest.raises(ValidationError):
        _body(tong_so_hv=0)


def test_hang_dt_chua_dang_nhap_401():
    assert client.get("/local/khoa-hoc/hang-dt").status_code == 401


def test_tao_chua_dang_nhap_401():
    assert client.post("/local/khoa-hoc/tao", json={}).status_code == 401


def test_tao_thieu_truong_422(auth_headers):
    r = client.post("/local/khoa-hoc/tao", headers=auth_headers, json={"hang_dt": "B"})
    assert r.status_code == 422


def test_tao_ngay_bg_truoc_kg_400(auth_headers):
    # Kiểm ngày nằm TRƯỚC khi chạm DB → 400 không cần SQL Server.
    r = client.post(
        "/local/khoa-hoc/tao",
        headers=auth_headers,
        json={"hang_dt": "B", "ten_kh": "T", "ngay_kg": "2026-10-15", "ngay_bg": "2026-10-01", "tong_so_hv": 10},
    )
    assert r.status_code == 400
