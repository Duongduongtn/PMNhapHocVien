"""KQD-04 đổi (task 137, TDD §11D.13) — giải trình + chuyển 14→90 HÀNG LOẠT, mẫu giải trình, lý do trên lưới.

Không nối CDB thật: cursor giả mô phỏng UPDATE có guard `TT_XuLy='14' AND KetLuanCSDT=1`, commit/rollback.
Ghi thật vào CDB production → nghiệm thu máy CSDT (Checkpoint 35).
"""
import pytest
from fastapi.testclient import TestClient

from app import config_store
from app.main import app
from app.routers import ketqua

client = TestClient(app)


def _hv(ma, tt="14", kl=1, gt="", csdt="75032", du=True, so_giay="SG-1"):
    r = {"MaDK": ma, "MaKhoaHoc": "K1", "MaCSDT": csdt, "TT_XuLy": tt, "KetLuanCSDT": kl, "GiaiTrinh": gt,
         "HangGPLX": "B11", "MaHangMoi": "B.01",
         "DiemKQLyThuyet": 8.0, "DiemKQMoPhong": 7.0, "DiemKQHinh": 8.0, "DiemKQTienLui": 7.0, "DiemKQThucHanh": 8.0,
         "TGThucHanhHinh": 34, "QDThucHanhHinh": 240, "TGThucHanhDuong": 20.0, "TongQDThucHanh": 810.0,
         "SoGiayCNTN": so_giay}
    if not du:
        r["DiemKQMoPhong"] = None
    return r


class _Db:
    def __init__(self, hv, loi_update=False, loi_commit=False, loi_doc_lai=False, doi_tt=None):
        self.hv = {h["MaDK"]: dict(h) for h in hv}
        self.loi_update, self.loi_commit, self.loi_doc_lai = loi_update, loi_commit, loi_doc_lai
        self.doi_tt = doi_tt or {}            # ma → TT_XuLy đổi ngay trước UPDATE (đua)
        self.executed, self.committed, self.rolled_back = [], 0, 0


class _Cur:
    def __init__(self, db):
        self.db, self._res = db, []

    def execute(self, sql, params=None):
        db = self.db
        db.executed.append((sql, params))
        p = tuple(params or ())
        if sql.startswith("SELECT B.MaDK, B.MaKhoaHoc"):
            self._res = [dict(db.hv[m]) for m in p if m in db.hv]
        elif sql.startswith("UPDATE dbo.NguoiLX_HoSo SET GiaiTrinh = CASE"):
            if db.loi_update:
                raise RuntimeError("deadlock")
            ghi_de, noi_dung, *ds = p
            for m in ds:
                if m in db.doi_tt:
                    db.hv[m]["TT_XuLy"] = db.doi_tt[m]
                h = db.hv.get(m)
                if h and h["TT_XuLy"] == "14" and h["KetLuanCSDT"] == 1:
                    if ghi_de == 1 or not (h["GiaiTrinh"] or ""):
                        h["GiaiTrinh"] = noi_dung
                    h["TT_XuLy"] = "90"
            self._res = []
        elif sql.startswith("SELECT MaDK, TT_XuLy"):
            if db.loi_doc_lai:
                raise RuntimeError("mất kết nối")
            self._res = [{"MaDK": m, "TT_XuLy": db.hv[m]["TT_XuLy"]} for m in p if m in db.hv]
        else:
            self._res = []

    def fetchall(self):
        return self._res

    def fetchone(self):
        return self._res[0] if self._res else None


