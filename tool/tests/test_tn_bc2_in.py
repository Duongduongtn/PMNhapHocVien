"""TNB-08 task 165 — kho SQLite lựa chọn/sổ phần thi + ghép dữ liệu bản in (cursor giả, không DB thật)."""
from datetime import date, datetime

import pytest

from app import tn_bc2_ban_in as kho
from app import tn_bc2_in as ib
from app import tn_bc2_service as svc

HOM_NAY = date(2026, 11, 21)
DM_ND = [(1, "SH lần đầu"), (2, "SH lại LT"), (3, "SH lại LT + H"), (4, "SH lại LT + H + Đ"), (5, "SH lại H + Đ"),
         (6, "SH lại Đ"), (7, "SH lại TH"), (8, "Sát hạch Hình"), (11, "SH lần đầu (L+M+H+Đ)"),
         (12, "SH lại L+M+H+Đ"), (18, "SH lại L+Đ")]
DM_DIEM = [{"Hang": "B2", "LtDiemToiThieu": 32, "HiDiemToiThieu": 80, "DdDiemToiThieu": 80},
           {"Hang": "A1", "LtDiemToiThieu": 21, "HiDiemToiThieu": 80, "DdDiemToiThieu": None}]


def hv(ma_dk, ten, hang="B2", kq="1", diem=(0, 0, 0), ma_cu=11, ten_cu="SH lần đầu (L+M+H+Đ)", ky="", noi_ct=" Xã A",
       cctn=None, gplx=""):
    return {"MaDK": ma_dk, "HoVaTen": ten, "NgaySinh": "01/01/2000", "SoCMT": "0700", "NoiCT": noi_ct, "GiayCNSK": True,
            "HangGPLXDaCo": gplx, "SoNamLX": 0, "SoKmLXAnToan": 0, "CCTN": cctn, "MaNDCu": ma_cu, "TenNDCu": ten_cu,
            "HangGPLX": hang, "KetQuaSH": kq, "KetQua_LyThuyet": diem[0], "KetQua_Hinh": diem[1],
            "KetQua_Duong": diem[2], "MaKySH": ky, "NgayQDTT": datetime(2026, 9, 1), "MaKhoaHoc": "70004K26B0107"}


class FakeCur:
    def __init__(self, dong, bc2_dong=False):
        self.dong, self.bc2_dong, self._kq = dong, bc2_dong, []

    def execute(self, q, ts=None):
        if "FROM BaoCaoII WHERE MaBCII" in q:
            self._kq = [] if ts[0] == "khong-co" else [{"MaBCII": ts[0], "MaBCI": "B1", "SoBaoCao": ts[0],
                        "NgayBaoCao": datetime(2026, 11, 6), "TongSoThiSinh": len(self.dong),
                        "TrangThai": 1 if self.bc2_dong else 0, "NguoiTao": "thu1", "NgayTao": datetime(2026, 11, 6)}]
        elif "FROM dbo.NguoiLX_HoSo A, dbo.NguoiLX B" in q:
            self._kq = self.dong
        elif "DM_NoiDungSH" in q:
            self._kq = [{"MaNoiDungSH": m, "TenNoiDungSH": t} for m, t in DM_ND]
        elif "DM_DiemSatHach" in q:
            self._kq = DM_DIEM
        elif "usp_BaoCao_TieuDe" in q:
            self._kq = [{"maKH": ts[0], "TenCSDT": "Trung Tâm", "HangGPLX": "B", "NgayKG": datetime(2026, 7, 30)}]
        else:
            raise AssertionError(q)

    def fetchall(self):
        return list(self._kq)

    def fetchone(self):
        return self._kq[0] if self._kq else None


@pytest.fixture(autouse=True)
def kho_tam(tmp_path, monkeypatch):
    monkeypatch.setattr(kho, "DB_PATH", tmp_path / "ban_in.sqlite")


def test_dong_va_mac_dinh_o_to_bo_m():
    cur = FakeCur([hv("D1", "AN"), hv("D2", "BÌNH", kq="RD", diem=(33, 90, 0), ma_cu=12, ten_cu="SH lại L+M+H+Đ")])
    dl = ib.du_lieu_ban_in(cur, "81/TTTĐ", hom_nay=HOM_NAY)
    a, b = dl["hoc_vien"]
    assert (a["ghi_chu"], a["phai_thi"], a["da_thi"]) == ("SH lần đầu", ["L", "H", "Đ"], False)
    assert (b["ghi_chu"], b["dat"], b["nguon"]) == ("SH lại Đ", ["L", "H"], "suy")
    assert a["pm_cu_khac"] and b["pm_cu_khac"]
    assert dl["ma_kh"] == "70004K26B0107" and dl["tieu_de"]["NgayKG"] == "2026-07-30T00:00:00"


