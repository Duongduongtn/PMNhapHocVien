"""TNB-03 (1/2) — task 98: tạo BC2 (`tn_bc2_service.tao_bc2` + `goi_y_so` + `tn_bc2_nhat_ky` + router).

Kết nối giả (không DB): khóa các bất biến của TDD §11F.3/§11F.0/§11F.7 v6.8 — chỉ gọi SP có sẵn
(không INSERT/UPDATE/DELETE trực tiếp), khóa chung `tnbc2_ghi` bao quanh và luôn nhả, đọc lại trước
khi ghi, trùng số (gộp Ð/Đ), chống tạo đôi khi thử lại, cảnh báo mô tô, tổng thí sinh đúng PM cũ,
nhật ký không chứa CMT/họ tên.
"""
from datetime import datetime

import pytest

from app import tn_bc2_nhat_ky as nk
from app import tn_bc2_service as svc

HOM_NAY = "2026-10-11"
KHOA_OTO = "70004K26B0108"
KHOA_MOTO = "70004K26A1015"
KHOA_KHONG_BC1 = "70004K26B9999"


class FakeCur:
    def __init__(self, st):
        self.st = st

    def execute(self, sql, params=()):
        s = " ".join(sql.split())
        self.st.log.append((s, tuple(params)))
        if "sp_getapplock" in s:
            self._rows = [{"r": self.st.applock}]
        elif "sp_releaseapplock" in s:
            self._rows = []
        elif s.startswith("EXEC usp_BaoCaoII_Insert"):
            if self.st.insert_loi:
                raise self.st.insert_loi
            p = params
            self.st.bc2.append({"MaBCII": p[0], "MaBCI": p[1], "SoBaoCao": p[3], "TrangThai": False,
                                "TongSoThiSinh": p[5]})
            self._rows = []
        elif s.startswith("SELECT MaBCII, MaBCI, TrangThai, TongSoThiSinh FROM BaoCaoII WHERE MaBCII"):
            self._rows = [r for r in self.st.bc2 if r["MaBCII"] == params[0]] if not self.st.mat_dong else []
        elif s.startswith("SELECT MaKH, TenKH, HangGPLX, NgayBG FROM KhoaHoc WHERE MaKH"):
            self._rows = [k for k in self.st.khoa if k["MaKH"] == params[0]]
        elif s.startswith("SELECT MaBCI, MaKH"):
            self._rows = self.st.bc1
        elif s.startswith("SELECT MaBCII, MaBCI, SoBaoCao"):
            self._rows = self.st.bc2
        else:
            raise AssertionError("câu lệnh lạ: " + s)

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class FakeConn:
    def __init__(self, bc2=(), applock=0, insert_loi=None, mat_dong=False):
        self.log = []
        self.applock, self.insert_loi, self.mat_dong = applock, insert_loi, mat_dong
        self.khoa = [
            {"MaKH": KHOA_OTO, "TenKH": "B.01K40", "HangGPLX": "B2", "NgayBG": "2026-09-18"},
            {"MaKH": KHOA_MOTO, "TenKH": "A1K126", "HangGPLX": "A1", "NgayBG": "2026-10-06"},
            {"MaKH": KHOA_KHONG_BC1, "TenKH": "B-K999", "HangGPLX": "B2", "NgayBG": "2026-09-01"},
        ]
        self.bc1 = [
            {"MaBCI": "857/26-TTTÐ", "MaKH": KHOA_OTO, "MaCSDT": "70004", "SoBaoCao": "857/26-TTTĐ", "SoHocSinh": 150},
            {"MaBCI": "A1A2870/26-TTTÐ", "MaKH": KHOA_MOTO, "MaCSDT": "70004", "SoBaoCao": "A1A2870/26-TTTĐ",
             "SoHocSinh": 150},
        ]
        self.bc2 = [dict(b) for b in bc2] or [
            {"MaBCII": "79/2026", "MaBCI": "852/26-TTTÐ", "SoBaoCao": "79/2026", "TrangThai": False, "TongSoThiSinh": 25},
            {"MaBCII": "80/2026", "MaBCI": "796/24", "SoBaoCao": "80/2026", "TrangThai": False, "TongSoThiSinh": 0},
            {"MaBCII": "62/2025", "MaBCI": "600/25-TTTÐ", "SoBaoCao": "62/2025", "TrangThai": True, "TongSoThiSinh": 30},
        ]

    def cursor(self, as_dict=True):
        return FakeCur(self)

    # tiện kiểm
    @property
    def cau_lenh(self):
        return [s for s, _ in self.log]

    def goi(self, prefix):
        return [(s, p) for s, p in self.log if s.startswith(prefix)]


