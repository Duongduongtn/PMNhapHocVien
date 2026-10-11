"""TNB-01 (1/3) — task 101: tốt nghiệp ô tô — ĐỌC + XEM LẠI (không ghi).

`khoa_tot_nghiep`, `hv_tot_nghiep`, `xem_lai_tot_nghiep` + luật `phan_tich_dong_tn` + router.
Khóa các bất biến: chỉ ô tô, cửa sổ khóa 13 tháng + công tắc khóa cũ, tìm không dấu, điền sẵn sổ,
số giấy kế tiếp (dãy chung toàn cơ sở), trùng số giấy trong lô/DB (loại trừ chính HV; không chặn
oan số trùng có sẵn), HV ≥ 11 chỉ ghi số giấy lần đầu, khóa chưa bế giảng chỉ xem, KHÔNG ghi gì.
"""
from contextlib import contextmanager
from datetime import datetime

import pytest

from app import tn_bc2_rules as r
from app import tn_bc2_service as svc

HOM_NAY = "2026-10-11"
KHOA = "70004K26B0108"          # ô tô, bế giảng 18/09/2026
KHOA_CU = "70004K24B0001"       # ô tô, bế giảng 01/10/2024 (ngoài cửa sổ)
KHOA_MOTO = "70004K26A1015"
KHOA_TUONG_LAI = "70004K26B9999"
CHUNG = {"so_so_tn": "01/XNĐT/2026", "ngay_vao_so": "2026-09-30", "so_quyet_dinh": "100/TTTĐ",
         "ngay_ra_qd": "2026-09-30", "ngay_in": "2026-09-30"}


def hv_row(ma, ten, tt="03", ma_kh=KHOA, hang="B2", ma_bc2="", giay="", so="", qd="", ngay="2026-09-30", cmt=None):
    return {"MaDK": ma, "SoHoSo": "12", "HoVaTen": ten, "NgaySinh": "20000131", "SoCMT": cmt or "079" + ma[-4:],
            "HangGPLX": hang, "TT_XuLy": tt, "MaBC2": ma_bc2, "MaKhoaHoc": ma_kh, "SoGiayCNTN": giay,
            "SoSoTN": so, "NgayVaoSoTN": datetime.fromisoformat(ngay) if so else None, "SoQuyetDinhTN": qd,
            "NgayRaQDTN": datetime.fromisoformat(ngay) if qd else None,
            "NgayInGiayTN": datetime.fromisoformat(ngay) if giay else None, "SoCCN": None}


def du_lieu():
    return [
        hv_row("T-0001", "Nguyễn Đức Anh", "03"),
        hv_row("T-0002", "Trần Thị Bích", "03"),
        hv_row("T-0003", "Lê Văn Cường", "09", giay="N1|7300", so="01/XNĐT/2026", qd="100/TTTĐ"),
        hv_row("T-0004", "Phạm Dũng", "11", ma_bc2="76/2026", so="01/XNĐT/2026", qd="100/TTTĐ"),     # đã vào BC2, thiếu giấy
        hv_row("T-0005", "Võ Em", "16", ma_bc2="62/2025", giay="N1|7001", so="01/XNĐT/2026", qd="100/TTTĐ"),
        hv_row("T-0006", "Hồ Giang", "01"),
        hv_row("M-0001", "Mô Tô", "03", hang="A1"),                                                  # sai loại
    ]