class _Conn:
    def __init__(self, db):
        self.db, self._cur = db, _Cur(db)

    def cursor(self, as_dict=False):
        return self._cur

    def commit(self):
        if self.db.loi_commit:
            raise RuntimeError("mất kết nối khi commit")
        self.db.committed += 1

    def rollback(self):
        self.db.rolled_back += 1

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture
def patch_db(monkeypatch):
    def _p(db, ma_may="75032"):
        monkeypatch.setattr("app.routers.ketqua._db_dich", lambda tk: "GPLX_CDB_CSDT")
        monkeypatch.setattr("app.routers.ketqua.sqlserver_conn_dich",
                            lambda d, autocommit=True, timeout=0: _Conn(db))
        monkeypatch.setattr("app.routers.ketqua.sync_helpers.get_ma_csdt_tu_qtht", lambda c: ma_may)
        return db
    return _p


def _post(auth_headers, ma_dk, noi_dung="Đã bổ sung hồ sơ.", **kw):
    return client.post("/local/ketqua/giai-trinh-lo", headers=auth_headers,
                       json={"ma_dk": ma_dk, "noi_dung": noi_dung, **kw})


# ── thuần: phân loại lô ──
def test_phan_loai_lo_day_du_cac_ly_do():
    rows = {r["MaDK"]: r for r in [
        _hv("OK"), _hv("KD", kl=0), _hv("DA90", tt="90"), _hv("DA12", tt="12"), _hv("DA13", tt="13"),
        _hv("09", tt="09"), _hv("CSKHAC", csdt="24005"), _hv("THIEU", du=False), _hv("NOSG", so_giay=""),
    ]}
    du, bo = ketqua.phan_loai_lo(
        ["OK", "KD", "DA90", "DA12", "DA13", "09", "CSKHAC", "THIEU", "NOSG", "KHONGCO"], rows, "75032")
    assert du == ["OK"]
    ly = {b["ma_dk"]: b["ly_do"] for b in bo}
    assert ly == {"KD": "khong_dat", "DA90": "da_o_dang_giai_trinh", "DA12": "da_gui_hoac_hoan_thanh",
                  "DA13": "da_gui_hoac_hoan_thanh", "09": "khong_con_o_so_tu_choi", "CSKHAC": "khong_thuoc_co_so",
                  "THIEU": "chua_du_diem", "NOSG": "chua_du_diem", "KHONGCO": "khong_tim_thay"}
    chi_tiet = {b["ma_dk"]: b.get("chi_tiet") for b in bo}
    assert "thieu_mon" in chi_tiet["THIEU"]["ly_do"] and chi_tiet["THIEU"]["mon_thieu"] == ["mo_phong"]
    assert "thieu_so_giay" in chi_tiet["NOSG"]["ly_do"]


def test_phan_loai_may_thieu_ma_csdt_khong_chan():
    du, _ = ketqua.phan_loai_lo(["A"], {"A": _hv("A", csdt="24005")}, None)
    assert du == ["A"]


# ── POST /giai-trinh-lo ──
def test_lo_lan_chi_chuyen_nguoi_du_dieu_kien(auth_headers, patch_db):
    db = patch_db(_Db([_hv("A"), _hv("B", kl=0), _hv("C", tt="09"), _hv("D", tt="13"), _hv("E", du=False)]))
    r = _post(auth_headers, ["A", "B", "C", "D", "E"])
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["da_chuyen"] == ["A"]
    assert {b["ma_dk"] for b in j["bo_qua"]} == {"B", "C", "D", "E"}
    assert db.hv["A"]["TT_XuLy"] == "90" and db.hv["A"]["GiaiTrinh"] == "Đã bổ sung hồ sơ."
    assert db.hv["B"]["TT_XuLy"] == "14" and db.hv["C"]["TT_XuLy"] == "09" and db.hv["D"]["TT_XuLy"] == "13"
    assert db.committed == 1 and db.rolled_back == 0