@pytest.fixture(autouse=True)
def _co_lap(tmp_path, monkeypatch):
    monkeypatch.setattr(nk, "DB_PATH", tmp_path / "tnbc2_nhat_ky.sqlite")
    svc.bo_cache()
    yield
    svc.bo_cache()


def tao(conn, so="81/2026", ma_kh=KHOA_OTO, ngay="2026-10-11", ghi_chu="", nguoi="thu1", **kw):
    return svc.tao_bc2(conn, ma_kh, so, ngay, ghi_chu, nguoi, hom_nay=HOM_NAY,
                       now=datetime(2026, 10, 11, 9, 30, 15), **kw)


# ── Ghi đúng SP, đúng tham số ──
def test_tao_bc2_oto_goi_dung_sp_va_tham_so_nhu_pm_cu():
    c = FakeConn()
    kq = tao(c)
    ins = c.goi("EXEC usp_BaoCaoII_Insert")
    assert len(ins) == 1
    p = ins[0][1]
    assert p == ("81/2026", "857/26-TTTÐ", "70004", "81/2026", datetime(2026, 10, 11), 0, None, 0, "thu1", None,
                 datetime(2026, 10, 11, 9, 30, 15), datetime(2026, 10, 11, 9, 30, 15))
    assert p[10] == p[11]                      # NgayTao = NgaySua
    assert kq["ma_bc2"] == "81/2026" and kq["da_ton_tai"] is False and kq["trang_thai"] == 0
    assert kq["tong_so_thi_sinh"] == 0 and kq["ma_bci"] == "857/26-TTTÐ"


def test_khong_co_cau_ghi_truc_tiep_va_khoa_bao_quanh_sp():
    c = FakeConn()
    tao(c)
    for s in c.cau_lenh:
        assert not any(k in s.upper() for k in ("INSERT INTO", "UPDATE ", "DELETE FROM")), s
    ds = c.cau_lenh
    i_khoa = next(i for i, s in enumerate(ds) if "sp_getapplock" in s)
    i_ins = next(i for i, s in enumerate(ds) if s.startswith("EXEC usp_BaoCaoII_Insert"))
    i_nha = next(i for i, s in enumerate(ds) if "sp_releaseapplock" in s)
    assert i_khoa < i_ins < i_nha
    assert c.goi("DECLARE @r INT")[0][1] == (svc.TEN_KHOA_GHI, svc.CHO_KHOA_GHI_MS)
    # đọc lại BC1/BC2 TRƯỚC khi ghi
    assert any(s.startswith("SELECT MaBCI, MaKH") for s in ds[i_khoa:i_ins])
    assert any(s.startswith("SELECT MaBCII, MaBCI, SoBaoCao") for s in ds[i_khoa:i_ins])


def test_moto_tong_so_thi_sinh_bang_so_hoc_sinh_bc1_va_so_luu_dang_db():
    c = FakeConn()
    kq = tao(c, so="870/26-TTTĐ", ma_kh=KHOA_MOTO, da_xem_canh_bao=True)
    p = c.goi("EXEC usp_BaoCaoII_Insert")[0][1]
    assert p[0] == "870/26-TTTÐ"       # MaBCII varchar: dạng DB (Đ → Ð)
    assert p[3] == "870/26-TTTĐ"       # SoBaoCao nvarchar: như nhân viên gõ
    assert p[5] == 150 and kq["tong_so_thi_sinh"] == 150
    assert p[2] == "70004"


def test_tong_so_thi_sinh_do_lap_truyen_vao_va_ghi_chu_co_noi_dung():
    c = FakeConn()
    kq = tao(c, ghi_chu="  Đợt tháng 10  ", tong_so_thi_sinh=37)
    p = c.goi("EXEC usp_BaoCaoII_Insert")[0][1]
    assert p[5] == 37 and p[6] == "Đợt tháng 10" and kq["tong_so_thi_sinh"] == 37


def test_ngay_mac_dinh_hom_nay_va_ngay_sai():
    c = FakeConn()
    tao(c, ngay="")
    assert c.goi("EXEC usp_BaoCaoII_Insert")[0][1][4] == datetime(2026, 10, 11)
    with pytest.raises(svc.LoiNghiepVu) as e:
        tao(FakeConn(), ngay="11/10/2026")
    assert e.value.ma == "ngay_khong_hop_le" and e.value.http == 400