class FakeCur:
    def __init__(self, st):
        self.st = st

    def execute(self, sql, params=()):
        st, s = self.st, " ".join(sql.split())
        st.log.append((s, tuple(params)))
        if s.startswith("SELECT k.MaKH, k.TenKH, k.HangGPLX, k.NgayKG, k.NgayBG, COUNT(h.MaDK)"):
            self._rows = st.khoa_tn
        elif s.startswith("SELECT MaKH, TenKH, HangGPLX, NgayBG FROM KhoaHoc WHERE MaKH"):
            self._rows = [k for k in st.khoa if k["MaKH"] == params[0]]
        elif "WHERE h.MaKhoaHoc = %s ORDER BY n.TenNLX" in s:
            self._rows = [h for h in st.hv if h["MaKhoaHoc"] == params[0]]
        elif "FROM NguoiLX_HoSo h LEFT JOIN NguoiLX n ON n.MaDK = h.MaDK WHERE h.MaDK IN" in s:
            self._rows = [h for h in st.hv if h["MaDK"] in params]
        elif s.startswith("SELECT TOP 1 SoGiayCNTN, NgayInGiayTN"):
            self._rows = [st.moi_nhat] if st.moi_nhat else []
        elif s.startswith("SELECT SoGiayCNTN, NgayInGiayTN FROM NguoiLX_HoSo WHERE SoGiayCNTN LIKE"):
            self._rows = st.giay_tien_to
        elif "REPLACE(ISNULL(SoGiayCNTN,''), '|', '') IN" in s:
            ks = set(params)
            self._rows = [g for g in st.giu if r.khoa_so_giay(g["SoGiayCNTN"]) in ks]
        else:
            raise AssertionError("câu lệnh lạ: " + s)

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class FakeDb:
    def __init__(self, hv=None):
        self.log = []
        self.hv = hv if hv is not None else du_lieu()
        self.khoa = [
            {"MaKH": KHOA, "TenKH": "B.01K40", "HangGPLX": "B2", "NgayBG": "2026-09-18"},
            {"MaKH": KHOA_CU, "TenKH": "B-K001", "HangGPLX": "B2", "NgayBG": "2024-10-01"},
            {"MaKH": KHOA_MOTO, "TenKH": "A1K126", "HangGPLX": "A1", "NgayBG": "2026-10-06"},
            {"MaKH": KHOA_TUONG_LAI, "TenKH": "B-K999", "HangGPLX": "B2", "NgayBG": "2026-12-31"},
        ]
        self.khoa_tn = [
            {"MaKH": KHOA, "TenKH": "B.01K40", "HangGPLX": "B2", "NgayKG": "2026-08-01", "NgayBG": "2026-09-18",
             "tong": 30, "c03": 5, "c09": 1, "c_bc2": 24},
            {"MaKH": KHOA_CU, "TenKH": "B-K001", "HangGPLX": "B2", "NgayKG": "2024-09-01", "NgayBG": "2024-10-01",
             "tong": 40, "c03": 0, "c09": 0, "c_bc2": 40},
            {"MaKH": KHOA_MOTO, "TenKH": "A1K126", "HangGPLX": "A1", "NgayKG": "2026-09-01", "NgayBG": "2026-10-06",
             "tong": 150, "c03": 0, "c09": 0, "c_bc2": 150},
            {"MaKH": KHOA_TUONG_LAI, "TenKH": "B-K999", "HangGPLX": "B2", "NgayKG": "2026-11-01", "NgayBG": "2026-12-31",
             "tong": 20, "c03": 20, "c09": 0, "c_bc2": 0},
        ]
        self.moi_nhat = {"SoGiayCNTN": "N1|7328", "NgayInGiayTN": datetime(2026, 9, 30)}
        self.giay_tien_to = [{"SoGiayCNTN": f"N1|{n}", "NgayInGiayTN": datetime(2026, 9, 30)} for n in (7001, 7300, 7328)]
        self.giu = []    # [{MaDK, SoGiayCNTN}] số giấy đang thuộc HV (cả ngoài khóa)

    def cursor(self):
        return FakeCur(self)


def xem(db, dong, chung=CHUNG, ma_kh=KHOA):
    return svc.xem_lai_tot_nghiep(db.cursor(), ma_kh, dong, chung, hom_nay=HOM_NAY)


def theo(kq):
    return {d["ma_dk"]: d for d in kq["dong"]}


