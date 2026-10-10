"""KQD-05 mở rộng (task 83) — "Sửa sau gửi" chọn từng HV, KHÔNG xóa gói.

Không nối CDB thật: cursor giả điều phối theo nội dung SQL. Ghi thật vào CDB production
→ nghiệm thu máy CSDT (mức 1). Ở đây khóa các bất biến: cổng gói chưa gửi, 13 chặn cả lô,
nhật ký ghi TRƯỚC, guard 12 + kết luận, không bao giờ xóa gói, GET tự dọn HV đã kết xuất lại.
"""
import pytest
from fastapi.testclient import TestClient

from app import sua_sau_gui as ssg
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _nhat_ky_tam(tmp_path, monkeypatch):
    monkeypatch.setattr(ssg, "DB_PATH", tmp_path / "ssg.sqlite")


def _hv(ma, tt, kl, kh="75032K260003", ten="HV Test"):
    return {"MaDK": ma, "MaKhoaHoc": kh, "TT_XuLy": tt, "KetLuanCSDT": kl, "HoVaTen": ten,
            "DiemKQLyThuyet": 8.0, "DiemKQMoPhong": 7.0, "DiemKQHinh": 9.0,
            "DiemKQTienLui": 8.5, "DiemKQThucHanh": 7.5}


class _Db:
    """Trạng thái CDB giả + log câu SQL đã chạy."""
    def __init__(self, hv, goi, ket_qua_update=True):
        self.hv = {h["MaDK"]: dict(h) for h in hv}
        self.goi = goi
        self.executed = []     # [(sql, params)]
        self.update_that_bai = not ket_qua_update


class _Cur:
    def __init__(self, db):
        self.db = db
        self._res = []

    def execute(self, sql, params=None):
        self.db.executed.append((sql, params))
        p = params or ()
        if "TRANS_CLI_HangDoiGui" in sql and sql.lstrip().upper().startswith("SELECT"):
            self._res = list(self.db.goi)
        elif sql.startswith("SELECT B.MaDK"):
            self._res = [dict(self.db.hv[m]) for m in p[1:] if m in self.db.hv]
        elif sql.startswith("SELECT MaDK, TT_XuLy"):
            self._res = [{"MaDK": m, "TT_XuLy": self.db.hv[m]["TT_XuLy"]} for m in p[1:] if m in self.db.hv]
        elif sql.startswith("UPDATE dbo.NguoiLX_HoSo"):
            ma = p[1]
            h = self.db.hv.get(ma)
            if h and not self.db.update_that_bai and h["TT_XuLy"] == "12" and h["KetLuanCSDT"] is not None:
                h["TT_XuLy"] = "09" if h["KetLuanCSDT"] == 1 else "10"
            self._res = []
        else:
            self._res = []

    def fetchall(self):
        return self._res

    def fetchone(self):
        return self._res[0] if self._res else None


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
    monkeypatch.setattr("app.routers.ketqua._db_dich", lambda tk: "GPLX_CDB_CSDT")
    monkeypatch.setattr("app.routers.ketqua.sqlserver_conn_dich", lambda d, autocommit=False: _Conn(db))
    monkeypatch.setattr("app.routers.ketqua._ma_csdt_hoac_loi", lambda conn: "75032")


def _goi(tt):
    return {"Id": "g1", "DuongDan": r"C:\KQDT_75032_75_K261002191716.zip", "TrangThai": tt,
            "KickThuocFile": 1, "NgayTao": "02/10/2026 19:23"}


def _co_update(db):
    return [s for s, _ in db.executed if s.startswith("UPDATE")]


# ── phân loại thuần ──
def test_phan_loai_hop_le_bo_qua_va_13():
    rows = [_hv("A", "12", 1), _hv("B", "12", None), _hv("C", "09", 1), _hv("D", "13", 1)]
    pl = ssg.phan_loai(rows, ["A", "B", "C", "D", "Z"])
    assert [r["MaDK"] for r in pl["hop_le"]] == ["A"]
    assert pl["bi_13"] == ["D"]
    ly_do = {b["ma_dk"]: b["ly_do"] for b in pl["bo_qua"]}
    assert set(ly_do) == {"B", "C", "Z"}
    assert "kết luận" in ly_do["B"] and "09" in ly_do["C"] and "Không tìm thấy" in ly_do["Z"]


