"""TNB-05 (1/2) — task 100: xem / gỡ / xóa BC2 (`chi_tiet_bc2`, `go_hv`, `xoa_bc2` + router).

Kết nối giả mở rộng từ `test_tn_bc2_lap` (mô phỏng đúng hành vi SP DB Nạp). Khóa các bất biến:
gỡ chỉ HV còn `11` đúng BC2, BC2 phải còn mở, đọc lại sát trước SP, `TT_XuLy_Old` rỗng/`11` cần xác
nhận, xóa BC2 ĐẾM `MaBC2` mọi `TT_XuLy` (không dùng `TongSoThiSinh`), BC2 đã đóng không xóa, số BC2
có dấu `/` đi qua route.
"""
from contextlib import contextmanager
from datetime import datetime

import pytest

from app import tn_bc2_nhat_ky as nk
from app import tn_bc2_service as svc
from tests.test_tn_bc2_lap import FakeConn as _Conn
from tests.test_tn_bc2_lap import FakeCur as _Cur
from tests.test_tn_bc2_lap import HOM_NAY, KHOA, hv

BC2 = "76/2026"


class Cur(_Cur):
    def execute(self, sql, params=()):
        st, s = self.st, " ".join(sql.split())
        if s.startswith("SELECT MaBCII, MaBCI, SoBaoCao, NgayBaoCao, TongSoThiSinh, TrangThai, NguoiTao, NgayTao"):
            st.log.append((s, tuple(params)))
            r = [b for b in st.bc2 if b["MaBCII"] == params[0]]
            self._rows = [{"MaBCII": b["MaBCII"], "MaBCI": b["MaBCI"], "SoBaoCao": b.get("SoBaoCao"),
                           "NgayBaoCao": datetime(2026, 10, 3), "TongSoThiSinh": b.get("TongSoThiSinh"),
                           "TrangThai": b.get("TrangThai"), "NguoiTao": "thu1", "NgayTao": datetime(2026, 10, 3, 8, 0)}
                          for b in r]
        elif s.startswith("SELECT h.MaDK, h.SoHoSo, n.HoVaTen, n.NgaySinh"):
            st.log.append((s, tuple(params)))
            self._rows = [
                {"MaDK": m, "SoHoSo": h["so_ho_so"], "HoVaTen": "Học viên " + m, "NgaySinh": "20000131",
                 "SoCMT": "079" + m[-4:], "HangGPLX": h["hang"], "TT_XuLy": h["tt"], "TT_XuLy_Old": h["tt_cu"],
                 "MaBC2": h["ma_bc2"], "SoGiayCNTN": h["giay"], "MaKhoaHoc": h["ma_kh"], "TenKH": "K", "NgayBG": h["bg"]}
                for m, h in st.hv.items() if h["ma_bc2"] == params[0]]
        elif s.startswith("SELECT COUNT(*) AS n FROM NguoiLX_HoSo WHERE MaBC2"):
            st.log.append((s, tuple(params)))
            self._rows = [{"n": sum(1 for h in st.hv.values() if h["ma_bc2"] == params[0])}]
        elif s.startswith("EXEC usp_BaoCaoII_Delete"):
            st.log.append((s, tuple(params)))
            if not st.khong_xoa_duoc:
                st.bc2 = [b for b in st.bc2 if b["MaBCII"] != params[0]]
            self._rows = []
        else:
            super().execute(sql, params)


class Conn(_Conn):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.khong_xoa_duoc = False

    def cursor(self, as_dict=True):
        return Cur(self)


@pytest.fixture(autouse=True)
def _co_lap(tmp_path, monkeypatch):
    monkeypatch.setattr(nk, "DB_PATH", tmp_path / "tnbc2_nhat_ky.sqlite")
    svc.bo_cache()
    yield
    svc.bo_cache()
    with svc._JOBS_KHOA:
        svc._JOBS.clear()


@contextmanager
def _ctx(c):
    yield c


def hvs_trong_bc2():
    return {
        "G-0001": hv("11", ma_bc2=BC2, cu="09"),
        "G-0002": hv("11", ma_bc2=BC2, cu="17", ma_kh="70004K25B0001", bg="2025-12-01"),   # thi lại khóa khác
        "G-0003": hv("13", ma_bc2=BC2, cu="11"),                                          # PM cũ đã nhập kết quả
        "G-0004": hv("11", ma_bc2=BC2, cu=""),                                            # thiếu trạng thái cũ
        "G-0005": hv("11", ma_bc2=BC2, cu="11"),                                          # trạng thái cũ cũng 11
        "O-0001": hv("11", ma_bc2="75/2026", cu="09"),                                    # BC2 khác
    }


