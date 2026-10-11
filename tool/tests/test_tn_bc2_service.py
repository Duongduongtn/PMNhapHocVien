"""TNB-04 (2/6) — task 97: đọc ứng viên cho "Lập BC2 / Thêm HV" (`tn_bc2_service` + router).

Cursor giả (không DB): khóa các bất biến của TDD §11F.4 v6.8 — gọi SP MỘT lần với `@MaKH=''`
(`@HangDT=''` ô tô, `'A1'` mô tô), một SELECT bổ sung theo MaDK, cache ~30 giây, KHÔNG có câu
ghi, đếm khóa từ chính tập đã tải, HV ở BC2 mở khác → không đưa được, dán danh sách.
"""
from contextlib import contextmanager

import pytest

from app import tn_bc2_service as svc
from app import tn_bc2_rules as rules

HOM_NAY = "2026-10-11"
KHOA_A = "75032K260007"   # ô tô, bế giảng 20/09/2026, có BC1
KHOA_B = "75032K250009"   # ô tô, bế giảng 15/01/2026 (cũ hơn cửa sổ? không: ≥ 2025-09-11)
KHOA_CU = "75032K240001"  # ô tô, bế giảng 01/10/2024 (ngoài cửa sổ)
KHOA_MOTO = "75032K260020"


def cmt_cua(ma_dk):
    """CMT duy nhất theo mã đăng ký (A-0001 → 079650001)."""
    return f"079{ord(ma_dk[0])}{ma_dk[-4:]}"


def sp_row(ma_dk, ma_kh, ten="Nguyễn Văn A", cmt=None):
    cmt = cmt or cmt_cua(ma_dk)
    return {"MaDK": ma_dk, "SoHoSo": "1", "HoVaTen": ten, "NgaySinh": "01/02/2000", "SoCMT": cmt,
            "SoGiayCNTN": "", "SoCCN": "", "MaKH": ma_kh, "TenKH": "Khóa " + ma_kh[-4:]}


def bs_row(ma_dk, tt, hang="B2", ma_bc2="", giay="N1|7282", bg="2026-09-20"):
    return {"MaDK": ma_dk, "TT_XuLy": tt, "MaBC2": ma_bc2, "HangGPLX": hang, "SoGiayCNTN": giay,
            "NgayBG": bg}


class FakeCur:
    def __init__(self, sp=(), bo_sung=(), khong_duoc=(), khoa=None, bc1=(), bc2=(), khoa_all=()):
        self.sp, self.bo_sung, self.khong_duoc = list(sp), list(bo_sung), list(khong_duoc)
        self.khoa, self.bc1, self.bc2, self.khoa_all = khoa, list(bc1), list(bc2), list(khoa_all)
        self.log, self._rows = [], []

    def execute(self, sql, params=()):
        self.log.append((sql, tuple(params)))
        s = " ".join(sql.split())
        if s.startswith("EXEC usp_NguoiLX_HoSo_ThemHS_BC2"):
            self._rows = self.sp
        elif "FROM NguoiLX_HoSo h JOIN KhoaHoc k" in s and "WHERE h.MaDK IN" in s:
            ids = set(params)
            self._rows = [r for r in self.bo_sung if r["MaDK"] in ids]
        elif "WHERE h.MaKhoaHoc = %s AND h.TT_XuLy NOT IN" in s:
            self._rows = [r for r in self.khong_duoc if r["MaKhoaHoc"] == params[0]]
        elif s.startswith("SELECT MaKH, TenKH, HangGPLX, NgayBG FROM KhoaHoc WHERE MaKH"):
            cand = ([self.khoa] if self.khoa else []) + self.khoa_all
            self._rows = [k for k in cand if k["MaKH"] == params[0]][:1]
        elif s.startswith("SELECT MaKH, TenKH, HangGPLX, NgayBG FROM KhoaHoc"):
            self._rows = self.khoa_all
        elif s.startswith("SELECT MaBCI, MaKH"):
            self._rows = self.bc1
        elif s.startswith("SELECT MaBCII"):
            self._rows = self.bc2
        else:
            raise AssertionError("câu lệnh lạ: " + s)

    def fetchall(self):
        return list(self._rows)

    def fetchone(self):
        return self._rows[0] if self._rows else None


