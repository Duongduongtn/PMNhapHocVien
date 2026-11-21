"""TNB-07 (1/2) — task 105: danh sách BC1/BC2 + nhật ký (`ds_bc1`, `ds_bc2`, `ds_nhat_ky` + router). CHỈ ĐỌC.

Khóa các bất biến: lọc loại (suy từ hạng khóa) và đang mở/đã đóng, "HV thực tế" bằng ĐÚNG MỘT truy vấn
(GROUP BY MaBC2), lệch Tổng ghi chỉ là đánh dấu, tên nghiệp vụ + tóm tắt đã/chưa ghi cho nhật ký, nhật ký
không chứa PII, route `GET /bc2` không bị `/bc2/{ma:path}` nuốt.
"""
from contextlib import contextmanager
from datetime import datetime

import pytest

from app import tn_bc2_nhat_ky as nk
from app import tn_bc2_service as svc


class FakeCur:
    def __init__(self, bc1=(), bc2=()):
        self.bc1, self.bc2, self.log = list(bc1), list(bc2), []

    def execute(self, sql, params=()):
        s = " ".join(sql.split())
        self.log.append(s)
        if s.startswith("SELECT c.MaBCI, c.SoBaoCao, c.NgayBaoCao, c.MaKH, c.SoHocSinh"):
            self._rows = self.bc1
        elif s.startswith("SELECT b.MaBCII, b.SoBaoCao, b.NgayBaoCao, b.MaBCI"):
            self._rows = self.bc2
        else:
            raise AssertionError("câu lệnh lạ: " + s)

    def fetchall(self):
        return list(self._rows)


def bc2_row(ma, loai="B2", tong=10, thuc=10, tt=False, bc1="858/26-TTTĐ", kh="70004K26B0108", nguoi="CSDTTHANHDAT",
            ngay=datetime(2026, 10, 3), kq=0):
    return {"MaBCII": ma, "SoBaoCao": ma, "NgayBaoCao": ngay, "MaBCI": bc1, "SoBC1": bc1, "MaKH": kh, "TenKH": "K " + kh[-4:],
            "HangGPLX": loai, "TongSoThiSinh": tong, "TrangThai": tt, "NguoiTao": nguoi, "NgayTao": ngay, "hv_thuc_te": thuc,
            "hv_ket_qua": kq}


def du_lieu_bc2():
    return [
        bc2_row("81/2026", tong=0, thuc=3, ngay=datetime(2026, 10, 11), nguoi="thu1"),            # tool tạo, lệch
        bc2_row("76/2026", tong=24, thuc=24),
        bc2_row("62/2025", tong=30, thuc=28, tt=True, ngay=datetime(2025, 11, 28)),               # đã đóng, lệch
        bc2_row("870/26-TTTÐ", loai="A1", tong=150, thuc=150, bc1="A1A2870/26-TTTÐ", kh="70004K26A1015"),
        bc2_row("867/26-TTTÐ", loai="A1", tong=150, thuc=149, tt=True, bc1="A1A2867/26-TTTÐ", kh="70004K26A1014"),
    ]


def test_ds_bc2_loc_loai_dang_mo_da_dong_va_lech():
    cur = FakeCur(bc2=du_lieu_bc2())
    tat_ca = svc.ds_bc2(cur)
    assert tat_ca["tong"] == 5 and tat_ca["dang_mo"] == 3 and tat_ca["da_dong"] == 2 and tat_ca["lech"] == 3
    oto = svc.ds_bc2(FakeCur(bc2=du_lieu_bc2()), "oto")
    assert [b["ma_bc2"] for b in oto["bc2"]] == ["81/2026", "76/2026", "62/2025"] and {b["loai"] for b in oto["bc2"]} == {"oto"}
    moto = svc.ds_bc2(FakeCur(bc2=du_lieu_bc2()), "moto")
    assert [b["ma_bc2"] for b in moto["bc2"]] == ["870/26-TTTÐ", "867/26-TTTÐ"]
    mo = svc.ds_bc2(FakeCur(bc2=du_lieu_bc2()), "oto", "mo")
    assert [b["ma_bc2"] for b in mo["bc2"]] == ["81/2026", "76/2026"] and all(b["dang_mo"] for b in mo["bc2"])
    dong = svc.ds_bc2(FakeCur(bc2=du_lieu_bc2()), "", "dong")
    assert [b["ma_bc2"] for b in dong["bc2"]] == ["62/2025", "867/26-TTTÐ"] and all(b["dong"] for b in dong["bc2"])


