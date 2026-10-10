"""PCG-04 (3/4) — task 87: POST /ghi (server kiểm lại + ghi từng dòng) + nhật ký.

Cursor giả ghi lại mọi `EXEC`; ghi thật vào CDB production → nghiệm thu máy CSDT (mức 1).
Bất biến khóa ở đây: cổng xác nhận, 409 khi còn ⛔/⚠ chưa xác nhận, thứ tự xóa→thêm→sửa,
tham số đúng (TenMonHoc "6", MaMonHoc NULL, GhiChu ''), giữ NguoiTao khi sửa, lỗi giữa chừng
trả đã/chưa ghi, và KHÔNG BAO GIỜ gọi SP xóa lan.
"""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app import phancong_nhat_ky as nk
from app.main import app

client = TestClient(app)
CAM = ("usp_KhoaHoc_GiaoVien_Delete", "usp_KhoaHoc_XeTap_Delete", "usp_VoHieuLuc")
KHOA = {"MaKH": "75032K260010", "TenKH": "C1-K15", "HangGPLX": "C1", "HangDT": "C1",
        "NgayKG": "2026-10-01", "NgayBG": "2026-12-20", "TongSoHV": 72, "dkkh": 0}
T0, T1 = datetime(2026, 10, 15), datetime(2026, 12, 20)


@pytest.fixture(autouse=True)
def _nhat_ky_tam(tmp_path, monkeypatch):
    monkeypatch.setattr(nk, "DB_PATH", tmp_path / "pc_nk.sqlite")


class _Db:
    def __init__(self, fail_at=None, warn_dkkh=False):
        self.execs, self.n_exec, self.fail_at = [], 0, fail_at
        self.khoa = dict(KHOA, dkkh=1 if warn_dkkh else 0)
        self.gv = [{"MaGV": m, "HoTenDem": "Trần Văn", "TenGV": t, "LoaiHinh_DaoTao": "TH", "TrangThai": 1,
                    "HangGPLX": "C1", "CacHangGPLXDuocDT": "B, C1"} for m, t in (("75032101", "An"), ("75032102", "Bình"))]
        gp = datetime(2027, 6, 30)
        self.xe = [{"BienSoXe": b, "HangGPLXXe": "C1", "NgayHHGPXTL": gp, "NgayHHGCNKD": gp, "TrangThai": 1}
                   for b in ("93C-1", "93C-2")]
        self.cur_gv = [
            {"MaLichLV": 1, "MaGV": "75032101", "la_ds": 1, "NgayBD": None, "NgayKT": None, "MaMonHoc": None, "TenMonHoc": None},
            {"MaLichLV": 2, "MaGV": "75032101", "la_ds": 0, "NgayBD": T0, "NgayKT": T1, "MaMonHoc": None, "TenMonHoc": "6"}]
        self.cur_xe = [
            {"MaLichSD": 10, "BienSoXe": "93C-1", "MaGV": None, "la_ds": 1, "NgayBD": None, "NgayKT": None, "DiaDiem": None},
            {"MaLichSD": 11, "BienSoXe": "93C-1", "MaGV": "75032101", "la_ds": 0, "NgayBD": T0, "NgayKT": T1, "DiaDiem": "tại trung tâm"}]


