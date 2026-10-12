"""KQD-10 — Sổ theo dõi kết quả học tập (mẫu Phụ lục VI, TT17): xếp tên tiếng Việt + định dạng in + luật kết quả."""
from __future__ import annotations

import io
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app import ketqua_so as so
from app.main import app
from app.routers import ketqua as k

client = TestClient(app)
KHOA = {"MaKH": "75032K260003", "TenKH": "B01-K40", "HangGPLX": "B11",
        "NgayKG": "30/07/2026", "NgayBG": "15/09/2026", "NgayThi": "20/09/2026"}
CO_SO = {"co_quan_chu_quan": "CÔNG TY A", "ten_co_so_dao_tao": "TRUNG TÂM GDNN B"}
LUC_LAP = datetime(2026, 10, 12, 14, 5)
_MAU = Path(__file__).resolve().parents[2] / "thamkhao" / "So_theo_doi_ket_qua_hoc_tap_DTLX_TT17.xlsx"


def _hv(ma="1", ten="Nguyễn Văn An", kl=1, **kw):
    r = {"MaDK": ma, "HoVaTen": ten, "NgaySinh": "19981120", "SoCMT": "0791", "SoHoSo": ma,
         "HangGPLX": "B11", "MaHangMoi": "B.01", "TT_XuLy": "09", "KetLuanCSDT": kl,
         "DiemKQLyThuyet": 8.0, "DiemKQMoPhong": 7.0, "DiemKQHinh": 8.0, "DiemKQTienLui": 7.0, "DiemKQThucHanh": 8.0}
    r.update(kw)
    return r


def _mo(rows, co_so=CO_SO, khoa=KHOA):
    return load_workbook(io.BytesIO(so.dung_so_theo_doi(khoa, rows, co_so, LUC_LAP)))


# ---- xếp theo TÊN, đúng thứ tự dấu tiếng Việt ----------------------------------------------------
def test_xep_theo_ten_roi_ho_dem():
    ds = ["Trần Thị An", "Lê Hoàng Bảo", "Nguyễn Văn An", "Đỗ Minh Cường", "Phạm Quốc Bảo", "Vũ Thị Yến"]
    assert sorted(ds, key=so.khoa_sap_xep) == [
        "Nguyễn Văn An", "Trần Thị An",          # cùng tên An → xét họ: Nguyễn < Trần
        "Lê Hoàng Bảo", "Phạm Quốc Bảo",         # cùng tên Bảo → họ Lê < Phạm
        "Đỗ Minh Cường", "Vũ Thị Yến"]


def test_thanh_dieu_khong_dau_huyen_sac_hoi_nga_nang():
    ds = ["A Bạ", "A Bã", "A Bả", "A Bá", "A Bà", "A Ba"]
    assert [x.split()[-1] for x in sorted(ds, key=so.khoa_sap_xep)] == ["Ba", "Bà", "Bá", "Bả", "Bã", "Bạ"]


def test_chu_cai_truoc_thanh_dieu_va_bang_chu_cai_viet():
    # chữ cái so trước: "Bạ" (b,a) đứng trước "Bảo" (b,a,o) dù nặng > hỏi; a < ă < â ; d < đ ; o < ô < ơ
    ds = ["X Bảo", "X Bạ", "X Ân", "X Ăn", "X Anh", "X Đạt", "X Dũng", "X Ơn", "X Ôn", "X On"]
    assert [x.split()[-1] for x in sorted(ds, key=so.khoa_sap_xep)] == \
        ["Anh", "Ăn", "Ân", "Bạ", "Bảo", "Dũng", "Đạt", "On", "Ôn", "Ơn"]


def test_xep_ten_trong_va_ten_mot_tu_khong_loi():
    ds = ["", "An", "Bình", "   "]
    r = sorted(ds, key=so.khoa_sap_xep)
    assert r[0] == "An" and r[1] == "Bình" and set(r[2:]) == {"", "   "}      # tên trống xếp cuối