def factory(cur):
    @contextmanager
    def _f():
        yield cur
    return _f


def khoa_row(ma, hang="B2", bg="2026-09-20", ten=None):
    return {"MaKH": ma, "TenKH": ten or "Khóa " + ma[-4:], "HangGPLX": hang, "NgayBG": bg}


def du_lieu_oto():
    """Khóa A: 3 sẵn sàng + 1 thiếu số giấy + 1 chưa tốt nghiệp (03); khóa B: 1 thi lại 17 + khóa A: 1 thi lại 18;
    khóa cũ: 1 thi lại 18 quá hạn; 1 HV `09` của khóa B (không hiện ở khóa A)."""
    sp, bs = [], []

    def them(ma_dk, ma_kh, tt, bg, **kw):
        sp.append(sp_row(ma_dk, ma_kh))
        bs.append(bs_row(ma_dk, tt, bg=bg, **kw))
    them("A-0001", KHOA_A, "09", "2026-09-20")
    them("A-0002", KHOA_A, "09", "2026-09-20")
    them("A-0003", KHOA_A, "09", "2026-09-20", ma_bc2="62/2025")      # BC2 cũ đã đóng → vẫn sẵn sàng
    them("A-0004", KHOA_A, "09", "2026-09-20", giay="")              # thiếu số giấy
    them("A-0005", KHOA_A, "03", "2026-09-20", giay="")              # chưa tốt nghiệp
    them("A-0006", KHOA_A, "18", "2026-09-20", ma_bc2="62/2025")     # thi lại cùng khóa
    them("B-0001", KHOA_B, "17", "2026-01-15", ma_bc2="62/2025")     # thi lại khóa khác (9 tháng)
    them("B-0002", KHOA_B, "09", "2026-01-15")                        # sẵn sàng của khóa B, KHÔNG hiện ở khóa A
    them("C-0001", KHOA_CU, "18", "2024-10-01")                       # thi lại quá hạn 12 tháng
    return sp, bs


def cur_oto(**kw):
    sp, bs = du_lieu_oto()
    return FakeCur(
        sp=sp, bo_sung=bs,
        khoa=khoa_row(KHOA_A),
        bc1=[{"MaBCI": "A857/26-TTTĐ", "MaKH": KHOA_A, "SoBaoCao": "857/26-TTTĐ", "SoHocSinh": 150},
             {"MaBCI": "B600/25-TTTĐ", "MaKH": KHOA_B, "SoBaoCao": "600/25-TTTĐ", "SoHocSinh": 80}],
        bc2=[{"MaBCII": "62/2025", "MaBCI": "B600/25-TTTĐ", "SoBaoCao": "62/2025", "TrangThai": 1, "TongSoThiSinh": 30},
             {"MaBCII": "75/2026", "MaBCI": "A857/26-TTTĐ", "SoBaoCao": "75/2026", "TrangThai": 0, "TongSoThiSinh": 42}],
        khoa_all=[khoa_row(KHOA_A), khoa_row(KHOA_B, bg="2026-01-15"), khoa_row(KHOA_CU, bg="2024-10-01"),
                  khoa_row(KHOA_MOTO, hang="A1", bg="2026-09-01"), khoa_row("75032K270001", bg="2026-12-31")],
        **kw)


@pytest.fixture(autouse=True)
def _xoa_cache():
    svc.bo_cache()
    yield
    svc.bo_cache()


def tap_oto():
    cur = cur_oto()
    return svc.lay_tap(factory(cur), "oto", HOM_NAY), cur