def go(c, ds, lo_id="lo-go-00001", **kw):
    return svc.go_hv(c, ma_bc2=kw.pop("ma_bc2", BC2), lo_id=lo_id, ds_ma_dk=ds, nguoi="thu1", **kw)


# ── Chi tiết ──
def test_chi_tiet_bc2_hoc_vien_go_duoc_ly_do_khoa_va_lech_tong_ghi():
    c = Conn(hvs_trong_bc2())
    cur = c.cursor()
    d = svc.chi_tiet_bc2(cur, BC2)
    assert d["ma_bc2"] == BC2 and d["dang_mo"] is True and d["loai"] == "oto" and d["ma_kh"] == KHOA
    assert d["tong_ghi"] == 24 and d["hv_thuc_te"] == 5 and d["lech"] is True and d["xoa_duoc"] is False
    h = {x["ma_dk"]: x for x in d["hoc_vien"]}
    assert set(h) == {"G-0001", "G-0002", "G-0003", "G-0004", "G-0005"}           # O-0001 thuộc BC2 khác
    assert h["G-0001"]["go_duoc"] is True and h["G-0001"]["ly_do_khoa"] == "" and h["G-0001"]["ngay_sinh"] == "31/01/2000"
    assert h["G-0001"]["ten_trang_thai"] == "Đã vào BC2, chờ kết quả" and h["G-0001"]["canh_bao_tt_cu"] is False
    assert h["G-0002"]["khac_khoa_bc1"] is True and h["G-0002"]["ten_trang_thai_cu"] == "Thi sát hạch chưa đạt"
    assert h["G-0003"]["go_duoc"] is False and "mất kết quả" in h["G-0003"]["ly_do_khoa"]
    assert h["G-0004"]["canh_bao_tt_cu"] is True and h["G-0004"]["go_duoc"] is True      # Old rỗng: cảnh báo, gỡ được
    assert h["G-0005"]["go_duoc"] is False and "cũng là" in h["G-0005"]["ly_do_khoa"]     # Old='11': khóa nút
    assert h["G-0005"]["canh_bao_tt_cu"] is False


def test_chi_tiet_bc2_dong_khoa_het_va_bc2_rong_xoa_duoc():
    c = Conn({}, bc2=[{"MaBCII": BC2, "MaBCI": "858/26-TTTÐ", "SoBaoCao": BC2, "TrangThai": True, "TongSoThiSinh": 0},
                      {"MaBCII": "90/2026", "MaBCI": "858/26-TTTÐ", "SoBaoCao": "90/2026", "TrangThai": False,
                       "TongSoThiSinh": 0}])
    assert svc.chi_tiet_bc2(c.cursor(), BC2)["xoa_duoc"] is False
    assert svc.chi_tiet_bc2(c.cursor(), "90/2026")["xoa_duoc"] is True
    with pytest.raises(svc.LoiNghiepVu) as e:
        svc.chi_tiet_bc2(c.cursor(), "khong-co")
    assert e.value.http == 404
    c2 = Conn(hvs_trong_bc2(), bc2=[{"MaBCII": BC2, "MaBCI": "858/26-TTTÐ", "SoBaoCao": BC2, "TrangThai": True,
                                     "TongSoThiSinh": 5}])
    d = svc.chi_tiet_bc2(c2.cursor(), BC2)
    assert all(x["go_duoc"] is False and "đã đóng" in x["ly_do_khoa"] for x in d["hoc_vien"])


