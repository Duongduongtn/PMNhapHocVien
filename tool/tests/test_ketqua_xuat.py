"""KQD-09 — xuất Excel kết quả học tập theo khóa: dựng workbook (hàm thuần) + endpoint chỉ đọc bằng cursor giả."""
from __future__ import annotations

import io
from contextlib import contextmanager
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app import ketqua_xuat as x
from app.main import app
from app.routers import ketqua as k

client = TestClient(app)

KHOA = {"MaKH": "75032K260003", "TenKH": "B01-K40", "HangGPLX": "B.01",
        "NgayKG": "30/07/2026", "NgayBG": "15/09/2026", "NgayThi": "20/09/2026"}
CO_SO = {"co_quan_chu_quan": "CÔNG TY CPDVDL THÀNH ĐẠT", "ten_co_so_dao_tao": "TRUNG TÂM GDNN THÀNH ĐẠT"}
LUC_LAP = datetime(2026, 10, 12, 14, 5)


def _hv(ma="75032-20260803-000001", ten="Nguyễn Thị Hòa", so="1", tt="09", kl=1, ns="19981120", **kw):
    r = {"MaDK": ma, "HoVaTen": ten, "NgaySinh": ns, "SoCMT": "079198001234", "SoHoSo": so,
         "HangGPLX": "B11", "MaHangMoi": "B.01", "TT_XuLy": tt, "KetLuanCSDT": kl,
         "DiemKQLyThuyet": 8.0, "DiemKQMoPhong": 7.0, "DiemKQHinh": 8.0, "DiemKQTienLui": 7.0, "DiemKQThucHanh": 8.0,
         "TGThucHanhHinh": 34, "QDThucHanhHinh": 240, "TGThucHanhDuong": 18.399999618530273,
         "TongQDThucHanh": 719.4000244140625, "SoGiayCNTN": "75032-20260803-000001-B.01"}
    r.update(kw)
    return r


def _mo(rows, **kw):
    data = x.dung_workbook(KHOA, rows, kw.pop("co_so", CO_SO), kw.pop("nguoi", "Nhân viên Hòa"),
                           LUC_LAP, kw.pop("ct", "cu"))
    return load_workbook(io.BytesIO(data)).active


def _cot(ws, ten):
    return next(c.column for c in ws[x.HANG_TIEU_DE] if c.value == ten)


# ---- khối đầu ---------------------------------------------------------------------------
def test_khoi_dau_du_thong_tin():
    ws = _mo([_hv(), _hv(ma="2", so="2", kl=0), _hv(ma="3", so="3", kl=None)])
    assert ws.title == "KET_QUA_HOC_TAP"
    assert ws["A1"].value == "CÔNG TY CPDVDL THÀNH ĐẠT" and ws["A2"].value == "TRUNG TÂM GDNN THÀNH ĐẠT"
    assert ws["A3"].value == "KẾT QUẢ HỌC TẬP CỦA HỌC VIÊN"
    assert "B01-K40 (75032K260003)" in ws["A4"].value and "Hạng: B.01" in ws["A4"].value
    assert "Cũ (TT12/2025)" in ws["A4"].value
    assert "Khai giảng: 30/07/2026" in ws["A5"].value and "Ngày thi: 20/09/2026" in ws["A5"].value
    assert "12/10/2026 14:05" in ws["A6"].value and "Người lập: Nhân viên Hòa" in ws["A6"].value
    assert ws["A7"].value == "Tổng 3 học viên   ·   Hoàn thành 1   ·   Chưa hoàn thành 1   ·   Chưa có kết luận 1"


def test_chuong_trinh_moi_va_co_so_trong_thi_de_trong():
    ws = _mo([_hv()], ct="moi", co_so={})
    assert "Mới (TT108/2026)" in ws["A4"].value
    assert ws["A1"].value in (None, "") and ws["A2"].value in (None, "")