class _Cur:
    def __init__(self, db):
        self.db, self.res = db, []

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if s.startswith("EXEC dbo."):
            if self.db.fail_at is not None and self.db.n_exec == self.db.fail_at:
                self.db.n_exec += 1
                raise RuntimeError("DB lỗi giả lập")
            self.db.n_exec += 1
            self.db.execs.append((s, params))
            self.res = []
        elif "QTHT_ThamSoHT" in s:
            self.res = [{"GiaTriTS": "75032"}]
        elif "FROM dbo.DM_MonHoc" in s:
            self.res = [{"MaMH": 4, "TenMH": "Luật GT đường bộ"}, {"MaMH": 6, "TenMH": "Thực hành lái xe"}]
        elif "FROM dbo.KhoaHoc kh WHERE kh.MaCSDT" in s:
            self.res = [self.db.khoa]
        elif "KhoaHoc_GiaoVien g JOIN dbo.KhoaHoc kh" in s or "KhoaHoc_XeTap x JOIN dbo.KhoaHoc kh" in s:
            self.res = []
        elif "FROM dbo.KhoaHoc_GiaoVien g WHERE g.MaKH" in s:
            self.res = list(self.db.cur_gv)
        elif "FROM dbo.KhoaHoc_XeTap x WHERE x.MaKH" in s:
            self.res = list(self.db.cur_xe)
        elif s.startswith("SELECT NguoiTao, NgayTao, SoHV"):
            self.res = [{"NguoiTao": "admin", "NgayTao": datetime(2026, 9, 1), "SoHV": None, "NgayHL": None,
                         "NgayHetHL": None, "BienSoXe": "", "GhiChu": ""}]
        elif s.startswith("SELECT NguoiTao, NgayTao, MaHV"):
            self.res = [{"NguoiTao": "admin", "NgayTao": datetime(2026, 9, 1), "MaHV": None, "TenHV": None,
                         "DiaDiem": "tại trung tâm", "GhiChu": ""}]
        elif s.startswith("SELECT TOP 1 DiaDiem"):
            self.res = [{"DiaDiem": "tại trung tâm Thành Đạt và trên đường"}]
        elif "FROM dbo.GiaoVien" in s:
            self.res = list(self.db.gv)
        elif "FROM dbo.XeTap" in s:
            self.res = list(self.db.xe)
        else:
            self.res = []

    def fetchall(self):
        return self.res

    def fetchone(self):
        return self.res[0] if self.res else None


class _Conn:
    def __init__(self, db):
        self._c = _Cur(db)

    def cursor(self, as_dict=False):
        return self._c

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _patch(monkeypatch, db):
    monkeypatch.setattr("app.routers.phancong._db_dich", lambda tk: "GPLX_CDB_CSDT")
    monkeypatch.setattr("app.routers.phancong.sqlserver_conn_dich", lambda d, autocommit=False: _Conn(db))


def hien_tai():
    return {"ma_kh": "75032K260010", "gv_khoa": ["75032101"],
            "pc": [{"id": 2, "ma": "75032101", "mon": [6], "tu": "2026-10-15T00:00", "den": "2026-12-20T00:00"}],
            "xe_khoa": ["93C-1"],
            "ghep": [{"id": 11, "ma": "75032101", "xe": "93C-1", "tu": "2026-10-15T00:00", "den": "2026-12-20T00:00"}]}


def them_gv102():
    d = hien_tai()
    d["gv_khoa"].append("75032102")
    d["pc"].append({"id": "n1", "ma": "75032102", "mon": [6], "tu": "2026-10-15T00:00", "den": "2026-12-20T00:00"})
    d["xe_khoa"].append("93C-2")
    d["ghep"].append({"id": "n2", "ma": "75032102", "xe": "93C-2", "tu": "2026-10-15T00:00", "den": "2026-12-20T00:00"})
    return d


def post(body, ok_csdl=True, ok_cb=False):
    return client.post("/local/phancong/ghi", json={**body, "xac_nhan_csdl_that": ok_csdl, "da_xem_canh_bao": ok_cb})


def khong_sp_xoa_lan(db):
    assert not any(any(c in s for c in CAM) for s, _ in db.execs)


# ── cổng ──
def test_thieu_xac_nhan_csdl_that_400_khong_dung_gi(auth_headers, monkeypatch):
    db = _Db(); _patch(monkeypatch, db)
    r = client.post("/local/phancong/ghi", headers=auth_headers, json={**them_gv102(), "xac_nhan_csdl_that": False})
    assert r.status_code == 400 and r.json()["detail"]["loi"] == "thieu_xac_nhan_csdl_that" and not db.execs