# ── Gỡ ──
def test_go_chi_hv_con_11_dung_bc2_va_ghi_nhat_ky_tung_hv():
    c = Conn(hvs_trong_bc2())
    kq = go(c, ["G-0001", "G-0002", "G-0003", "O-0001", "KHONG-CO"])
    assert kq["trang_thai"] == "xong" and kq["da_go"] == ["G-0001", "G-0002"]
    ly = {b["ma_dk"]: b["ma_ly_do"] for b in kq["bo_qua"]}
    assert ly == {"G-0003": "da_co_ket_qua", "O-0001": "khong_con_o_bc2", "KHONG-CO": "hv_khong_ton_tai"}
    sp = c.goi("EXEC usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2")
    assert [p for _s, p in sp] == [("G-0001", "12", BC2, 101), ("G-0002", "12", BC2, 101)]
    assert c.hv["G-0001"]["tt"] == "09" and c.hv["G-0001"]["ma_bc2"] == ""
    assert c.hv["G-0002"]["tt"] == "17"                       # thi lại: về 17, KHÔNG quay lại BC2 cũ
    assert c.hv["G-0003"]["tt"] == "13" and c.hv["O-0001"]["ma_bc2"] == "75/2026"
    assert {h["ma_dk"]: h["ket_qua"] for h in nk.lo_hv("lo-go-00001")}["G-0001"] == "da_go"
    ds = [s for s, _ in c.log]
    assert ds.index(next(s for s in ds if "sp_getapplock" in s)) < ds.index(next(s for s in ds if "Update_DanhSachHocSinhBC2" in s))
    for s in ds:
        assert not any(k in s.upper() for k in ("INSERT INTO", "UPDATE ", "DELETE FROM")), s


def test_go_bc2_da_dong_hoac_khong_co_khong_ghi_gi():
    c = Conn(hvs_trong_bc2(), bc2=[{"MaBCII": BC2, "MaBCI": "858/26-TTTÐ", "SoBaoCao": BC2, "TrangThai": True,
                                    "TongSoThiSinh": 5}])
    with pytest.raises(svc.LoiNghiepVu) as e:
        go(c, ["G-0001"])
    assert e.value.ma == "bc2_da_dong"
    with pytest.raises(svc.LoiNghiepVu) as e:
        go(c, ["G-0001"], ma_bc2="999/2020")
    assert e.value.ma == "bc2_khong_ton_tai" and e.value.http == 404
    assert c.goi("EXEC usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2") == []
    assert len(c.goi("EXEC sp_releaseapplock")) == 2


def test_go_hv_co_tt_cu_rong_can_xac_nhan_roi_moi_go():
    c = Conn(hvs_trong_bc2())
    with pytest.raises(svc.LoiNghiepVu) as e:
        go(c, ["G-0001", "G-0004"])
    assert e.value.ma == "can_xac_nhan_canh_bao" and e.value.http == 409
    assert {w["ma_dk"]: w["ma"] for w in e.value.du_lieu["canh_bao"]} == {"G-0004": "trang_thai_cu_rong"}
    assert c.goi("EXEC usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2") == []       # chưa ghi gì, kể cả G-0001
    kq = go(c, ["G-0001", "G-0004"], lo_id="lo-go-00002", da_xem_canh_bao=True)
    assert kq["da_go"] == ["G-0001", "G-0004"] and [w["ma"] for w in kq["canh_bao"]] == ["trang_thai_cu_rong"]
    assert c.hv["G-0004"]["tt"] == ""                                            # về giá trị rỗng, đã được cảnh báo


def test_go_hv_co_tt_cu_la_11_bi_chan_khong_can_xac_nhan_cung_khong_gop():
    """Chốt 11/10/2026 (A): Old='11' → gỡ ra HV kẹt 11 không BC2 → KHÔNG gỡ (khớp hoàn tác), kể cả khi đã tích xác nhận."""
    c = Conn(hvs_trong_bc2())
    for xn in (False, True):
        kq = go(c, ["G-0001", "G-0005"], lo_id=f"lo-go-0000{3 if xn else 4}", da_xem_canh_bao=xn)
        assert kq["da_go"] == ["G-0001"] if not xn else kq["da_go"] == []     # lần 2 G-0001 đã gỡ ở lần 1
        ly = {b["ma_dk"]: b["ma_ly_do"] for b in kq["bo_qua"]}
        assert ly["G-0005"] == "trang_thai_cu_la_11"
    assert c.hv["G-0005"]["tt"] == "11" and c.hv["G-0005"]["ma_bc2"] == BC2