def test_hang_khoa_lay_hang_moi_pho_bien_nhat_khong_lay_ma_cu_cua_khoa():
    ws = _mo([_hv(), _hv(ma="2", so="2")])                    # KHOA.HangGPLX = "B.01" nhưng DB thật trả mã cũ "B11"
    khoa_cu = dict(KHOA, HangGPLX="B11")
    data = x.dung_workbook(khoa_cu, [_hv(), _hv(ma="2", so="2")], CO_SO, "NV", LUC_LAP)
    assert "Hạng: B.01" in load_workbook(io.BytesIO(data)).active["A4"].value
    assert ws["A4"].value                                      # khối đầu vẫn dựng được


def test_diem_lam_tron_1_chu_so_khong_lo_duoi_real():
    ws = _mo([_hv(DiemKQLyThuyet=9.300000190734863)])
    assert ws.cell(row=x.HANG_TIEU_DE + 1, column=_cot(ws, "Lý thuyết")).value == 9.3


# ---- bảng -----------------------------------------------------------------------------------
def test_22_cot_dung_thu_tu_va_tieu_de():
    ws = _mo([_hv()])
    tieu_de = [c.value for c in ws[x.HANG_TIEU_DE]]
    assert len(tieu_de) == 22
    assert tieu_de[:6] == ["STT", "Mã đăng ký", "Họ và tên", "Ngày sinh", "Số CCCD", "Hạng"]
    assert tieu_de[6:11] == ["Lý thuyết", "Mô phỏng", "Sa hình", "Chữ chi", "Đường trường"]
    assert tieu_de[11:13] == ["Điểm Lý thuyết", "Điểm Thực hành"]
    assert tieu_de[-1] == "Ghi chú"


def test_dong_hoan_thanh_day_du_va_dinh_dang():
    ws = _mo([_hv()])
    r = x.HANG_TIEU_DE + 1
    v = lambda ten: ws.cell(row=r, column=_cot(ws, ten))
    assert v("STT").value == 1
    assert v("Họ và tên").value == "Nguyễn Thị Hòa"                       # tiếng Việt có dấu không vỡ
    assert v("Ngày sinh").value == datetime(1998, 11, 20)                 # ô ngày THẬT, không phải chuỗi
    assert v("Ngày sinh").number_format == "dd/mm/yyyy"
    assert v("Số CCCD").value == "079198001234" and v("Số CCCD").number_format == "@"   # chuỗi, không 1.2E+11
    assert v("Hạng").value == "B.01"
    assert [v(t).value for t in ("Lý thuyết", "Mô phỏng", "Sa hình", "Chữ chi", "Đường trường")] == [8, 7, 8, 7, 8]
    assert v("Điểm Lý thuyết").value == 7.5                                # TB(8, 7)
    assert v("Điểm Thực hành").value == 7.7                                # TB(8, 7, 8) = 7,67 → 7,7
    assert v("Giờ đường").value == 18.4                                    # real của CDB 18.399999… → làm tròn 2 chữ số
    assert v("Kết quả khóa học").value == "Hoàn thành"
    assert v("Ngày xét hoàn thành").value == datetime(2026, 9, 20)         # ngày thi của khóa
    assert v("Trạng thái hồ sơ").value == "Đã cập nhật · Đạt"
    assert v("Số giấy HTKH").value == "75032-20260803-000001-B.01"


def test_ket_qua_khong_dat_va_chua_co_ket_luan():
    ws = _mo([_hv(kl=0, tt="10"), _hv(ma="2", so="2", kl=None, tt="03")])
    r1, r2 = x.HANG_TIEU_DE + 1, x.HANG_TIEU_DE + 2
    c = _cot(ws, "Kết quả khóa học")
    assert ws.cell(row=r1, column=c).value == "Chưa hoàn thành"
    assert ws.cell(row=r1, column=_cot(ws, "Ngày xét hoàn thành")).value is None   # chỉ hiện khi Hoàn thành
    assert ws.cell(row=r2, column=c).value is None                                  # chưa có kết luận → trống