# ---- định dạng in/khối đầu/bảng — bám file mẫu --------------------------------------------------------
def test_chi_1_sheet_dung_ten_khong_bia_khong_chu_ky():
    wb = _mo([_hv()])
    assert wb.sheetnames == ["SO_PHU_LUC_VI"]
    ws = wb.active
    cuoi = so.HANG_DU_LIEU_DAU + 1
    assert all(c.value in (None, "") for r in ws.iter_rows(min_row=cuoi + 1, max_row=cuoi + 6) for c in r)  # không chữ ký


def test_trang_in_a4_doc_le_hep_lap_tieu_de_danh_so_trang():
    ws = _mo([_hv()]).active
    assert ws.page_setup.paperSize == 9 and ws.page_setup.orientation == "portrait"
    assert ws.page_setup.fitToWidth == 1 and ws.page_setup.fitToHeight == 0
    assert ws.sheet_properties.pageSetUpPr.fitToPage is True
    assert ws.print_options.horizontalCentered is True
    pm = ws.page_margins
    assert (round(pm.left * 2.54, 2), round(pm.right * 2.54, 2), round(pm.top * 2.54, 2), round(pm.bottom * 2.54, 2)) \
        == (2.0, 1.0, 1.5, 1.5)                                              # lề thu hẹp theo yêu cầu (mẫu 3/2/2/2)
    assert ws.print_title_rows == "$10:$11"                                  # 2 hàng tiêu đề lặp mọi trang
    assert ws.oddFooter.center.text == "Trang &P/&N" and ws.evenFooter.center.text == "Trang &P/&N"
    assert ws.sheet_view.showGridLines is False


def test_khoi_dau_bang_va_o_gop_giong_mau():
    ws = _mo([_hv()]).active
    assert {str(m) for m in ws.merged_cells.ranges} == {
        "A1:D2", "E1:H2", "A4:H4", "A6:H6", "A7:H7", "A8:H8",
        "A10:A11", "B10:B11", "C10:C11", "D10:E10", "F10:F11", "G10:G11", "H10:H11"}
    assert ws["A1"].value == "CÔNG TY A\nTRUNG TÂM GDNN B"
    assert ws["E1"].value == "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nĐộc lập - Tự do - Hạnh phúc"
    assert ws["A4"].value == "SỔ THEO DÕI KẾT QUẢ HỌC TẬP" and ws["A4"].font.sz == 14 and ws["A4"].font.b
    assert ws["A6"].value == "Khóa học: B01-K40"
    assert ws["A7"].value == "Ngày lập: 12/10/2026"                         # chỉ ngày, KHÔNG giờ phút
    assert ws["A8"].value == "Người lập:"                                    # để trống, ký tay sau khi in
    tieu_de = [ws.cell(row=10, column=c).value for c in range(1, 9)]
    assert tieu_de == ["Số\nTT", "Họ tên\nhọc viên", "Khóa\nhọc", "Kết quả học tập", None,
                       "Kết quả\nkhóa học", "Ngày xét hoàn thành\nkhóa học", "Xác nhận của\ncơ sở đào tạo"]
    assert ws["D11"].value == "Lý thuyết" and ws["E11"].value == "Thực hành"
    for o in ("A10", "D11", "H10"):
        assert ws[o].fill.fgColor.rgb.endswith("D9EAF7") and ws[o].font.b and ws[o].border.left.style == "thin"
    assert ws["A1"].font.name == "Times New Roman" and ws["B12"].font.name == "Times New Roman" and ws["B12"].font.sz == 12


def test_chieu_cao_va_do_rong_cot():
    ws = _mo([_hv()]).active
    assert [ws.row_dimensions[r].height for r in (1, 2, 4, 6, 10, 11, 12)] == [32.1, 21.95, 26.1, 20.1, 38.1, 30.0, 21.95]
    rong = {c: ws.column_dimensions[c].width for c in "ABCDEFGH"}
    assert rong["A"] == 4.4 and rong["D"] == rong["E"] == 7.4 and rong["G"] == 13.4 and rong["H"] == 12.4
    assert 25 <= rong["B"] <= 34 and 9.4 <= rong["C"] <= 14 and rong["F"] >= 15