# ── Đọc: đúng SP, đúng tham số, một lần, không ghi ──
def test_goi_sp_mot_lan_voi_ma_kh_rong_va_hang_dt_theo_loai():
    tap, cur = tap_oto()
    sp_calls = [c for c in cur.log if c[0].startswith("EXEC usp_NguoiLX_HoSo_ThemHS_BC2")]
    assert len(sp_calls) == 1
    assert sp_calls[0][1] == ("", "", "", "", "", "", "", 0, "")          # @MaKH='' ; ô tô → @HangDT=''
    cur_m = FakeCur(sp=[], bo_sung=[])
    svc.lay_tap(factory(cur_m), "moto", HOM_NAY)
    assert [c for c in cur_m.log if c[0].startswith("EXEC")][0][1][6] == "A1"


def test_khong_co_cau_ghi_nao():
    _, cur = tap_oto()
    for sql, _p in cur.log:
        up = sql.upper()
        assert not any(k in up for k in ("INSERT ", "UPDATE ", "DELETE ")), sql
        assert up.startswith("EXEC USP_NGUOILX_HOSO_THEMHS_BC2") or up.startswith("SELECT"), sql


def test_cot_bo_sung_duoc_gan_vao_hv_va_so_giay_lay_ban_goc():
    tap, _ = tap_oto()
    hv = next(h for h in tap["hvs"] if h["ma_dk"] == "A-0001")
    assert hv["tt"] == "09" and hv["hang"] == "B2" and hv["bg"] == "2026-09-20" and hv["so_giay"] == "N1|7282"
    assert tap["bc2_map"] == {"62/2025": 1, "75/2026": 0}
    assert tap["bc1_theo_khoa"][KHOA_A]["so_bao_cao"] == "857/26-TTTĐ"


def test_cache_30_giay_va_lam_tuoi():
    cur = cur_oto()
    t = [100.0]
    now = lambda: t[0]   # noqa: E731
    svc.lay_tap(factory(cur), "oto", HOM_NAY, now=now)
    t[0] = 129.0
    svc.lay_tap(factory(cur), "oto", HOM_NAY, now=now)
    assert sum(c[0].startswith("EXEC") for c in cur.log) == 1          # còn trong 30 giây → dùng cache
    t[0] = 131.5
    svc.lay_tap(factory(cur), "oto", HOM_NAY, now=now)
    assert sum(c[0].startswith("EXEC") for c in cur.log) == 2          # quá 30 giây → đọc lại
    svc.lay_tap(factory(cur), "oto", HOM_NAY, lam_tuoi=True, now=now)
    assert sum(c[0].startswith("EXEC") for c in cur.log) == 3          # làm tươi → bỏ cache
    svc.bo_cache()
    svc.lay_tap(factory(cur), "oto", HOM_NAY, now=now)
    assert sum(c[0].startswith("EXEC") for c in cur.log) == 4


def test_hv_bien_mat_giua_hai_truy_van_bi_bo():
    sp, bs = du_lieu_oto()
    cur = FakeCur(sp=sp, bo_sung=[b for b in bs if b["MaDK"] != "A-0001"], khoa=khoa_row(KHOA_A))
    tap = svc.lay_tap(factory(cur), "oto", HOM_NAY)
    assert "A-0001" not in {h["ma_dk"] for h in tap["hvs"]}


def test_chia_khoi_in_khi_nhieu_hv():
    sp = [sp_row(f"X-{i:05d}", KHOA_A) for i in range(2000)]
    bs = [bs_row(f"X-{i:05d}", "09") for i in range(2000)]
    cur = FakeCur(sp=sp, bo_sung=bs)
    tap = svc.lay_tap(factory(cur), "oto", HOM_NAY)
    n_select = [c for c in cur.log if "WHERE h.MaDK IN" in c[0]]
    assert len(tap["hvs"]) == 2000 and len(n_select) == 3 and all(len(c[1]) <= 900 for c in n_select)