def test_mo_to_giu_dung_chu_phan_mem_cu():
    cur = FakeCur([hv("M1", "CƯỜNG", hang="A1", ma_cu=1, ten_cu="SH lần đầu")])
    h = ib.du_lieu_ban_in(cur, "870/26", hom_nay=HOM_NAY)["hoc_vien"][0]
    assert h["ghi_chu"] == "SH lần đầu" and not h["pm_cu_khac"] and h["phan"] == ["LT", "TH"]


def test_cot_in_giu_nguyen_gia_tri_sp_cu():
    cur = FakeCur([hv("D1", "AN", noi_ct=" Phường X", cctn=None)])
    dong = ib.du_lieu_crystal(ib.du_lieu_ban_in(cur, "81/TTTĐ", hom_nay=HOM_NAY))["dong"][0]
    assert dong["NoiCT"] == " Phường X" and dong["CCTN"] is None and dong["GhiChu"] == "SH lần đầu"
    assert set(dong) == {"HoVaTen", "NgaySinh", "SoCMT", "NoiCT", "GiayCNSK", "HangGPLXDaCo", "SoNamLX",
                         "SoKmLXAnToan", "CCTN", "GhiChu"}


def test_luu_lua_chon_doi_ghi_chu_va_tom_tat():
    cur = FakeCur([hv("D1", "AN"), hv("D2", "BÌNH")])
    dl = ib.luu_noi_dung_thi(cur, "81/TTTĐ", [{"ma_dk": "D1", "phai_thi": ["L", "Đ"]}], "thu1", hom_nay=HOM_NAY)
    a = dl["hoc_vien"][0]
    assert (a["ghi_chu"], a["da_sua"], a["nguon"], a["dat"]) == ("SH lại L+Đ", True, "sua", ["H"])
    assert dl["so_chon_lai"] == 1
    bi = kho.ban_in_cho_ds([dl["ma_bc2"]])[dl["ma_bc2"]]
    assert (bi["so_chon_lai"], bi["so_can_chon"]) == (1, 0)
    # về mặc định
    dl = ib.luu_noi_dung_thi(cur, "81/TTTĐ", [{"ma_dk": "D1", "phai_thi": None}], "thu1", hom_nay=HOM_NAY)
    assert dl["hoc_vien"][0]["ghi_chu"] == "SH lần đầu" and dl["so_chon_lai"] == 0


def test_tat_het_phan_la_can_chon():
    cur = FakeCur([hv("D1", "AN")])
    dl = ib.luu_noi_dung_thi(cur, "81/TTTĐ", [{"ma_dk": "D1", "phai_thi": []}], "thu1", hom_nay=HOM_NAY)
    assert dl["hoc_vien"][0]["ma_nd"] is None and dl["so_can_chon"] == 1


def test_luu_sai_phan_va_sai_hoc_vien_bao_400():
    cur = FakeCur([hv("D1", "AN")])
    with pytest.raises(svc.LoiNghiepVu) as e:
        ib.luu_noi_dung_thi(cur, "81/TTTĐ", [{"ma_dk": "D1", "phai_thi": ["M"]}], "thu1", hom_nay=HOM_NAY)
    assert e.value.ma == "phan_thi_khong_hop_le"
    with pytest.raises(svc.LoiNghiepVu) as e:
        ib.luu_noi_dung_thi(cur, "81/TTTĐ", [{"ma_dk": "X9", "phai_thi": ["L"]}], "thu1", hom_nay=HOM_NAY)
    assert e.value.ma == "hv_khong_thuoc_bc2"


def test_bc2_khong_ton_tai_404():
    with pytest.raises(svc.LoiNghiepVu) as e:
        ib.du_lieu_ban_in(FakeCur([]), "khong-co", hom_nay=HOM_NAY)
    assert e.value.http == 404


