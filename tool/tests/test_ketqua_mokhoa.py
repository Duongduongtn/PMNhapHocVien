"""Unit test mỏng cho KQD-05 mở khóa (task 76) — phần logic thuần không cần DB.

Ghi/xóa thật trên CDB đích + cổng B-1 happy-path → nghiệm thu máy CSDT (mức 1).
Ở đây chỉ kiểm `_goi_row` tách tên tệp từ DuongDan (DuongDan live có cả 'C:\\…').
"""
from app.routers import ketqua as k


def test_goi_row_tach_ten_file_tu_duong_dan_windows():
    r = {"Id": "abc-123", "DuongDan": r"C:\KQDT_75032_75_K261002191716.zip",
         "TrangThai": "0", "KickThuocFile": 2048, "NgayTao": "02/10/2026 19:23"}
    out = k._goi_row(r)
    assert out["id"] == "abc-123"
    assert out["ten_file"] == "KQDT_75032_75_K261002191716.zip"
    assert out["ngay_tao"] == "02/10/2026 19:23"
    assert out["kich_thuoc"] == 2048


def test_goi_row_ten_file_khi_chi_co_ten_khong_co_thu_muc():
    out = k._goi_row({"Id": "x", "DuongDan": "KQDT_75032.zip",
                      "TrangThai": "1", "KickThuocFile": None, "NgayTao": None})
    assert out["ten_file"] == "KQDT_75032.zip"
    assert out["ngay_tao"] is None


def test_goi_row_duong_dan_lan_dau_phan_cach_xuoi():
    out = k._goi_row({"Id": "y", "DuongDan": "/var/out/KQDT_9.zip",
                      "TrangThai": "0", "KickThuocFile": 1, "NgayTao": "01/01/2026 00:00"})
    assert out["ten_file"] == "KQDT_9.zip"


def test_goi_row_duong_dan_rong():
    out = k._goi_row({"Id": "z", "DuongDan": None,
                      "TrangThai": "0", "KickThuocFile": None, "NgayTao": None})
    assert out["ten_file"] == ""
    assert out["duong_dan"] == ""