def test_giu_giai_trinh_rieng_tru_khi_ghi_de(auth_headers, patch_db):
    db = patch_db(_Db([_hv("A", gt="Riêng của A"), _hv("B")]))
    j = _post(auth_headers, ["A", "B"]).json()
    assert sorted(j["da_chuyen"]) == ["A", "B"] and j["giu_rieng"] == 1
    assert db.hv["A"]["GiaiTrinh"] == "Riêng của A"
    assert db.hv["B"]["GiaiTrinh"] == "Đã bổ sung hồ sơ."
    db2 = patch_db(_Db([_hv("A", gt="Riêng của A")]))
    j2 = _post(auth_headers, ["A"], ghi_de_rieng=True).json()
    assert j2["da_chuyen"] == ["A"] and j2["giu_rieng"] == 0
    assert db2.hv["A"]["GiaiTrinh"] == "Đã bổ sung hồ sơ."


def test_update_loi_rollback_khong_chuyen_ai_502(auth_headers, patch_db):
    db = patch_db(_Db([_hv("A"), _hv("B")], loi_update=True))
    r = _post(auth_headers, ["A", "B"])
    assert r.status_code == 502
    assert r.json()["detail"]["loi"] == "lo_loi" and r.json()["detail"]["da_chuyen"] == []
    assert db.rolled_back == 1 and db.committed == 0
    assert db.hv["A"]["TT_XuLy"] == "14"


def test_commit_loi_bao_khong_ro(auth_headers, patch_db):
    patch_db(_Db([_hv("A")], loi_commit=True))
    r = _post(auth_headers, ["A"])
    assert r.status_code == 502 and r.json()["detail"]["ketqua"] == "khong_ro"


def test_doc_lai_loi_bao_khong_ro(auth_headers, patch_db):
    patch_db(_Db([_hv("A")], loi_doc_lai=True))
    r = _post(auth_headers, ["A"])
    assert r.status_code == 502 and r.json()["detail"]["ketqua"] == "khong_ro"


def test_goi_lai_idempotent(auth_headers, patch_db):
    db = patch_db(_Db([_hv("A")]))
    assert _post(auth_headers, ["A"]).json()["da_chuyen"] == ["A"]
    j = _post(auth_headers, ["A"]).json()
    assert j["da_chuyen"] == [] and j["bo_qua"] == [{"ma_dk": "A", "ly_do": "da_o_dang_giai_trinh"}]


def test_doi_trang_thai_giua_chung_khong_bi_ghi_de(auth_headers, patch_db):
    db = patch_db(_Db([_hv("A"), _hv("B")], doi_tt={"B": "12"}))
    j = _post(auth_headers, ["A", "B"]).json()
    assert j["da_chuyen"] == ["A"]
    assert {"ma_dk": "B", "ly_do": "khong_con_o_so_tu_choi"} in j["bo_qua"]
    assert db.hv["B"]["TT_XuLy"] == "12" and db.hv["B"]["GiaiTrinh"] == ""     # guard SQL: không ghi đè


def test_bien_lo_422(auth_headers, patch_db):
    patch_db(_Db([_hv("A")]))
    assert _post(auth_headers, []).status_code == 422
    assert _post(auth_headers, ["", "  "]).status_code == 422
    assert _post(auth_headers, [f"M{i}" for i in range(201)]).status_code == 422
    assert _post(auth_headers, ["A"], noi_dung="   ").status_code == 422
    assert _post(auth_headers, ["A"], noi_dung="x" * 1001).status_code == 422


def test_khu_trung_ma_dk(auth_headers, patch_db):
    db = patch_db(_Db([_hv("A")]))
    j = _post(auth_headers, ["A", "A", " A "]).json()
    assert j["da_chuyen"] == ["A"]
    update = [p for s, p in db.executed if s.startswith("UPDATE")][0]
    assert list(update[2:]) == ["A"]


def test_toan_bo_bo_qua_khong_goi_update(auth_headers, patch_db):
    db = patch_db(_Db([_hv("A", kl=0)]))
    j = _post(auth_headers, ["A"]).json()
    assert j["da_chuyen"] == [] and j["bo_qua"][0]["ly_do"] == "khong_dat"
    assert not [s for s, _ in db.executed if s.startswith("UPDATE")]
    assert db.committed == 0