def test_lua_chon_thanh_goc_lan_sau_va_cong_ket_qua_ky_moi():
    # BC2 cũ: user cho thi chỉ Đ (đã đạt L, H) — DB lúc đó kỳ K1
    cur = FakeCur([hv("D1", "AN", kq="RD", diem=(33, 90, 0), ky="K1", ma_cu=12, ten_cu="SH lại L+M+H+Đ")])
    assert ib.du_lieu_ban_in(cur, "66/2026", hom_nay=HOM_NAY)["hoc_vien"][0]["ghi_chu"] == "SH lại Đ"  # mặc định
    ib.ghi_da_in(cur, "66/2026", "thu1", hom_nay=HOM_NAY)   # in BC2 cũ → chụp phần thi (giữ mặc định vẫn ghi)
    # Kỳ K2: thi Đ rồi rớt → DB chỉ còn kỳ gần nhất (L=H=0), BC2 mới vẫn chỉ thi Đ nhờ sổ
    cur2 = FakeCur([hv("D1", "AN", kq="RO", diem=(0, 0, 40), ky="K2", ma_cu=12, ten_cu="SH lại L+M+H+Đ")])
    h = ib.du_lieu_ban_in(cur2, "81/TTTĐ", hom_nay=HOM_NAY)["hoc_vien"][0]
    assert (h["ghi_chu"], h["dat"], h["nguon"]) == ("SH lại Đ", ["L", "H"], "so")
    lich = kho.lich_su("D1")
    assert [x["nguon"] for x in lich] == ["in", "so"]


def test_ket_qua_cu_chua_doi_ky_khong_cong_nham():
    cur = FakeCur([hv("D1", "AN", kq="RD", diem=(33, 90, 0), ky="K1", ma_cu=12, ten_cu="SH lại L+M+H+Đ")])
    ib.ghi_da_in(cur, "66/2026", "thu1", hom_nay=HOM_NAY)
    ib.du_lieu_ban_in(cur, "81/TTTĐ", hom_nay=HOM_NAY)          # DB vẫn kỳ K1 → chưa có kết quả mới
    assert [x["nguon"] for x in kho.lich_su("D1")] == ["in"]


def test_chup_lai_khong_ghi_trung():
    cur = FakeCur([hv("D1", "AN")])
    ib.ghi_da_in(cur, "81/TTTĐ", "thu1", hom_nay=HOM_NAY)
    ib.ghi_da_in(cur, "81/TTTĐ", "thu1", hom_nay=HOM_NAY)
    assert len(kho.lich_su("D1")) == 1


def test_sua_roi_ky_moi_cong_dat():
    # chọn thi H + Đ ở BC2 cũ (L đã đạt), kỳ mới rớt đường với H 90 → cộng H
    cur = FakeCur([hv("D1", "AN", kq="RH", diem=(33, 0, 0), ky="K1", ma_cu=5, ten_cu="SH lại H + Đ")])
    ib.luu_noi_dung_thi(cur, "66/2026", [{"ma_dk": "D1", "phai_thi": ["H", "Đ"]}], "thu1", hom_nay=HOM_NAY)
    ib.ghi_da_in(cur, "66/2026", "thu1", hom_nay=HOM_NAY)
    cur2 = FakeCur([hv("D1", "AN", kq="RD", diem=(0, 90, 10), ky="K2", ma_cu=6, ten_cu="SH lại Đ")])
    h = ib.du_lieu_ban_in(cur2, "81/TTTĐ", hom_nay=HOM_NAY)["hoc_vien"][0]
    assert (h["ghi_chu"], h["dat"]) == ("SH lại Đ", ["L", "H"])


def test_mac_dinh_khong_tinh_lua_chon_cua_chinh_bc2():
    cur = FakeCur([hv("D1", "AN")])
    ib.luu_noi_dung_thi(cur, "81/TTTĐ", [{"ma_dk": "D1", "phai_thi": ["H"]}], "thu1", hom_nay=HOM_NAY)
    h = ib.du_lieu_ban_in(cur, "81/TTTĐ", hom_nay=HOM_NAY)["hoc_vien"][0]
    assert h["mac_dinh"]["ghi_chu"] == "SH lần đầu" and h["ghi_chu"] == "Sát hạch Hình"


def test_ban_in_cho_ds_co_lan_in():
    kho.ghi_lan_in("81/TTTÐ", "thu1", 128, 3)
    bi = kho.ban_in_cho_ds(["81/TTTÐ", "83/TTTÐ"])
    assert bi["81/TTTÐ"]["da_in_luc"] and "83/TTTÐ" not in bi


