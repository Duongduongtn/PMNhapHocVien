"""KQD-07 (task 119) — kiểm trước kết xuất: luật thuần `hv_chua_du` + endpoint chỉ đọc bằng cursor giả."""
from __future__ import annotations

from contextlib import contextmanager

from fastapi.testclient import TestClient

from app import ketqua_quydoi as q
from app.main import app
from app.routers import ketqua as k

client = TestClient(app)

_DU = {"ly_thuyet": 8.0, "mo_phong": 7.0, "hinh": 9.0, "tien_lui": 6.0, "duong": 8.0}
_RONG = {m: None for m in q.MON}


def _hv(**kw):
    base = {"tt_xuly": "09", "ket_luan": "dat", "diem": dict(_DU),
            "gio_san": 34, "km_san": 240, "gio_duong": 20, "km_duong": 810}
    base.update(kw)
    return base


# ---- luật thuần --------------------------------------------------------------
def test_du_ca_5_mon_gio_km_ket_luan():
    assert q.hv_chua_du(_hv()) == {"ly_do": [], "mon_thieu": []}


def test_chua_co_diem():
    r = q.hv_chua_du(_hv(tt_xuly="03", ket_luan=None, diem=dict(_RONG)))
    assert q.LY_DO_CHUA_CO_DIEM in r["ly_do"] and q.LY_DO_THIEU_MON not in r["ly_do"]


def test_thieu_mon_nem_ro_mon_nao():
    d = dict(_DU, hinh=None, tien_lui=None)
    r = q.hv_chua_du(_hv(diem=d))
    assert r["ly_do"] == [q.LY_DO_THIEU_MON]
    assert r["mon_thieu"] == ["hinh", "tien_lui"]


def test_thieu_gio_km_moi_o_deu_tinh():
    for o in ("gio_san", "km_san", "gio_duong", "km_duong"):
        assert q.hv_chua_du(_hv(**{o: None}))["ly_do"] == [q.LY_DO_THIEU_GIO_KM]


def test_gio_km_duong_duoi_nguong_goi_y_khong_vao_ly_do():
    # B số sàn gợi ý ≥ 20 giờ / 810 km đường — dưới ngưỡng chỉ là cảnh báo, không phải "thiếu"
    assert q.hv_chua_du(_hv(gio_duong=5, km_duong=100))["ly_do"] == []


def test_thieu_ket_luan_chi_voi_09_10():
    assert q.hv_chua_du(_hv(tt_xuly="09", ket_luan=None))["ly_do"] == [q.LY_DO_THIEU_KET_LUAN]
    assert q.hv_chua_du(_hv(tt_xuly="03", ket_luan=None))["ly_do"] == []


def test_nhieu_ly_do_cung_luc():
    r = q.hv_chua_du(_hv(diem=dict(_DU, duong=None), gio_san=None, ket_luan=None))
    assert r["ly_do"] == [q.LY_DO_THIEU_MON, q.LY_DO_THIEU_GIO_KM, q.LY_DO_THIEU_KET_LUAN]


def test_la_mo_to():
    assert q.la_mo_to("A1", None) and q.la_mo_to(None, "A2") and q.la_mo_to(" a ", "B1")
    assert not q.la_mo_to("B", "B2") and not q.la_mo_to("C1", None) and not q.la_mo_to(None, None)


# ---- endpoint (cursor giả) ----------------------------------------------------
def _row(ma_dk, tt, hang="B", **kw):
    r = {"MaDK": ma_dk, "HoVaTen": f"HV {ma_dk}", "NgaySinh": "20000101", "SoCMT": "0010" + ma_dk,
         "SoHoSo": "1", "HangGPLX": hang, "MaHangMoi": hang, "TT_XuLy": tt, "KetLuanCSDT": 1,
         "DiemKQLyThuyet": 8, "DiemKQMoPhong": 7, "DiemKQHinh": 9, "DiemKQTienLui": 6, "DiemKQThucHanh": 8,
         "TGThucHanhHinh": 34, "QDThucHanhHinh": 240, "TGThucHanhDuong": 20, "TongQDThucHanh": 810}
    r.update(kw)
    return r


class _Cur:
    def __init__(self, rows, log):
        self.rows, self.log = rows, log

    def execute(self, sql, params=()):
        self.log.append((sql, params))

    def fetchall(self):
        return self.rows


def _gia_lap(monkeypatch, rows, log):
    @contextmanager
    def conn(_db, **_kw):
        class C:
            def cursor(self, as_dict=False):
                return _Cur(rows, log)
        yield C()

    monkeypatch.setattr(k, "_db_dich", lambda tk: "DB")
    monkeypatch.setattr(k, "sqlserver_conn_dich", conn)


