"""KQD-03 backend (task 138, TDD §11D.13) — nhóm trạng thái CÓ ĐIỀU KIỆN dùng chung cho đếm `/khoa` và lọc `/hoc-vien`.

"Còn sót kết xuất" (`capnhat`) = 09/10 + 90 Đạt; HV 90 Không đạt/trống kết luận KHÔNG tính (CDB không kết xuất).
Kiểm hành vi thật của các điều kiện SQL bằng sqlite (cú pháp chuẩn AND/OR/IN/IS NULL), và kiểm SQL do router dựng.
"""
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import ketqua

client = TestClient(app)

# (MaDK, TT_XuLy, KetLuanCSDT)
HV = [
    ("a03", "03", None), ("a04", "04", None),
    ("a09", "09", 1), ("a10", "10", 0),
    ("a90d", "90", 1), ("a90k", "90", 0), ("a90n", "90", None),
    ("a14", "14", 1), ("a12", "12", 1), ("a13", "13", 1),
]


@pytest.fixture
def db():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE h (MaDK TEXT, TT_XuLy TEXT, KetLuanCSDT INTEGER)")
    c.executemany("INSERT INTO h VALUES (?,?,?)", HV)
    yield c
    c.close()


def _ma(db, nhom):
    sql = "SELECT MaDK FROM h WHERE " + ketqua._NHOM_DK[nhom].format(a="h")
    return {r[0] for r in db.execute(sql)}


def test_capnhat_con_sot_gom_09_10_va_90_dat(db):
    assert _ma(db, "capnhat") == {"a09", "a10", "a90d"}


def test_90_khong_dat_hoac_trong_ket_luan_khong_tinh_con_sot(db):
    ds = _ma(db, "capnhat")
    assert "a90k" not in ds and "a90n" not in ds


def test_cho_kx_09_va_90_dat(db):
    assert _ma(db, "chokx") == {"a09", "a90d"}


def test_khong_dat_chi_10(db):
    assert _ma(db, "khongdat") == {"a10"}


def test_can_xu_ly_14_va_90_khong_dat_hoac_trong(db):
    assert _ma(db, "canxuly") == {"a14", "a90k", "a90n"}


def test_da_gui_12_13(db):
    assert _ma(db, "dagui") == {"a12", "a13"}


def test_moi_hv_co_dung_mot_vi_tri_trong_cac_tab_khong_chong_lan(db):
    """Dải tab: Chưa nhập · Chờ kết xuất · Không đạt · Cần xử lý · Đã gửi — phủ hết, không HV nào ở 2 tab."""
    chua_nhap = {m for m, tt, _ in HV if tt in ("03", "04")}
    cac_tab = [chua_nhap, _ma(db, "chokx"), _ma(db, "khongdat"), _ma(db, "canxuly"), _ma(db, "dagui")]
    hop = set().union(*cac_tab)
    assert hop == {m for m, _, _ in HV}
    assert sum(len(t) for t in cac_tab) == len(HV)


# ── SQL router dựng ──
class _Cur:
    def __init__(self, rows_khoa=None, rows_hv=None):
        self.rows_khoa, self.rows_hv, self.executed, self._res = rows_khoa or [], rows_hv or [], [], []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        self._res = self.rows_khoa if "FROM dbo.KhoaHoc" in sql else self.rows_hv

    def fetchall(self):
        return self._res

    def fetchone(self):
        return self._res[0] if self._res else None


class _Conn:
    def __init__(self, cur):
        self._cur = cur

    def cursor(self, as_dict=False):
        return self._cur

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _patch(monkeypatch, cur):
    monkeypatch.setattr("app.routers.ketqua._db_dich", lambda tk: "GPLX_CDB_CSDT")
    monkeypatch.setattr("app.routers.ketqua.sqlserver_conn_dich", lambda d, autocommit=True, timeout=0: _Conn(cur))
    monkeypatch.setattr("app.routers.ketqua.sync_helpers.get_ma_csdt_tu_qtht", lambda c: "75032")
    return cur


def test_khoa_dem_theo_nhom_co_dieu_kien(auth_headers, monkeypatch):
    row = {"MaKH": "K1", "TenKH": "B-K1", "HangGPLX": "B", "NgayKG": "01/09/2026", "NgayBG": "02/09/2026",
           "NgayThi": "20/09/2026", "dem_dangky": 3, "dem_capnhat": 8, "dem_chokx": 6, "dem_khongdat": 2,
           "dem_canxuly": 4, "dem_dagui": 5, "dem_tuchoi": 1, "dem_giaitrinh": 3, "dem_ketxuat": 5}
    cur = _patch(monkeypatch, _Cur(rows_khoa=[row]))
    r = client.get("/local/ketqua/khoa", headers=auth_headers)
    assert r.status_code == 200, r.text
    dem = r.json()[0]["dem"]
    assert dem["capnhat"] == 8 and dem["chokx"] == 6 and dem["khongdat"] == 2
    assert dem["canxuly"] == 4 and dem["dagui"] == 5
    assert dem["dangky"] == 3 and dem["tuchoi"] == 1 and dem["giaitrinh"] == 3 and dem["ketxuat"] == 5   # cũ giữ nguyên
    sql = cur.executed[0][0]
    assert "(h.TT_XuLy = '90' AND h.KetLuanCSDT = 1)" in sql          # điều kiện 90 Đạt có trong đếm "capnhat"
    assert "AS dem_capnhat" in sql and "AS dem_canxuly" in sql


@pytest.mark.parametrize("nhom,mong", [("capnhat", "({a}.TT_XuLy IN ('09','10')"), ("canxuly", "{a}.TT_XuLy = '14'"),
                                       ("chokx", "{a}.TT_XuLy = '09'"), ("dagui", "IN ('12','13')")])
def test_hoc_vien_loc_theo_nhom_co_dieu_kien(auth_headers, monkeypatch, nhom, mong):
    cur = _patch(monkeypatch, _Cur(rows_hv=[]))
    r = client.get(f"/local/ketqua/hoc-vien?ma_kh=K1&trang_thai={nhom}", headers=auth_headers)
    assert r.status_code == 200
    sql, params = cur.executed[0]
    assert mong.format(a="B") in sql
    assert params == ("K1",)                      # điều kiện nằm trong SQL, không thêm tham số mã


def test_hoc_vien_nhom_tuple_cu_van_chay(auth_headers, monkeypatch):
    cur = _patch(monkeypatch, _Cur(rows_hv=[]))
    client.get("/local/ketqua/hoc-vien?ma_kh=K1&trang_thai=tuchoi", headers=auth_headers)
    sql, params = cur.executed[0]
    assert "B.TT_XuLy IN (%s)" in sql and params == ("K1", "14")


def test_kiem_truoc_van_09_10_chua_them_90(auth_headers, monkeypatch):
    """Task 139 mới thêm 90 vào kiểm trước kết xuất — task 138 giữ nguyên."""
    cur = _patch(monkeypatch, _Cur(rows_hv=[]))
    client.get("/local/ketqua/kiem-truoc?ma_kh=K1", headers=auth_headers)
    sql, params = cur.executed[0]
    assert params == ("K1", "03", "04", "09", "10")