# ── Luật thuần ──
def test_bo_dau_khoa_so_giay_tach_va_ke_tiep():
    assert r.bo_dau("Nguyễn Đức Anh") == "nguyen duc anh" and r.bo_dau("ĐỖ Đạt") == "do dat"
    assert r.khoa_so_giay("N1|7282") == r.khoa_so_giay(" n1 | 7282 ") == "n17282"
    assert r.tach_so_giay("N1|7282") == ("N1", 7282) and r.tach_so_giay("N17282") is None
    ds = [("N1|7001", "2026-09-01"), ("N|9310", "2020-05-01"), ("N1|7328", "2026-09-30"), ("khac", "2026-10-01")]
    assert r.so_giay_ke_tiep(ds) == "N1|7329"              # tiền tố của số in gần nhất, MAX+1 trong tiền tố đó
    assert r.so_giay_ke_tiep([]) == "" and r.so_giay_ke_tiep([("abc", "2026-01-01")]) == ""


def test_trang_thai_tot_nghiep_va_chuan_ngay():
    assert r.trang_thai_tot_nghiep("03") == "chua_tot_nghiep" and r.trang_thai_tot_nghiep("09") == "da_tot_nghiep"
    assert r.trang_thai_tot_nghiep("11") == "da_vao_bc2" and r.trang_thai_tot_nghiep("09", "76/2026") == "da_vao_bc2"
    assert r.trang_thai_tot_nghiep("01") == "khac"
    assert r.chuan_ngay("30/09/2026") == "2026-09-30" and r.chuan_ngay("2026-09-30") == "2026-09-30"
    assert r.chuan_ngay("") == "" and r.chuan_ngay("31/02/2026") is None and r.chuan_ngay("abc") is None


# ── Danh sách khóa ──
def test_khoa_tot_nghiep_chi_oto_cua_so_va_so_giay_ke_tiep():
    db = FakeDb()
    kq = svc.khoa_tot_nghiep(db.cursor(), "oto", False, HOM_NAY)
    ma = [k["ma_kh"] for k in kq["khoa"]]
    assert ma == [KHOA_TUONG_LAI, KHOA]                       # mô tô và khóa ngoài cửa sổ bị loại; mới nhất trước
    assert kq["moc_cua_so"] == "2025-09-11" and kq["so_giay_ke_tiep"] == "N1|7329"
    k = {x["ma_kh"]: x for x in kq["khoa"]}
    assert k[KHOA]["ghi_duoc"] is True and k[KHOA]["khoa_cu"] is False
    assert (k[KHOA]["tong"], k[KHOA]["chua_tot_nghiep"], k[KHOA]["da_tot_nghiep"], k[KHOA]["da_vao_bc2"]) == (30, 5, 1, 24)
    assert k[KHOA_TUONG_LAI]["ghi_duoc"] is False             # chưa bế giảng: chỉ xem
    cu = {x["ma_kh"]: x for x in svc.khoa_tot_nghiep(db.cursor(), "oto", True, HOM_NAY)["khoa"]}
    assert KHOA_CU in cu and cu[KHOA_CU]["khoa_cu"] is True and KHOA_MOTO not in cu


