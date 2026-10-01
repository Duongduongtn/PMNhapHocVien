"""NAP-03 — test chuẩn hóa địa chỉ + tra_map (SQLite tạm, không cần DB thật).

Danh sách Tỉnh/Xã (ds_tinh/ds_xa) nối SQL Server → kiểm live, không unit test ở đây.
"""
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import dvhc

client = TestClient(app)


# ---- Chuẩn hóa -------------------------------------------------------------
def test_norm_prov():
    assert dvhc.norm_prov("Thành phố Hà Nội") == "hà nội"
    assert dvhc.norm_prov("Tỉnh Đồng Nai") == "đồng nai"


def test_norm_ward_dist():
    assert dvhc.norm_ward("Phường Phúc Xá") == "phúc xá"
    assert dvhc.norm_dist("Quận Ba Đình") == "ba đình"
    assert dvhc.norm_ward("Thị trấn Yên Viên") == "yên viên"


def test_norm_dau_nhay_cong():
    # dấu nháy cong U+2019 -> thẳng, để khớp dữ liệu DB
    assert dvhc.norm_ward("Xã Ea H’leo") == "ea h'leo"


# ---- tra_map với SQLite tạm ------------------------------------------------
@pytest.fixture
def tmp_map(tmp_path, monkeypatch):
    p = tmp_path / "m.sqlite"
    conn = sqlite3.connect(str(p))
    conn.execute(
        "CREATE TABLE dm_dvhc_map (id INTEGER PRIMARY KEY, ten_tinh_cu TEXT, ten_huyen_cu TEXT, "
        "ten_xa_cu TEXT, ma_dvhc_moi TEXT, ma_dvql_moi TEXT, ten_xa_moi TEXT, ten_tinh_moi TEXT, "
        "ten_xa_moi_norm TEXT, ten_tinh_moi_norm TEXT, is_divided INTEGER)"
    )
    conn.executemany(
        "INSERT INTO dm_dvhc_map (ten_tinh_cu,ten_huyen_cu,ten_xa_cu,ma_dvhc_moi,ma_dvql_moi,"
        "ten_xa_moi,ten_tinh_moi,ten_xa_moi_norm,ten_tinh_moi_norm,is_divided) VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            # key cũ đã CHUẨN HÓA (lower, bỏ tiền tố) — đúng dạng builder nạp;
            # kèm tên mới chuẩn hóa (ten_*_moi_norm) để khớp khi nhập địa chỉ ĐÃ MỚI
            ("hà nội", "ba đình", "phúc xá", "00097", "01", "Hồng Hà", "Thành phố Hà Nội", "hồng hà", "hà nội", 0),
            ("x", "y", "chia", "11111", "50", "Xã A", "Tỉnh X", "a", "x", 1),       # cờ chia
            ("z", "z", "nhieu", "22221", "60", "Xã M", "Tỉnh Z", "m", "z", 0),      # 1 key cũ ->
            ("z", "z", "nhieu", "22222", "60", "Xã N", "Tỉnh Z", "n", "z", 0),      # 2 xã mới
        ],
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(dvhc, "MAP_SQLITE", p)
    return p


def test_map_khop_dieu_kien(tmp_map):
    r = dvhc.tra_map("Thành phố Hà Nội", "Quận Ba Đình", "Phường Phúc Xá")
    assert r["matched"] is True and r["divided"] is False
    assert r["ma_dvhc"] == "00097" and r["ma_dvql"] == "01"
    assert r["ten_xa"] == "Hồng Hà" and r["ten_tinh"] == "Thành phố Hà Nội"


def test_map_xa_chia_co_co(tmp_map):
    r = dvhc.tra_map("Tỉnh X", "Huyện Y", "Xã Chia")
    assert r["matched"] is True and r["divided"] is True  # is_divided=1 -> chọn tay


def test_map_xa_chia_nhieu_dong(tmp_map):
    r = dvhc.tra_map("Tỉnh Z", "Huyện Z", "Xã Nhieu")
    assert r["divided"] is True  # 1 địa chỉ cũ -> nhiều xã mới


def test_map_dia_chi_da_moi(tmp_map):
    # Nhập địa chỉ ĐÃ MỚI (tỉnh + xã mới, không có huyện) vẫn khớp qua fallback
    r = dvhc.tra_map("Thành phố Hà Nội", "", "Hồng Hà")
    assert r["matched"] is True and r["divided"] is False
    assert r["ma_dvhc"] == "00097" and r["ma_dvql"] == "01"


def test_map_khong_khop(tmp_map):
    assert dvhc.tra_map("Tỉnh K", "Huyện K", "Xã K") is None


# ---- Validate endpoint -----------------------------------------------------
def test_xa_thieu_tinh_422(auth_headers):
    # Đã đăng nhập để qua cổng HTG-01③ → mới tới tầng validate (thiếu tinh → 422).
    assert client.get("/local/dvhc/xa", headers=auth_headers).status_code == 422


def test_dvhc_chua_dang_nhap_401():
    assert client.get("/local/dvhc/tinh").status_code == 401