def test_go_hv_pm_cu_doi_giua_chung_bi_bo_qua():
    c = Conn(hvs_trong_bc2())
    c.doi_truoc_sp["G-0002"] = {"tt": "13"}                   # PM cũ nhập kết quả ngay trước khi tool ghi
    kq = go(c, ["G-0001", "G-0002"])
    assert kq["da_go"] == ["G-0001"]
    assert kq["bo_qua"][0]["ma_dk"] == "G-0002" and kq["bo_qua"][0]["ma_ly_do"] == "doi_giua_chung"
    assert c.hv["G-0002"]["tt"] == "13" and c.hv["G-0002"]["ma_bc2"] == BC2


def test_go_loi_db_giua_chung_tra_da_chua_go():
    c = Conn({f"G-{i:04d}": hv("11", ma_bc2=BC2, cu="09") for i in range(1, 4)})
    goc = Cur.execute

    def execute(self, sql, params=()):
        if " ".join(sql.split()).startswith("EXEC usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2") and params[0] == "G-0002":
            raise RuntimeError("mất kết nối")
        return goc(self, sql, params)

    Cur.execute = execute
    try:
        kq = go(c, ["G-0001", "G-0002", "G-0003"])
    finally:
        Cur.execute = goc
    assert kq["trang_thai"] == "loi_giua_chung" and kq["da_go"] == ["G-0001"]
    assert kq["chua_ghi"] == ["G-0002", "G-0003"] and kq["loi"]["ma_dk"] == "G-0002"


def test_go_ds_rong_va_qua_nhieu():
    c = Conn(hvs_trong_bc2())
    with pytest.raises(svc.LoiNghiepVu) as e:
        go(c, [])
    assert e.value.ma == "khong_co_hoc_vien"
    with pytest.raises(svc.LoiNghiepVu) as e:
        go(c, [f"X{i}" for i in range(5001)])
    assert e.value.ma == "qua_nhieu_dong"


def test_go_khong_che_lo_them_cho_hoan_tac():
    """Gỡ thủ công có loại lô riêng: không lọt vào "lô THÊM gần nhất" của hoàn tác."""
    c = Conn({f"D-{i:04d}": hv("09") for i in range(1, 4)})
    svc.lap_bc2(c, lo_id="lo-them-0001", ma_kh=KHOA, ma_bc2=BC2, so_bao_cao="", ngay_bao_cao="", ghi_chu="",
                ds_ma_dk=["D-0001", "D-0002", "D-0003"], nguoi="thu1", hom_nay=HOM_NAY)
    go(c, ["D-0001"], lo_id="lo-go-00009")
    kq = svc.hoan_tac(c, ma_bc2=BC2, lo_id="lo-hoantac1", nguoi="thu1")
    assert kq["lo_goc"] == "lo-them-0001" and kq["da_go"] == ["D-0002", "D-0003"]
    assert [b["ma_ly_do"] for b in kq["bo_qua"]] == ["khong_con_o_bc2"]       # D-0001 đã được gỡ tay


# ── Xóa ──
def test_xoa_bc2_rong_con_mo_goi_sp_va_ghi_nhat_ky():
    c = Conn({}, bc2=[{"MaBCII": "90/2026", "MaBCI": "858/26-TTTÐ", "SoBaoCao": "90/2026", "TrangThai": False,
                       "TongSoThiSinh": 0}])
    kq = svc.xoa_bc2(c, "90/2026", "thu1")
    assert kq == {"ma_bc2": "90/2026", "da_xoa": True}
    assert c.goi("EXEC usp_BaoCaoII_Delete")[0][1] == ("90/2026",)
    assert all(b["MaBCII"] != "90/2026" for b in c.bc2)
    assert nk.gan_day(nk.XOA_BC2)[0]["trang_thai"] == "xong"
    assert len(c.goi("EXEC sp_releaseapplock")) == 1


def test_xoa_bc2_con_hv_dem_theo_ma_bc2_moi_tt_xu_ly_khong_dung_tong_ghi():
    # TongSoThiSinh = 0 (PM cũ không đếm) nhưng DB còn HV ở BC2 → phải chặn
    c = Conn({"X-0001": hv("13", ma_bc2="90/2026", cu="11")},
             bc2=[{"MaBCII": "90/2026", "MaBCI": "858/26-TTTÐ", "SoBaoCao": "90/2026", "TrangThai": False,
                   "TongSoThiSinh": 0}])
    with pytest.raises(svc.LoiNghiepVu) as e:
        svc.xoa_bc2(c, "90/2026", "thu1")
    assert e.value.ma == "con_hoc_vien" and e.value.http == 409 and e.value.du_lieu == {"so_hv": 1}
    assert c.goi("EXEC usp_BaoCaoII_Delete") == []