def test_chua_du_diem_de_trong_khong_dien_0_va_ghi_chu_dung_mon():
    ws = _mo([_hv(kl=None, tt="04", DiemKQMoPhong=None, DiemKQTienLui=None)])
    r = x.HANG_TIEU_DE + 1
    assert ws.cell(row=r, column=_cot(ws, "Mô phỏng")).value is None
    assert ws.cell(row=r, column=_cot(ws, "Điểm Lý thuyết")).value is None       # thiếu 1 môn → trống
    assert ws.cell(row=r, column=_cot(ws, "Điểm Thực hành")).value is None
    ghi_chu = ws.cell(row=r, column=_cot(ws, "Ghi chú")).value
    assert "Thiếu: Mô phỏng, Chữ chi" in ghi_chu


def test_chua_co_diem_nao():
    r = _hv(kl=None, tt="03", DiemKQLyThuyet=None, DiemKQMoPhong=None, DiemKQHinh=None,
            DiemKQTienLui=None, DiemKQThucHanh=None, TGThucHanhDuong=None, TongQDThucHanh=None)
    ws = _mo([r])
    assert ws.cell(row=x.HANG_TIEU_DE + 1, column=_cot(ws, "Ghi chú")).value == "Chưa có điểm"


def test_canh_bao_gio_km_duong_duoi_nguong_trong_ghi_chu():
    # B.01 gợi ý giờ đường ≥ 12, km ≥ 710
    ws = _mo([_hv(TGThucHanhDuong=10.5, TongQDThucHanh=600.0)])
    ghi_chu = ws.cell(row=x.HANG_TIEU_DE + 1, column=_cot(ws, "Ghi chú")).value
    assert "Giờ đường 10.5 < 12" in ghi_chu and "Km đường 600 < 710" in ghi_chu


def test_diem_duoi_5_chu_do_va_hoan_thanh_chu_xanh():
    ws = _mo([_hv(DiemKQMoPhong=4.0), _hv(ma="2", so="2")])
    r1, r2 = x.HANG_TIEU_DE + 1, x.HANG_TIEU_DE + 2
    assert ws.cell(row=r1, column=_cot(ws, "Mô phỏng")).font.color.rgb.endswith("C00000")
    assert ws.cell(row=r2, column=_cot(ws, "Kết quả khóa học")).font.color.rgb.endswith("1E7B34")


def test_stt_theo_so_ho_so_va_khong_loai_hv_da_ket_xuat():
    rows = [_hv(ma="C", so="10", tt="13"), _hv(ma="A", so="2", tt="12"), _hv(ma="B", so="3", tt="14")]
    ws = _mo(rows)
    ma = [ws.cell(row=x.HANG_TIEU_DE + i, column=2).value for i in (1, 2, 3)]
    assert ma == ["A", "B", "C"]                                           # theo SoHoSo 2 < 3 < 10 (số, không chữ)
    tt = [ws.cell(row=x.HANG_TIEU_DE + i, column=_cot(ws, "Trạng thái hồ sơ")).value for i in (1, 2, 3)]
    assert tt == ["Đã kết xuất gửi Sở", "Sở từ chối", "Hoàn thành"]       # 12/13/14 vẫn có mặt


def test_loc_dong_bang_in_a4_ngang():
    ws = _mo([_hv(), _hv(ma="2", so="2")])
    assert ws.auto_filter.ref == f"A{x.HANG_TIEU_DE}:V{x.HANG_TIEU_DE + 2}"
    assert ws.freeze_panes == f"A{x.HANG_TIEU_DE + 1}"
    assert ws.page_setup.orientation == "landscape" and ws.page_setup.paperSize == 9
    assert ws.print_title_rows == f"${x.HANG_TIEU_DE}:${x.HANG_TIEU_DE}"


def test_ngay_sinh_sai_dang_thi_de_trong_khong_vo_file():
    ws = _mo([_hv(ns="1998"), _hv(ma="2", so="2", ns=None)])
    c = _cot(ws, "Ngày sinh")
    assert ws.cell(row=x.HANG_TIEU_DE + 1, column=c).value is None and ws.cell(row=x.HANG_TIEU_DE + 2, column=c).value is None