# ── mẫu giải trình ──
@pytest.fixture
def kho_cau_hinh(monkeypatch):
    kho = {}
    monkeypatch.setattr(config_store, "load_config", lambda: kho)
    monkeypatch.setattr(config_store, "save_config", lambda d: kho.update(d))
    return kho


def test_mau_theo_co_so_tach_rieng(kho_cau_hinh):
    config_store.set_mau_giai_trinh("t1", ["Mẫu A"], None)
    config_store.set_mau_giai_trinh("t2", ["Mẫu B"], None)
    assert config_store.get_mau_giai_trinh("t1")["mau"] == ["Mẫu A"]
    assert config_store.get_mau_giai_trinh("t2")["mau"] == ["Mẫu B"]


def test_chuan_hoa_mau_bo_rong_va_trung():
    assert config_store.chuan_hoa_mau([" a ", "", "a", "b ", "  "]) == ["a", "b"]


def test_chuan_hoa_mau_vuot_gioi_han():
    with pytest.raises(ValueError):
        config_store.chuan_hoa_mau([f"m{i}" for i in range(21)])
    with pytest.raises(ValueError):
        config_store.chuan_hoa_mau(["x" * 1001])


def test_api_mau_put_get_phien_ban(auth_headers, kho_cau_hinh):
    r0 = client.get("/local/ketqua/mau-giai-trinh?target_key=t1", headers=auth_headers).json()
    assert r0 == {"mau": [], "phien_ban": 0}
    r1 = client.put("/local/ketqua/mau-giai-trinh?target_key=t1", headers=auth_headers,
                    json={"mau": ["A", "", "A", "B"], "phien_ban": 0})
    assert r1.status_code == 200 and r1.json() == {"mau": ["A", "B"], "phien_ban": 1}
    # người khác vừa lưu → phiên bản lệch
    r2 = client.put("/local/ketqua/mau-giai-trinh?target_key=t1", headers=auth_headers,
                    json={"mau": ["C"], "phien_ban": 0})
    assert r2.status_code == 409 and r2.json()["detail"]["loi"] == "mau_da_doi"
    assert client.get("/local/ketqua/mau-giai-trinh?target_key=t1", headers=auth_headers).json()["mau"] == ["A", "B"]


def test_api_mau_vuot_gioi_han_422(auth_headers, kho_cau_hinh):
    r = client.put("/local/ketqua/mau-giai-trinh?target_key=t1", headers=auth_headers,
                   json={"mau": [f"m{i}" for i in range(21)]})
    assert r.status_code == 422
    r = client.put("/local/ketqua/mau-giai-trinh?target_key=t1", headers=auth_headers, json={"mau": ["x" * 1001]})
    assert r.status_code == 422


def test_luu_mau_khong_lam_mat_cau_hinh_khac(kho_cau_hinh):
    kho_cau_hinh["kqd_chuong_trinh"] = {"K1": "moi"}
    kho_cau_hinh["sync_targets"] = [{"key": "t1"}]
    config_store.set_mau_giai_trinh("t1", ["A"], None)
    assert kho_cau_hinh["kqd_chuong_trinh"] == {"K1": "moi"} and kho_cau_hinh["sync_targets"] == [{"key": "t1"}]


