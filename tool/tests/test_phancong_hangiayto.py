"""PCG-06 (task 121) — hạn giấy tờ xe/GPLX GV + GV/xe ngưng còn phân công. Chỉ đọc, cursor giả."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date

from fastapi.testclient import TestClient

from app import phancong_hangiayto as hg
from app import phancong_rules as rules
from app.main import app
from app.routers import phancong as pc

client = TestClient(app)
HOM_NAY = date(2026, 10, 12)


# ---- luật thuần --------------------------------------------------------------
def test_phan_loai_han_bien_va_ngay_hom_nay():
    f = lambda d, n=30: rules.phan_loai_han(d, HOM_NAY, n)
    assert f("2026-10-11") == rules.HAN_HET      # hôm qua → quá hạn
    assert f("2026-10-12") == rules.HAN_SAP      # đúng hôm nay vẫn dùng được
    assert f("2026-11-11") == rules.HAN_SAP      # đúng biên +30 ngày
    assert f("2026-11-12") == rules.HAN_CON      # +31 ngày
    assert f("") == rules.HAN_CHUA and f(None) == rules.HAN_CHUA


def test_phan_loai_han_theo_nguong():
    assert rules.phan_loai_han("2026-10-20", HOM_NAY, 8) == rules.HAN_SAP
    assert rules.phan_loai_han("2026-10-20", HOM_NAY, 7) == rules.HAN_CON


# ---- cursor giả --------------------------------------------------------------
class _Cur:
    def __init__(self, db):
        self.db, self.res = db, []

    def execute(self, sql, params=()):
        self.db.log.append((" ".join(sql.split()), params))
        s = " ".join(sql.split())
        if "FROM dbo.KhoaHoc_XeTap" in s:
            self.res = self.db.xe_khoa
        elif "FROM dbo.KhoaHoc_GiaoVien" in s:
            self.res = self.db.gv_khoa
        elif "FROM dbo.XeTap" in s:
            self.res = self.db.xe
        elif "FROM dbo.GiaoVien" in s:
            self.res = self.db.gv
        else:
            self.res = []

    def fetchall(self):
        return self.res

    def fetchone(self):
        return self.res[0] if self.res else None


class _Db:
    def __init__(self, xe=(), gv=(), xe_khoa=(), gv_khoa=()):
        self.log = []
        self.xe, self.gv, self.xe_khoa, self.gv_khoa = list(xe), list(gv), list(xe_khoa), list(gv_khoa)

    def cursor(self, as_dict=False):
        return _Cur(self)


def _xe(bs, pxtl=None, kd=None, hang="B1"):
    return {"BienSoXe": bs, "HangGPLXXe": hang, "NgayHHGPXTL": pxtl, "NgayHHGCNKD": kd}


def _gv(ma, ngay=None, ho="Nguyễn Văn", ten="An"):
    return {"MaGV": ma, "HoTenDem": ho, "TenGV": ten, "HangGPLX": "B2", "NgayHHGPLX": ngay}


def _k(ma_kh, **kw):
    return {"MaKH": ma_kh, "TenKH": f"Khóa {ma_kh}", **kw}


def test_nhom_xe_do_vang_gop_cung_ngay_chua_khai_va_khoa_dang_dung():
    db = _Db(
        xe=[_xe("A1", "2026-10-01", "2026-10-01"),        # cả hai loại cùng ngày, quá hạn → gộp 1 dòng
            _xe("A2", "2026-10-20", "2027-05-01"),        # chỉ giấy phép sắp hết
            _xe("A3", "2027-06-01", "2027-06-01"),        # còn hạn xa → không hiện
            _xe("A4", None, None),                        # chưa khai
            _xe("A5", None, "2026-09-30")],               # một ngày trống, một ngày quá hạn
        xe_khoa=[{"BienSoXe": "A1", "HangGPLXXe": "B1", "TT_DM": 1, **_k("K1")},
                 {"BienSoXe": "A1", "HangGPLXXe": "B1", "TT_DM": 1, **_k("K1")},   # trùng → gộp
                 {"BienSoXe": "A1", "HangGPLXXe": "B1", "TT_DM": 1, **_k("K2")}],
    )
    r = hg.han_giay_to(db, "75032", HOM_NAY, 30)
    het = {d["bien_so"]: d for d in r["xe"]["het_han"]}
    assert set(het) == {"A1", "A5"}
    assert [g["giay"] for g in het["A1"]["giay"]] == ["gpxtl", "gcnkd"]       # một dòng, nêu cả hai loại
    assert het["A1"]["giay"][0]["con_ngay"] == -11
    assert [k["ma_kh"] for k in het["A1"]["khoa"]] == ["K1", "K2"]
    assert [g["giay"] for g in het["A5"]["giay"]] == ["gcnkd"]
    assert [d["bien_so"] for d in r["xe"]["sap_het"]] == ["A2"]
    assert r["xe"]["sap_het"][0]["giay"][0]["con_ngay"] == 8
    assert [d["bien_so"] for d in r["xe"]["chua_khai"]] == ["A4"]
    assert r["dem"]["xe_het_han"] == 2 and r["dem"]["xe_sap_het"] == 1 and r["dem"]["xe_chua_khai"] == 1
    assert [d["bien_so"] for d in r["xe"]["het_han"]] == ["A5", "A1"]          # xếp theo ngày hết hạn sớm nhất
    assert het["A5"]["khoa"] == []     # không ở khóa nào → rỗng


def test_nhom_giao_vien():
    db = _Db(
        gv=[_gv("G1", "2026-09-01"), _gv("G2", "2026-10-30", ten="Bình"), _gv("G3", "2028-01-01"), _gv("G4", None)],
        gv_khoa=[{"MaGV": "G2", "HoTenDem": "Nguyễn Văn", "TenGV": "Bình", "HangGPLX": "B2",
                  "TT_DM": 1, **_k("K9")}],
    )
    r = hg.han_giay_to(db, "75032", HOM_NAY, 30)
    assert [d["ma_gv"] for d in r["gv"]["het_han"]] == ["G1"]
    assert r["gv"]["het_han"][0]["ho_ten"] == "Nguyễn Văn An"
    assert [d["ma_gv"] for d in r["gv"]["sap_het"]] == ["G2"]
    assert r["gv"]["sap_het"][0]["khoa"] == [{"ma_kh": "K9", "ten_kh": "Khóa K9"}]
    assert [d["ma_gv"] for d in r["gv"]["chua_khai"]] == ["G4"]


def test_nhom_ngung_con_phan_cong():
    db = _Db(
        xe_khoa=[{"BienSoXe": "X9", "HangGPLXXe": "C1", "TT_DM": 0, **_k("K1")},
                 {"BienSoXe": "X9", "HangGPLXXe": "C1", "TT_DM": 0, **_k("K2")},
                 {"BienSoXe": "X8", "HangGPLXXe": "C1", "TT_DM": 1, **_k("K1")}],     # còn hoạt động → không vào
        gv_khoa=[{"MaGV": "G9", "HoTenDem": "Lê", "TenGV": "Cường", "HangGPLX": "B2", "TT_DM": False, **_k("K3")}],
    )
    r = hg.han_giay_to(db, "75032", HOM_NAY, 30)
    assert [d["bien_so"] for d in r["ngung"]["xe"]] == ["X9"]
    assert [k["ma_kh"] for k in r["ngung"]["xe"][0]["khoa"]] == ["K1", "K2"]
    assert r["ngung"]["gv"][0]["ma_gv"] == "G9" and r["ngung"]["gv"][0]["ho_ten"] == "Lê Cường"
    assert r["dem"]["ngung_xe"] == 1 and r["dem"]["ngung_gv"] == 1


def test_khong_co_gi_sap_het_han_va_chi_doc():
    db = _Db(xe=[_xe("A3", "2027-06-01", "2027-06-01")], gv=[_gv("G3", "2028-01-01")])
    r = hg.han_giay_to(db, "75032", HOM_NAY, 30)
    assert all(v == 0 for v in r["dem"].values())
    assert db.log and all(s.upper().startswith("SELECT") for s, _ in db.log)      # chỉ SELECT
    assert all(p[0] == "75032" for _, p in db.log)                               # lọc MaCSDT, tham số hóa
    assert db.log[2][1][1] == "20261012"                                         # NgayBG >= hôm nay


# ---- endpoint -----------------------------------------------------------------
def _gia_lap(monkeypatch, db):
    @contextmanager
    def conn(_d, **_k):
        yield db

    monkeypatch.setattr(pc, "_db_dich", lambda tk: "DB")
    monkeypatch.setattr(pc, "sqlserver_conn_dich", conn)
    monkeypatch.setattr(pc, "_csdt", lambda c: "75032")


def test_endpoint_tra_ve_va_ngay_mac_dinh_30(monkeypatch, auth_headers):
    _gia_lap(monkeypatch, _Db(gv=[_gv("G1", "2020-01-01")]))
    r = client.get("/local/phancong/han-giay-to", headers=auth_headers)
    assert r.status_code == 200
    j = r.json()
    assert j["nguong"] == 30 and j["dem"]["gv_het_han"] == 1


def test_endpoint_gioi_han_ngay(monkeypatch, auth_headers):
    _gia_lap(monkeypatch, _Db())
    assert client.get("/local/phancong/han-giay-to?ngay=0", headers=auth_headers).status_code == 422
    assert client.get("/local/phancong/han-giay-to?ngay=366", headers=auth_headers).status_code == 422
    assert client.get("/local/phancong/han-giay-to?ngay=365", headers=auth_headers).status_code == 200


def test_endpoint_chua_dang_nhap():
    assert client.get("/local/phancong/han-giay-to").status_code in (401, 403)