def test_con_loi_chan_409_khong_ghi(auth_headers, monkeypatch):
    db = _Db(); _patch(monkeypatch, db)
    d = them_gv102(); d["gv_khoa"] = ["75032101"]                 # phân công GV 102 nhưng GV chưa thuộc khóa
    r = client.post("/local/phancong/ghi", headers=auth_headers, json={**d, "xac_nhan_csdl_that": True})
    assert r.status_code == 409 and r.json()["detail"]["loi"] == "con_loi_chan" and not db.execs


def test_con_canh_bao_thieu_xac_nhan_409(auth_headers, monkeypatch):
    db = _Db(warn_dkkh=True); _patch(monkeypatch, db)              # khóa đã DKKH → ⚠
    r = client.post("/local/phancong/ghi", headers=auth_headers, json={**them_gv102(), "xac_nhan_csdl_that": True})
    assert r.status_code == 409 and r.json()["detail"]["loi"] == "thieu_xac_nhan_canh_bao" and not db.execs
    r2 = client.post("/local/phancong/ghi", headers=auth_headers,
                     json={**them_gv102(), "xac_nhan_csdl_that": True, "da_xem_canh_bao": True})
    assert r2.status_code == 200 and r2.json()["ok"] is True and db.execs


def test_khong_thay_doi_thi_khong_ghi(auth_headers, monkeypatch):
    db = _Db(); _patch(monkeypatch, db)
    r = client.post("/local/phancong/ghi", headers=auth_headers, json={**hien_tai(), "xac_nhan_csdl_that": True})
    assert r.status_code == 200 and r.json()["da_ghi"] == [] and not db.execs


# ── ghi ──
def test_them_dung_thu_tu_va_tham_so(auth_headers, monkeypatch):
    db = _Db(); _patch(monkeypatch, db)
    r = client.post("/local/phancong/ghi", headers=auth_headers, json={**them_gv102(), "xac_nhan_csdl_that": True})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["ok"] is True and [x["loai"] for x in j["da_ghi"]] == ["gv_them", "xe_them", "pc_them", "gh_them"]
    sps = [s.split()[1].replace("dbo.", "") for s, _ in db.execs]
    assert sps == ["usp_KhoaHoc_GiaoVien_Insert", "usp_KhoaHoc_XeTap_Insert",
                   "usp_LichLV_KhoaHoc_GiaoVien_Insert", "LichSD_KhoaHoc_XeTap_Insert"]
    pc_sql, pc_p = db.execs[2]
    assert "@TenMonHoc=%s" in pc_sql and "@MaMonHoc=%s" in pc_sql
    cols = [c.split("=")[0].lstrip("@") for c in pc_sql.split("dbo.usp_LichLV_KhoaHoc_GiaoVien_Insert ")[1].split(", ")]
    d = dict(zip(cols, pc_p))
    assert d["TenMonHoc"] == "6" and d["MaMonHoc"] is None and d["GhiChu"] == "" and d["IsKhoaHocGiaoVien"] == 0
    assert d["NguoiTao"] == "op-test" and d["MaGV"] == "75032102" and d["NgayBD"] == datetime(2026, 10, 15)
    gh_sql, gh_p = db.execs[3]
    gcols = [c.split("=")[0].lstrip("@") for c in gh_sql.split("dbo.LichSD_KhoaHoc_XeTap_Insert ")[1].split(", ")]
    g = dict(zip(gcols, gh_p))
    assert g["BienSoXe"] == "93C-2" and g["IsKhoaHocXeTap"] == 0 and g["DiaDiem"] == "tại trung tâm Thành Đạt và trên đường"
    khong_sp_xoa_lan(db)