def test_ds_bc2_lech_chi_la_danh_dau_va_truong_hop_null():
    b = {b["ma_bc2"]: b for b in svc.ds_bc2(FakeCur(bc2=du_lieu_bc2()))["bc2"]}
    assert b["81/2026"]["lech"] is True and b["81/2026"]["tong_ghi"] == 0 and b["81/2026"]["hv_thuc_te"] == 3
    assert b["76/2026"]["lech"] is False and b["62/2025"]["lech"] is True
    assert b["81/2026"]["nguoi_tao"] == "thu1" and b["81/2026"]["ngay_bao_cao"] == "2026-10-11"
    r = bc2_row("90/2026", tong=None, thuc=0)
    assert svc.ds_bc2(FakeCur(bc2=[r]))["bc2"][0]["lech"] is False       # chưa có Tổng ghi → không đánh dấu lệch


def test_ds_bc2_dung_mot_truy_van_group_by_khong_dem_tung_bc2():
    cur = FakeCur(bc2=du_lieu_bc2())
    svc.ds_bc2(cur, "oto", "mo")
    assert len(cur.log) == 1                                            # đúng MỘT truy vấn cho cả danh sách
    assert "GROUP BY MaBC2" in cur.log[0] and cur.log[0].count("COUNT(*)") == 1
    for s in cur.log:
        assert s.startswith("SELECT") and not any(k in s.upper() for k in ("INSERT", "UPDATE ", "DELETE", "EXEC"))


def test_bc2_thieu_bc1_hoac_khoa_khong_bi_doan_la_oto():
    r = bc2_row("91/2026", loai=None)
    assert svc.ds_bc2(FakeCur(bc2=[r]), "oto")["tong"] == 0 and svc.ds_bc2(FakeCur(bc2=[r]), "moto")["tong"] == 0
    kq = svc.ds_bc2(FakeCur(bc2=[r]))
    assert kq["tong"] == 1 and kq["bc2"][0]["loai"] == ""


def test_ds_bc1_loc_loai_va_so_bc2():
    bc1 = [
        {"MaBCI": "858/26-TTTÐ", "SoBaoCao": "858/26-TTTĐ", "NgayBaoCao": datetime(2026, 9, 20), "MaKH": "70004K26B0108",
         "SoHocSinh": 30, "TenKH": "B.01K40", "HangGPLX": "B2", "NgayBG": datetime(2026, 9, 18), "so_bc2": 2},
        {"MaBCI": "A1A2870/26-TTTÐ", "SoBaoCao": "A1A2870/26-TTTĐ", "NgayBaoCao": datetime(2026, 9, 30),
         "MaKH": "70004K26A1015", "SoHocSinh": 150, "TenKH": "A1K126", "HangGPLX": "A1", "NgayBG": datetime(2026, 10, 6),
         "so_bc2": 1},
    ]
    kq = svc.ds_bc1(FakeCur(bc1=bc1), "moto")
    assert kq["tong"] == 1 and kq["bc1"][0]["so_bao_cao"] == "A1A2870/26-TTTĐ" and kq["bc1"][0]["so_bc2"] == 1
    assert svc.ds_bc1(FakeCur(bc1=bc1))["tong"] == 2
    assert svc.ds_bc1(FakeCur(bc1=bc1), "oto")["bc1"][0]["ten_kh"] == "B.01K40"


# ── Nhật ký ──
@pytest.fixture
def nhat_ky_db(tmp_path):
    return tmp_path / "nk.sqlite"