# ── HV của khóa ──
def test_hv_tot_nghiep_loc_loai_trang_thai_va_so_chung():
    db = FakeDb()
    kq = svc.hv_tot_nghiep(db.cursor(), KHOA, "", "", HOM_NAY)
    ma = [h["ma_dk"] for h in kq["hoc_vien"]]
    assert "M-0001" not in ma and len(ma) == 6                 # HV mô tô (hạng A) không hiện ở tốt nghiệp ô tô
    assert kq["ghi_duoc"] is True and kq["tong"] == 6 and kq["so_giay_ke_tiep"] == "N1|7329"
    assert kq["dem"] == {"chua_tot_nghiep": 2, "da_tot_nghiep": 1, "da_vao_bc2": 2}      # T-0006 (01) không thuộc nhóm nào
    h = {x["ma_dk"]: x for x in kq["hoc_vien"]}
    assert h["T-0003"]["trang_thai_tn"] == "da_tot_nghiep" and h["T-0003"]["so_giay"] == "N1|7300"
    assert h["T-0003"]["ngay_in"] == "2026-09-30" and h["T-0003"]["so_so_tn"] == "01/XNĐT/2026"
    assert h["T-0004"]["trang_thai_tn"] == "da_vao_bc2" and h["T-0004"]["sua_duoc"] is True
    assert h["T-0006"]["trang_thai_tn"] == "khac" and h["T-0006"]["sua_duoc"] is False and "chưa tới bước" in h["T-0006"]["ly_do_khoa"]
    assert kq["so_chung"]["so_so_tn"] == "01/XNĐT/2026" and kq["so_chung"]["so_quyet_dinh"] == "100/TTTĐ"
    assert kq["so_chung"]["so_hv"] == 3
    assert [x["ma_dk"] for x in svc.hv_tot_nghiep(db.cursor(), KHOA, "", "da_tot_nghiep", HOM_NAY)["hoc_vien"]] == ["T-0003"]


def test_hv_tot_nghiep_tim_khong_dau_cmt_ma_dk():
    db = FakeDb()
    tim = lambda q: [h["ma_dk"] for h in svc.hv_tot_nghiep(db.cursor(), KHOA, q, "", HOM_NAY)["hoc_vien"]]  # noqa: E731
    assert tim("duc anh") == ["T-0001"] and tim("NGUYỄN ĐỨC") == ["T-0001"] and tim("dung") == ["T-0004"]
    assert tim("0790002") == ["T-0002"]                        # theo CMT
    assert tim("t-0005") == ["T-0005"]                         # theo mã đăng ký, không phân biệt hoa/thường
    assert tim("khong co") == []


def test_hv_tot_nghiep_khoa_chua_be_giang_chi_xem_va_khoa_cu_huy_hieu_va_mo_to_400():
    db = FakeDb(hv=[hv_row("F-0001", "Học Viên", "03", ma_kh=KHOA_TUONG_LAI)])
    kq = svc.hv_tot_nghiep(db.cursor(), KHOA_TUONG_LAI, "", "", HOM_NAY)
    assert kq["ghi_duoc"] is False and kq["hoc_vien"][0]["sua_duoc"] is False and "chưa bế giảng" in kq["hoc_vien"][0]["ly_do_khoa"]
    db2 = FakeDb(hv=[hv_row("C-0001", "Cũ", "03", ma_kh=KHOA_CU)])
    k2 = svc.hv_tot_nghiep(db2.cursor(), KHOA_CU, "", "", HOM_NAY)
    assert k2["khoa_cu"] is True and k2["hoc_vien"][0]["khoa_cu"] is True and k2["hoc_vien"][0]["sua_duoc"] is True
    with pytest.raises(svc.LoiNghiepVu) as e:
        svc.hv_tot_nghiep(db.cursor(), KHOA_MOTO, "", "", HOM_NAY)
    assert e.value.ma == "chi_o_to" and e.value.http == 400
    with pytest.raises(svc.LoiNghiepVu) as e:
        svc.hv_tot_nghiep(db.cursor(), "khong-co", "", "", HOM_NAY)
    assert e.value.http == 404