# ── Bước ①: khoa-san-sang ──
def test_khoa_san_sang_dem_tu_tap_da_tai_va_khoa_chua_co_bc1():
    tap, cur = tap_oto()
    kq = svc.khoa_san_sang(tap, "oto")
    theo = {k["ma_kh"]: k for k in kq["khoa"]}
    a = theo[KHOA_A]
    assert (a["san_sang"], a["can_xem"], a["thi_lai_cua_khoa"]) == (3, 2, 1)
    assert a["co_bc1"] is True and a["so_bc1"] == "857/26-TTTĐ"
    assert {b["ma"] for b in a["bc2_cua_khoa"]} == {"75/2026"}
    assert theo[KHOA_B]["san_sang"] == 1 and theo[KHOA_B]["thi_lai_cua_khoa"] == 1
    # thi lại tính bất kể khóa: tổng 3 HV (A-0006, B-0001, C-0001); trong 12 tháng: A-0006 (0), B-0001 (9) → 2
    assert kq["thi_lai_tat_ca"] == 3 and a["thi_lai"] == 2 and theo[KHOA_B]["thi_lai"] == 2
    # không gọi SP thêm lần nào cho từng khóa
    assert sum(c[0].startswith("EXEC") for c in cur.log) == 1


def test_khoa_san_sang_cua_so_13_thang_va_cong_tac_khoa_cu():
    tap, _ = tap_oto()
    mac_dinh = {k["ma_kh"] for k in svc.khoa_san_sang(tap, "oto")["khoa"]}
    assert KHOA_CU not in mac_dinh and KHOA_A in mac_dinh
    cu = {k["ma_kh"]: k for k in svc.khoa_san_sang(tap, "oto", cu=True)["khoa"]}
    assert KHOA_CU in cu and cu[KHOA_CU]["khoa_cu"] is True and cu[KHOA_CU]["thi_lai_cua_khoa"] == 1


def test_khoa_san_sang_khong_hien_khoa_chua_be_giang_hay_khac_loai():
    tap, _ = tap_oto()
    ma = {k["ma_kh"] for k in svc.khoa_san_sang(tap, "oto", cu=True)["khoa"]}
    assert "75032K270001" not in ma and KHOA_MOTO not in ma


def test_khoa_khong_co_bc1_hien_co_bc1_false():
    sp, bs = du_lieu_oto()
    cur = FakeCur(sp=sp, bo_sung=bs, khoa_all=[khoa_row(KHOA_A)])   # không có BC1 nào
    tap = svc.lay_tap(factory(cur), "oto", HOM_NAY)
    a = svc.khoa_san_sang(tap, "oto")["khoa"][0]
    assert a["co_bc1"] is False and a["so_bc1"] == "" and a["bc2_cua_khoa"] == []


def test_moc_cua_so_khoa():
    assert svc.moc_cua_so_khoa("2026-10-11") == "2025-09-11"
    assert svc.moc_cua_so_khoa("2026-01-31") == "2024-12-31"
    assert svc.moc_cua_so_khoa("2026-03-31") == "2025-02-28"


# ── Bước ②: ung-vien ──
KHOA_CHON_A = {"ma_kh": KHOA_A, "ten_kh": "Khóa K007", "loai": "oto", "bg": "2026-09-20"}


def test_ung_vien_bon_nhom_va_dem():
    tap, _ = tap_oto()
    kq = svc.ung_vien(tap, KHOA_CHON_A)
    nhom = {k: sorted(x["ma_dk"] for x in v) for k, v in kq["nhom"].items()}
    assert nhom["san_sang"] == ["A-0001", "A-0002", "A-0003"]
    assert nhom["can_xem"] == ["A-0004", "A-0005"]
    assert nhom["thi_lai"] == ["A-0006", "B-0001", "C-0001"]
    assert "B-0002" not in sum(nhom.values(), [])           # 09 của khóa khác không hiện
    assert kq["dem"]["san_sang"] == 3 and kq["dem"]["thi_lai_trong_nguong"] == 2
    san = {x["ma_dk"]: x for x in kq["nhom"]["san_sang"]}
    assert san["A-0001"]["tich_san"] is True
    xem = {x["ma_dk"]: x for x in kq["nhom"]["can_xem"]}
    assert xem["A-0004"]["goi_y_xu_ly"] == rules.GOI_Y_TOT_NGHIEP and xem["A-0005"]["ma_ly_do"] == "chua_tot_nghiep"
    thi = {x["ma_dk"]: x for x in kq["nhom"]["thi_lai"]}
    assert all(not x["tich_san"] for x in thi.values())
    assert thi["C-0001"]["tuoi_thang"] == 24 and thi["C-0001"]["trong_nguong"] is False  # quá hạn nhưng VẪN trả
    assert kq["bc1"]["so_bao_cao"] == "857/26-TTTĐ"


