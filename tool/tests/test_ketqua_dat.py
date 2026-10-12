"""KQD-08 — nạp giờ/km đường từ PDF DAT: luật thuần + 2 endpoint bằng cursor giả."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import ketqua_dat as d
from app.main import app
from app.routers import ketqua as k

client = TestClient(app)
_THAMKHAO = Path(__file__).resolve().parents[2] / "thamkhao"


# ---- doc_gio / doc_km ---------------------------------------------------------
@pytest.mark.parametrize("raw,ket_qua", [
    ("16:19", 16.32), ("0:59", 0.98), ("28:26", 28.43), ("24:20", 24.33), ("20:30", 20.5),
    ("20:00:36", 20.01), ("20,5", 20.5), ("20.5", 20.5), ("12", 12.0), ("", None), (None, None),
])
def test_doc_gio(raw, ket_qua):
    assert d.doc_gio(raw) == ket_qua


@pytest.mark.parametrize("raw", ["20:75", "20:5x", "abc", "1:2:3:4", "20:30:75"])
def test_doc_gio_sai_dang(raw):
    with pytest.raises(d.LoiDat):
        d.doc_gio(raw)


@pytest.mark.parametrize("raw,ket_qua", [
    ("725,63", 725.63), ("1.008,19", 1008.19), ("0,00", 0.0), ("19,87", 19.87), ("810", 810.0), ("", None),
])
def test_doc_km(raw, ket_qua):
    assert d.doc_km(raw) == ket_qua


@pytest.mark.parametrize("raw", ["12.34", "1,008.19", "abc", "1.00,5"])
def test_doc_km_sai_dang(raw):
    with pytest.raises(d.LoiDat):
        d.doc_km(raw)


# ---- đọc PDF mẫu thật (bỏ qua nếu máy không có thư mục thamkhao/) --------------
@pytest.mark.parametrize("ten,ma_kh,hang,so_dong", [
    ("DAT B.01-K39.pdf", "75032K260002", "B.01", 60),
    ("DAT B.01-K40.pdf", "75032K260003", "B.01", 30),
    ("DAT C1-K10.pdf", "70004K26C1007", "C1", 64),
    ("DAT C1-K11.pdf", "75032K26C1005", "C1", 32),
])
def test_doc_pdf_mau(ten, ma_kh, hang, so_dong):
    p = _THAMKHAO / ten
    if not p.exists():
        pytest.skip("không có file mẫu")
    r = d.doc_pdf_dat(p.read_bytes())
    assert (r["ma_kh"], r["hang"], len(r["dong"])) == (ma_kh, hang, so_dong)
    assert [x["stt"] for x in r["dong"]] == list(range(1, so_dong + 1))   # nhiều trang vẫn đủ, đúng thứ tự
    assert all(x["loi"] is None for x in r["dong"])


def test_doc_pdf_dong_chua_chay_dat():
    p = _THAMKHAO / "DAT C1-K10.pdf"
    if not p.exists():
        pytest.skip("không có file mẫu")
    r = d.doc_pdf_dat(p.read_bytes())
    chua = [x for x in r["dong"] if x["gio"] is None]
    assert len(chua) == 1 and chua[0]["km"] == 0.0 and chua[0]["ghi_chu"] == "KHÔNG ĐẠT"
    cao = [x for x in r["dong"] if x["gio"] and x["gio"] >= 24]
    assert cao                                   # giờ ≥ 24 không bị cắt


def test_doc_pdf_khong_phai_pdf():
    with pytest.raises(d.LoiDat):
        d.doc_pdf_dat(b"%PDF-1.4 hong")


# ---- doi_chieu ----------------------------------------------------------------
def _hv(ma, tt="09", gio=None, km=None, hang="B"):
    return {"MaDK": ma, "HoVaTen": f"HV {ma}", "SoCMT": "0" + ma, "TT_XuLy": tt, "MaHangMoi": hang,
            "HangGPLX": hang, "TGThucHanhDuong": gio, "TongQDThucHanh": km}


def _dong(ma, gio, km, stt=1, loi=None):
    return {"stt": stt, "ma_hv": ma, "ho_ten": f"File {ma}", "ngay_sinh": "01/01/2000",
            "gio": gio, "km": km, "ghi_chu": "ĐẠT", "loi": loi}


def test_doi_chieu_khop_co_thay_doi_tick_san():
    r = d.doi_chieu([_dong("1", 16.32, 725.63)], [_hv("1", gio=10.0, km=500.0)])
    x = r["dong"][0]
    assert (x["tinh_trang"], x["co_thay_doi"], x["tick_san"], x["chon_duoc"]) == (d.KHOP, True, True, True)
    assert (x["gio_cu"], x["gio_moi"], x["km_cu"], x["km_moi"]) == (10.0, 16.32, 500.0, 725.63)


def test_doi_chieu_float32_khong_bi_coi_la_thay_doi():
    # CDB lưu real: 18.4 đọc ra 18.399999618530273 → so sau làm tròn 2 chữ số, không báo thay đổi
    r = d.doi_chieu([_dong("1", 18.4, 719.4)], [_hv("1", gio=18.399999618530273, km=719.4000244140625)])
    assert r["dong"][0]["co_thay_doi"] is False and r["dong"][0]["tick_san"] is False
    assert r["dong"][0]["gio_cu"] == 18.4


def test_doi_chieu_chua_chay_dat_bo_tick():
    r = d.doi_chieu([_dong("1", None, 0.0)], [_hv("1", gio=12.0, km=700.0)])
    x = r["dong"][0]
    assert (x["tinh_trang"], x["tick_san"], x["chon_duoc"]) == (d.CHUA_CHAY_DAT, False, True)


def test_doi_chieu_khong_co_trong_khoa_va_vang_trong_file():
    r = d.doi_chieu([_dong("9", 20.0, 800.0)], [_hv("1")])
    assert r["dong"][0]["tinh_trang"] == d.KHONG_CO_TRONG_KHOA and not r["dong"][0]["chon_duoc"]
    assert [v["ma_dk"] for v in r["vang_trong_file"]] == ["1"]


@pytest.mark.parametrize("tt", ["12", "13"])
def test_doi_chieu_da_ket_xuat_khong_tick_duoc(tt):
    x = d.doi_chieu([_dong("1", 20.0, 800.0)], [_hv("1", tt=tt)])["dong"][0]
    assert x["tinh_trang"] == d.DA_KET_XUAT and not x["chon_duoc"] and not x["tick_san"]


def test_doi_chieu_dong_loi_va_trung():
    r = d.doi_chieu(
        [_dong("1", None, None, stt=1, loi="Giờ '20:75' sai dạng"), _dong("2", 20.0, 800.0, stt=2),
         _dong("2", 21.0, 810.0, stt=3)],
        [_hv("1"), _hv("2")],
    )
    assert r["dong"][0]["tinh_trang"] == d.LOI_DONG
    assert r["dong"][1]["tinh_trang"] == d.KHOP
    assert r["dong"][2]["tinh_trang"] == d.TRUNG_DONG and not r["dong"][2]["chon_duoc"]


def test_doi_chieu_canh_bao_duoi_nguong():
    # B số sàn gợi ý giờ ≥ 20, km ≥ 810
    x = d.doi_chieu([_dong("1", 15.0, 700.0)], [_hv("1")])["dong"][0]
    assert [c["loai"] for c in x["canh_bao"]] == ["gio_duong", "km_duong"]
    assert x["tick_san"] is True               # cảnh báo vàng, vẫn tick sẵn


# ---- endpoint (cursor giả) ------------------------------------------------------
class _Cur:
    def __init__(self, rows, log, rowcount_theo_ma=None):
        self.rows, self.log, self.rc, self.rowcount = rows, log, rowcount_theo_ma or {}, 0

    def execute(self, sql, params=()):
        self.log.append((sql, params))
        if sql.lstrip().upper().startswith("UPDATE"):
            self.rowcount = self.rc.get(params[2], 1)

    def fetchall(self):
        return self.rows


def _gia_lap(monkeypatch, rows, log, rowcount_theo_ma=None, loi_o=None):
    ket = {"commit": 0, "rollback": 0}

    @contextmanager
    def conn(_db, **_kw):
        class C:
            def cursor(self, as_dict=False):
                cur = _Cur(rows, log, rowcount_theo_ma)
                if loi_o:
                    goc = cur.execute

                    def ex(sql, params=()):
                        if sql.lstrip().upper().startswith("UPDATE") and params[2] == loi_o:
                            raise RuntimeError("DB hỏng")
                        goc(sql, params)
                    cur.execute = ex
                return cur

            def commit(self):
                ket["commit"] += 1

            def rollback(self):
                ket["rollback"] += 1
        yield C()

    monkeypatch.setattr(k, "_db_dich", lambda tk: "DB")
    monkeypatch.setattr(k, "sqlserver_conn_dich", conn)
    return ket


def _pdf_gia(ma_kh="KX"):
    return {"ma_kh": ma_kh, "hang": "B", "dong": [_dong("1", 16.32, 725.63)]}


def _post_xem(monkeypatch, auth_headers, pdf, ma_kh="KX", ten="dat.pdf", noi_dung=b"%PDF-1.4 x"):
    monkeypatch.setattr(k.ketqua_dat, "doc_pdf_dat", lambda b: pdf)
    return client.post("/local/ketqua/dat/xem-truoc", headers=auth_headers, data={"ma_kh": ma_kh},
                       files={"file": (ten, noi_dung, "application/pdf")})


def test_xem_truoc_khop_va_chi_doc(monkeypatch, auth_headers):
    log: list = []
    _gia_lap(monkeypatch, [_hv("1", gio=10.0, km=500.0), _hv("2")], log)
    r = _post_xem(monkeypatch, auth_headers, _pdf_gia())
    assert r.status_code == 200
    j = r.json()
    assert j["tong_file"] == 1 and j["dong"][0]["tinh_trang"] == "khop"
    assert [v["ma_dk"] for v in j["vang_trong_file"]] == ["2"]
    assert all(s.lstrip().upper().startswith("SELECT") for s, _ in log)   # không ghi gì


def test_xem_truoc_sai_khoa_bi_chan(monkeypatch, auth_headers):
    _gia_lap(monkeypatch, [], [])
    r = _post_xem(monkeypatch, auth_headers, _pdf_gia("KHAC"))
    assert r.status_code == 400 and "KHAC" in r.json()["detail"]


def test_xem_truoc_khong_phai_pdf(monkeypatch, auth_headers):
    _gia_lap(monkeypatch, [], [])
    assert _post_xem(monkeypatch, auth_headers, _pdf_gia(), ten="a.xlsx").status_code == 400
    assert _post_xem(monkeypatch, auth_headers, _pdf_gia(), noi_dung=b"PK\x03\x04").status_code == 400


def test_luu_chi_ghi_2_cot_va_bo_qua_dong_khong_hop_le(monkeypatch, auth_headers):
    log: list = []
    ket = _gia_lap(monkeypatch, [], log, rowcount_theo_ma={"2": 0})
    r = client.post("/local/ketqua/dat/luu", headers=auth_headers, json={
        "ma_kh": "KX", "dong": [{"ma_dk": "1", "gio_duong": 16.32, "km_duong": 725.63},
                                {"ma_dk": "2", "gio_duong": 20, "km_duong": 800}]})
    assert r.status_code == 200
    j = r.json()
    assert j["da_luu"] == 1 and [b["ma_dk"] for b in j["bo_qua"]] == ["2"]
    assert ket == {"commit": 1, "rollback": 0}
    sql = log[0][0]
    assert "TGThucHanhDuong" in sql and "TongQDThucHanh" in sql
    assert "DiemKQ" not in sql and "KetLuan" not in sql and "TT_XuLy=" not in sql.replace(" ", "")
    assert "NOT IN ('12','13')" in sql and log[0][1] == (16.32, 725.63, "1", "KX")
    assert not any("EXEC" in s.upper() for s, _ in log)                  # không gọi SP


def test_luu_loi_giua_chung_rollback_ca_lo(monkeypatch, auth_headers):
    ket = _gia_lap(monkeypatch, [], [], loi_o="2")
    r = client.post("/local/ketqua/dat/luu", headers=auth_headers, json={
        "ma_kh": "KX", "dong": [{"ma_dk": "1", "gio_duong": 16, "km_duong": 700},
                                {"ma_dk": "2", "gio_duong": 17, "km_duong": 710}]})
    assert r.status_code == 502 and "chưa có dòng nào" in r.json()["detail"]
    assert ket == {"commit": 0, "rollback": 1}


def test_luu_gio_km_ngoai_khung_bi_tu_choi(monkeypatch, auth_headers):
    _gia_lap(monkeypatch, [], [])
    for bad in ({"gio_duong": -1, "km_duong": 1}, {"gio_duong": 1, "km_duong": 1e9}):
        r = client.post("/local/ketqua/dat/luu", headers=auth_headers,
                        json={"ma_kh": "KX", "dong": [{"ma_dk": "1", **bad}]})
        assert r.status_code == 422


def test_hoc_vien_tra_gio_km_da_lam_tron(monkeypatch, auth_headers):
    row = {"MaDK": "1", "HoVaTen": "A", "NgaySinh": "20000101", "SoCMT": "0", "SoHoSo": "1",
           "HangGPLX": "B", "MaHangMoi": "B", "TT_XuLy": "09", "KetLuanCSDT": 1,
           "DiemKQLyThuyet": 8, "DiemKQMoPhong": 7, "DiemKQHinh": 9, "DiemKQTienLui": 6, "DiemKQThucHanh": 8,
           "TGThucHanhHinh": 34, "QDThucHanhHinh": 240,
           "TGThucHanhDuong": 18.399999618530273, "TongQDThucHanh": None}
    _gia_lap(monkeypatch, [row], [])
    j = client.get("/local/ketqua/hoc-vien?ma_kh=KX", headers=auth_headers).json()
    assert j[0]["gio_duong"] == 18.4 and j[0]["km_duong"] is None


# ---- lý do "không có trong khóa" ----------------------------------------------
def _item(ma="9", ten="NGUYỄN VĂN A", ns="01/02/2000"):
    return {"ma_dk": ma, "ho_ten": ten, "ngay_sinh": ns, "ghi_chu": None}


def test_ngay_sinh_luu():
    assert d.ngay_sinh_luu("01/02/2000") == "20000201"
    assert d.ngay_sinh_luu("1/2/2000") == "20000201"
    assert d.ngay_sinh_luu("2000") == "" and d.ngay_sinh_luu("") == ""


def test_ly_do_ma_thuoc_khoa_khac():
    it = _item()
    d.gan_ly_do_khong_co([it], {"9": [{"MaDK": "9", "MaKhoaHoc": "K2", "TrangThai": 1, "TenKH": "Khóa 2"}]}, {}, "K1")
    assert it["khoa_khac"] == "Khóa 2 (K2)" and "đã đổi khóa" in it["ghi_chu"]


def test_ly_do_cung_khoa_nhung_khong_hoat_dong():
    it = _item()
    d.gan_ly_do_khong_co([it], {"9": [{"MaDK": "9", "MaKhoaHoc": "K1", "TrangThai": 0, "TenKH": "K"}]}, {}, "K1")
    assert it["khoa_khac"] is None and "không còn ở trạng thái hoạt động" in it["ghi_chu"]


def test_ly_do_lech_ma_theo_ten_ngay_sinh():
    it = _item()
    theo_ten = {("NGUYỄN VĂN A", "20000201"): [{"MaDK": "77", "MaKhoaHoc": "K1", "TrangThai": 1, "TenKH": "K"}]}
    d.gan_ly_do_khong_co([it], {}, theo_ten, "K1")
    assert "LỆCH MÃ" in it["ghi_chu"] and "77" in it["ghi_chu"]
    it2 = _item()
    theo_ten = {("NGUYỄN VĂN A", "20000201"): [{"MaDK": "77", "MaKhoaHoc": "K2", "TrangThai": 1, "TenKH": "Khóa 2"}]}
    d.gan_ly_do_khong_co([it2], {}, theo_ten, "K1")
    assert it2["khoa_khac"] == "Khóa 2 (K2)" and "lệch mã" in it2["ghi_chu"]


def test_ly_do_khong_thay_o_dau_va_loi_ket_noi():
    it = _item()
    d.gan_ly_do_khong_co([it], {}, {}, "K1")
    assert "chưa nạp/đồng bộ" in it["ghi_chu"]
    it2 = _item()
    d.gan_ly_do_khong_co([it2], None, None, "K1")
    assert "lỗi kết nối" in it2["ghi_chu"]


def test_xem_truoc_gan_ly_do_cho_dong_khong_co(monkeypatch, auth_headers):
    _gia_lap(monkeypatch, [_hv("1", gio=10.0, km=500.0)], [])
    monkeypatch.setattr(k, "_tra_cuu_khong_co", lambda items, tk: (
        {"9": [{"MaDK": "9", "MaKhoaHoc": "K2", "TrangThai": 1, "TenKH": "Khóa 2"}]}, {}, set()))
    pdf = {"ma_kh": "KX", "hang": "B", "dong": [_dong("1", 16.32, 725.63), _dong("9", 20.0, 800.0, stt=2)]}
    j = _post_xem(monkeypatch, auth_headers, pdf).json()
    kc = [x for x in j["dong"] if x["tinh_trang"] == "khong_co_trong_khoa"][0]
    assert kc["khoa_khac"] == "Khóa 2 (K2)" and "đổi khóa" in kc["ghi_chu"]


def test_tra_cuu_loi_ket_noi_khong_lam_hong_xem_truoc(monkeypatch):
    def hong(_db):
        raise RuntimeError("mất kết nối")
    monkeypatch.setattr(k, "_db_dich", lambda tk: "DB")
    monkeypatch.setattr(k, "sqlserver_conn_dich", hong)
    assert k._tra_cuu_khong_co([_item()], None) == (None, None, set())


# =============================================================================
# KQD-08 — bổ sung sau /kiemthu (12/10/2026): nhánh còn sót + biên + ranh giới
# =============================================================================
import json  # noqa: E402
import sys  # noqa: E402
import types  # noqa: E402

_VEC = json.loads((Path(__file__).parent / "fixtures" / "gio_km_vectors.json").read_text(encoding="utf-8"))


# ---- vector chung với TypeScript ------------------------------------------------
@pytest.mark.parametrize("raw,mong", _VEC["gio"])
def test_vector_chung_gio(raw, mong):
    if mong == "sai":
        with pytest.raises(d.LoiDat):
            d.doc_gio(raw)
    else:
        assert d.doc_gio(raw) == mong


@pytest.mark.parametrize("raw,mong", _VEC["km"])
def test_vector_chung_km(raw, mong):
    if mong == "sai":
        with pytest.raises(d.LoiDat):
            d.doc_km(raw)
    else:
        assert d.doc_km(raw) == mong


# ---- S1–S5: doi_chieu ------------------------------------------------------------
@pytest.mark.parametrize("gio,km", [(None, 700.0), (20.0, None)])
def test_s1_thieu_mot_trong_hai_la_loi_dong(gio, km):
    x = d.doi_chieu([_dong("1", gio, km)], [_hv("1")])["dong"][0]
    assert x["tinh_trang"] == d.LOI_DONG and x["chon_duoc"] is False and x["tick_san"] is False
    assert x["ghi_chu"] == "Thiếu giờ hoặc quãng đường."


def test_s2_gio_0_km_0_la_chua_chay_dat_con_gio_duong_km_0_van_khop():
    chua = d.doi_chieu([_dong("1", 0.0, 0.0)], [_hv("1")])["dong"][0]
    assert chua["tinh_trang"] == d.CHUA_CHAY_DAT
    khop = d.doi_chieu([_dong("1", 5.0, 0.0)], [_hv("1")])["dong"][0]
    assert khop["tinh_trang"] == d.KHOP and khop["chon_duoc"] is True and khop["km_moi"] == 0.0


@pytest.mark.parametrize("tt", ["03", "14", "90", None, ""])
def test_s3_trang_thai_khac_12_13_van_chon_duoc(tt):
    assert d.doi_chieu([_dong("1", 20.0, 800.0)], [_hv("1", tt=tt)])["dong"][0]["chon_duoc"] is True


def test_s3_12_co_khoang_trang_van_khoa_va_thang_dong_loi():
    assert d.doi_chieu([_dong("1", 20.0, 800.0)], [_hv("1", tt=" 12 ")])["dong"][0]["tinh_trang"] == d.DA_KET_XUAT
    loi = d.doi_chieu([_dong("1", None, None, loi="Giờ 20:75 sai dạng")], [_hv("1", tt="12")])["dong"][0]
    assert loi["tinh_trang"] == d.DA_KET_XUAT                     # 12/13 thắng dòng lỗi
    chua = d.doi_chieu([_dong("1", None, 0.0)], [_hv("1", tt="13")])["dong"][0]
    assert chua["tinh_trang"] == d.DA_KET_XUAT and chua["chon_duoc"] is False


def test_s4_cu_co_gio_ma_km_null_la_co_thay_doi_va_bang_nhau_thi_khong_tick():
    x = d.doi_chieu([_dong("1", 10.0, 700.0)], [_hv("1", gio=10.0, km=None)])["dong"][0]
    assert x["co_thay_doi"] is True and x["tick_san"] is True
    y = d.doi_chieu([_dong("1", 10.0, 700.0)], [_hv("1", gio=10.0, km=700.0)])["dong"][0]
    assert y["co_thay_doi"] is False and y["tick_san"] is False


def test_s5_hai_dong_cung_ma_khong_co_trong_khoa_van_la_khong_co_khong_phai_trung():
    r = d.doi_chieu([_dong("9", 20.0, 800.0, stt=1), _dong("9", 21.0, 810.0, stt=2)], [_hv("1")])
    assert [x["tinh_trang"] for x in r["dong"]] == [d.KHONG_CO_TRONG_KHOA, d.KHONG_CO_TRONG_KHOA]


def test_s5_dong_dau_chua_chay_dat_thi_dong_sau_hop_le_van_la_trung():
    r = d.doi_chieu([_dong("2", None, 0.0, stt=1), _dong("2", 21.0, 810.0, stt=2)], [_hv("2")])
    assert [x["tinh_trang"] for x in r["dong"]] == [d.CHUA_CHAY_DAT, d.TRUNG_DONG]


# ---- S7: doc_pdf_dat với pdfplumber giả (không cần file PDF thật, không chứa PII) ---------
class _Trang:
    def __init__(self, text="", bang=None):
        self._text, self._bang = text, bang or []

    def extract_text(self):
        return self._text

    def extract_tables(self):
        return self._bang


class _Pdf:
    def __init__(self, trang):
        self.pages = trang

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _gia_pdfplumber(monkeypatch, trang=None, loi=None):
    def mo(_f):
        if loi:
            raise loi
        return _Pdf(trang)
    monkeypatch.setitem(sys.modules, "pdfplumber", types.SimpleNamespace(open=mo))


_DAU = "BÁO CÁO ...\n1.Mãkhóa học:75032K260002 (B01-K39)\n2.Hạngđào tạo:B.01\n"
_HDR = ["STT", "Mã học viên", "Họ và tên", "Ngày sinh", "Tổng thời gian", "Tổng quãng đường", "Ghi chú"]


def test_s7_dong_loi_chi_gan_dong_do_dong_khac_van_doc(monkeypatch):
    _gia_pdfplumber(monkeypatch, [_Trang(_DAU, [[
        _HDR,
        ["1", "M1", "NGUYỄN VĂN AN", "01/01/2000", "20:75", "700,00", "ĐẠT"],
        ["2", "M2", "LÊ THỊ BÌNH", "02/02/2001", "16:19", "725,63", "ĐẠT"],
    ]])])
    r = d.doc_pdf_dat(b"x")
    assert r["ma_kh"] == "75032K260002" and r["hang"] == "B.01"
    assert r["dong"][0]["loi"] and r["dong"][0]["gio"] is None
    assert r["dong"][1]["loi"] is None and r["dong"][1]["gio"] == 16.32 and r["dong"][1]["km"] == 725.63


def test_s7_hai_trang_header_lap_ma_khoa_chi_o_trang_1(monkeypatch):
    _gia_pdfplumber(monkeypatch, [
        _Trang(_DAU, [[_HDR, ["1", "M1", "A", "01/01/2000", "10:00", "500,00", "ĐẠT"]]]),
        _Trang("", [[_HDR, ["2", "M2", "B", "01/01/2000", "11:30", "600,00", "ĐẠT"]]]),
    ])
    r = d.doc_pdf_dat(b"x")
    assert [x["stt"] for x in r["dong"]] == [1, 2] and r["dong"][1]["gio"] == 11.5


def test_s7_thieu_ma_khoa_hoac_thieu_bang_thi_bao_loi(monkeypatch):
    _gia_pdfplumber(monkeypatch, [_Trang("Báo cáo bất kỳ", [[_HDR, ["1", "M1", "A", "x", "10:00", "5,00", ""]]])])
    with pytest.raises(d.LoiDat, match="Mã khóa học"):
        d.doc_pdf_dat(b"x")
    _gia_pdfplumber(monkeypatch, [_Trang(_DAU, [])])
    with pytest.raises(d.LoiDat, match="bảng"):
        d.doc_pdf_dat(b"x")


def test_s7_bang_thieu_cot_ghi_chu_van_doc_duoc(monkeypatch):
    _gia_pdfplumber(monkeypatch, [_Trang(_DAU, [[["1", "M1", "A", "01/01/2000", "10:00", "500,00"]]])])
    r = d.doc_pdf_dat(b"x")
    assert len(r["dong"]) == 1 and r["dong"][0]["ghi_chu"] == "" and r["dong"][0]["km"] == 500.0


def test_s7_pdfplumber_nem_loi_la_thi_bao_chung_khong_lo_chi_tiet(monkeypatch):
    _gia_pdfplumber(monkeypatch, loi=ValueError("boom: /tmp/secret.pdf stack"))
    with pytest.raises(d.LoiDat) as e:
        d.doc_pdf_dat(b"x")
    assert "Không đọc được file PDF" in str(e.value) and "boom" not in str(e.value)


# ---- S8: ranh giới file ở endpoint xem trước -------------------------------------------
_5MB = 5 * 1024 * 1024


def test_s8_dung_5mb_qua_5mb_cong_1_byte_bi_413(monkeypatch, auth_headers):
    _gia_lap(monkeypatch, [_hv("1", gio=10.0, km=500.0)], [])
    ok = _post_xem(monkeypatch, auth_headers, _pdf_gia(), noi_dung=b"%PDF" + b"0" * (_5MB - 4))
    assert ok.status_code == 200
    qua = _post_xem(monkeypatch, auth_headers, _pdf_gia(), noi_dung=b"%PDF" + b"0" * (_5MB - 3))
    assert qua.status_code == 413


def test_s8_duoi_pdf_hoa_va_ma_khoa_lech_hoa_thuong_van_qua(monkeypatch, auth_headers):
    _gia_lap(monkeypatch, [_hv("1", gio=10.0, km=500.0)], [])
    assert _post_xem(monkeypatch, auth_headers, _pdf_gia("KX"), ma_kh="kx", ten="DAT.PDF").status_code == 200


def test_s8_pdf_hong_thi_400_tieng_viet_khong_500(monkeypatch, auth_headers):
    _gia_lap(monkeypatch, [], [])
    r = client.post("/local/ketqua/dat/xem-truoc", headers=auth_headers, data={"ma_kh": "KX"},
                    files={"file": ("dat.pdf", b"%PDF-1.4 hong", "application/pdf")})
    assert r.status_code == 400 and "Không đọc được file PDF" in r.json()["detail"]


# ---- S9: mất kết nối ở truy vấn chính -------------------------------------------------------
def test_s9_mat_ket_noi_o_truy_van_chinh_thi_bao_loi_khong_ghi(monkeypatch, auth_headers):
    @contextmanager
    def hong(_db, **_kw):
        raise RuntimeError("mất kết nối")
        yield  # pragma: no cover

    monkeypatch.setattr(k, "_db_dich", lambda tk: "DB")
    monkeypatch.setattr(k, "sqlserver_conn_dich", hong)
    r = _post_xem(monkeypatch, auth_headers, _pdf_gia())
    assert r.status_code == 502 and "SQL Server" in r.json()["detail"]


# ---- S10–S12: /dat/luu ---------------------------------------------------------------------------
def _luu(auth_headers, dong, ma_kh="KX", headers=True):
    return client.post("/local/ketqua/dat/luu", headers=auth_headers if headers else {},
                       json={"ma_kh": ma_kh, "dong": dong})


@pytest.mark.parametrize("gio,km", [(0, 0), (999, 99999)])
def test_s10_bien_duoi_va_tren_deu_qua(monkeypatch, auth_headers, gio, km):
    _gia_lap(monkeypatch, [], [])
    r = _luu(auth_headers, [{"ma_dk": "1", "gio_duong": gio, "km_duong": km}])
    assert r.status_code == 200 and r.json()["da_luu"] == 1


@pytest.mark.parametrize("dong", [
    [{"ma_dk": "1", "gio_duong": 999.01, "km_duong": 1}],
    [{"ma_dk": "1", "gio_duong": 1, "km_duong": 100000}],
    [],
    [{"ma_dk": "1", "gio_duong": 1}],
    [{"ma_dk": "1", "gio_duong": None, "km_duong": 1}],
])
def test_s10_ngoai_khung_hoac_thieu_truong_la_422(monkeypatch, auth_headers, dong):
    _gia_lap(monkeypatch, [], [])
    assert _luu(auth_headers, dong).status_code == 422


def test_s10_qua_1000_dong_la_422_va_khong_co_phien_la_401_403(monkeypatch, auth_headers):
    _gia_lap(monkeypatch, [], [])
    nhieu = [{"ma_dk": str(i), "gio_duong": 1, "km_duong": 1} for i in range(1001)]
    assert _luu(auth_headers, nhieu).status_code == 422
    assert _luu(auth_headers, [{"ma_dk": "1", "gio_duong": 1, "km_duong": 1}], headers=False).status_code in (401, 403)


def test_s11_ma_dk_co_ky_tu_sql_chi_nam_trong_tham_so(monkeypatch, auth_headers):
    log: list = []
    _gia_lap(monkeypatch, [], log)
    doc_hai = "1'; DROP TABLE NguoiLX_HoSo;--"
    assert _luu(auth_headers, [{"ma_dk": doc_hai, "gio_duong": 1, "km_duong": 1}]).status_code == 200
    sql, params = log[0]
    assert "DROP" not in sql and params[2] == doc_hai


def test_s12_ba_dong_hai_bi_bo_qua_da_luu_la_1_moi_dong_bo_qua_co_ly_do(monkeypatch, auth_headers):
    _gia_lap(monkeypatch, [], [], rowcount_theo_ma={"2": 0, "3": 0})
    r = _luu(auth_headers, [{"ma_dk": m, "gio_duong": 10, "km_duong": 500} for m in ("1", "2", "3")]).json()
    assert r["da_luu"] == 1 and [b["ma_dk"] for b in r["bo_qua"]] == ["2", "3"]
    assert all(b["ly_do"] for b in r["bo_qua"])


# ---- sau /kiemthu: chốt 6 điểm (CHANGES #70) ----------------------------------------------
@pytest.mark.parametrize("dau", [
    "1.Mãkhóa học:75032K260002 (B01-K39)",     # có dấu cách như file thật
    "1.Mãkhóa học:75032K260002(B01-K39)",      # dính liền, không dấu cách
    "1.Mãkhóa học: 75032K260002\n2.Hạngđào tạo:B.01",
])
def test_ma_khoa_chi_lay_chu_va_so(monkeypatch, dau):
    _gia_pdfplumber(monkeypatch, [_Trang(dau, [[["1", "M1", "A", "01/01/2000", "10:00", "500,00", "ĐẠT"]]])])
    assert d.doc_pdf_dat(b"x")["ma_kh"] == "75032K260002"


def test_luu_chi_ghi_ho_so_dang_hoat_dong_cung_dieu_kien_voi_xem_truoc(monkeypatch, auth_headers):
    log: list = []
    _gia_lap(monkeypatch, [], log)
    assert _luu(auth_headers, [{"ma_dk": "1", "gio_duong": 10, "km_duong": 500}]).status_code == 200
    sql = log[0][0]
    assert "TrangThai = 1" in sql and "NOT IN ('12','13')" in sql


# ---- sau /reviewtdd §11D.10 (CHANGES #71): F6 trần tra cứu ------------------------------------
def test_f6_dong_vuot_tran_tra_ten_khong_bi_bao_khong_tim_thay():
    items = [_item(ma=f"M{i}", ten=f"HV {i}") for i in range(3)]
    d.gan_ly_do_khong_co(items, {}, {}, "K1", chua_tra={"M2"})
    assert "chưa nạp/đồng bộ" in items[0]["ghi_chu"] and "chưa nạp/đồng bộ" in items[1]["ghi_chu"]
    assert items[2]["ghi_chu"] == d.LY_DO_CHUA_TRA and items[2]["khoa_khac"] is None


def test_f6_tra_cuu_chi_tra_50_ten_va_danh_dau_phan_con_lai(monkeypatch):
    truy_van: list[str] = []

    class _C:
        def execute(self, sql, params=()):
            truy_van.append(sql)

        def fetchall(self):
            return []

    @contextmanager
    def conn(_db, **_kw):
        class X:
            def cursor(self, as_dict=False):
                return _C()
        yield X()

    monkeypatch.setattr(k, "_db_dich", lambda tk: "DB")
    monkeypatch.setattr(k, "sqlserver_conn_dich", conn)
    items = [_item(ma=f"M{i:03d}", ten=f"HV {i}") for i in range(60)]
    theo_ma, theo_ten, chua_tra = k._tra_cuu_khong_co(items, None)
    assert sum("a.HoVaTen" in s for s in truy_van) == 50          # đúng trần 50 truy vấn theo tên
    assert chua_tra == {f"M{i:03d}" for i in range(50, 60)}        # 10 dòng cuối chưa được tra
    d.gan_ly_do_khong_co(items, theo_ma, theo_ten, "K1", chua_tra)
    assert items[49]["ghi_chu"].startswith("Không tìm thấy")
    assert items[50]["ghi_chu"] == d.LY_DO_CHUA_TRA


def test_f6_vuot_tran_500_ma_chi_gui_500_tham_so_va_phan_du_la_chua_tra(monkeypatch):
    cau_hoi: list[tuple] = []

    class _C:
        def execute(self, sql, params=()):
            cau_hoi.append((sql, params))

        def fetchall(self):
            return []

    @contextmanager
    def conn(_db, **_kw):
        class X:
            def cursor(self, as_dict=False):
                return _C()
        yield X()

    monkeypatch.setattr(k, "_db_dich", lambda tk: "DB")
    monkeypatch.setattr(k, "sqlserver_conn_dich", conn)
    items = [{"ma_dk": f"M{i:04d}", "ho_ten": "", "ngay_sinh": ""} for i in range(503)]
    _, _, chua_tra = k._tra_cuu_khong_co(items, None)
    sql_ma, tham_so = cau_hoi[0]
    assert len(tham_so) == 500 and sql_ma.count("%s") == 500         # IN (...) đúng 500 mã
    assert {"M0500", "M0501", "M0502"} <= chua_tra                    # 3 mã vượt trần mã chưa hề được tra
