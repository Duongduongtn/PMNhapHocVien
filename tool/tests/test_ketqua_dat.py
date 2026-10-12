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
        {"9": [{"MaDK": "9", "MaKhoaHoc": "K2", "TrangThai": 1, "TenKH": "Khóa 2"}]}, {}))
    pdf = {"ma_kh": "KX", "hang": "B", "dong": [_dong("1", 16.32, 725.63), _dong("9", 20.0, 800.0, stt=2)]}
    j = _post_xem(monkeypatch, auth_headers, pdf).json()
    kc = [x for x in j["dong"] if x["tinh_trang"] == "khong_co_trong_khoa"][0]
    assert kc["khoa_khac"] == "Khóa 2 (K2)" and "đổi khóa" in kc["ghi_chu"]


def test_tra_cuu_loi_ket_noi_khong_lam_hong_xem_truoc(monkeypatch):
    def hong(_db):
        raise RuntimeError("mất kết nối")
    monkeypatch.setattr(k, "_db_dich", lambda tk: "DB")
    monkeypatch.setattr(k, "sqlserver_conn_dich", hong)
    assert k._tra_cuu_khong_co([_item()], None) == (None, None)