def test_thi_lai_thang_chi_doi_co_trong_nguong_khong_an_hv():
    tap, _ = tap_oto()
    kq6 = svc.ung_vien(tap, KHOA_CHON_A, thi_lai_thang=6)
    assert len(kq6["nhom"]["thi_lai"]) == 3 and kq6["dem"]["thi_lai_trong_nguong"] == 1   # chỉ A-0006 (0 tháng)


def test_hv_o_bc2_mo_khac_la_khong_duoc_kem_ly_do_go():
    tap, cur = tap_oto()
    kd = [{"ma_dk": "A-0100", "so_ho_so": "9", "ten": "Trần B", "ngay_sinh": "01/01/1999", "cmt": "079199000100",
           "so_giay": "N1|1", "hang": "B2", "ma_kh": KHOA_A, "ten_kh": "Khóa K007", "tt": "11", "ma_bc2": "75/2026",
           "bg": "2026-09-20"},
          {"ma_dk": "A-0101", "so_ho_so": "10", "ten": "Lê C", "ngay_sinh": "", "cmt": "", "so_giay": "N1|2",
           "hang": "B2", "ma_kh": KHOA_A, "ten_kh": "Khóa K007", "tt": "16", "ma_bc2": "62/2025", "bg": "2026-09-20"}]
    kq = svc.ung_vien(tap, KHOA_CHON_A, khong_duoc_them=kd)
    khong = {x["ma_dk"]: x for x in kq["nhom"]["khong_duoc"]}
    assert khong["A-0100"]["ma_ly_do"] == "dang_o_bc2_mo" and khong["A-0100"]["goi_y_xu_ly"] == rules.GOI_Y_GO_BC2
    assert "75/2026" in khong["A-0100"]["ly_do"]
    assert khong["A-0101"]["ma_ly_do"] == "co_ket_qua_cuoi"
    assert kq["dem"]["khong_duoc"] == 2


def test_hv_dang_o_chinh_bc2_dang_them_khong_hien_lai():
    tap, _ = tap_oto()
    kd = [{"ma_dk": "A-0100", "so_ho_so": "9", "ten": "Trần B", "ngay_sinh": "", "cmt": "079199000100",
           "so_giay": "N1|1", "hang": "B2", "ma_kh": KHOA_A, "ten_kh": "Khóa K007", "tt": "11", "ma_bc2": "75/2026",
           "bg": "2026-09-20"}]
    kq = svc.ung_vien(tap, KHOA_CHON_A, ma_bc2="75/2026", khong_duoc_them=kd)
    assert kq["nhom"]["khong_duoc"] == []


def test_tran_khong_duoc():
    tap, _ = tap_oto()
    kd = [{"ma_dk": f"K-{i:04d}", "so_ho_so": "", "ten": "X", "ngay_sinh": "", "cmt": "", "so_giay": "", "hang": "B2",
           "ma_kh": KHOA_A, "ten_kh": "K", "tt": "16", "ma_bc2": "62/2025", "bg": "2026-09-20"}
          for i in range(svc.TOI_DA_KHONG_DUOC + 40)]
    kq = svc.ung_vien(tap, KHOA_CHON_A, khong_duoc_them=kd)
    assert len(kq["nhom"]["khong_duoc"]) == svc.TOI_DA_KHONG_DUOC
    assert kq["dem"]["khong_duoc"] == svc.TOI_DA_KHONG_DUOC + 40      # đếm đủ dù cắt trần danh sách


def test_loai_cua_khoa():
    cur = cur_oto()
    assert svc.loai_cua_khoa(cur, KHOA_A)["loai"] == "oto"
    cur_m = FakeCur(khoa=khoa_row(KHOA_MOTO, hang="A1"))
    assert svc.loai_cua_khoa(cur_m, KHOA_MOTO)["loai"] == "moto"
    with pytest.raises(svc.LoiNghiepVu) as e:
        svc.loai_cua_khoa(cur_m, "khong-co")
    assert e.value.http == 404


