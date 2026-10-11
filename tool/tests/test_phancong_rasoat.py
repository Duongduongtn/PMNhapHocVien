"""PCG-05 — rà soát khóa: đếm GV/xe trong danh sách, chưa phân công/ghép, ngoài danh sách. Chỉ đọc."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class _Cur:
    def __init__(self, db):
        self.db, self.res = db, []

    def execute(self, sql, params=None):
        self.db.log.append(sql)
        s = " ".join(sql.split())
        if "QTHT_ThamSoHT" in s:
            self.res = [{"GiaTriTS": "75032"}]
        elif "JOIN dbo.KhoaHoc_GiaoVien g" in s:
            self.res = self.db.gv
        elif "JOIN dbo.KhoaHoc_XeTap x" in s:
            self.res = self.db.xe
        elif "FROM dbo.KhoaHoc kh WHERE" in s:
            self.res = self.db.khoa
        else:
            self.res = []

    def fetchall(self):
        return self.res

    def fetchone(self):
        return self.res[0] if self.res else None


class _Db:
    def __init__(self):
        self.log = []
        k = lambda ma, ten: {"MaKH": ma, "TenKH": ten, "HangGPLX": "C1", "HangDT": "C1",
                             "NgayKG": "2026-10-01", "NgayBG": "2026-12-20", "dkkh": 0}
        self.khoa = [k("K1", "C1-K15"), k("K2", "C1-K14"), k("K3", "C1-K13")]
        self.gv = [
            {"MaKH": "K1", "MaGV": "A", "la_ds": 1}, {"MaKH": "K1", "MaGV": "A", "la_ds": 0},
            {"MaKH": "K2", "MaGV": "A", "la_ds": 1}, {"MaKH": "K2", "MaGV": "B", "la_ds": 0},   # A chưa PC; B ngoài DS
        ]
        self.xe = [
            {"MaKH": "K1", "BienSoXe": "X1", "la_ds": 1}, {"MaKH": "K1", "BienSoXe": "X1", "la_ds": 0},
            {"MaKH": "K2", "BienSoXe": "X2", "la_ds": 0},                                          # ghép ngoài DS (khóa cũ)
        ]


class _Conn:
    def __init__(self, db):
        self._cur = _Cur(db)

    def cursor(self, as_dict=False):
        return self._cur

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_ra_soat_dem_dung_va_ket_luan(auth_headers, monkeypatch):
    db = _Db()
    monkeypatch.setattr("app.routers.phancong._db_dich", lambda tk: "GPLX_CDB_CSDT")
    monkeypatch.setattr("app.routers.phancong.sqlserver_conn_dich", lambda d, autocommit=False: _Conn(db))
    r = client.get("/local/phancong/ra-soat", headers=auth_headers)
    assert r.status_code == 200, r.text
    j = {x["ma_kh"]: x for x in r.json()}
    assert (j["K1"]["gv_ds"], j["K1"]["gv_chua_pc"], j["K1"]["xe_chua_ghep"], j["K1"]["can_xu_ly"]) == (1, 0, 0, False)
    k2 = j["K2"]
    assert (k2["gv_chua_pc"], k2["pc_ngoai_ds"], k2["xe_ds"], k2["ghep_ngoai_ds"], k2["can_xu_ly"]) == (1, 1, 0, 1, True)
    assert j["K3"]["gv_ds"] == 0 and j["K3"]["can_xu_ly"] is True       # khóa chưa có GV → Cần xử lý
    assert not any(s.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE", "EXEC")) for s in db.log)


def test_pcg05_xe_chua_ghep_chi_la_thong_tin_ket_luan_van_on(auth_headers, monkeypatch):   # CHANGES #58 (E-7)
    db = _Db()
    db.xe.append({"MaKH": "K1", "BienSoXe": "X9", "la_ds": 1})        # K1 có thêm 1 xe trong danh sách, chưa ghép cho ai
    monkeypatch.setattr("app.routers.phancong._db_dich", lambda tk: "GPLX_CDB_CSDT")
    monkeypatch.setattr("app.routers.phancong.sqlserver_conn_dich", lambda d, autocommit=False: _Conn(db))
    j = {x["ma_kh"]: x for x in client.get("/local/phancong/ra-soat", headers=auth_headers).json()}
    assert j["K1"]["xe_chua_ghep"] == 1 and j["K1"]["can_xu_ly"] is False