def test_ten_dai_khong_xuong_dong_cot_ho_ten_gian_toi_tran_roi_thu_chu():
    dai = "Nguyễn Hoàng Phương Thảo Nguyên Vy Khánh Linh Anh"           # > 40 ký tự
    ws = _mo([_hv(ten="Lê An"), _hv(ma="2", ten=dai)]).active
    assert ws.column_dimensions["B"].width == 34                          # chạm trần
    for r in (12, 13):
        c = ws.cell(row=r, column=2)
        assert not c.alignment.wrap_text and c.alignment.shrink_to_fit is True and c.alignment.horizontal == "left"
        assert c.alignment.indent == 0
    ws2 = _mo([_hv(ten="Lê An")]).active
    assert ws2.column_dimensions["B"].width == 25                         # tên ngắn: giữ độ rộng mẫu


# ---- dữ liệu ----------------------------------------------------------------------------------------------
def test_dong_du_lieu_sap_xep_stt_lien_tuc_va_gia_tri():
    ws = _mo([_hv("1", "Trần Thị An"), _hv("2", "Lê Hoàng Bảo"), _hv("3", "Nguyễn Văn An")]).active
    ten = [ws.cell(row=r, column=2).value for r in (12, 13, 14)]
    assert ten == ["Nguyễn Văn An", "Trần Thị An", "Lê Hoàng Bảo"]
    assert [ws.cell(row=r, column=1).value for r in (12, 13, 14)] == [1, 2, 3]
    r = 12
    assert ws.cell(row=r, column=3).value == "B01-K40"
    assert ws.cell(row=r, column=4).value == 7.5 and ws.cell(row=r, column=4).number_format == "0.0"     # TB(8, 7)
    assert ws.cell(row=r, column=5).value == 7.7                                                          # TB(8, 7, 8)
    assert ws.cell(row=r, column=6).value == "Hoàn thành"
    ngay = ws.cell(row=r, column=7)
    assert ngay.value == datetime(2026, 9, 20) and ngay.number_format == "dd/mm/yyyy"   # ngày thi khóa, không giờ
    assert ws.cell(row=r, column=8).value is None and ws.cell(row=r, column=8).border.left.style == "thin"


def test_chua_hoan_thanh_chu_do_khong_co_ngay_xet():
    ws = _mo([_hv(kl=0)]).active
    assert ws["F12"].value == "Chưa hoàn thành" and ws["F12"].font.color.rgb.endswith("C00000")
    assert ws["G12"].value is None


def test_thieu_diem_de_trong_ke_ca_khi_da_co_ket_luan():
    ws = _mo([_hv(kl=1, DiemKQHinh=None)]).active                         # PM cũ lưu "Đạt" nhưng thiếu Sa hình
    assert ws["D12"].value == 7.5                                          # LT đủ 2 môn
    assert ws["E12"].value is None                                         # TH thiếu → trống
    assert ws["F12"].value is None and ws["G12"].value is None             # luật sổ mẫu: chưa đủ 5 nội dung → trống


def test_chua_co_ket_luan_va_chua_co_diem():
    r = _hv(kl=None, DiemKQLyThuyet=None, DiemKQMoPhong=None, DiemKQHinh=None, DiemKQTienLui=None, DiemKQThucHanh=None)
    ws = _mo([r]).active
    assert [ws.cell(row=12, column=c).value for c in (4, 5, 6, 7)] == [None, None, None, None]
    assert ws["B12"].value == "Nguyễn Văn An"                              # học viên vẫn có dòng


def test_co_so_trong_thi_de_trong_khong_vo():
    ws = _mo([_hv()], co_so={}).active
    assert ws["A1"].value in (None, "")
    assert ws["A4"].value == "SỔ THEO DÕI KẾT QUẢ HỌC TẬP"


def test_cong_thuc_excel_bi_ep_kieu_chu_va_ky_tu_dieu_khien_khong_vo_file():
    ws = _mo([_hv(ten='=HYPERLINK("http://e.x","click")'), _hv(ma="2", ten="Lê \x00Văn\x0b Cường")],
             co_so={"co_quan_chu_quan": "=cmd|' /C calc'!A0", "ten_co_so_dao_tao": "TT"}).active
    assert ws["A1"].data_type == "s" and ws["A1"].quotePrefix is True
    ten = {ws.cell(row=r, column=2).value: ws.cell(row=r, column=2).data_type for r in (12, 13)}
    assert ten['=HYPERLINK("http://e.x","click")'] == "s"
    assert "Lê Văn Cường" in ten


