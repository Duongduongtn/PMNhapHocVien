"""KQD-04 đổi (task 136, TDD §11D.13) — `POST /local/ketqua/cap-nhat`: HV 14 → 90 + giải trình hiệu lực.

Không nối CDB thật: cursor giả điều phối theo nội dung SQL và mô phỏng đúng SP `_CapNhat`
(giữ 90/13/14, ngược lại 09/10). Ghi thật vào CDB production → nghiệm thu máy CSDT (Checkpoint 35).
Khóa các bất biến: bảng quy tắc 14→90, giải trình riêng/chung, chặn 12/13, đổi trạng thái giữa chừng,
cơ sở khác, bước chuyển lỗi vẫn 200 + cảnh báo, hồi quy luồng 03→09/10 của KQD-02.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import ketqua

client = TestClient(app)

DAT = {"ly_thuyet": 28, "mo_phong": 7, "hinh": 85, "tien_lui": 7, "duong": 85}
TRUOT = {"ly_thuyet": 28, "mo_phong": 7, "hinh": 70, "tien_lui": 7, "duong": 85}


class _Db:
    def __init__(self, tt="14", giai_trinh="", ma_csdt="75032", doi_tt_truoc_sp=None, loi_chuyen_90=False):
        self.hv = {"TT_XuLy": tt, "GiaiTrinh": giai_trinh, "KetLuanCSDT": None, "MaCSDT": ma_csdt}
        self.doi_tt_truoc_sp = doi_tt_truoc_sp      # đổi TT ngay sau lần đọc đầu → mô phỏng PM CDB kết xuất lại
        self.loi_chuyen_90 = loi_chuyen_90
        self.executed = []
        self._da_doc_dau = False


class _Cur:
    def __init__(self, db):
        self.db = db
        self._res = []

    def execute(self, sql, params=None):
        db = self.db
        db.executed.append((sql, params))
        p = params or ()
        h = db.hv
        if sql.startswith("SELECT hs.MaKhoaHoc"):
            self._res = [{"MaKhoaHoc": "K1", "TT_XuLy": h["TT_XuLy"], "HangGPLX": "B11", "MaHangMoi": "B.01",
                          "MaCSDT": h["MaCSDT"], "GiaiTrinh": h["GiaiTrinh"], "NgayBG": "20260915", "NgayThi": "20260920"}]
            if db.doi_tt_truoc_sp:
                h["TT_XuLy"] = db.doi_tt_truoc_sp          # đổi SAU lần đọc đầu
        elif sql.startswith("UPDATE dbo.NguoiLX_HoSo SET GiaiTrinh"):
            if h["TT_XuLy"] not in ("12", "13"):
                h["GiaiTrinh"] = p[0] or ""
            self._res = []
        elif sql.startswith("SELECT TT_XuLy, ISNULL(GiaiTrinh"):
            self._res = [{"TT_XuLy": h["TT_XuLy"], "GiaiTrinh": h["GiaiTrinh"]}]
        elif sql.startswith("EXEC dbo.usp_NguoiLX_KetQuaDaoTao_CSDT_CapNhat"):
            kl = p[6]
            h["KetLuanCSDT"] = 1 if kl == "1" else 0
            if h["TT_XuLy"] not in ("90", "13", "14"):
                h["TT_XuLy"] = "09" if kl == "1" else "10"
            self._res = []
        elif sql.startswith("UPDATE dbo.NguoiLX_HoSo SET TT_XuLy='90'"):
            if db.loi_chuyen_90:
                raise RuntimeError("mất kết nối")
            if h["TT_XuLy"] == "14" and h["KetLuanCSDT"] == 1 and (h["GiaiTrinh"] or "") != "":
                h["TT_XuLy"] = "90"
            self._res = []
        else:
            self._res = []

    def fetchone(self):
        return self._res[0] if self._res else None

    def fetchall(self):
        return self._res


class _Conn:
    def __init__(self, db):
        self._cur = _Cur(db)

    def cursor(self, as_dict=False):
        return self._cur

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture
def patch_db(monkeypatch):
    def _p(db, ma_may="75032"):
        monkeypatch.setattr("app.routers.ketqua._db_dich", lambda tk: "GPLX_CDB_CSDT")
        monkeypatch.setattr("app.routers.ketqua.sqlserver_conn_dich", lambda d, autocommit=False: _Conn(db))
        monkeypatch.setattr("app.routers.ketqua.sync_helpers.get_ma_csdt_tu_qtht", lambda conn: ma_may)
        monkeypatch.setattr("app.routers.ketqua.config_store.get_kqd_chuong_trinh", lambda ma_kh: "cu")
        return db
    return _p


def _post(auth_headers, diem, **kw):
    body = {"ma_dk": "75032-A", "diem_goc": diem, **kw}
    return client.post("/local/ketqua/cap-nhat", headers=auth_headers, json=body)


# ── thuần: giải trình hiệu lực ──
def test_hieu_luc_rieng_co_chu_thang_chung():
    assert ketqua.giai_trinh_hieu_luc("Riêng", "Chung", "") == (True, "Riêng")


def test_hieu_luc_rieng_rong_khong_chung_thi_xoa():
    assert ketqua.giai_trinh_hieu_luc("", None, "Cũ") == (True, None)


def test_hieu_luc_chung_chi_ghi_khi_cot_trong():
    assert ketqua.giai_trinh_hieu_luc(None, "Chung", "") == (True, "Chung")
    assert ketqua.giai_trinh_hieu_luc(None, "Chung", "Đã có riêng") == (False, None)   # chung không đè riêng


def test_hieu_luc_khong_gui_gi_giu_nguyen():
    assert ketqua.giai_trinh_hieu_luc(None, None, "Cũ") == (False, None)


# ── bảng quy tắc 14→90 ──
def test_14_dat_co_giai_trinh_rieng_len_90(auth_headers, patch_db):
    db = patch_db(_Db("14"))
    r = _post(auth_headers, DAT, giai_trinh="Đã nộp lại ảnh đạt chuẩn.")
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["tt_moi"] == "90" and j["thieu_giai_trinh"] is False and j["canh_bao"] is None
    assert db.hv["TT_XuLy"] == "90" and db.hv["GiaiTrinh"] == "Đã nộp lại ảnh đạt chuẩn."


def test_14_dat_dung_giai_trinh_chung_len_90(auth_headers, patch_db):
    db = patch_db(_Db("14"))
    r = _post(auth_headers, DAT, giai_trinh_chung="Giải trình chung của khóa.")
    j = r.json()
    assert j["tt_moi"] == "90"
    assert db.hv["GiaiTrinh"] == "Giải trình chung của khóa."


def test_14_dat_thieu_giai_trinh_giu_14_va_bao(auth_headers, patch_db):
    db = patch_db(_Db("14"))
    r = _post(auth_headers, DAT)
    j = r.json()
    assert j["tt_moi"] == "14" and j["thieu_giai_trinh"] is True
    assert db.hv["TT_XuLy"] == "14"


def test_14_khong_dat_giu_14_du_co_giai_trinh(auth_headers, patch_db):
    db = patch_db(_Db("14"))
    r = _post(auth_headers, TRUOT, giai_trinh="Có giải trình")
    j = r.json()
    assert j["ket_luan"] == "khong_dat" and j["tt_moi"] == "14" and j["thieu_giai_trinh"] is False
    assert db.hv["TT_XuLy"] == "14"


def test_90_sua_tiep_giu_90(auth_headers, patch_db):
    db = patch_db(_Db("90", giai_trinh="Đã có"))
    r = _post(auth_headers, DAT)
    assert r.json()["tt_moi"] == "90"
    # không gọi UPDATE chuyển 90 vì HV không ở 14
    assert not [s for s, _ in db.executed if s.startswith("UPDATE dbo.NguoiLX_HoSo SET TT_XuLy='90'")]


@pytest.mark.parametrize("tt", ["12", "13"])
def test_12_13_chan_409_khong_ghi_gi(auth_headers, patch_db, tt):
    db = patch_db(_Db(tt, giai_trinh="Cũ"))
    r = _post(auth_headers, DAT, giai_trinh="Mới")
    assert r.status_code == 409
    assert db.hv["GiaiTrinh"] == "Cũ"
    assert not [s for s, _ in db.executed if s.startswith("EXEC")]


# ── giải trình: chung không đè riêng ──
def test_chung_khong_de_giai_trinh_da_co(auth_headers, patch_db):
    db = patch_db(_Db("14", giai_trinh="Giải trình riêng đã có"))
    r = _post(auth_headers, DAT, giai_trinh_chung="Chung")
    assert r.json()["tt_moi"] == "90"
    assert db.hv["GiaiTrinh"] == "Giải trình riêng đã có"


def test_giai_trinh_qua_1000_ky_tu_400(auth_headers, patch_db):
    patch_db(_Db("14"))
    assert _post(auth_headers, DAT, giai_trinh="x" * 1001).status_code == 400
    assert _post(auth_headers, DAT, giai_trinh_chung="x" * 1001).status_code == 400


# ── đua trạng thái / cơ sở / lỗi bước chuyển ──
def test_trang_thai_vua_doi_sang_12_409_khong_goi_sp(auth_headers, patch_db):
    db = patch_db(_Db("14", doi_tt_truoc_sp="12"))
    r = _post(auth_headers, DAT, giai_trinh="x")
    assert r.status_code == 409
    assert r.json()["detail"]["loi"] == "trang_thai_da_doi"
    assert not [s for s, _ in db.executed if s.startswith("EXEC")]


def test_hv_khac_co_so_403(auth_headers, patch_db):
    db = patch_db(_Db("14", ma_csdt="24005"), ma_may="75032")
    r = _post(auth_headers, DAT, giai_trinh="x")
    assert r.status_code == 403
    assert not [s for s, _ in db.executed if s.startswith("EXEC") or s.startswith("UPDATE")]


def test_may_thieu_ma_csdt_khong_chan(auth_headers, patch_db):
    db = patch_db(_Db("03", ma_csdt="75032"), ma_may=None)
    assert _post(auth_headers, DAT).status_code == 200


def test_buoc_chuyen_loi_van_200_co_canh_bao(auth_headers, patch_db):
    db = patch_db(_Db("14", loi_chuyen_90=True))
    r = _post(auth_headers, DAT, giai_trinh="Có giải trình")
    assert r.status_code == 200
    j = r.json()
    assert j["canh_bao"] == "chua_chuyen_90" and j["tt_moi"] == "14"
    assert db.hv["KetLuanCSDT"] == 1          # điểm đã ghi


# ── hồi quy KQD-02: nhập điểm lần đầu 03/04 → 09/10 ──
@pytest.mark.parametrize("diem,tt_moi", [(DAT, "09"), (TRUOT, "10")])
def test_hoi_quy_03_len_09_10(auth_headers, patch_db, diem, tt_moi):
    db = patch_db(_Db("03"))
    r = _post(auth_headers, diem)
    assert r.status_code == 200
    assert r.json()["tt_moi"] == tt_moi and r.json()["thieu_giai_trinh"] is False
    assert db.hv["TT_XuLy"] == tt_moi
    # không đụng GiaiTrinh khi client không gửi
    assert not [s for s, _ in db.executed if s.startswith("UPDATE dbo.NguoiLX_HoSo SET GiaiTrinh")]


# ── bổ sung sau soát nghiệp vụ ──
def test_xoa_giai_trinh_qua_endpoint_khi_rieng_rong_va_khong_chung(auth_headers, patch_db):
    db = patch_db(_Db("14", giai_trinh="Cũ"))
    r = _post(auth_headers, TRUOT, giai_trinh="")
    assert r.status_code == 200
    assert db.hv["GiaiTrinh"] == ""            # đã xóa
    assert r.json()["tt_moi"] == "14"


def test_giai_trinh_khoang_trang_dau_cuoi_duoc_cat(auth_headers, patch_db):
    db = patch_db(_Db("14"))
    _post(auth_headers, DAT, giai_trinh="   Có chữ   ")
    assert db.hv["GiaiTrinh"] == "Có chữ"


def test_doc_lai_loi_van_bao_dung_90(auth_headers, patch_db, monkeypatch):
    """Chuyển 90 thành công nhưng SELECT đọc lại lỗi → không báo 14/thieu_giai_trinh oan."""
    db = patch_db(_Db("14"))
    goc = _Cur.execute
    dem = {"n": 0}

    def execute(self, sql, params=None):
        if sql.startswith("SELECT TT_XuLy, ISNULL(GiaiTrinh"):
            dem["n"] += 1
            if dem["n"] >= 2:                    # lần 1 = đọc trước SP; lần 2 = đọc sau chuyển → lỗi
                raise RuntimeError("mất kết nối")
        return goc(self, sql, params)
    monkeypatch.setattr(_Cur, "execute", execute)
    r = _post(auth_headers, DAT, giai_trinh="Có giải trình")
    assert r.status_code == 200
    assert r.json()["tt_moi"] == "90" and r.json()["thieu_giai_trinh"] is False


def test_sua_le_giu_quydoi_khong_doi_hanh_vi(auth_headers, patch_db):
    """KQD-06: chỉ sửa 1 môn, 4 môn còn lại giữ quy đổi đã lưu — vẫn qua SP, HV 09 lên Đạt."""
    db = patch_db(_Db("09"))
    r = _post(auth_headers, {"hinh": 85},
              giu_quydoi={"ly_thuyet": 8.0, "mo_phong": 7.0, "tien_lui": 7.0, "duong": 8.0})
    assert r.status_code == 200, r.text
    assert r.json()["ket_luan"] == "dat" and r.json()["tt_moi"] == "09"