def test_gio_km_so_nguyen_khong_co_dau_cham_thua():
    # "0.##" làm Excel hiện "34." với số nguyên → số nguyên dùng "0", số lẻ dùng "0.##"
    ws = _mo([_hv(TGThucHanhHinh=34, QDThucHanhHinh=240, TGThucHanhDuong=18.5, TongQDThucHanh=719.4)])
    r = x.HANG_TIEU_DE + 1
    assert ws.cell(row=r, column=_cot(ws, "Giờ sân")).number_format == "0"
    assert ws.cell(row=r, column=_cot(ws, "Km sân")).number_format == "0"
    assert ws.cell(row=r, column=_cot(ws, "Giờ đường")).number_format == "0.##"
    assert ws.cell(row=r, column=_cot(ws, "Km đường")).number_format == "0.##"


def test_luu_file_khong_ghi_de_va_dem_tang_dan(tmp_path):
    f1 = x.luu_file(tmp_path, "KQ_K1_12-10-2026.xlsx", b"a")
    f2 = x.luu_file(tmp_path, "KQ_K1_12-10-2026.xlsx", b"b")
    assert f1.name == "KQ_K1_12-10-2026.xlsx" and f2.name == "KQ_K1_12-10-2026_2.xlsx"
    assert f1.read_bytes() == b"a" and f2.read_bytes() == b"b"


def test_output_dir_chay_dev_la_tool_output_va_ghi_duoc():
    from app import paths
    d = paths.output_dir()
    assert d.name == "output" and d.is_dir()
    assert not (d / ".ghi_thu").exists()                                    # file dò quyền ghi đã dọn


def test_ten_file_ascii_an_toan():
    assert x.ten_file("75032K260003", date(2026, 10, 12)) == "KetQuaHocTap_75032K260003_12-10-2026.xlsx"
    assert x.ten_file("../a b/ý", date(2026, 10, 12)) == "KetQuaHocTap_ab_12-10-2026.xlsx"
    assert x.ten_file("", date(2026, 10, 12)) == "KetQuaHocTap_khoa_12-10-2026.xlsx"


# ---- endpoint (cursor giả) -----------------------------------------------------------------------
class _Cur:
    def __init__(self, khoa, rows, log):
        self.khoa, self.rows, self.log, self._r = khoa, rows, log, []

    def execute(self, sql, params=()):
        self.log.append((sql, params))
        self._r = [self.khoa] if "FROM dbo.KhoaHoc" in sql else self.rows

    def fetchone(self):
        return self._r[0] if self._r else None

    def fetchall(self):
        return self._r


def _gia_lap(monkeypatch, khoa, rows, log):
    @contextmanager
    def conn(_db, **_kw):
        class C:
            def cursor(self, as_dict=False):
                return _Cur(khoa, rows, log)
        yield C()

    monkeypatch.setattr(k, "_db_dich", lambda tk: "DB")
    monkeypatch.setattr(k, "sqlserver_conn_dich", conn)


def test_endpoint_luu_file_vao_thu_muc_output_chi_doc_db(monkeypatch, auth_headers, tmp_path):
    log: list = []
    _gia_lap(monkeypatch, KHOA, [_hv(), _hv(ma="2", so="2", ten="Lê Văn Đức")], log)
    monkeypatch.setattr(k.config_store, "load_config", lambda: {"ten_co_so_dao_tao": "TT GDNN THÀNH ĐẠT"})
    monkeypatch.setattr(k.paths, "output_dir", lambda: tmp_path)
    r = client.post("/local/ketqua/xuat-excel?ma_kh=75032K260003", headers=auth_headers)
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True and j["so_hoc_vien"] == 2
    assert j["ten_file"].startswith("KetQuaHocTap_75032K260003_") and j["ten_file"].endswith(".xlsx")
    assert j["thu_muc"] == str(tmp_path) and j["duong_dan"] == str(tmp_path / j["ten_file"])
    ws = load_workbook(tmp_path / j["ten_file"]).active                 # file thật nằm trong output
    assert ws["A2"].value == "TT GDNN THÀNH ĐẠT"
    assert "Người lập: NV Nạp (test)" in ws["A6"].value                   # họ tên người đăng nhập
    assert ws.cell(row=x.HANG_TIEU_DE + 2, column=3).value == "Lê Văn Đức"
    assert log and all(s.lstrip().upper().startswith("SELECT") for s, _ in log)   # DB: chỉ đọc