# ── Chặn ──
def test_trung_so_chan_va_khong_ghi_ke_ca_eth_dau_gach():
    c = FakeConn()
    with pytest.raises(svc.LoiNghiepVu) as e:
        tao(c, so="80/2026")
    assert e.value.ma == "trung_so" and e.value.http == 409
    assert c.goi("EXEC usp_BaoCaoII_Insert") == []
    c2 = FakeConn(bc2=[{"MaBCII": "870/26-TTTÐ", "MaBCI": "OTHER", "SoBaoCao": "870/26-TTTĐ", "TrangThai": False,
                        "TongSoThiSinh": 0}])
    with pytest.raises(svc.LoiNghiepVu) as e:
        tao(c2, so="870/26-tttđ", ma_kh=KHOA_MOTO, da_xem_canh_bao=True)
    assert e.value.ma == "trung_so" and c2.goi("EXEC usp_BaoCaoII_Insert") == []


def test_khoa_chua_co_bc1_va_khoa_khong_ton_tai():
    c = FakeConn()
    with pytest.raises(svc.LoiNghiepVu) as e:
        tao(c, ma_kh=KHOA_KHONG_BC1)
    assert e.value.ma == "khoa_chua_co_bc1" and e.value.http == 409
    with pytest.raises(svc.LoiNghiepVu) as e:
        tao(c, ma_kh="khong-co")
    assert e.value.http == 404
    assert c.goi("EXEC usp_BaoCaoII_Insert") == []
    assert len(c.goi("EXEC sp_releaseapplock")) == 2          # khóa luôn được nhả dù lỗi


def test_so_rong_qua_dai_va_vuot_do_dai():
    for so, ma in (("   ", "thieu_so"), ("1234567890/2026", "so_qua_dai")):
        c = FakeConn()
        with pytest.raises(svc.LoiNghiepVu) as e:
            tao(c, so=so)
        assert e.value.ma == ma and c.log == []               # chưa vào DB, chưa lấy khóa
    c = FakeConn()
    with pytest.raises(svc.LoiNghiepVu) as e:
        tao(c, ghi_chu="x" * 256)
    assert e.value.ma == "vuot_do_dai" and c.log == []
    with pytest.raises(svc.LoiNghiepVu) as e:
        tao(c, nguoi="n" * 31)
    assert e.value.ma == "vuot_do_dai"


def test_khoa_ghi_ban_thi_409_dang_ghi_khong_ghi_gi():
    c = FakeConn(applock=-1)
    with pytest.raises(svc.LoiNghiepVu) as e:
        tao(c)
    assert e.value.ma == "dang_ghi" and e.value.http == 409
    assert c.goi("EXEC usp_BaoCaoII_Insert") == [] and c.goi("EXEC sp_releaseapplock") == []


# ── Chống tạo đôi / cảnh báo ──
def test_thu_lai_sau_khi_da_tao_tra_da_ton_tai_khong_ghi_lan_hai():
    c = FakeConn()
    k1 = tao(c, so="81/2026")
    k2 = tao(c, so="81/2026", thu_lai=True)
    assert k1["da_ton_tai"] is False and k2["da_ton_tai"] is True and k2["ma_bc2"] == "81/2026"
    assert len(c.goi("EXEC usp_BaoCaoII_Insert")) == 1


def test_go_trung_dung_so_bc2_cua_khoa_ma_khong_thu_lai_van_la_chan():
    """PRD TNB-03: số BC2 trùng → chặn. Chỉ khi client báo `thu_lai` mới coi là đã tạo xong."""
    c = FakeConn()
    tao(c, so="81/2026")
    with pytest.raises(svc.LoiNghiepVu) as e:
        tao(c, so="81/2026")
    assert e.value.ma == "trung_so" and len(c.goi("EXEC usp_BaoCaoII_Insert")) == 1
    # thu_lai nhưng BC2 đó thuộc BC1 khác → vẫn chặn
    with pytest.raises(svc.LoiNghiepVu) as e:
        tao(c, so="80/2026", thu_lai=True)
    assert e.value.ma == "trung_so"


def test_moto_tong_so_thi_sinh_khong_ghi_de_duoc():
    c = FakeConn()
    kq = tao(c, so="870/26-TTTĐ", ma_kh=KHOA_MOTO, da_xem_canh_bao=True, tong_so_thi_sinh=3)
    assert kq["tong_so_thi_sinh"] == 150 and c.goi("EXEC usp_BaoCaoII_Insert")[0][1][5] == 150