def test_doc_khong_duoc_cua_khoa_dinh_dang_ngay_sinh_va_loc_theo_khoa():
    cur = FakeCur(khong_duoc=[
        {"MaDK": "A-0100", "SoHoSo": "9", "HoVaTen": "Trần B", "NgaySinh": "19990131", "SoCMT": "079199000100",
         "SoGiayCNTN": "N1|1", "HangGPLX": "B2", "TT_XuLy": "11", "MaBC2": "75/2026", "MaKhoaHoc": KHOA_A,
         "TenKH": "Khóa K007", "NgayBG": "2026-09-20"},
        {"MaDK": "Z-1", "SoHoSo": "1", "HoVaTen": "Khác", "NgaySinh": "", "SoCMT": "", "SoGiayCNTN": "", "HangGPLX": "B2",
         "TT_XuLy": "11", "MaBC2": "x", "MaKhoaHoc": KHOA_B, "TenKH": "K", "NgayBG": "2026-01-15"}])
    out = svc.doc_ngoai_tap_cua_khoa(cur, KHOA_A)
    assert len(out) == 1 and out[0]["ngay_sinh"] == "31/01/1999" and out[0]["tt"] == "11"


# ── Dán danh sách ──
def test_khop_danh_sach_theo_cmt_va_ma_dk_va_bao_khong_khop():
    tap, _ = tap_oto()
    ds = [cmt_cua("A-0001"), "a-0002", "999999999999", "", cmt_cua("A-0004")]
    kq = svc.khop_danh_sach(tap, KHOA_CHON_A, ds)
    assert kq["tong_dong"] == 4
    assert {x["ma_dk"] for x in kq["khop"]} == {"A-0001", "A-0002"}
    assert kq["khong_khop"] == ["999999999999"]
    # A-0004 (09 thiếu số giấy → can_xem) khớp nhưng không tích được
    assert [x["ma_dk"] for x in kq["khong_dua_duoc"]] == ["A-0004"]
    assert kq["khong_dua_duoc"][0]["ma_ly_do"] == "thieu_so_giay"


def test_khop_danh_sach_hv_khoa_khac_la_khong_dua_duoc_khac_khoa_va_khong_trung_lap():
    tap, _ = tap_oto()
    kq = svc.khop_danh_sach(tap, KHOA_CHON_A, [cmt_cua("A-0001"), cmt_cua("A-0001"), "B-0002", cmt_cua("A-0006")])
    assert [x["ma_dk"] for x in kq["khop"]] == ["A-0001", "A-0006"]          # A-0001 chỉ một lần; A-0006 thi lại
    assert kq["khong_dua_duoc"][0]["ma_dk"] == "B-0002" and kq["khong_dua_duoc"][0]["ma_ly_do"] == "khac_khoa"


def test_khop_danh_sach_gioi_han_dau_vao():
    tap, _ = tap_oto()
    with pytest.raises(svc.LoiNghiepVu) as e:
        svc.khop_danh_sach(tap, KHOA_CHON_A, ["1"] * 5001)
    assert e.value.ma == "qua_nhieu_dong"
    with pytest.raises(svc.LoiNghiepVu) as e:
        svc.khop_danh_sach(tap, KHOA_CHON_A, ["x" * 41])
    assert e.value.ma == "dong_qua_dai"


# ── Router ──
class _Client:
    """TestClient gắn sẵn header session operator giả (fixture `auth_headers`)."""

    def __init__(self, c, h):
        self._c, self._h = c, h

    def get(self, url, **kw):
        return self._c.get(url, headers=self._h, **kw)

    def post(self, url, **kw):
        return self._c.post(url, headers=self._h, **kw)