def test_nhat_ky_ghi_cho_kx_doi_trang_thai():
    ids = ssg.ghi([_hv("A", "12", 1), _hv("B", "12", 0)], "Sửa nhầm môn LT", "op-test")
    assert set(ids) == {"A", "B"}
    cho = ssg.cho_kx()
    assert {c["ma_dk"] for c in cho} == {"A", "B"}
    assert '"ly_thuyet": 8.0' in cho[0]["diem_truoc_json"]
    ssg.doi_trang_thai([ids["A"]], ssg.DA_KX)
    assert [c["ma_dk"] for c in ssg.cho_kx()] == ["B"]
    ssg.doi_trang_thai([ids["A"]], ssg.HUY)         # đã da_kx → không đổi lại
    assert [c["ma_dk"] for c in ssg.cho_kx()] == ["B"]


# ── POST /mo-sua-sau-gui ──
def test_con_goi_chua_gui_409_khong_dung_gi(auth_headers, monkeypatch):
    db = _Db([_hv("A", "12", 1)], [_goi("0")])
    _patch(monkeypatch, db)
    r = client.post("/local/ketqua/mo-sua-sau-gui", headers=auth_headers, json={"ma_dk": ["A"], "ly_do": "x"})
    assert r.status_code == 409
    assert r.json()["detail"]["loi"] == "con_goi_chua_gui"
    assert not _co_update(db)
    assert ssg.cho_kx() == []


def test_co_hv_13_chan_ca_lo(auth_headers, monkeypatch):
    db = _Db([_hv("A", "12", 1), _hv("D", "13", 1)], [_goi("1")])
    _patch(monkeypatch, db)
    r = client.post("/local/ketqua/mo-sua-sau-gui", headers=auth_headers, json={"ma_dk": ["A", "D"], "ly_do": "x"})
    assert r.status_code == 409
    assert r.json()["detail"] == {**r.json()["detail"], "loi": "co_hv_13", "ma_dk": ["D"]}
    assert not _co_update(db)
    assert db.hv["A"]["TT_XuLy"] == "12"
    assert ssg.cho_kx() == []


def test_mo_thanh_cong_chi_hv_duoc_chon_khong_xoa_goi(auth_headers, monkeypatch):
    db = _Db([_hv("A", "12", 1), _hv("B", "12", 0), _hv("C", "12", None), _hv("E", "03", None),
              _hv("F", "12", 1)],                      # F không được chọn
             [_goi("1")])
    _patch(monkeypatch, db)
    r = client.post("/local/ketqua/mo-sua-sau-gui", headers=auth_headers,
                    json={"ma_dk": ["A", "B", "C", "E"], "ly_do": "  Nhập nhầm điểm sa hình  "})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["so_mo"] == 2
    assert {m["ma_dk"]: m["tt_moi"] for m in body["mo"]} == {"A": "09", "B": "10"}
    assert {b["ma_dk"] for b in body["bo_qua"]} == {"C", "E"}
    assert db.hv["F"]["TT_XuLy"] == "12"                # không được chọn → giữ nguyên
    # lý do (đã strip) truyền vào UPDATE; không bao giờ xóa gói
    ups = [(s, p) for s, p in db.executed if s.startswith("UPDATE")]
    assert len(ups) == 2 and all(p[0] == "Nhập nhầm điểm sa hình" for _, p in ups)
    assert not any("HangDoiGui_Delete" in s or s.lstrip().upper().startswith("DELETE") for s, _ in db.executed)
    # nhật ký
    cho = {c["ma_dk"]: c for c in ssg.cho_kx()}
    assert set(cho) == {"A", "B"} and cho["A"]["nguoi"] == "op-test"
    assert cho["A"]["ly_do"] == "Nhập nhầm điểm sa hình"


def test_ly_do_rong_400_khong_ghi(auth_headers, monkeypatch):
    db = _Db([_hv("A", "12", 1)], [_goi("1")])
    _patch(monkeypatch, db)
    r = client.post("/local/ketqua/mo-sua-sau-gui", headers=auth_headers, json={"ma_dk": ["A"], "ly_do": "   "})
    assert r.status_code == 400
    assert not _co_update(db) and ssg.cho_kx() == []