def test_xoa_theo_ma_lich_tung_dong_khong_sp_xoa_lan(auth_headers, monkeypatch):
    db = _Db(); _patch(monkeypatch, db)
    d = hien_tai(); d["pc"] = []; d["ghep"] = []                    # xóa phân công + ghép xe; GV/xe giữ
    r = client.post("/local/phancong/ghi", headers=auth_headers,
                    json={**d, "xac_nhan_csdl_that": True, "da_xem_canh_bao": True})
    assert r.status_code == 200, r.text
    assert [x["loai"] for x in r.json()["da_ghi"]] == ["gh_xoa", "pc_xoa"]
    assert db.execs[0] == ("EXEC dbo.usp_LSD_KhoaHoc_Xetap_Delete @MaLichSD=%s", (11,))
    assert db.execs[1] == ("EXEC dbo.usp_LLV_KhoaHoc_GiaoVien_Delete @MaLichLV=%s", (2,))
    khong_sp_xoa_lan(db)


def test_go_gv_xoa_phan_cong_roi_dong_danh_sach(auth_headers, monkeypatch):
    db = _Db(); _patch(monkeypatch, db)
    d = hien_tai(); d["gv_khoa"] = []; d["pc"] = []; d["ghep"] = []
    r = client.post("/local/phancong/ghi", headers=auth_headers,
                    json={**d, "xac_nhan_csdl_that": True, "da_xem_canh_bao": True})
    assert r.status_code == 200, r.text
    assert [x["loai"] for x in r.json()["da_ghi"]] == ["gh_xoa", "pc_xoa", "gv_go"]
    assert [p for _, p in db.execs] == [(11,), (2,), (1,)]          # MaLichSD 11 → MaLichLV 2 → MaLichLV 1 (dòng danh sách)
    khong_sp_xoa_lan(db)


def test_sua_giu_nguoi_tao_goc(auth_headers, monkeypatch):
    db = _Db(); _patch(monkeypatch, db)
    d = hien_tai(); d["pc"][0]["den"] = "2026-12-10T00:00"           # đổi ngày kết thúc (⚠ TH chưa tới bế giảng)
    d["ghep"][0]["den"] = "2026-12-10T00:00"
    r = client.post("/local/phancong/ghi", headers=auth_headers,
                    json={**d, "xac_nhan_csdl_that": True, "da_xem_canh_bao": True})
    assert r.status_code == 200, r.text
    assert [x["loai"] for x in r.json()["da_ghi"]] == ["pc_sua", "gh_sua"]
    sql, p = db.execs[0]
    cols = [c.split("=")[0].lstrip("@") for c in sql.split("dbo.usp_LichLV_KhoaHoc_GiaoVien_Update ")[1].split(", ")]
    u = dict(zip(cols, p))
    assert u["NguoiTao"] == "admin" and u["NgayTao"] == datetime(2026, 9, 1)     # không đè người tạo gốc
    assert u["NguoiSua"] == "op-test" and u["MaLichLV"] == 2 and u["NgayKT"] == datetime(2026, 12, 10)


def test_loi_giua_chung_tra_da_ghi_va_chua_ghi_va_nhat_ky(auth_headers, monkeypatch):
    db = _Db(fail_at=1); _patch(monkeypatch, db)
    r = client.post("/local/phancong/ghi", headers=auth_headers, json={**them_gv102(), "xac_nhan_csdl_that": True})
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is False and len(j["da_ghi"]) == 1 and len(j["chua_ghi"]) == 3 and j["loi"] == "RuntimeError"
    log = nk.gan_day("75032K260010")
    assert len(log) == 1 and log[0]["trang_thai"] == "loi_giua_chung" and log[0]["nguoi"] == "op-test"
    assert log[0]["thay_doi"]["gv_them"] == [{"ma": "75032102"}]
    g = client.get("/local/phancong/nhat-ky?ma_kh=75032K260010", headers=auth_headers).json()
    assert g and g[0]["id"] == log[0]["id"]


def test_ghi_thanh_cong_ghi_nhat_ky_xong(auth_headers, monkeypatch):
    db = _Db(); _patch(monkeypatch, db)
    client.post("/local/phancong/ghi", headers=auth_headers, json={**them_gv102(), "xac_nhan_csdl_that": True})
    log = nk.gan_day("75032K260010")
    assert log[0]["trang_thai"] == "xong" and len(log[0]["ket_qua"]["da_ghi"]) == 4