@pytest.fixture
def client(monkeypatch, auth_headers):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.routers import tn_bc2 as router

    cur = cur_oto(khong_duoc=[{
        "MaDK": "A-0100", "SoHoSo": "9", "HoVaTen": "Trần B", "NgaySinh": "19990131", "SoCMT": "079199000100",
        "SoGiayCNTN": "N1|1", "HangGPLX": "B2", "TT_XuLy": "11", "MaBC2": "75/2026", "MaKhoaHoc": KHOA_A,
        "TenKH": "Khóa K007", "NgayBG": "2026-09-20"}])
    monkeypatch.setattr(router, "sqlserver_cursor", factory(cur))
    monkeypatch.setattr(svc, "hom_nay_iso", lambda: HOM_NAY)
    return _Client(TestClient(app), auth_headers), cur


def test_router_can_session(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    assert c.get("/local/tnbc2/bc2/khoa-san-sang", params={"loai": "oto"}).status_code in (401, 403)


def test_router_khoa_san_sang_ung_vien_khop(client):
    c, cur = client
    r = c.get("/local/tnbc2/bc2/khoa-san-sang", params={"loai": "oto"})
    assert r.status_code == 200
    ds = {k["ma_kh"]: k for k in r.json()["khoa"]}
    assert ds[KHOA_A]["san_sang"] == 3

    r = c.get("/local/tnbc2/bc2/ung-vien", params={"ma_kh": KHOA_A})
    assert r.status_code == 200
    j = r.json()
    assert j["loai"] == "oto" and j["dem"]["san_sang"] == 3 and j["dem"]["khong_duoc"] == 1
    assert j["nhom"]["khong_duoc"][0]["ma_ly_do"] == "dang_o_bc2_mo"

    r = c.post("/local/tnbc2/bc2/khop-danh-sach", json={"ma_kh": KHOA_A, "dong": [cmt_cua("A-0001"), "nope"]})
    assert r.status_code == 200 and r.json()["so_khop"] == 1 and r.json()["khong_khop"] == ["nope"]
    # SP chỉ chạy một lần dù gọi 3 endpoint (cache)
    assert sum(x[0].startswith("EXEC") for x in cur.log) == 1


def test_router_loi_bc2_va_khoa(client):
    c, _ = client
    assert c.get("/local/tnbc2/bc2/ung-vien", params={"ma_kh": "khong-co"}).status_code == 404
    r = c.get("/local/tnbc2/bc2/ung-vien", params={"ma_kh": KHOA_B, "ma_bc2": "62/2025"})
    assert r.status_code == 409 and r.json()["detail"]["ma"] == "bc2_da_dong"
    r = c.get("/local/tnbc2/bc2/ung-vien", params={"ma_kh": KHOA_A, "ma_bc2": "62/2025"})     # BC2 của khóa B
    assert r.status_code == 409 and r.json()["detail"]["ma"] == "bc2_khac_khoa"
    r = c.get("/local/tnbc2/bc2/ung-vien", params={"ma_kh": KHOA_CU})                         # khóa chưa có BC1
    assert r.status_code == 409 and r.json()["detail"]["ma"] == "khoa_chua_co_bc1"
    r = c.get("/local/tnbc2/bc2/ung-vien", params={"ma_kh": KHOA_A, "ma_bc2": "999/2020"})
    assert r.status_code == 404 and r.json()["detail"]["ma"] == "bc2_khong_ton_tai"
    r = c.get("/local/tnbc2/bc2/ung-vien", params={"ma_kh": KHOA_A, "ma_bc2": "75/2026"})
    assert r.status_code == 200 and r.json()["ma_bc2"] == "75/2026"
    r = c.post("/local/tnbc2/bc2/khop-danh-sach", json={"ma_kh": KHOA_A, "dong": ["1"] * 5001})
    assert r.status_code == 400 and r.json()["detail"]["ma"] == "qua_nhieu_dong"
    assert c.get("/local/tnbc2/bc2/khoa-san-sang", params={"loai": "xe"}).status_code == 422


# ── Kiểm đầu vào + phạm vi "Không đưa được" ──
def test_kiem_dau_vao():
    tap, _ = tap_oto()
    svc.kiem_dau_vao(tap, KHOA_A, "")                       # chưa có BC2, khóa có BC1 → ok
    svc.kiem_dau_vao(tap, KHOA_A, "75/2026")                # BC2 mở thuộc đúng khóa → ok
    for ma_kh, ma_bc2, ma, http in [(KHOA_CU, "", "khoa_chua_co_bc1", 409), (KHOA_A, "999/2020", "bc2_khong_ton_tai", 404),
                                    (KHOA_A, "62/2025", "bc2_khac_khoa", 409), (KHOA_B, "62/2025", "bc2_da_dong", 409),
                                    (KHOA_B, "75/2026", "bc2_khac_khoa", 409), (KHOA_CU, "75/2026", "bc2_khac_khoa", 409)]:
        with pytest.raises(svc.LoiNghiepVu) as e:
            svc.kiem_dau_vao(tap, ma_kh, ma_bc2)
        assert (e.value.ma, e.value.http) == (ma, http), (ma_kh, ma_bc2)


def test_khong_duoc_chi_cua_khoa_chon_va_tran_khong_cat_nham_hv_khoa_chon():
    """HV khóa KHÁC bị khong_duoc (vd khóa chưa bế giảng) không được chiếm chỗ trong trần 500 của
    nhóm Không đưa được của khóa đang chọn."""
    sp, bs = du_lieu_oto()
    for i in range(700):      # 700 HV khóa chưa bế giảng đứng TRƯỚC trong danh sách SP
        sp.insert(0, sp_row(f"F-{i:04d}", "75032K270001"))
        bs.insert(0, bs_row(f"F-{i:04d}", "09", bg="2026-12-31"))
    cur = FakeCur(sp=sp, bo_sung=bs, khoa=khoa_row(KHOA_A),
                  bc1=[{"MaBCI": "A857/26-TTTĐ", "MaKH": KHOA_A, "SoBaoCao": "857/26-TTTĐ", "SoHocSinh": 150}])
    tap = svc.lay_tap(factory(cur), "oto", HOM_NAY)
    ngoai = [{"ma_dk": "A-0100", "so_ho_so": "9", "ten": "Trần B", "ngay_sinh": "", "cmt": "079199000100",
              "so_giay": "N1|1", "hang": "B2", "ma_kh": KHOA_A, "ten_kh": "K", "tt": "11", "ma_bc2": "75/2026",
              "bg": "2026-09-20"}]
    kq = svc.ung_vien(tap, KHOA_CHON_A, khong_duoc_them=ngoai)
    assert [x["ma_dk"] for x in kq["nhom"]["khong_duoc"]] == ["A-0100"]
    assert kq["dem"]["khong_duoc"] == 1


def test_trang_thai_la_cua_khoa_chon_la_can_xem_kem_goi_y_cuu():
    tap, _ = tap_oto()
    ngoai = [{"ma_dk": "A-0200", "so_ho_so": "11", "ten": "Phạm D", "ngay_sinh": "", "cmt": "079199000200",
              "so_giay": "", "hang": "B2", "ma_kh": KHOA_A, "ten_kh": "K", "tt": "12", "ma_bc2": "", "bg": "2026-09-20"},
             {"ma_dk": "A-0201", "so_ho_so": "12", "ten": "Vũ E", "ngay_sinh": "", "cmt": "079199000201",
              "so_giay": "", "hang": "B2", "ma_kh": KHOA_A, "ten_kh": "K", "tt": "05", "ma_bc2": "", "bg": "2026-09-20"}]
    kq = svc.ung_vien(tap, KHOA_CHON_A, khong_duoc_them=ngoai)
    xem = {x["ma_dk"]: x for x in kq["nhom"]["can_xem"]}
    assert xem["A-0200"]["ma_ly_do"] == "trang_thai_la" and xem["A-0200"]["goi_y_xu_ly"] == rules.GOI_Y_CUU
    khong = {x["ma_dk"]: x for x in kq["nhom"]["khong_duoc"]}
    assert khong["A-0201"]["ma_ly_do"] == "trang_thai_ngoai_tap"      # mã lạ không cứu được → không đưa được