# ---- đối chiếu trực tiếp với file mẫu (bỏ qua nếu máy không có thamkhao/) -------------------------------------------
@pytest.mark.skipif(not _MAU.exists(), reason="không có file mẫu thamkhao/")
def test_giong_file_mau_ve_cau_truc_in_va_o_gop():
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mau = load_workbook(_MAU)["SO_PHU_LUC_VI"]
    ws = _mo([_hv()]).active
    assert ws.page_setup.paperSize == mau.page_setup.paperSize == 9
    assert ws.page_setup.orientation == mau.page_setup.orientation
    assert ws.print_title_rows == mau.print_title_rows
    assert ws.oddFooter.center.text == mau.oddFooter.center.text
    assert ws.print_options.horizontalCentered == mau.print_options.horizontalCentered
    assert {str(m) for m in ws.merged_cells.ranges} == {str(m) for m in mau.merged_cells.ranges}
    for o in ("A10", "D11", "A4", "A1"):
        assert (ws[o].font.name, ws[o].font.sz, ws[o].font.b) == (mau[o].font.name, mau[o].font.sz, mau[o].font.b)
        assert ws[o].fill.fgColor.rgb == mau[o].fill.fgColor.rgb
    for r in (1, 2, 4, 6, 10, 11):
        assert ws.row_dimensions[r].height == mau.row_dimensions[r].height


# ---- endpoint ---------------------------------------------------------------------------------------------------------------
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


def test_endpoint_luu_so_vao_output_chi_doc_db(monkeypatch, auth_headers, tmp_path):
    log: list = []
    _gia_lap(monkeypatch, KHOA, [_hv("1", "Trần Thị An"), _hv("2", "Nguyễn Văn An")], log)
    monkeypatch.setattr(k.paths, "output_dir", lambda: tmp_path)
    monkeypatch.setattr(k.config_store, "load_config", lambda: {"ten_co_so_dao_tao": "TRUNG TÂM GDNN B"})
    r = client.post("/local/ketqua/xuat-so-theo-doi?ma_kh=75032K260003", headers=auth_headers)
    assert r.status_code == 200
    j = r.json()
    assert j["ten_file"].startswith("SoTheoDoiKetQuaHocTap_75032K260003_") and j["so_hoc_vien"] == 2
    ws = load_workbook(tmp_path / j["ten_file"]).active
    assert ws.title == "SO_PHU_LUC_VI" and ws["A1"].value == "TRUNG TÂM GDNN B"
    assert ws["B12"].value == "Nguyễn Văn An" and ws["B13"].value == "Trần Thị An"
    assert log and all(s.lstrip().upper().startswith("SELECT") for s, _ in log)


def test_endpoint_khoa_rong_la_404_va_can_phien(monkeypatch, auth_headers):
    _gia_lap(monkeypatch, KHOA, [], [])
    r = client.post("/local/ketqua/xuat-so-theo-doi?ma_kh=75032K260003", headers=auth_headers)
    assert r.status_code == 404 and "chưa có học viên" in r.json()["detail"]
    assert client.post("/local/ketqua/xuat-so-theo-doi?ma_kh=X").status_code in (401, 403)


def test_ten_file_so_va_ngay_lap_excel_chi_tiet_chi_ngay():
    from datetime import date

    from app import ketqua_xuat as kx
    assert kx.ten_file("75032K260003", date(2026, 10, 12), so.TIEN_TO_FILE) == "SoTheoDoiKetQuaHocTap_75032K260003_12-10-2026.xlsx"
    ws = load_workbook(io.BytesIO(kx.dung_workbook(KHOA, [_hv()], CO_SO, "NV", LUC_LAP))).active
    assert "Ngày lập: 12/10/2026" in ws["A6"].value and "14:05" not in ws["A6"].value
