"""KQD-07 đổi (task 139, TDD §11D.9/§11D.13) — kiểm trước kết xuất xét thêm HV 90 và 14 Đạt.

Ba lý do mới: `thieu_giai_trinh` (14 Đạt chưa giải trình) · `khong_dat_o_90` (90 mà Không đạt) ·
`giai_trinh_trong` (90 mà GiaiTrinh rỗng). `thieu_ket_luan` mở rộng sang 90. Luật thuần `hv_chua_du` +
endpoint chỉ đọc bằng cursor giả.
"""
from contextlib import contextmanager

from fastapi.testclient import TestClient

from app import ketqua_quydoi as q
from app.main import app
from app.routers import ketqua as k

client = TestClient(app)
_DU = {"ly_thuyet": 8.0, "mo_phong": 7.0, "hinh": 9.0, "tien_lui": 6.0, "duong": 8.0}


def _hv(**kw):
    base = {"tt_xuly": "90", "ket_luan": "dat", "diem": dict(_DU), "gio_san": 34, "km_san": 240,
            "gio_duong": 20, "km_duong": 810, "giai_trinh": "Đã nộp lại"}
    base.update(kw)
    return base


# ── luật thuần ──
def test_90_dat_du_giai_trinh_du_dieu_kien():
    assert q.hv_chua_du(_hv()) == {"ly_do": [], "mon_thieu": []}


def test_90_khong_dat():
    assert q.hv_chua_du(_hv(ket_luan="khong_dat"))["ly_do"] == [q.LY_DO_KHONG_DAT_O_90]


def test_90_giai_trinh_trong_hoac_khoang_trang():
    assert q.hv_chua_du(_hv(giai_trinh=""))["ly_do"] == [q.LY_DO_GIAI_TRINH_TRONG]
    assert q.hv_chua_du(_hv(giai_trinh="   "))["ly_do"] == [q.LY_DO_GIAI_TRINH_TRONG]


def test_90_tron_ket_luan_thieu_ket_luan():
    r = q.hv_chua_du(_hv(ket_luan=None))
    assert q.LY_DO_THIEU_KET_LUAN in r["ly_do"] and q.LY_DO_KHONG_DAT_O_90 not in r["ly_do"]


def test_14_dat_thieu_giai_trinh():
    assert q.hv_chua_du(_hv(tt_xuly="14", giai_trinh=""))["ly_do"] == [q.LY_DO_THIEU_GIAI_TRINH]


def test_14_dat_co_giai_trinh_khong_thieu():
    assert q.hv_chua_du(_hv(tt_xuly="14"))["ly_do"] == []


def test_14_khong_dat_khong_nhac_giai_trinh():
    """14 Không đạt: không có chuyện 'thiếu giải trình' — không kết xuất được dù có giải trình hay không."""
    assert q.hv_chua_du(_hv(tt_xuly="14", ket_luan="khong_dat", giai_trinh=""))["ly_do"] == []


def test_09_10_khong_xet_giai_trinh():
    assert q.hv_chua_du(_hv(tt_xuly="09", giai_trinh=""))["ly_do"] == []


def test_khong_truyen_giai_trinh_thi_khong_xet_luat_giai_trinh():
    """Lô giải trình (`phan_loai_lo`) không truyền `giai_trinh` — nội dung ghi cùng lúc nên không phải 'thiếu'."""
    hv = _hv(tt_xuly="14")
    hv.pop("giai_trinh")
    assert q.hv_chua_du(hv)["ly_do"] == []


# ── endpoint ──
def _row(ma, tt, kl=1, gt="", **kw):
    r = {"MaDK": ma, "HoVaTen": f"HV {ma}", "SoCMT": "079" + ma, "TT_XuLy": tt, "KetLuanCSDT": kl,
         "HangGPLX": "B11", "MaHangMoi": "B.01",
         "DiemKQLyThuyet": 8, "DiemKQMoPhong": 7, "DiemKQHinh": 9, "DiemKQTienLui": 6, "DiemKQThucHanh": 8,
         "TGThucHanhHinh": 34, "QDThucHanhHinh": 240, "TGThucHanhDuong": 20, "TongQDThucHanh": 810,
         "GiaiTrinh": gt}
    r.update(kw)
    return r


class _Cur:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, sql, params=None):
        pass

    def fetchall(self):
        return self.rows


def _gia_lap(monkeypatch, rows):
    @contextmanager
    def conn(_db, **_kw):
        class C:
            def cursor(self, as_dict=False):
                return _Cur(rows)
        yield C()
    monkeypatch.setattr(k, "_db_dich", lambda tk: "DB")
    monkeypatch.setattr(k, "sqlserver_conn_dich", conn)


def test_endpoint_dem_va_liet_ke_ba_ly_do_moi(monkeypatch, auth_headers):
    rows = [
        _row("1", "90", 1, "Đã nộp"),            # đủ
        _row("2", "90", 0, "Đã nộp"),            # khong_dat_o_90
        _row("3", "90", 1, ""),                  # giai_trinh_trong
        _row("4", "90", None, "Đã nộp"),         # thieu_ket_luan
        _row("5", "14", 1, ""),                  # thieu_giai_trinh
        _row("6", "14", 1, "Đã nộp"),            # đủ (chờ chuyển 90)
    ]
    _gia_lap(monkeypatch, rows)
    j = client.get("/local/ketqua/kiem-truoc?ma_kh=KX", headers=auth_headers).json()
    assert (j["tong"], j["du"]) == (6, 2)
    ly = {t["ma_dk"]: t["ly_do"] for t in j["thieu"]}
    assert ly == {"2": ["khong_dat_o_90"], "3": ["giai_trinh_trong"], "4": ["thieu_ket_luan"],
                  "5": ["thieu_giai_trinh"]}
    for ld in ("khong_dat_o_90", "giai_trinh_trong", "thieu_ket_luan", "thieu_giai_trinh"):
        assert j["dem"][ld] == 1
    assert {"chua_co_diem", "thieu_mon", "thieu_gio_km"} <= set(j["dem"])      # khóa cũ giữ nguyên