def test_nhat_ky_ten_nghiep_vu_tom_tat_va_khong_pii(nhat_ky_db):
    i1 = nk.bat_dau("thu1", nk.THEM_HV, "70004K26B0108", "81/2026", 4, "Thêm 4 HV",
                    {"ma_dk": ["A-1", "A-2"], "ten": "Nguyễn Văn A", "cmt": "079200000001"}, lo_id="lo-1", db_path=nhat_ky_db)
    nk.ket_thuc(i1, "xong", {"da_them": 3, "bo_qua": 1, "chua_ghi": 0}, db_path=nhat_ky_db)
    i2 = nk.bat_dau("thu1", nk.CUU, "70004K26B0108", "", 1, "Cứu trạng thái: Đã học xong, chưa tốt nghiệp (03) → Thi sát hạch chưa đạt (17)", {"ma_dk": "A-9", "ly_do": "x"},
                    db_path=nhat_ky_db)
    nk.ket_thuc(i2, "xong", {"tt_cu": "03", "tt_moi": "17"}, db_path=nhat_ky_db)
    i3 = nk.bat_dau("thu2", nk.TOT_NGHIEP, "70004K26B0107", "", 5, "Tốt nghiệp 5 HV", {"ma_dk": ["B-1"]},
                    db_path=nhat_ky_db)
    nk.ket_thuc(i3, "loi_giua_chung", {"da_ghi": 2, "chua_ghi": 3}, db_path=nhat_ky_db)
    i4 = nk.bat_dau("thu1", nk.TAO_BC2, "70004K26B0108", "82/2026", 0, "Tạo BC2 82/2026", {}, db_path=nhat_ky_db)
    kq = svc.ds_nhat_ky(db_path=nhat_ky_db)
    assert kq["tong"] == 4
    d = {r["id"]: r for r in kq["nhat_ky"]}
    assert d[i1]["ten_loai"] == "Thêm học viên vào BC2" and d[i1]["ket_qua"] == {
        "da_ghi": 3, "chua_ghi": 0, "bo_qua": 1, "tom_tat": "Đã thêm 3 · Bỏ qua 1"}
    assert d[i1]["ma_bc2"] == "81/2026" and d[i1]["so_hv"] == 4 and d[i1]["nguoi"] == "thu1"
    assert d[i2]["ten_loai"] == "Cứu trạng thái" and d[i2]["ket_qua"]["tom_tat"] == "Đã học xong, chưa tốt nghiệp (03) → Thi sát hạch chưa đạt (17)"
    assert d[i3]["ten_loai"] == "Cập nhật tốt nghiệp" and d[i3]["ten_trang_thai"].startswith("Lỗi giữa chừng")
    assert d[i3]["ket_qua"]["da_ghi"] == 2 and d[i3]["ket_qua"]["chua_ghi"] == 3
    assert d[i4]["ten_trang_thai"] == "Đang chạy hoặc bị gián đoạn"          # còn `bat_dau`: treo hoặc đang chạy
    blob = repr(kq)
    for pii in ("Nguyễn Văn A", "079200000001", "A-1", "A-2"):
        assert pii not in blob


def test_nhat_ky_loc_theo_loai_ma_bc2_va_gioi_han(nhat_ky_db):
    for n in range(7):
        i = nk.bat_dau("thu1", nk.THEM_HV, "K", "81/2026", 1, "t", {}, db_path=nhat_ky_db)
        nk.ket_thuc(i, "xong", {"da_them": 1}, db_path=nhat_ky_db)
    i = nk.bat_dau("thu1", nk.XOA_BC2, "", "90/2026", 0, "Xóa", {}, db_path=nhat_ky_db)
    nk.ket_thuc(i, "xong", {}, db_path=nhat_ky_db)
    assert svc.ds_nhat_ky(loai="them_hv", db_path=nhat_ky_db)["tong"] == 7
    assert svc.ds_nhat_ky(ma_bc2="90/2026", db_path=nhat_ky_db)["nhat_ky"][0]["ten_loai"] == "Xóa BC2"
    assert svc.ds_nhat_ky(gioi_han=3, db_path=nhat_ky_db)["tong"] == 3
    assert svc.ds_nhat_ky(gioi_han=0, db_path=nhat_ky_db)["tong"] == 1     # kẹp tối thiểu 1


def test_nhat_ky_ma_bc2_co_d_gach_doi_sang_dang_db(nhat_ky_db):
    i = nk.bat_dau("thu1", nk.TAO_BC2, "K", "870/26-TTTÐ", 0, "Tạo", {}, db_path=nhat_ky_db)
    nk.ket_thuc(i, "xong", {}, db_path=nhat_ky_db)
    assert svc.ds_nhat_ky(ma_bc2="870/26-TTTĐ", db_path=nhat_ky_db)["tong"] == 1