def test_xoa_bc2_da_dong_khong_co_va_sp_khong_co_hieu_luc():
    c = Conn({}, bc2=[{"MaBCII": "91/2026", "MaBCI": "858/26-TTTÐ", "SoBaoCao": "91/2026", "TrangThai": True,
                       "TongSoThiSinh": 0}])
    with pytest.raises(svc.LoiNghiepVu) as e:
        svc.xoa_bc2(c, "91/2026", "thu1")
    assert e.value.ma == "bc2_da_dong" and c.goi("EXEC usp_BaoCaoII_Delete") == []
    with pytest.raises(svc.LoiNghiepVu) as e:
        svc.xoa_bc2(c, "khong-co", "thu1")
    assert e.value.http == 404
    c2 = Conn({}, bc2=[{"MaBCII": "92/2026", "MaBCI": "858/26-TTTÐ", "SoBaoCao": "92/2026", "TrangThai": False,
                        "TongSoThiSinh": 0}])
    c2.khong_xoa_duoc = True
    with pytest.raises(RuntimeError):
        svc.xoa_bc2(c2, "92/2026", "thu1")
    assert nk.gan_day(nk.XOA_BC2)[0]["trang_thai"] == "loi_giua_chung"


def test_xoa_bc2_so_co_d_gach_dang_db():
    c = Conn({}, bc2=[{"MaBCII": "870/26-TTTÐ", "MaBCI": "A1A2870/26-TTTÐ", "SoBaoCao": "870/26-TTTĐ",
                       "TrangThai": False, "TongSoThiSinh": 150}])
    svc.xoa_bc2(c, "870/26-TTTĐ", "thu1")                                # nhập dạng Đ, DB lưu dạng Ð
    assert c.goi("EXEC usp_BaoCaoII_Delete")[0][1] == ("870/26-TTTÐ",)


# ── Router ──
@pytest.fixture
def client(monkeypatch, auth_headers):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.routers import tn_bc2 as router

    conn = Conn(hvs_trong_bc2())
    conn.bc2.append({"MaBCII": "90/2026", "MaBCI": "858/26-TTTÐ", "SoBaoCao": "90/2026", "TrangThai": False,
                     "TongSoThiSinh": 0})

    @contextmanager
    def _conn(autocommit=True):
        yield conn

    @contextmanager
    def _cur(as_dict=True):
        yield conn.cursor()

    monkeypatch.setattr(router, "sqlserver_conn", _conn)
    monkeypatch.setattr(router, "sqlserver_cursor", _cur)
    monkeypatch.setattr(svc, "hom_nay_iso", lambda: HOM_NAY)
    goc = svc.khoi_chay
    monkeypatch.setattr(svc, "khoi_chay", lambda *a, **k: goc(*a, **{**k, "dong_bo": True}))
    c = TestClient(app)

    class _C:
        def get(self, u, **kw):
            return c.get(u, headers=auth_headers, **kw)

        def post(self, u, **kw):
            return c.post(u, headers=auth_headers, **kw)

        def delete(self, u, **kw):
            return c.delete(u, headers=auth_headers, **kw)
    return _C(), conn


