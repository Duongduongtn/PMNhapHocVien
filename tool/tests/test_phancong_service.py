"""PCG-04 (2/4) — task 86: đọc CDB + `/kiem-tra` (không ghi). Cursor giả điều phối theo SQL."""
from datetime import datetime

from fastapi.testclient import TestClient

from app import phancong_service as svc
from app.main import app

client = TestClient(app)


# ── hàm thuần ──
def test_doc_mon_ba_dinh_dang():
    t2i = {"thực hành lái xe": 6, "luật gt đường bộ": 4}
    assert svc.doc_mon(6, "Thực hành lái xe", t2i) == [6]               # trước 07/2026
    assert svc.doc_mon(None, "5,9", t2i) == [5, 9]                      # từ 29/07/2026
    assert svc.doc_mon(None, "1, 8", t2i) == [1, 8]
    assert svc.doc_mon(None, "Luật GT đường bộ", t2i) == [4]            # tên
    assert svc.doc_mon(None, "", t2i) == [] and svc.doc_mon(None, "???", t2i) == []


def test_ghi_mon_sap_tang_khong_trung():
    assert svc.ghi_mon([8, 1, 8]) == "1,8"
    assert svc.ghi_mon([6]) == "6"


def test_hang_nhom_tach_hang_gp_het():
    assert svc.hang_nhom("B.01") == "B" and svc.hang_nhom("C1") == "C1" and svc.hang_nhom(None) == ""
    assert svc.tach_hang("B, C1") == ["B", "C1"] and svc.tach_hang(None) == []
    assert svc.gp_het_som_nhat(datetime(2027, 6, 30), datetime(2026, 11, 30)) == "2026-11-30"
    assert svc.gp_het_som_nhat(None, None) == ""
    assert svc.iso_dt(datetime(2026, 10, 7, 7, 30, 15)) == "2026-10-07T07:30"
    assert svc.iso_dt("2026-10-07 07:30:00") == "2026-10-07T07:30" and svc.iso_dt("2026-10-07") == "2026-10-07T00:00"


# ── cursor giả ──
KHOA = {"MaKH": "75032K260010", "TenKH": "C1-K15", "HangGPLX": "C1", "HangDT": "C1",
        "NgayKG": "2026-10-01", "NgayBG": "2026-12-20", "TongSoHV": 72, "dkkh": 0}


class _Cur:
    def __init__(self, db):
        self.db, self.res = db, []

    def execute(self, sql, params=None):
        self.db.log.append((sql, params))
        s = " ".join(sql.split())
        if "QTHT_ThamSoHT" in s:
            self.res = [{"GiaTriTS": "75032"}]
        elif "FROM dbo.DM_MonHoc" in s:
            self.res = [{"MaMH": 4, "TenMH": "Luật GT đường bộ"}, {"MaMH": 6, "TenMH": "Thực hành lái xe"}]
        elif "FROM dbo.KhoaHoc kh WHERE kh.MaCSDT" in s:
            ok = self.db.khoa and (params is None or len(params) < 2 or params[1] == KHOA["MaKH"] or "LIKE" in s)
            self.res = [KHOA] if ok else []
        elif "FROM dbo.KhoaHoc_GiaoVien g JOIN dbo.KhoaHoc kh" in s:
            self.res = list(self.db.ban_gv)
        elif "FROM dbo.KhoaHoc_XeTap x JOIN dbo.KhoaHoc kh" in s:
            self.res = list(self.db.ban_xe)
        elif "FROM dbo.KhoaHoc_GiaoVien g WHERE g.MaKH" in s:
            self.res = list(self.db.cur_gv)
        elif "FROM dbo.KhoaHoc_XeTap x WHERE x.MaKH" in s:
            self.res = list(self.db.cur_xe)
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


class _Db:
    def __init__(self, **kw):
        self.log, self.khoa = [], True
        self.gv = [
            {"MaGV": "75032101", "HoTenDem": "Trần Văn", "TenGV": "An", "LoaiHinh_DaoTao": "TH", "TrangThai": 1,
             "HangGPLX": "C1", "CacHangGPLXDuocDT": "B, C1"},
        ]
        self.xe = [{"BienSoXe": "93C-1", "HangGPLXXe": "C1", "NgayHHGPXTL": datetime(2027, 6, 30),
                    "NgayHHGCNKD": datetime(2027, 6, 30), "TrangThai": 1}]
        self.ban_gv, self.ban_xe, self.cur_gv, self.cur_xe = [], [], [], []
        self.__dict__.update(kw)