def test_moto_da_co_bc2_thi_can_xac_nhan_canh_bao():
    c = FakeConn(bc2=[{"MaBCII": "870/26-TTTÐ", "MaBCI": "A1A2870/26-TTTÐ", "SoBaoCao": "870/26-TTTĐ",
                       "TrangThai": False, "TongSoThiSinh": 150}])
    with pytest.raises(svc.LoiNghiepVu) as e:
        tao(c, so="871/26-TTTĐ", ma_kh=KHOA_MOTO)
    assert e.value.ma == "can_xac_nhan_canh_bao" and e.value.http == 409
    assert e.value.du_lieu["canh_bao"][0]["ma"] == "bc1_da_co_bc2_moto"
    assert c.goi("EXEC usp_BaoCaoII_Insert") == []
    kq = tao(c, so="871/26-TTTĐ", ma_kh=KHOA_MOTO, da_xem_canh_bao=True)
    assert kq["canh_bao"][0]["ma"] == "bc1_da_co_bc2_moto" and len(c.goi("EXEC usp_BaoCaoII_Insert")) == 1


def test_oto_nhieu_bc2_cho_mot_bc1_khong_canh_bao():
    c = FakeConn(bc2=[{"MaBCII": "75/2026", "MaBCI": "857/26-TTTÐ", "SoBaoCao": "75/2026", "TrangThai": False,
                       "TongSoThiSinh": 40}])
    assert tao(c, so="81/2026")["canh_bao"] == []


# ── Lỗi từ DB ──
def test_loi_khoa_chinh_tu_db_thanh_trung_so_va_nhat_ky_that_bai():
    c = FakeConn(insert_loi=Exception("(2627, b'Violation of PRIMARY KEY constraint')"))
    with pytest.raises(svc.LoiNghiepVu) as e:
        tao(c)
    assert e.value.ma == "trung_so"
    assert nk.gan_day(nk.TAO_BC2)[0]["trang_thai"] == "that_bai"
    assert len(c.goi("EXEC sp_releaseapplock")) == 1


def test_khong_thay_dong_vua_tao_la_loi_giua_chung_khong_phai_that_bai():
    """SP đã chạy nên không được ghi nhật ký "thất bại" (có thể đã tạo)."""
    c = FakeConn(mat_dong=True)
    with pytest.raises(RuntimeError):
        tao(c)
    assert nk.gan_day(nk.TAO_BC2)[0]["trang_thai"] == "loi_giua_chung"


# ── Nhật ký ──
def test_nhat_ky_bat_dau_roi_xong_va_khong_chua_pii():
    c = FakeConn()
    tao(c, so="81/2026", nguoi="thu1")
    d = nk.gan_day()[0]
    assert d["loai"] == "tao_bc2" and d["nguoi"] == "thu1" and d["trang_thai"] == "xong"
    assert d["ma_kh"] == KHOA_OTO and d["ma_bc2"] == "81/2026"
    assert d["ket_qua"]["ma_bc2"] == "81/2026"
    # lọc PII
    i = nk.bat_dau("thu1", nk.THEM_HV, KHOA_OTO, "81/2026", 2, "thêm", {"ma_dk": ["A-1", "A-2"],
                   "ten": "Nguyễn Văn A", "ds": [{"ma_dk": "A-1", "cmt": "079200000001", "ho_ten": "X"}]})
    nk.ket_thuc(i, "xong", {"so_cmt": "079", "da_them": 2})
    d = nk.gan_day(nk.THEM_HV)[0]
    assert d["chi_tiet"] == {"ma_dk": ["A-1", "A-2"], "ds": [{"ma_dk": "A-1"}]}
    assert d["ket_qua"] == {"da_them": 2}


# ── Gợi ý số ──
def test_goi_y_so_oto_va_moto():
    c = FakeConn()
    cur = c.cursor()
    g = svc.goi_y_so(cur, KHOA_OTO, HOM_NAY)
    assert g["so"] == "81/2026" and g["loai"] == "oto" and g["co_bc1"] is True and g["trung"] is False
    gm = svc.goi_y_so(cur, KHOA_MOTO, HOM_NAY)
    assert gm["so"] == "870/26-TTTĐ" and gm["loai"] == "moto" and gm["bc1"]["so_hoc_sinh"] == 150
    gk = svc.goi_y_so(cur, KHOA_KHONG_BC1, HOM_NAY)
    assert gk["co_bc1"] is False and gk["bc1"] is None