def test_xuat_hai_lan_khong_ghi_de_file_cu(monkeypatch, auth_headers, tmp_path):
    _gia_lap(monkeypatch, KHOA, [_hv()], [])
    monkeypatch.setattr(k.paths, "output_dir", lambda: tmp_path)
    ten = [client.post("/local/ketqua/xuat-excel?ma_kh=75032K260003", headers=auth_headers).json()["ten_file"]
           for _ in range(3)]
    assert len(set(ten)) == 3 and ten[1].endswith("_2.xlsx") and ten[2].endswith("_3.xlsx")
    assert len(list(tmp_path.glob("*.xlsx"))) == 3


def test_khong_ghi_duoc_thu_muc_output_thi_bao_ro(monkeypatch, auth_headers):
    _gia_lap(monkeypatch, KHOA, [_hv()], [])

    def hong():
        raise OSError("read-only")
    monkeypatch.setattr(k.paths, "output_dir", hong)
    r = client.post("/local/ketqua/xuat-excel?ma_kh=75032K260003", headers=auth_headers)
    assert r.status_code == 500 and "thư mục output" in r.json()["detail"] and "read-only" not in r.text


def test_mo_thu_muc_chi_mo_duong_dan_co_dinh_va_can_phien(monkeypatch, auth_headers, tmp_path):
    mo: list = []
    monkeypatch.setattr(k.paths, "output_dir", lambda: tmp_path)
    monkeypatch.setattr("os.startfile", lambda p: mo.append(p), raising=False)
    assert client.post("/local/ketqua/mo-thu-muc-xuat").status_code in (401, 403)
    r = client.post("/local/ketqua/mo-thu-muc-xuat", headers=auth_headers, json={"duong_dan": "C:/Windows"})
    assert r.status_code == 200 and mo == [str(tmp_path)]                  # bỏ qua mọi đầu vào từ client


def test_endpoint_khoa_khong_ton_tai_hoac_khong_co_hv_la_404(monkeypatch, auth_headers):
    _gia_lap(monkeypatch, None, [], [])
    assert client.post("/local/ketqua/xuat-excel?ma_kh=X", headers=auth_headers).status_code == 404
    _gia_lap(monkeypatch, KHOA, [], [])
    r = client.post("/local/ketqua/xuat-excel?ma_kh=75032K260003", headers=auth_headers)
    assert r.status_code == 404 and "chưa có học viên" in r.json()["detail"]


def test_endpoint_mat_ket_noi_va_khong_phien(monkeypatch, auth_headers):
    @contextmanager
    def hong(_db, **_kw):
        raise RuntimeError("mất kết nối")
        yield  # pragma: no cover

    monkeypatch.setattr(k, "_db_dich", lambda tk: "DB")
    monkeypatch.setattr(k, "sqlserver_conn_dich", hong)
    assert client.post("/local/ketqua/xuat-excel?ma_kh=X", headers=auth_headers).status_code == 502
    assert client.post("/local/ketqua/xuat-excel?ma_kh=X").status_code in (401, 403)


def test_dung_workbook_loi_thi_bao_chung_khong_lo_chi_tiet(monkeypatch, auth_headers):
    _gia_lap(monkeypatch, KHOA, [_hv()], [])

    def no(*a, **kw):
        raise ValueError("secret: C:/path/noi_bo")
    monkeypatch.setattr(k.ketqua_xuat, "dung_workbook", no)
    r = client.post("/local/ketqua/xuat-excel?ma_kh=75032K260003", headers=auth_headers)
    assert r.status_code == 500 and "secret" not in r.text and "noi_bo" not in r.text