class _Conn:
    def __init__(self, db):
        self._cur = _Cur(db)

    def cursor(self, as_dict=False):
        return self._cur

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _patch(monkeypatch, db):
    monkeypatch.setattr("app.routers.phancong._db_dich", lambda tk: "GPLX_CDB_CSDT")
    monkeypatch.setattr("app.routers.phancong.sqlserver_conn_dich", lambda d, autocommit=False: _Conn(db))


def _nhap(**kw):
    b = {"ma_kh": "75032K260010", "gv_khoa": ["75032101"],
         "pc": [{"id": 1, "ma": "75032101", "mon": [6], "tu": "2026-10-15T00:00", "den": "2026-12-20T00:00"}],
         "xe_khoa": ["93C-1"],
         "ghep": [{"ma": "75032101", "xe": "93C-1", "tu": "2026-10-15T00:00", "den": "2026-12-20T00:00"}]}
    b.update(kw)
    return b


# ── endpoint ──
def test_kiem_tra_hop_le_khong_loi(auth_headers, monkeypatch):
    db = _Db()
    _patch(monkeypatch, db)
    r = client.post("/local/phancong/kiem-tra", headers=auth_headers, json=_nhap())
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["co_chan"] is False and j["tom_tat"]["chan"] == 0 and j["tom_tat"]["canh_bao"] == 0
    assert not any(s.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE", "EXEC")) for s, _ in db.log)


def test_kiem_tra_trung_khoa_khac_va_loai_tru_khoa_dang_sua(auth_headers, monkeypatch):
    ban = [{"MaGV": "75032101", "MaKH": "75032K260005", "TenKH": "B-K148", "NgayBD": datetime(2026, 8, 22),
            "NgayKT": datetime(2026, 10, 20), "NgayBG": "2026-10-20"}]
    db = _Db(ban_gv=ban)
    _patch(monkeypatch, db)
    r = client.post("/local/phancong/kiem-tra", headers=auth_headers, json=_nhap())
    j = r.json()
    assert j["co_chan"] is False                       # trùng chỉ cảnh báo — vẫn ghi được
    assert any(v["ma"] == "gv_trung_khoa_khac" and v["muc"] == "canh_bao" and "B-K148" in v["noi_dung"] for v in j["vande"])
    # SQL "bận" phải loại chính khóa đang sửa (bản nháp đã chứa trạng thái khóa này)
    sqls = [(s, p) for s, p in db.log if "KhoaHoc_GiaoVien g JOIN" in " ".join(s.split())]
    assert sqls and "g.MaKH <> %s" in " ".join(sqls[0][0].split()) and sqls[0][1][0] == "75032K260010"


def test_kiem_tra_xe_het_han_va_gv_ngoai_danh_sach(auth_headers, monkeypatch):
    db = _Db(xe=[{"BienSoXe": "93C-1", "HangGPLXXe": "C1", "NgayHHGPXTL": datetime(2026, 11, 30),
                  "NgayHHGCNKD": datetime(2027, 1, 1), "TrangThai": 1}])
    _patch(monkeypatch, db)
    j = client.post("/local/phancong/kiem-tra", headers=auth_headers, json=_nhap(gv_khoa=[])).json()
    ma = {v["ma"] for v in j["vande"] if v["muc"] == "chan"}
    assert {"xe_het_han", "gv_ngoai_khoa"} <= ma


def test_kiem_tra_khoa_khong_ton_tai_404(auth_headers, monkeypatch):
    _patch(monkeypatch, _Db(khoa=False))
    r = client.post("/local/phancong/kiem-tra", headers=auth_headers, json=_nhap())
    assert r.status_code == 404


def test_hien_trang_doc_dung_hai_tang_va_dinh_dang_mon(auth_headers, monkeypatch):
    db = _Db(
        cur_gv=[
            {"MaLichLV": 1, "MaGV": "75032101", "la_ds": 1, "NgayBD": None, "NgayKT": None, "MaMonHoc": None, "TenMonHoc": None},
            {"MaLichLV": 2, "MaGV": "75032101", "la_ds": 0, "NgayBD": datetime(2026, 10, 15), "NgayKT": datetime(2026, 12, 20),
             "MaMonHoc": None, "TenMonHoc": "6"},
            {"MaLichLV": 3, "MaGV": "75032101", "la_ds": 0, "NgayBD": datetime(2026, 10, 2, 7, 30),
             "NgayKT": datetime(2026, 10, 2, 11, 30), "MaMonHoc": 4, "TenMonHoc": "Luật GT đường bộ"},
        ],
        cur_xe=[
            {"MaLichSD": 10, "BienSoXe": "93C-1", "MaGV": None, "la_ds": 1, "NgayBD": None, "NgayKT": None, "DiaDiem": None},
            {"MaLichSD": 11, "BienSoXe": "93C-1", "MaGV": "75032101", "la_ds": 0, "NgayBD": datetime(2026, 10, 15),
             "NgayKT": datetime(2026, 12, 20), "DiaDiem": "tại trung tâm"},
        ],
    )
    _patch(monkeypatch, db)
    j = client.get("/local/phancong/khoa/75032K260010", headers=auth_headers).json()
    assert j["khoa"]["hang_nhom"] == "C1" and j["khoa"]["kg"] == "2026-10-01"
    assert [g["ma"] for g in j["gv_khoa"]] == ["75032101"]
    assert [(p["mon"], p["tu"], p["den"]) for p in j["pc"]] == [
        ([6], "2026-10-15T00:00", "2026-12-20T00:00"), ([4], "2026-10-02T07:30", "2026-10-02T11:30")]
    assert [x["bs"] for x in j["xe_khoa"]] == ["93C-1"]
    assert j["ghep"][0]["ma"] == "75032101" and j["ghep"][0]["xe"] == "93C-1"


def test_danh_muc_gv_xe_kem_ban(auth_headers, monkeypatch):
    ban = [{"MaGV": "75032101", "MaKH": "75032K260005", "TenKH": "B-K148", "NgayBD": datetime(2026, 8, 22),
            "NgayKT": datetime(2026, 10, 20), "NgayBG": "2026-10-20"}]
    db = _Db(ban_gv=ban)
    _patch(monkeypatch, db)
    g = client.get("/local/phancong/giao-vien?ma_kh=75032K260010", headers=auth_headers).json()["giao_vien"]
    assert g[0]["ma"] == "75032101" and g[0]["ten"] == "Trần Văn An" and g[0]["loai"] == "TH"
    assert g[0]["hang_duoc_day"] == ["B", "C1"] and g[0]["ban"][0]["khoa"] == "B-K148"
    assert g[0]["hop_hang"] is True                      # khóa C1, GV được đào tạo B/C1 → hợp
    x = client.get("/local/phancong/xe?ma_kh=75032K260010", headers=auth_headers).json()["xe"]
    assert x[0]["bs"] == "93C-1" and x[0]["gp_het"] == "2027-06-30" and x[0]["ban"] == []


# ── Hạ mức dữ liệu cũ không đụng tới ──
def test_ha_muc_du_lieu_cu_chi_ap_cho_dong_giu_nguyen():
    hien = {"gv_khoa": [{"id": 1, "ma": "A"}], "xe_khoa": [], "pc": [
        {"id": 5, "ma": "A", "mon": [6], "tu": "2026-10-15T00:00", "den": "2026-12-20T00:00"}],
        "ghep": [{"id": 9, "ma": "A", "xe": "X1", "tu": "2026-10-15T00:00", "den": "2026-12-20T00:00"}]}
    pc = [{"id": 5, "ma": "A", "mon": [6], "tu": "2026-10-15T00:00", "den": "2026-12-20T00:00"},   # giữ nguyên
          {"id": None, "ma": "A", "mon": [4], "tu": "2026-10-02T00:00", "den": "2026-10-03T00:00"}]  # mới
    ghep = [{"ma": "A", "xe": "X1", "tu": "2026-10-15T00:00", "den": "2026-12-20T00:00"}]
    v = [{"muc": "chan", "ma": "xe_ngoai_khoa", "ref": "gh-A", "noi_dung": "Xe chưa thuộc danh sách"},
         {"muc": "chan", "ma": "gv_ngoai_khoa", "ref": "pc-None", "noi_dung": "mới"},
         {"muc": "chan", "ma": "thieu_mon", "ref": "pc-5", "noi_dung": "cũ"}]
    out = svc.ha_muc_du_lieu_cu(v, hien, ["A"], pc, [], ghep)
    assert out[0]["muc"] == "canh_bao" and out[0]["du_lieu_cu"] and out[0]["noi_dung"].startswith("Dữ liệu cũ")
    assert out[1]["muc"] == "chan" and "du_lieu_cu" not in out[1]                     # dòng mới vẫn chặn
    assert out[2]["muc"] == "canh_bao"                                                 # pc-5 giữ nguyên
    # sửa dòng cũ (đổi ngày) → hết được hạ mức
    pc2 = [{**pc[0], "den": "2026-12-19T00:00"}]
    assert svc.ha_muc_du_lieu_cu([v[2]], hien, ["A"], pc2, [], ghep)[0]["muc"] == "chan"


# ── PCG-03 (2/2) — gợi ý ghép xe ──
def test_goi_y_ghep_xe_chon_xe_hop_le_uu_tien_dung_hang_va_khong_ghi(auth_headers, monkeypatch):
    db = _Db(xe=[
        {"BienSoXe": "93C-0", "HangGPLXXe": "C1", "NgayHHGPXTL": datetime(2026, 11, 30),   # hết hạn trước bế giảng → loại
         "NgayHHGCNKD": datetime(2027, 6, 30), "TrangThai": 1},
        {"BienSoXe": "93C-1", "HangGPLXXe": "B1", "NgayHHGPXTL": datetime(2027, 6, 30),    # lệch hạng khóa C1 → cảnh báo
         "NgayHHGCNKD": datetime(2027, 6, 30), "TrangThai": 1},
        {"BienSoXe": "93C-2", "HangGPLXXe": "C1", "NgayHHGPXTL": datetime(2027, 6, 30),    # đúng hạng → được chọn
         "NgayHHGCNKD": datetime(2027, 6, 30), "TrangThai": 1},
    ])
    _patch(monkeypatch, db)
    body = _nhap(xe_khoa=["93C-0", "93C-1", "93C-2"], ghep=[])
    r = client.post("/local/phancong/goi-y-ghep-xe", headers=auth_headers, json=body)
    assert r.status_code == 200, r.text
    g = r.json()["goi_y"]
    assert len(g) == 1 and g[0]["ma"] == "75032101" and g[0]["xe"] == "93C-2" and g[0]["canh_bao"] == []
    assert g[0]["tu"] == "2026-10-15T00:00" and g[0]["den"] == "2026-12-20T00:00"
    assert not any(s.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE", "EXEC")) for s, _ in db.log)


def test_goi_y_ghep_xe_het_xe_hop_le_tra_ly_do(auth_headers, monkeypatch):
    db = _Db(xe=[{"BienSoXe": "93C-1", "HangGPLXXe": "C1", "NgayHHGPXTL": datetime(2026, 11, 30),
                  "NgayHHGCNKD": datetime(2027, 6, 30), "TrangThai": 1}])
    _patch(monkeypatch, db)
    j = client.post("/local/phancong/goi-y-ghep-xe", headers=auth_headers, json=_nhap(ghep=[])).json()
    assert j["goi_y"][0]["xe"] == "" and "không có xe" in j["goi_y"][0]["ly_do"].lower()


def test_goi_y_ghep_xe_bo_qua_gv_da_co_xe_va_moi_xe_mot_gv(auth_headers, monkeypatch):
    db = _Db(gv=[
        {"MaGV": "75032101", "HoTenDem": "Trần Văn", "TenGV": "An", "LoaiHinh_DaoTao": "TH", "TrangThai": 1,
         "HangGPLX": "C1", "CacHangGPLXDuocDT": "B, C1"},
        {"MaGV": "75032102", "HoTenDem": "Lê Văn", "TenGV": "Bình", "LoaiHinh_DaoTao": "TH", "TrangThai": 1,
         "HangGPLX": "C1", "CacHangGPLXDuocDT": "B, C1"},
    ])
    _patch(monkeypatch, db)
    pc2 = {"id": 2, "ma": "75032102", "mon": [6], "tu": "2026-10-15T00:00", "den": "2026-12-20T00:00"}
    base = _nhap(gv_khoa=["75032101", "75032102"], ghep=[])
    base["pc"].append(pc2)
    j = client.post("/local/phancong/goi-y-ghep-xe", headers=auth_headers, json=base).json()["goi_y"]
    assert [x["xe"] for x in j] == ["93C-1", ""]          # chỉ 1 xe → GV thứ hai không có xe
    base["ghep"] = [{"ma": "75032101", "xe": "93C-1", "tu": "2026-10-15T00:00", "den": "2026-12-20T00:00"}]
    j2 = client.post("/local/phancong/goi-y-ghep-xe", headers=auth_headers, json=base).json()["goi_y"]
    assert [x["ma"] for x in j2] == ["75032102"] and j2[0]["xe"] == ""    # GV 1 đã có xe → bỏ qua; xe 93C-1 đã dùng