# ── Router ──
@pytest.fixture
def client(monkeypatch, auth_headers, tmp_path):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.routers import tn_bc2 as router

    cur = FakeCur(bc2=du_lieu_bc2())

    @contextmanager
    def _cur(as_dict=True):
        yield cur

    monkeypatch.setattr(router, "sqlserver_cursor", _cur)
    monkeypatch.setattr(nk, "DB_PATH", tmp_path / "nk.sqlite")
    from app import tn_bc2_ban_in as _kho
    monkeypatch.setattr(_kho, "DB_PATH", tmp_path / "ban_in.sqlite")
    i = nk.bat_dau("thu1", nk.TAO_BC2, "K", "81/2026", 0, "Tạo BC2 81/2026", {})
    nk.ket_thuc(i, "xong", {"ma_bc2": "81/2026"})
    c = TestClient(app)

    class _C:
        def get(self, u, **kw):
            return c.get(u, headers=auth_headers, **kw)
    return _C(), cur


def test_router_bc2_bc1_nhat_ky_khong_bi_route_catch_all_nuot(client):
    c, cur = client
    r = c.get("/local/tnbc2/bc2", params={"loai": "oto", "dong": "mo"})
    assert r.status_code == 200 and [b["ma_bc2"] for b in r.json()["bc2"]] == ["81/2026", "76/2026"]
    assert c.get("/local/tnbc2/bc2", params={"loai": "xe"}).status_code == 422
    assert c.get("/local/tnbc2/bc2", params={"dong": "khac"}).status_code == 422
    r = c.get("/local/tnbc2/bc1")
    assert r.status_code == 200 and r.json()["tong"] == 0
    r = c.get("/local/tnbc2/nhat-ky", params={"loai": "tao_bc2"})
    assert r.status_code == 200 and r.json()["nhat_ky"][0]["ten_loai"] == "Tạo BC2"
    assert c.get("/local/tnbc2/nhat-ky", params={"gioi_han": 0}).status_code == 422
    assert c.get("/local/tnbc2/nhat-ky", params={"gioi_han": 501}).status_code == 422


# ── TNB-07 (CHANGES #104): cột Trạng thái 3 giá trị; BC2 đã gửi / có kết quả bị khóa dù chưa đóng ──
def test_ds_bc2_trang_thai_3_gia_tri_va_khoa_khi_da_co_ket_qua():
    rows = [bc2_row("81/2026", thuc=3),                                  # đang mở: mọi HV còn "Đã vào BC2"
            bc2_row("76/2026", thuc=24, kq=24),                          # chưa đóng nhưng đã có kết quả
            bc2_row("62/2025", thuc=28, tt=True, kq=28)]                 # đã đóng
    r = svc.ds_bc2(FakeCur(bc2=rows))
    b = {x["ma_bc2"]: x for x in r["bc2"]}
    assert (b["81/2026"]["trang_thai"], b["76/2026"]["trang_thai"], b["62/2025"]["trang_thai"]) == (0, 2, 1)
    assert b["81/2026"]["dang_mo"] is True and b["76/2026"]["dang_mo"] is False and b["62/2025"]["dang_mo"] is False
    assert b["76/2026"]["dong"] is False and b["76/2026"]["hv_ket_qua"] == 24 and b["62/2025"]["dong"] is True
    assert (r["dang_mo"], r["da_dong"], r["co_ket_qua"]) == (1, 1, 1)
    mo = svc.ds_bc2(FakeCur(bc2=rows), "", "mo")
    assert [x["ma_bc2"] for x in mo["bc2"]] == ["81/2026"]
    khoa = svc.ds_bc2(FakeCur(bc2=rows), "", "dong")
    assert [x["ma_bc2"] for x in khoa["bc2"]] == ["76/2026", "62/2025"]


def test_ds_bc2_mot_hv_co_ket_qua_la_du_de_khoa_ca_bc2():
    r = svc.ds_bc2(FakeCur(bc2=[bc2_row("90/2026", thuc=100, kq=1)]))
    assert r["bc2"][0]["trang_thai"] == 2 and r["bc2"][0]["dang_mo"] is False