# ── Router TNB-08: số BC2 có dấu "/" không được route {ma:path} chung nuốt ──
@pytest.fixture
def client(monkeypatch, auth_headers):
    from contextlib import contextmanager
    from fastapi.testclient import TestClient
    from app.main import app
    from app.routers import tn_bc2 as router

    cur = FakeCur([hv("D1", "AN"), hv("D2", "BÌNH", kq="RD", diem=(33, 90, 0), ma_cu=12, ten_cu="SH lại L+M+H+Đ")])

    @contextmanager
    def _cur(as_dict=True):
        yield cur

    monkeypatch.setattr(router, "sqlserver_cursor", _cur)
    c = TestClient(app)

    class _C:
        def get(self, u, **kw): return c.get(u, headers=auth_headers, **kw)
        def put(self, u, **kw): return c.put(u, headers=auth_headers, **kw)
        def post(self, u, **kw): return c.post(u, headers=auth_headers, **kw)
        def raw_get(self, u): return c.get(u)
    return _C()


def test_router_ban_in_so_bc2_co_dau_gach_cheo(client):
    r = client.get("/local/tnbc2/bc2/81/2026/ban-in")
    assert r.status_code == 200
    j = r.json()
    assert j["ma_bc2"] == "81/2026" and [h["ghi_chu"] for h in j["hoc_vien"]] == ["SH lần đầu", "SH lại Đ"]


def test_router_luu_va_da_in_va_danh_muc(client):
    r = client.put("/local/tnbc2/bc2/81/2026/noi-dung-thi", json={"ds": [{"ma_dk": "D1", "phai_thi": ["H", "Đ"]}]})
    assert r.status_code == 200 and r.json()["hoc_vien"][0]["ghi_chu"] == "SH lại H + Đ"
    r = client.post("/local/tnbc2/bc2/81/2026/da-in")
    assert r.status_code == 200 and r.json()["so_hv"] == 2
    assert client.get("/local/tnbc2/noi-dung-sh").json()["muc"][0] == {"ma": 1, "ten": "SH lần đầu"}


def test_router_phan_thi_sai_va_bc2_khong_co(client):
    r = client.put("/local/tnbc2/bc2/81/2026/noi-dung-thi", json={"ds": [{"ma_dk": "D1", "phai_thi": ["M"]}]})
    assert r.status_code == 400 and r.json()["detail"]["ma"] == "phan_thi_khong_hop_le"
    assert client.put("/local/tnbc2/bc2/81/2026/noi-dung-thi", json={"ds": []}).status_code == 422
    assert client.get("/local/tnbc2/bc2/khong-co/ban-in").status_code == 404


def test_router_can_phien(client):
    assert client.raw_get("/local/tnbc2/bc2/81/2026/ban-in").status_code in (401, 403)


# ── Hồi quy từ soát nghiệp vụ TNB-08 (21/11/2026) ──
def test_ve_mac_dinh_rut_lua_chon_khoi_so_bc2_sau_khong_bi_anh_huong():
    cur = FakeCur([hv("D1", "AN", kq="RD", diem=(33, 90, 0), ky="K1", ma_cu=12, ten_cu="SH lại L+M+H+Đ")])
    ib.luu_noi_dung_thi(cur, "A/2026", [{"ma_dk": "D1", "phai_thi": ["H", "Đ"]}], "thu1", hom_nay=HOM_NAY)   # sửa ở BC2 A
    ib.luu_noi_dung_thi(cur, "A/2026", [{"ma_dk": "D1", "phai_thi": None}], "thu1", hom_nay=HOM_NAY)          # ↺ ở BC2 A
    assert [x["nguon"] for x in kho.lich_su("D1")] == []                       # dòng "Anh sửa" đã rút
    h = ib.du_lieu_ban_in(cur, "B/2026", hom_nay=HOM_NAY)["hoc_vien"][0]       # BC2 B: điền theo DB, không theo lựa chọn đã bỏ
    assert (h["ghi_chu"], h["nguon"]) == ("SH lại Đ", "suy")


def test_chinh_ve_gia_tri_mac_dinh_cung_rut_so():
    cur = FakeCur([hv("D1", "AN")])
    ib.luu_noi_dung_thi(cur, "A/2026", [{"ma_dk": "D1", "phai_thi": ["L", "Đ"]}], "thu1", hom_nay=HOM_NAY)
    ib.luu_noi_dung_thi(cur, "A/2026", [{"ma_dk": "D1", "phai_thi": ["L", "H", "Đ"]}], "thu1", hom_nay=HOM_NAY)  # bấm lại = mặc định
    assert kho.lich_su("D1") == []