# ── Xem lại ──
def test_xem_lai_ket_qua_du_kien_tung_loai_hv():
    db = FakeDb()
    kq = xem(db, [{"ma_dk": "T-0001", "so_giay": "N1|7329"},          # 03 + số giấy → 09
                  {"ma_dk": "T-0002", "so_giay": ""},                  # 03, chưa có giấy → lưu sổ trước
                  {"ma_dk": "T-0003", "so_giay": "N1|7330"},           # 09 đổi số giấy → giữ 09, sửa thông tin
                  {"ma_dk": "T-0004", "so_giay": "N1|7331"}])          # 11 thiếu giấy → ghi giấy, không đổi trạng thái
    d = theo(kq)
    assert d["T-0001"]["ket_qua"] == r.KQ_LEN_09 and d["T-0001"]["ghi_duoc"] is True
    assert d["T-0002"]["ket_qua"] == r.KQ_LUU_SO_TRUOC
    assert d["T-0003"]["ket_qua"] == r.KQ_GIU_09
    assert d["T-0004"]["ket_qua"] == r.KQ_DA_VAO_BC2
    assert [w["ma"] for w in d["T-0004"]["canh_bao"]] == ["bao_cao_da_lap_khong_doi_theo"]
    assert kq["co_chan"] is False and kq["ghi_duoc_khoa"] is True and kq["tong"] == 4
    assert kq["khoang_so"] == {"tien_to": "N1", "tu": 7329, "den": 7331, "so_luong": 3}
    assert d["T-0001"]["hieu_luc"]["so_so_tn"] == "01/XNĐT/2026" and d["T-0001"]["hieu_luc"]["ngay_in"] == "2026-09-30"
    assert kq["dem"][r.KQ_LEN_09] == 1
    # chỉ SELECT — không ghi gì
    for s, _p in db.log:
        assert s.startswith("SELECT") and not any(k in s.upper() for k in ("INSERT", "UPDATE ", "DELETE", "EXEC"))


def test_xem_lai_chan_trang_thai_sua_da_vao_bc2_khong_hop_le_va_09_trong():
    db = FakeDb()
    kq = xem(db, [{"ma_dk": "T-0005", "so_giay": "N1|7500"},          # 16, đã có giấy khác → chặn sửa
                  {"ma_dk": "T-0006", "so_giay": "N1|7501"},          # 01 → chưa tới bước tốt nghiệp
                  {"ma_dk": "T-0003", "so_giay": ""},                 # 09 để trống → dùng "Hủy tốt nghiệp"
                  {"ma_dk": "M-0001", "so_giay": "N1|7502"}])         # mô tô → sai loại
    d = theo(kq)
    assert {c["ma"] for c in d["T-0005"]["chan"]} == {"da_vao_bc2_khong_sua"}
    assert {c["ma"] for c in d["T-0006"]["chan"]} == {"trang_thai_khong_hop_le"}
    assert d["T-0003"]["ket_qua"] == r.KQ_BO_QUA and d["T-0003"]["thong_tin"][0]["ma"] == "dung_huy_tot_nghiep"
    assert {c["ma"] for c in d["M-0001"]["chan"]} == {"sai_loai"}
    assert kq["co_chan"] is True


def test_xem_lai_trung_trong_lo_va_trung_db_loai_tru_chinh_hv_va_khong_chan_oan_so_trung_cu():
    db = FakeDb()
    db.giu = [{"MaDK": "X-0001", "SoGiayCNTN": "N1|7329"},        # đã thuộc HV khác trong DB
              {"MaDK": "T-0003", "SoGiayCNTN": "N1|7300"},        # chính T-0003
              {"MaDK": "X-0002", "SoGiayCNTN": "N1|7300"}]        # số trùng CÓ SẴN từ trước (legacy)
    kq = xem(db, [{"ma_dk": "T-0001", "so_giay": "N1|7329"},      # đổi sang số của X-0001 → chặn
                  {"ma_dk": "T-0002", "so_giay": "n1|7340"},
                  {"ma_dk": "T-0004", "so_giay": "N1 | 7340"},     # trùng T-0002 trong lô (khác hoa/thường, khoảng trắng)
                  {"ma_dk": "T-0003", "so_giay": "N1|7300"}])     # giữ nguyên số của chính mình dù đang trùng cũ
    d = theo(kq)
    assert {c["ma"] for c in d["T-0001"]["chan"]} == {"trung_db"}
    assert {c["ma"] for c in d["T-0002"]["chan"]} == {"trung_trong_lo"}
    assert {c["ma"] for c in d["T-0004"]["chan"]} == {"trung_trong_lo"}
    assert d["T-0003"]["chan"] == [] and d["T-0003"]["thong_tin"][0]["ma"] == "trung_co_san"
    assert d["T-0003"]["ket_qua"] in (r.KQ_KHONG_DOI, r.KQ_GIU_09)