def test_update_khong_lui_duoc_thi_huy_nhat_ky(auth_headers, monkeypatch):
    """HV bị đổi trạng thái giữa chừng (UPDATE không ăn) → báo bỏ qua + dòng nhật ký 'huy'."""
    db = _Db([_hv("A", "12", 1)], [_goi("1")], ket_qua_update=False)
    _patch(monkeypatch, db)
    r = client.post("/local/ketqua/mo-sua-sau-gui", headers=auth_headers, json={"ma_dk": ["A"], "ly_do": "x"})
    assert r.status_code == 200
    assert r.json()["so_mo"] == 0 and r.json()["bo_qua"][0]["ma_dk"] == "A"
    assert ssg.cho_kx() == []                           # đã 'huy' → không hiện khối đỏ oan


# ── GET /sua-sau-gui ──
def test_get_khoi_do_va_tu_bien_mat_khi_ve_lai_12(auth_headers, monkeypatch):
    db = _Db([_hv("A", "12", 1), _hv("B", "12", 0)], [_goi("1")])
    _patch(monkeypatch, db)
    client.post("/local/ketqua/mo-sua-sau-gui", headers=auth_headers, json={"ma_dk": ["A", "B"], "ly_do": "Sửa"})

    r = client.get("/local/ketqua/sua-sau-gui", headers=auth_headers)
    assert r.status_code == 200
    ds = r.json()
    assert {x["ma_dk"] for x in ds} == {"A", "B"}
    a = next(x for x in ds if x["ma_dk"] == "A")
    assert a["tt_xuly"] == "09" and a["diem_truoc"]["ly_thuyet"] == 8.0
    assert a["diem_hien"]["ket_luan"] == "dat" and a["nguoi"] == "op-test"
    assert len(a["luc_mo"]) == 16 and a["luc_mo"][2] == "/" and a["luc_mo"][10] == " "   # dd/mm/yyyy HH:mm

    db.hv["A"]["TT_XuLy"] = "12"                        # phần mềm CDB kết xuất lại → về 12
    ds2 = client.get("/local/ketqua/sua-sau-gui", headers=auth_headers).json()
    assert [x["ma_dk"] for x in ds2] == ["B"]
    assert [c["ma_dk"] for c in ssg.cho_kx()] == ["B"]  # A đã đánh da_kx


def test_get_rong_khong_cham_db(auth_headers, monkeypatch):
    db = _Db([], [])
    _patch(monkeypatch, db)
    assert client.get("/local/ketqua/sua-sau-gui", headers=auth_headers).json() == []
    assert db.executed == []


def test_ly_do_qua_1000_400_nhung_khoang_trang_thua_thi_qua(auth_headers, monkeypatch):
    db = _Db([_hv("A", "12", 1)], [_goi("1")])
    _patch(monkeypatch, db)
    r = client.post("/local/ketqua/mo-sua-sau-gui", headers=auth_headers,
                    json={"ma_dk": ["A"], "ly_do": "x" * 1001})
    assert r.status_code == 400 and not _co_update(db)
    r = client.post("/local/ketqua/mo-sua-sau-gui", headers=auth_headers,
                    json={"ma_dk": ["A"], "ly_do": "  " + "x" * 1000 + "  "})
    assert r.status_code == 200 and r.json()["so_mo"] == 1       # đủ 1000 sau strip → qua


def test_mo_lai_hv_da_ket_xuat_lai_khong_trung_dong(auth_headers, monkeypatch):
    db = _Db([_hv("A", "12", 1)], [_goi("1")])
    _patch(monkeypatch, db)
    client.post("/local/ketqua/mo-sua-sau-gui", headers=auth_headers, json={"ma_dk": ["A"], "ly_do": "lần 1"})
    db.hv["A"]["TT_XuLy"] = "12"                       # CDB kết xuất lại, chưa ai gọi GET
    client.post("/local/ketqua/mo-sua-sau-gui", headers=auth_headers, json={"ma_dk": ["A"], "ly_do": "lần 2"})
    cho = ssg.cho_kx()
    assert len(cho) == 1 and cho[0]["ly_do"] == "lần 2"