def test_ve_mac_dinh_giu_dong_da_in_va_ket_qua_so():
    cur = FakeCur([hv("D1", "AN")])
    ib.luu_noi_dung_thi(cur, "A/2026", [{"ma_dk": "D1", "phai_thi": ["Đ"]}], "thu1", hom_nay=HOM_NAY)
    ib.ghi_da_in(cur, "A/2026", "thu1", hom_nay=HOM_NAY)                       # in thật → dòng "in"
    ib.luu_noi_dung_thi(cur, "A/2026", [{"ma_dk": "D1", "phai_thi": None}], "thu1", hom_nay=HOM_NAY)
    assert [x["nguon"] for x in kho.lich_su("D1")] == ["in"]


def test_dong_da_chon_lai_in_chu_danh_muc_khong_phai_chu_ham_cu():
    # hàm cũ trả mã 6 với chữ riêng "SH lại Đ (chữ cũ)"; chưa chọn lại → giữ chữ cũ; đã chọn lại → chữ DM_NoiDungSH
    cur = FakeCur([hv("D1", "AN", kq="RD", diem=(33, 90, 0), ma_cu=6, ten_cu="SH lại Đ (chữ cũ)")])
    h = ib.du_lieu_ban_in(cur, "A/2026", hom_nay=HOM_NAY)["hoc_vien"][0]
    assert h["ghi_chu"] == "SH lại Đ (chữ cũ)"
    h = ib.luu_noi_dung_thi(cur, "A/2026", [{"ma_dk": "D1", "phai_thi": ["H", "Đ"]}], "thu1", hom_nay=HOM_NAY)["hoc_vien"][0]
    assert h["ghi_chu"] == "SH lại H + Đ"
    h = ib.luu_noi_dung_thi(cur, "A/2026", [{"ma_dk": "D1", "phai_thi": ["Đ"]}], "thu1", hom_nay=HOM_NAY)["hoc_vien"][0]
    # chọn đúng bằng mặc định = về mặc định: không còn "đã sửa", in lại chữ phần mềm cũ như dòng chưa chọn lại
    assert h["ghi_chu"] == "SH lại Đ (chữ cũ)" and h["da_sua"] is False


def test_router_xem_truoc_bc2_rong_409_va_da_in_qua_http(client, monkeypatch):
    from app import tn_bc2_in as _ib
    r = client.post("/local/tnbc2/bc2/81/2026/da-in")
    assert r.status_code == 200 and r.json()["ok"] is True
    base = _ib.du_lieu_ban_in
    monkeypatch.setattr(_ib, "du_lieu_ban_in", lambda cur, ma, **kw: {**base(cur, ma, **kw), "hoc_vien": []})
    r = client.post("/local/tnbc2/bc2/81/2026/xem-truoc")
    assert r.status_code == 409 and r.json()["detail"]["ma"] == "bc2_khong_co_hoc_vien"


def test_cot_ban_in_loi_sqlite_khong_lam_hong_danh_sach(monkeypatch, auth_headers):
    from contextlib import contextmanager
    from fastapi.testclient import TestClient
    from app.main import app
    from app.routers import tn_bc2 as router

    class _CurDs:
        def execute(self, q, ts=None): pass
        def fetchall(self): return []
    @contextmanager
    def _cur(as_dict=True):
        yield _CurDs()
    monkeypatch.setattr(router, "sqlserver_cursor", _cur)
    monkeypatch.setattr(router.svc, "ds_bc2", lambda cur, loai, dong: {"bc2": [{"ma_bc2": "81/2026"}], "tong": 1})
    monkeypatch.setattr(router.ban_in, "ban_in_cho_ds", lambda ds: (_ for _ in ()).throw(RuntimeError("sqlite khóa")))
    r = TestClient(app).get("/local/tnbc2/bc2", headers=auth_headers)
    assert r.status_code == 200 and r.json()["bc2"][0]["ban_in"] is None


def test_ket_noi_sqlite_duoc_dong(tmp_path):
    import sqlite3
    with kho._ket_noi(tmp_path / "k.sqlite") as conn:
        pass
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")


def test_ma_bc2_vao_mau_in_doi_eth_thanh_d():
    dl = {"ma_kh": "K", "ma_bc2": "870/26-TTTÐ", "tieu_de": {}, "hoc_vien": []}
    assert ib.du_lieu_crystal(dl)["ma_bc2"] == "870/26-TTTĐ"