# ---- cấu hình tên cơ sở ---------------------------------------------------------------------------------
def test_put_co_so_chi_gop_2_khoa_khong_lam_roi_khoa_khac(monkeypatch, auth_headers):
    luu: dict = {}
    monkeypatch.setattr(k.config_store, "load_config", lambda: {"sqlserver_host": "H", "kqd_chuong_trinh": {"K1": "moi"}})
    monkeypatch.setattr(k.config_store, "save_config", lambda d: luu.update(d))
    monkeypatch.setattr(k.config_store, "masked_config", lambda: dict(luu))
    r = client.put("/local/config/co-so", headers=auth_headers,
                   json={"co_quan_chu_quan": "  CÔNG TY A  ", "ten_co_so_dao_tao": "TRUNG TÂM B"})
    assert r.status_code == 200
    assert luu["co_quan_chu_quan"] == "CÔNG TY A" and luu["ten_co_so_dao_tao"] == "TRUNG TÂM B"
    assert luu["sqlserver_host"] == "H" and luu["kqd_chuong_trinh"] == {"K1": "moi"}   # khóa khác còn nguyên


# ---- sau /reviewtdd §11D.11 (CHANGES #73) ----------------------------------------------------------
@pytest.mark.parametrize("doc_hai", [
    '=HYPERLINK("http://e.x","click")', "=cmd|' /C calc'!A0", "+1+1", "-2+3", "@SUM(1)", "\t=1+1",
])
def test_formula_injection_o_chu_bi_ep_kieu_chuoi(doc_hai):
    ws = _mo([_hv(ten=doc_hai, SoGiayCNTN=doc_hai)], co_so={"co_quan_chu_quan": doc_hai, "ten_co_so_dao_tao": doc_hai})
    for o in (ws["A1"], ws["A2"], ws.cell(row=x.HANG_TIEU_DE + 1, column=3),
              ws.cell(row=x.HANG_TIEU_DE + 1, column=_cot(ws, "Số giấy HTKH"))):
        assert o.data_type == "s", (o.coordinate, o.data_type)       # KHÔNG phải 'f' (công thức)
        assert o.quotePrefix is True


def test_ky_tu_dieu_khien_khong_lam_hong_ca_file():
    ws = _mo([_hv(ten="NGUYỄN \x00VĂN\x0b A"), _hv(ma="2", so="2")])
    assert ws.cell(row=x.HANG_TIEU_DE + 1, column=3).value == "NGUYỄN VĂN A"       # ký tự lạ bị bỏ
    assert ws.cell(row=x.HANG_TIEU_DE + 2, column=3).value == "Nguyễn Thị Hòa"    # dòng khác vẫn đủ


def test_chuoi_qua_dai_bi_cat_32000():
    ws = _mo([_hv(ten="A" * 40000)])
    assert len(ws.cell(row=x.HANG_TIEU_DE + 1, column=3).value) == 32000


def test_hang_hoa_phieu_lay_theo_chu_cai_on_dinh():
    rows = [_hv(MaHangMoi="B"), _hv(ma="2", so="2", MaHangMoi="B.01")]
    for _ in range(5):                                    # chạy nhiều lần: kết quả không đổi
        data = x.dung_workbook(dict(KHOA, HangGPLX="B11"), list(reversed(rows)), CO_SO, "NV", LUC_LAP)
        assert "Hạng: B   ·" in load_workbook(io.BytesIO(data)).active["A4"].value   # "B" < "B.01"


def test_ten_khoa_co_ky_tu_dieu_khien_van_dung_duoc():
    khoa = dict(KHOA, TenKH="K40\x00 \x07 đặc biệt")
    data = x.dung_workbook(khoa, [_hv()], CO_SO, "NV", LUC_LAP)
    assert "K40  đặc biệt" in load_workbook(io.BytesIO(data)).active["A4"].value


def test_put_co_so_can_phien(monkeypatch):
    r = client.put("/local/config/co-so", json={"co_quan_chu_quan": "A", "ten_co_so_dao_tao": "B"})
    assert r.status_code in (401, 403)