# ── GET /hoc-vien: lý do Sở từ chối + giải trình lên lưới ──
def test_hoc_vien_tra_ly_do_tu_choi_va_giai_trinh(auth_headers, monkeypatch):
    row = {"MaDK": "A", "HoVaTen": "Nguyễn A", "NgaySinh": "20000101", "SoCMT": "079", "SoHoSo": "1",
           "HangGPLX": "B11", "MaHangMoi": "B.01", "TT_XuLy": "14", "KetLuanCSDT": 1,
           "DiemKQLyThuyet": 8, "DiemKQMoPhong": 7, "DiemKQHinh": 8, "DiemKQTienLui": 7, "DiemKQThucHanh": 8,
           "TGThucHanhHinh": 34, "QDThucHanhHinh": 240, "TGThucHanhDuong": 20, "TongQDThucHanh": 810,
           "SoGiayCNTN": "SG", "GiaiTrinh": " Đã bổ sung ", "LyDoTuChoiKQDT": "Ảnh không đạt chuẩn"}
    monkeypatch.setattr("app.routers.ketqua._doc_hv_khoa", lambda ma_kh, nhom, tk: [row])
    r = client.get("/local/ketqua/hoc-vien?ma_kh=K1", headers=auth_headers)
    assert r.status_code == 200
    j = r.json()[0]
    assert j["ly_do_tu_choi"] == "Ảnh không đạt chuẩn" and j["giai_trinh"] == "Đã bổ sung"
    row2 = {**row, "GiaiTrinh": None, "LyDoTuChoiKQDT": "  "}
    monkeypatch.setattr("app.routers.ketqua._doc_hv_khoa", lambda ma_kh, nhom, tk: [row2])
    j2 = client.get("/local/ketqua/hoc-vien?ma_kh=K1", headers=auth_headers).json()[0]
    assert j2["ly_do_tu_choi"] is None and j2["giai_trinh"] is None


# ── bổ sung sau soát nghiệp vụ task 137 ──
def test_sql_giai_trinh_chi_khoang_trang_coi_nhu_trong():
    """R1: GiaiTrinh toàn khoảng trắng phải bị coi là trống (SQL dùng LTRIM/RTRIM, khớp .strip() ở Python)."""
    assert "LTRIM(RTRIM(ISNULL(GiaiTrinh" in ketqua._SQL_LO_GHI
    assert "LTRIM(RTRIM(ISNULL(GiaiTrinh" in ketqua._SQL_14_SANG_90


def test_giu_rieng_chi_dem_nguoi_da_chuyen(auth_headers, patch_db):
    """R6: người có giải trình riêng nhưng bị đổi trạng thái giữa chừng KHÔNG được tính vào giu_rieng."""
    db = patch_db(_Db([_hv("A", gt="Riêng A"), _hv("B", gt="Riêng B")], doi_tt={"B": "12"}))
    j = _post(auth_headers, ["A", "B"]).json()
    assert j["da_chuyen"] == ["A"] and j["giu_rieng"] == 1


def test_ghi_cau_hinh_that_nguyen_tu_va_khong_mat_khoa_khac(tmp_path, monkeypatch):
    """R3: đường ghi THẬT (mã hóa + file tạm + os.replace), không còn file .tmp, khóa khác nguyên vẹn."""
    monkeypatch.setattr(config_store, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config_store, "KEY_FILE", tmp_path / "key.bin")
    monkeypatch.setattr(config_store, "CONFIG_FILE", tmp_path / "config.enc")
    config_store.set_kqd_chuong_trinh("K1", "moi")
    config_store.save_sync_config([{"key": "t1", "name": "Đích 1", "database": "DB1"}], "t1", None)
    config_store.set_mau_giai_trinh("t1", ["Mẫu 1"], 0)
    assert config_store.get_kqd_chuong_trinh("K1") == "moi"
    assert config_store.get_sync_config()["targets"][0]["key"] == "t1"
    assert config_store.get_mau_giai_trinh("t1") == {"mau": ["Mẫu 1"], "phien_ban": 1}
    assert not list(tmp_path.glob("*.tmp"))
    # hai luồng cùng sửa: không mất cập nhật
    import threading
    def ghi(i):
        for j in range(15):
            config_store.sua_config(lambda d, i=i, j=j: d.setdefault("dem", {}).__setitem__(f"{i}-{j}", 1))
    ts = [threading.Thread(target=ghi, args=(i,)) for i in range(4)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(config_store.load_config()["dem"]) == 60
    assert config_store.get_kqd_chuong_trinh("K1") == "moi"