def test_xem_lai_khoa_chua_be_giang_do_dai_ngay_va_thieu_so():
    db = FakeDb(hv=[hv_row("F-0001", "Tương Lai", "03", ma_kh=KHOA_TUONG_LAI)])
    kq = xem(db, [{"ma_dk": "F-0001", "so_giay": "N1|7329"}], ma_kh=KHOA_TUONG_LAI)
    assert kq["ghi_duoc_khoa"] is False
    assert "khoa_chua_be_giang" in {c["ma"] for c in theo(kq)["F-0001"]["chan"]}
    db = FakeDb()
    kq = xem(db, [{"ma_dk": "T-0001", "so_giay": "x" * 21},
                  {"ma_dk": "T-0002", "so_giay": "N1|7329"}], chung=dict(CHUNG, so_so_tn="s" * 51, ngay_in="31/02/2026"))
    d = theo(kq)
    ma1 = {c["ma"] for c in d["T-0001"]["chan"]}
    assert "vuot_do_dai" in ma1 and "ngay_khong_hop_le" in ma1
    kq = xem(db, [{"ma_dk": "T-0001", "so_giay": "N1|7329"}], chung={})        # không sổ, không QĐ → không cấp giấy được
    assert {c["ma"] for c in theo(kq)["T-0001"]["chan"]} == {"thieu_so_so_hoac_quyet_dinh"}


def test_xem_lai_hv_khac_khoa_khong_ton_tai_rong_va_qua_nhieu():
    db = FakeDb(hv=du_lieu() + [hv_row("K-0001", "Khóa Khác", "03", ma_kh="70004K26B0107")])
    kq = xem(db, [{"ma_dk": "K-0001", "so_giay": "N1|7329"}, {"ma_dk": "KHONG-CO", "so_giay": "N1|7330"}])
    d = theo(kq)
    assert d["K-0001"]["chan"][0]["ma"] == "khac_khoa" and d["KHONG-CO"]["chan"][0]["ma"] == "hv_khong_ton_tai"
    with pytest.raises(svc.LoiNghiepVu) as e:
        xem(db, [])
    assert e.value.ma == "khong_co_hoc_vien"
    with pytest.raises(svc.LoiNghiepVu) as e:
        xem(db, [{"ma_dk": f"X{i}", "so_giay": ""} for i in range(5001)])
    assert e.value.ma == "qua_nhieu_dong"
    with pytest.raises(svc.LoiNghiepVu) as e:
        xem(db, [{"ma_dk": "T-0001", "so_giay": ""}], ma_kh=KHOA_MOTO)
    assert e.value.ma == "chi_o_to"


def test_xem_lai_hv_da_vao_bc2_giu_nguyen_khong_doi_va_khoa_cu_canh_bao():
    db = FakeDb(hv=[hv_row("C-0001", "Cũ", "03", ma_kh=KHOA_CU), hv_row("C-0002", "Cũ Hai", "11", ma_kh=KHOA_CU, ma_bc2="1/2024",
                                                                         giay="N1|1000", so="01/2024", qd="1/TTTĐ")])
    kq = svc.xem_lai_tot_nghiep(db.cursor(), KHOA_CU,
                                [{"ma_dk": "C-0001", "so_giay": "N1|1001"}, {"ma_dk": "C-0002", "so_giay": "N1|1000"}],
                                {"so_so_tn": "01/2024", "so_quyet_dinh": "1/TTTĐ"}, hom_nay=HOM_NAY)
    d = theo(kq)
    assert "khoa_cu" in {w["ma"] for w in d["C-0001"]["canh_bao"]} and d["C-0001"]["ket_qua"] == r.KQ_LEN_09
    assert d["C-0002"]["ket_qua"] == r.KQ_KHONG_DOI
    assert any(w["ma"] == "khoa_cu" and w["so_dong"] == 2 for w in kq["canh_bao"])