def test_goi_y_so_moto_trung_so_da_co_va_bc2_cua_khoa():
    c = FakeConn(bc2=[{"MaBCII": "870/26-TTTÐ", "MaBCI": "A1A2870/26-TTTÐ", "SoBaoCao": "870/26-TTTĐ",
                       "TrangThai": False, "TongSoThiSinh": 150}])
    g = svc.goi_y_so(c.cursor(), KHOA_MOTO, HOM_NAY)
    assert g["trung"] is True and [b["ma"] for b in g["bc2_cua_khoa"]] == ["870/26-TTTÐ"]


# ── Router ──
@pytest.fixture
def client(monkeypatch, auth_headers):
    from contextlib import contextmanager
    from fastapi.testclient import TestClient
    from app.main import app
    from app.routers import tn_bc2 as router

    conn = FakeConn()

    @contextmanager
    def _conn(autocommit=True):
        yield conn

    @contextmanager
    def _cur(as_dict=True):
        yield conn.cursor()

    monkeypatch.setattr(router, "sqlserver_conn", _conn)
    monkeypatch.setattr(router, "sqlserver_cursor", _cur)
    monkeypatch.setattr(svc, "hom_nay_iso", lambda: HOM_NAY)
    c = TestClient(app)

    class _C:
        def get(self, u, **kw):
            return c.get(u, headers=auth_headers, **kw)

        def post(self, u, **kw):
            return c.post(u, headers=auth_headers, **kw)
    return _C(), conn


def test_router_tao_bc2_can_cong_xac_nhan_va_ghi_nguoi_tao_la_ten_dang_nhap(client):
    c, conn = client
    body = {"ma_kh": KHOA_OTO, "so_bao_cao": "81/2026", "ngay_bao_cao": "2026-10-11"}
    r = c.post("/local/tnbc2/bc2", json=body)
    assert r.status_code == 400 and r.json()["detail"]["ma"] == "thieu_xac_nhan_csdl_that"
    assert conn.goi("EXEC usp_BaoCaoII_Insert") == []
    r = c.post("/local/tnbc2/bc2", json=dict(body, xac_nhan_csdl_that=True))
    assert r.status_code == 200 and r.json()["ma_bc2"] == "81/2026" and r.json()["da_ton_tai"] is False
    assert conn.goi("EXEC usp_BaoCaoII_Insert")[0][1][8] == "op-test"      # NguoiTao = tên đăng nhập tool
    r = c.post("/local/tnbc2/bc2", json=dict(body, so_bao_cao="80/2026", xac_nhan_csdl_that=True))
    assert r.status_code == 409 and r.json()["detail"]["ma"] == "trung_so"
    r = c.post("/local/tnbc2/bc2", json=dict(body, xac_nhan_csdl_that=True))           # gõ trùng lần nữa → chặn
    assert r.status_code == 409 and r.json()["detail"]["ma"] == "trung_so"
    r = c.post("/local/tnbc2/bc2", json=dict(body, xac_nhan_csdl_that=True, thu_lai=True))   # gửi lại → đã tồn tại
    assert r.status_code == 200 and r.json()["da_ton_tai"] is True


def test_router_canh_bao_tra_danh_sach_canh_bao(client):
    c, conn = client
    conn.bc2.append({"MaBCII": "870/26-TTTÐ", "MaBCI": "A1A2870/26-TTTÐ", "SoBaoCao": "870/26-TTTĐ",
                     "TrangThai": False, "TongSoThiSinh": 150})
    r = c.post("/local/tnbc2/bc2", json={"ma_kh": KHOA_MOTO, "so_bao_cao": "871/26-TTTĐ", "xac_nhan_csdl_that": True})
    assert r.status_code == 409
    d = r.json()["detail"]
    assert d["ma"] == "can_xac_nhan_canh_bao" and d["canh_bao"][0]["ma"] == "bc1_da_co_bc2_moto"


def test_router_goi_y_so(client):
    c, _ = client
    r = c.get("/local/tnbc2/bc2/goi-y-so", params={"ma_kh": KHOA_OTO})
    assert r.status_code == 200 and r.json()["so"] == "81/2026"
    assert c.get("/local/tnbc2/bc2/goi-y-so", params={"ma_kh": "khong-co"}).status_code == 404