def test_router_chi_tiet_go_xoa_voi_so_bc2_co_dau_gach_cheo(client):
    c, conn = client
    r = c.get("/local/tnbc2/bc2/76/2026")
    assert r.status_code == 200 and r.json()["hv_thuc_te"] == 5 and r.json()["ma_bc2"] == "76/2026"
    assert c.get("/local/tnbc2/bc2/khong/co").status_code == 404
    # các route cố định vẫn đúng chỗ, không bị `{ma:path}` nuốt
    assert c.get("/local/tnbc2/bc2/goi-y-so", params={"ma_kh": KHOA}).status_code == 200
    assert c.get("/local/tnbc2/bc2/lo/khong-co-lo").status_code == 404
    body = {"lo_id": "lo-router-go1", "ds_ma_dk": ["G-0001", "G-0002"]}
    r = c.post("/local/tnbc2/bc2/76/2026/go", json=body)
    assert r.status_code == 400 and r.json()["detail"]["ma"] == "thieu_xac_nhan_csdl_that"
    r = c.post("/local/tnbc2/bc2/76/2026/go", json=dict(body, xac_nhan_csdl_that=True))
    assert r.status_code == 200 and r.json()["da_go"] == ["G-0001", "G-0002"] and r.json()["xong"] is True
    assert c.get("/local/tnbc2/bc2/lo/lo-router-go1").json()["trang_thai"] == "xong"
    n = len(conn.goi("EXEC usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2"))
    r = c.post("/local/tnbc2/bc2/76/2026/go", json=dict(body, xac_nhan_csdl_that=True))      # cùng lo_id → không chạy lại
    assert r.status_code == 200 and len(conn.goi("EXEC usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2")) == n
    # xóa
    assert c.delete("/local/tnbc2/bc2/90/2026").status_code == 400
    r = c.delete("/local/tnbc2/bc2/76/2026", params={"xac_nhan_csdl_that": True})
    assert r.status_code == 409 and r.json()["detail"]["ma"] == "con_hoc_vien"
    r = c.delete("/local/tnbc2/bc2/90/2026", params={"xac_nhan_csdl_that": True})
    assert r.status_code == 200 and r.json()["da_xoa"] is True


def test_router_go_canh_bao_tra_409_dong_bo_va_bc2_dong(client):
    c, conn = client
    r = c.post("/local/tnbc2/bc2/76/2026/go",
               json={"lo_id": "lo-router-go2", "ds_ma_dk": ["G-0004"], "xac_nhan_csdl_that": True})   # Old rỗng
    assert r.status_code == 409
    d = r.json()["detail"]
    assert d["ma"] == "can_xac_nhan_canh_bao" and d["canh_bao"][0]["ma_dk"] == "G-0004"
    assert conn.goi("EXEC usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2") == []
    conn.bc2[0]["TrangThai"] = True
    r = c.post("/local/tnbc2/bc2/76/2026/go",
               json={"lo_id": "lo-router-go3", "ds_ma_dk": ["G-0001"], "xac_nhan_csdl_that": True})
    assert r.status_code == 409 and r.json()["detail"]["ma"] == "bc2_da_dong"


def test_lam_tiep_cung_lo_id_khong_de_dau_da_go_thanh_bo_qua():
    c = Conn({f"G-{i:04d}": hv("11", ma_bc2=BC2, cu="09") for i in range(1, 4)})
    goc = Cur.execute

    def execute(self, sql, params=()):
        if " ".join(sql.split()).startswith("EXEC usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2") and params[0] == "G-0002":
            raise RuntimeError("mất kết nối")
        return goc(self, sql, params)

    Cur.execute = execute
    try:
        k1 = go(c, ["G-0001", "G-0002", "G-0003"])
    finally:
        Cur.execute = goc
    assert k1["da_go"] == ["G-0001"] and k1["chua_ghi"] == ["G-0002", "G-0003"]
    k2 = go(c, ["G-0001", "G-0002", "G-0003"])                    # cùng lo_id, hết lỗi
    assert k2["trang_thai"] == "xong" and k2["da_go"] == ["G-0001", "G-0002", "G-0003"]
    assert k2["bo_qua"] == []                                      # G-0001 KHÔNG bị tính "không còn ở BC2"
    kqs = {h["ma_dk"]: h["ket_qua"] for h in nk.lo_hv("lo-go-00001")}
    assert kqs == {"G-0001": "da_go", "G-0002": "da_go", "G-0003": "da_go"}
    assert len(c.goi("EXEC usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2")) == 3     # G-0001 không bị gọi SP lần hai


def test_chi_tiet_dem_tho_ke_ca_hv_thieu_nguoilx_va_loai_suy_tu_hv():
    c = Conn({"G-0001": hv("11", ma_bc2=BC2, cu="09", hang="A1")},
             bc2=[{"MaBCII": BC2, "MaBCI": "KHONG-CO-BC1", "SoBaoCao": BC2, "TrangThai": False, "TongSoThiSinh": 1}])
    d = svc.chi_tiet_bc2(c.cursor(), BC2)
    assert d["hv_thuc_te"] == 1 and d["ma_kh"] == "" and d["loai"] == "moto"      # không đoán 'oto'
    assert any("LEFT JOIN NguoiLX" in s for s, _ in c.log)