def test_kiem_truoc_phan_loai_va_chi_doc(monkeypatch, auth_headers):
    rows = [
        _row("1", "09"),                                                   # đủ
        _row("2", "03", DiemKQLyThuyet=None, DiemKQMoPhong=None, DiemKQHinh=None,
             DiemKQTienLui=None, DiemKQThucHanh=None, KetLuanCSDT=None,
             TGThucHanhHinh=None, QDThucHanhHinh=None, TGThucHanhDuong=None, TongQDThucHanh=None),
        _row("3", "10", DiemKQTienLui=None),                               # thiếu môn
        _row("4", "03", hang="A1", DiemKQLyThuyet=None),                   # mô tô → bỏ ra
    ]
    log: list = []
    _gia_lap(monkeypatch, rows, log)
    r = client.get("/local/ketqua/kiem-truoc?ma_kh=KX", headers=auth_headers)
    assert r.status_code == 200
    j = r.json()
    assert (j["tong"], j["du"], j["mo_to_bo_qua"]) == (3, 1, 1)
    assert {t["ma_dk"] for t in j["thieu"]} == {"2", "3"}
    assert j["dem"]["chua_co_diem"] == 1 and j["dem"]["thieu_mon"] == 1
    assert j["dem"]["thieu_gio_km"] == 1 and j["dem"]["thieu_ket_luan"] == 0  # HV 2 là 03 → không tính kết luận
    # chỉ SELECT, chỉ 4 trạng thái 03/04/09/10 (12/13/14/90 không vào truy vấn)
    assert len(log) == 1 and log[0][0].lstrip().upper().startswith("SELECT")
    assert log[0][1] == ("KX", "03", "04", "09", "10")


def test_kiem_truoc_canh_bao_vang_giờ_km_duong(monkeypatch, auth_headers):
    rows = [
        _row("5", "10", DiemKQTienLui=None, TGThucHanhDuong=18, TongQDThucHanh=700),  # thiếu môn + dưới gợi ý
        _row("6", "10", DiemKQTienLui=None),                                          # thiếu môn, đủ giờ/km
    ]
    _gia_lap(monkeypatch, rows, [])
    j = client.get("/local/ketqua/kiem-truoc?ma_kh=KX", headers=auth_headers).json()
    cb = {t["ma_dk"]: t["canh_bao"] for t in j["thieu"]}
    assert cb["5"] == [{"loai": "gio_duong", "gia_tri": 18.0, "goi_y": 20},
                       {"loai": "km_duong", "gia_tri": 700.0, "goi_y": 810}]
    assert cb["6"] == []
    # cảnh báo KHÔNG biến HV đủ điều kiện thành thiếu
    j2 = client.get("/local/ketqua/kiem-truoc?ma_kh=KX", headers=auth_headers).json()
    assert all("thieu_gio_km" not in t["ly_do"] for t in j2["thieu"])


def test_canh_bao_duong_don_vi():
    assert q.canh_bao_duong(None, None, "B") == []                       # trống = thieu_gio_km, không cảnh báo
    assert q.canh_bao_duong(5, 100, None) == []                           # hạng lạ: không có mức gợi ý
    assert q.canh_bao_duong(12, 710, "B01") == []                         # đúng mức biên → không cảnh báo
    assert [w["loai"] for w in q.canh_bao_duong(11, 700, "B01")] == ["gio_duong", "km_duong"]


def test_luat_mon_bat_buoc_chi_doc(auth_headers):
    j = client.get("/local/ketqua/luat", headers=auth_headers).json()
    assert j == {"mon_bat_buoc": ["ly_thuyet", "mo_phong", "hinh", "tien_lui", "duong"]}
    assert client.get("/local/ketqua/luat").status_code in (401, 403)


def test_kiem_truoc_khoa_khong_co_hv(monkeypatch, auth_headers):
    _gia_lap(monkeypatch, [], [])
    j = client.get("/local/ketqua/kiem-truoc?ma_kh=KX", headers=auth_headers).json()
    assert (j["tong"], j["du"], j["thieu"]) == (0, 0, [])


def test_kiem_truoc_thieu_ma_kh_422(auth_headers):
    assert client.get("/local/ketqua/kiem-truoc", headers=auth_headers).status_code == 422


def test_kiem_truoc_chua_dang_nhap():
    assert client.get("/local/ketqua/kiem-truoc?ma_kh=KX").status_code in (401, 403)


def test_tt04_chua_co_diem_va_09_diem_rong_bat_thuong():
    assert q.LY_DO_CHUA_CO_DIEM in q.hv_chua_du(_hv(tt_xuly="04", ket_luan=None, diem=dict(_RONG)))["ly_do"]
    # 09/10 mà điểm rỗng hết (bất thường): ra "chưa có điểm" + "thiếu kết luận", không im lặng
    r = q.hv_chua_du(_hv(tt_xuly="09", ket_luan=None, diem=dict(_RONG)))
    assert r["ly_do"] == [q.LY_DO_CHUA_CO_DIEM, q.LY_DO_THIEU_KET_LUAN]