# ── Router ──
@pytest.fixture
def client(monkeypatch, auth_headers):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.routers import tn_bc2 as router

    db = FakeDb()

    @contextmanager
    def _cur(as_dict=True):
        yield db.cursor()

    monkeypatch.setattr(router, "sqlserver_cursor", _cur)
    monkeypatch.setattr(svc, "hom_nay_iso", lambda: HOM_NAY)
    c = TestClient(app)

    class _C:
        def get(self, u, **kw):
            return c.get(u, headers=auth_headers, **kw)

        def post(self, u, **kw):
            return c.post(u, headers=auth_headers, **kw)
    return _C(), db


def test_router_khoa_hv_va_xem_lai(client):
    c, db = client
    r1 = c.get("/local/tnbc2/khoa", params={"loai": "oto"})
    assert r1.status_code == 200 and [k["ma_kh"] for k in r1.json()["khoa"]] == [KHOA_TUONG_LAI, KHOA]
    assert c.get("/local/tnbc2/khoa", params={"loai": "moto"}).json()["detail"]["ma"] == "chi_o_to"
    assert c.get("/local/tnbc2/khoa", params={"loai": "oto", "cu": True}).status_code == 200
    r2 = c.get("/local/tnbc2/tot-nghiep/hv", params={"ma_kh": KHOA, "q": "duc anh"})
    assert r2.status_code == 200 and [h["ma_dk"] for h in r2.json()["hoc_vien"]] == ["T-0001"]
    assert c.get("/local/tnbc2/tot-nghiep/hv", params={"ma_kh": KHOA, "trang_thai": "linh-tinh"}).status_code == 422
    assert c.get("/local/tnbc2/tot-nghiep/hv", params={"ma_kh": "khong-co"}).status_code == 404
    r3 = c.post("/local/tnbc2/tot-nghiep/xem-lai",
                json={"ma_kh": KHOA, "dong": [{"ma_dk": "T-0001", "so_giay": "N1|7329"}], "chung": CHUNG})
    assert r3.status_code == 200 and r3.json()["dong"][0]["ket_qua"] == "se_len_09" and r3.json()["co_chan"] is False
    # xem lại không cần cổng xác nhận và không ghi gì
    assert all(s.startswith("SELECT") for s, _ in db.log)
    r4 = c.post("/local/tnbc2/tot-nghiep/xem-lai", json={"ma_kh": KHOA, "dong": [], "chung": {}})
    assert r4.status_code == 400 and r4.json()["detail"]["ma"] == "khong_co_hoc_vien"


def test_dem_khoa_khop_voi_dem_hv_chi_tinh_hv_chua_vao_bc2():
    """`/khoa` và `/tot-nghiep/hv` phải cùng một cách đếm (03/09 chưa có MaBC2)."""
    assert "TT_XuLy = '03' AND ISNULL(h.MaBC2,'') = ''" in svc._Q_KHOA_TN
    assert "TT_XuLy = '09' AND ISNULL(h.MaBC2,'') = ''" in svc._Q_KHOA_TN


def test_router_vuot_do_dai_la_chan_trong_ket_qua_khong_phai_422(client):
    c, _db = client
    r_ = c.post("/local/tnbc2/tot-nghiep/xem-lai",
                json={"ma_kh": KHOA, "dong": [{"ma_dk": "T-0001", "so_giay": "x" * 100}],
                      "chung": dict(CHUNG, so_so_tn="s" * 120)})
    assert r_.status_code == 200
    ma = {c_["ma"] for c_ in r_.json()["dong"][0]["chan"]}
    assert "vuot_do_dai" in ma and r_.json()["co_chan"] is True
