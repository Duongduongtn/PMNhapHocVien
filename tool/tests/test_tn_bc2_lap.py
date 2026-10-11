"""TNB-04 (3/6) — task 99: lập BC2 + thêm HV + hoàn tác + chạy nền idempotent.

Kết nối giả mô phỏng đúng hành vi các SP của DB Nạp (đã đọc định nghĩa 11/10/2026):
`usp_NguoiLX_Update_ThemHSBC2` (KHÔNG có điều kiện: MaBC2, TT_XuLy='11', TT_XuLy_Old = cũ) và
`usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2 @TrangThaiXuLy=101` (TT_XuLy = TT_XuLy_Old, MaBC2='').
Khóa các bất biến: thứ tự khóa→đọc lại→Insert→từng HV, "Làm tiếp" KHÔNG gọi lại SP với HV đã 11
đúng BC2, BC2 đóng giữa chừng không ghi, HV đổi giữa chừng bị bỏ qua, `lo_id` idempotent, hoàn tác
đúng lô gần nhất của BC2 một lần.
"""
from contextlib import contextmanager
from datetime import datetime

import pytest

from app import tn_bc2_nhat_ky as nk
from app import tn_bc2_service as svc

HOM_NAY = "2026-10-11"
NOW = datetime(2026, 10, 11, 9, 30, 15)
KHOA = "70004K26B0108"
KHOA_MOTO = "70004K26A1015"


def hv(tt="09", ma_kh=KHOA, hang="B2", ma_bc2="", giay="N1|7282", bg="2026-09-18", cu=""):
    return {"tt": tt, "tt_cu": cu, "ma_bc2": ma_bc2, "hang": hang, "giay": giay, "ma_kh": ma_kh, "bg": bg,
            "so_ho_so": "12"}


class FakeCur:
    def __init__(self, st):
        self.st = st

    def execute(self, sql, params=()):
        st, s = self.st, " ".join(sql.split())
        st.log.append((s, tuple(params)))
        if "sp_getapplock" in s:
            self._rows = [{"r": st.applock}]
        elif "sp_releaseapplock" in s:
            self._rows = []
        elif s.startswith("SELECT MaKH, TenKH, HangGPLX, NgayBG FROM KhoaHoc WHERE MaKH"):
            self._rows = [k for k in st.khoa if k["MaKH"] == params[0]]
        elif s.startswith("SELECT MaBCI, MaKH"):
            self._rows = st.bc1
        elif s.startswith("SELECT MaBCII, MaBCI, SoBaoCao"):
            self._rows = st.bc2
        elif s.startswith("EXEC usp_BaoCaoII_Insert"):
            p = params
            st.bc2.append({"MaBCII": p[0], "MaBCI": p[1], "SoBaoCao": p[3], "TrangThai": False, "TongSoThiSinh": p[5]})
            self._rows = []
        elif s.startswith("SELECT MaBCII, MaBCI, TrangThai, TongSoThiSinh FROM BaoCaoII WHERE MaBCII"):
            self._rows = [r for r in st.bc2 if r["MaBCII"] == params[0]]
        elif "WHERE h.MaDK IN" in s:
            self._rows = [self._hv_row(m) for m in params if m in st.hv]
        elif s.startswith("SELECT TT_XuLy, TT_XuLy_Old, MaBC2, SoHoSo FROM NguoiLX_HoSo WHERE MaDK"):
            ma = params[0]
            if ma in st.doi_truoc_sp:                      # PM cũ đổi HV ngay trước khi tool ghi
                st.hv[ma].update(st.doi_truoc_sp.pop(ma))
            h = st.hv.get(ma)
            self._rows = [{"TT_XuLy": h["tt"], "TT_XuLy_Old": h["tt_cu"], "MaBC2": h["ma_bc2"],
                           "SoHoSo": h["so_ho_so"]}] if h else []
        elif s.startswith("EXEC usp_NguoiLX_Update_ThemHSBC2"):
            ma, so_hs, ma_bc2 = params
            assert len(so_hs) <= 5                         # @SoHoSo varchar(5)
            if ma in st.loi_sp:
                raise RuntimeError("mất kết nối")
            h = st.hv[ma]
            h["tt_cu"], h["tt"], h["ma_bc2"] = h["tt"], "11", ma_bc2     # đúng SP: không điều kiện
            if ma in st.old_la_11:
                h["tt_cu"] = "11"
            self._rows = []
        elif s.startswith("EXEC usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2"):
            ma, _so, _bc2, kieu = params
            assert kieu == 101
            h = st.hv[ma]
            h["tt"], h["ma_bc2"] = h["tt_cu"], ""
            self._rows = []
        else:
            raise AssertionError("câu lệnh lạ: " + s)

    def _hv_row(self, ma):
        h = self.st.hv[ma]
        return {"MaDK": ma, "SoHoSo": h["so_ho_so"], "TT_XuLy": h["tt"], "TT_XuLy_Old": h["tt_cu"], "MaBC2": h["ma_bc2"],
                "HangGPLX": h["hang"], "SoGiayCNTN": h["giay"], "MaKhoaHoc": h["ma_kh"], "TenKH": "K", "NgayBG": h["bg"]}

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class FakeConn:
    def __init__(self, hvs, bc2=None, applock=0):
        self.log, self.applock = [], applock
        self.hv = {k: dict(v) for k, v in hvs.items()}
        self.doi_truoc_sp, self.loi_sp, self.old_la_11 = {}, set(), set()
        self.khoa = [
            {"MaKH": KHOA, "TenKH": "B.01K40", "HangGPLX": "B2", "NgayBG": "2026-09-18"},
            {"MaKH": KHOA_MOTO, "TenKH": "A1K126", "HangGPLX": "A1", "NgayBG": "2026-10-06"},
        ]
        self.bc1 = [
            {"MaBCI": "858/26-TTTÐ", "MaKH": KHOA, "MaCSDT": "70004", "SoBaoCao": "858/26-TTTĐ", "SoHocSinh": 40},
            {"MaBCI": "A1A2870/26-TTTÐ", "MaKH": KHOA_MOTO, "MaCSDT": "70004", "SoBaoCao": "A1A2870/26-TTTĐ",
             "SoHocSinh": 150},
        ]
        self.bc2 = [dict(b) for b in (bc2 if bc2 is not None else [
            {"MaBCII": "76/2026", "MaBCI": "858/26-TTTÐ", "SoBaoCao": "76/2026", "TrangThai": False, "TongSoThiSinh": 24},
            {"MaBCII": "62/2025", "MaBCI": "600/25-TTTÐ", "SoBaoCao": "62/2025", "TrangThai": True, "TongSoThiSinh": 30},
        ])]

    def cursor(self, as_dict=True):
        return FakeCur(self)

    def goi(self, prefix):
        return [(s, p) for s, p in self.log if s.startswith(prefix)]

    @property
    def sp_them(self):
        return self.goi("EXEC usp_NguoiLX_Update_ThemHSBC2")


@contextmanager
def _ctx(conn):
    yield conn


@pytest.fixture(autouse=True)
def _co_lap(tmp_path, monkeypatch):
    monkeypatch.setattr(nk, "DB_PATH", tmp_path / "tnbc2_nhat_ky.sqlite")
    svc.bo_cache()
    yield
    svc.bo_cache()
    with svc._JOBS_KHOA:
        svc._JOBS.clear()


def hvs_oto(n=3):
    return {f"D-{i:04d}": hv("09") for i in range(1, n + 1)}


def lap(conn, ds, lo_id="lo-0000001", ma_bc2="", so="81/2026", **kw):
    return svc.lap_bc2(conn, lo_id=lo_id, ma_kh=kw.pop("ma_kh", KHOA), ma_bc2=ma_bc2, so_bao_cao=so,
                       ngay_bao_cao="2026-10-11", ghi_chu="", ds_ma_dk=ds, nguoi=kw.pop("nguoi", "thu1"),
                       hom_nay=HOM_NAY, now=NOW, **kw)


# ── Lập BC2 mới + thêm ──
def test_lap_bc2_moi_oto_thu_tu_va_tham_so():
    c = FakeConn(hvs_oto(3))
    kq = lap(c, ["D-0001", "D-0002", "D-0003"])
    assert kq["trang_thai"] == "xong" and kq["da_tao_bc2"] is True and kq["ma_bc2"] == "81/2026"
    assert kq["da_them"] == ["D-0001", "D-0002", "D-0003"] and kq["bo_qua"] == [] and kq["chua_ghi"] == []
    ins = c.goi("EXEC usp_BaoCaoII_Insert")
    assert len(ins) == 1 and ins[0][1][5] == 3                       # TongSoThiSinh = số HV còn lại, tính TRƯỚC khi thêm
    assert [p for _s, p in c.sp_them] == [("D-0001", "12", "81/2026"), ("D-0002", "12", "81/2026"),
                                          ("D-0003", "12", "81/2026")]
    # thứ tự: khóa → đọc lại → Insert → SP từng HV → nhả khóa
    ds = [s for s, _ in c.log]
    i_k = next(i for i, s in enumerate(ds) if "sp_getapplock" in s)
    i_i = next(i for i, s in enumerate(ds) if s.startswith("EXEC usp_BaoCaoII_Insert"))
    i_h = next(i for i, s in enumerate(ds) if s.startswith("EXEC usp_NguoiLX_Update_ThemHSBC2"))
    i_n = next(i for i, s in enumerate(ds) if "sp_releaseapplock" in s)
    assert i_k < i_i < i_h < i_n
    assert any("WHERE h.MaDK IN" in s for s in ds[i_k:i_i])           # đọc lại cả lô trước khi tạo BC2
    for s in ds:
        assert not any(k in s.upper() for k in ("INSERT INTO", "UPDATE ", "DELETE FROM")), s
    assert all(c.hv[m]["tt"] == "11" and c.hv[m]["ma_bc2"] == "81/2026" and c.hv[m]["tt_cu"] == "09" for m in kq["da_them"])


def test_bc2_co_san_khong_insert_va_bo_qua_hv_khong_hop_le():
    hvs = hvs_oto(2)
    hvs["X-0001"] = hv("11", ma_bc2="76/2026")                        # đang ở BC2 mở (cùng BC2 → đã có)
    hvs["X-0002"] = hv("11", ma_bc2="75/2026")                        # BC2 mở khác không tồn tại trong fake → như đóng
    hvs["X-0003"] = hv("03", giay="")                                 # ô tô chưa tốt nghiệp → can_xem
    hvs["X-0004"] = hv("09", hang="A1")                               # sai loại
    hvs["X-0005"] = hv("16")                                          # đã có kết quả cuối
    hvs["X-0006"] = hv("09", ma_kh="70004K26B9999", bg="2026-12-31")  # khóa chưa bế giảng
    c = FakeConn(hvs)
    kq = lap(c, ["D-0001", "D-0002", "X-0001", "X-0002", "X-0003", "X-0004", "X-0005", "X-0006", "KHONG-CO"],
             ma_bc2="76/2026")
    assert c.goi("EXEC usp_BaoCaoII_Insert") == [] and kq["da_tao_bc2"] is False
    assert kq["da_them"] == ["D-0001", "D-0002"] and kq["da_co_tu_truoc"] == ["X-0001"]
    ly = {b["ma_dk"]: b["ma_ly_do"] for b in kq["bo_qua"]}
    assert ly == {"X-0002": "da_vao_bc2_dong", "X-0003": "chua_tot_nghiep", "X-0004": "sai_loai",
                  "X-0005": "co_ket_qua_cuoi", "X-0006": "khoa_chua_be_giang", "KHONG-CO": "hv_khong_ton_tai"}
    assert [p[0] for _s, p in c.sp_them] == ["D-0001", "D-0002"]      # không SP nào cho HV bị bỏ qua


def test_thi_lai_khoa_khac_duoc_them_va_giu_tt_cu():
    hvs = {"T-0001": hv("17", ma_kh="70004K25B0001", bg="2025-12-01", ma_bc2="62/2025", cu="13")}
    c = FakeConn(hvs)
    kq = lap(c, ["T-0001"], ma_bc2="76/2026")
    assert kq["da_them"] == ["T-0001"]
    assert c.hv["T-0001"]["tt_cu"] == "17" and c.hv["T-0001"]["ma_bc2"] == "76/2026"


def test_moto_tong_so_thi_sinh_la_so_hoc_sinh_bc1():
    hvs = {"M-0001": hv("03", ma_kh=KHOA_MOTO, hang="A1", giay="", bg="2026-10-06")}
    c = FakeConn(hvs)
    kq = lap(c, ["M-0001"], ma_kh=KHOA_MOTO, so="870/26-TTTĐ")
    assert kq["trang_thai"] == "xong" and c.goi("EXEC usp_BaoCaoII_Insert")[0][1][5] == 150


# ── Chặn cả lô ──
def test_bc2_da_dong_hoac_khac_khoa_hoac_khong_co_hv_hop_le_khong_ghi_gi():
    c = FakeConn(hvs_oto(2))
    for ma_bc2, ma in (("62/2025", "bc2_khac_khoa"), ("999/2020", "bc2_khong_ton_tai")):
        with pytest.raises(svc.LoiNghiepVu) as e:
            lap(c, ["D-0001"], ma_bc2=ma_bc2)
        assert e.value.ma == ma
    c2 = FakeConn(hvs_oto(1), bc2=[{"MaBCII": "76/2026", "MaBCI": "858/26-TTTÐ", "SoBaoCao": "76/2026",
                                    "TrangThai": True, "TongSoThiSinh": 24}])
    with pytest.raises(svc.LoiNghiepVu) as e:
        lap(c2, ["D-0001"], ma_bc2="76/2026")
    assert e.value.ma == "bc2_da_dong"
    c3 = FakeConn({"X-0001": hv("16")})
    with pytest.raises(svc.LoiNghiepVu) as e:
        lap(c3, ["X-0001"])                                           # chưa có BC2, không HV nào hợp lệ → không tạo BC2 rỗng
    assert e.value.ma == "khong_co_hoc_vien_hop_le"
    for conn in (c, c2, c3):
        assert conn.goi("EXEC usp_BaoCaoII_Insert") == [] and conn.sp_them == []
        assert len(conn.goi("EXEC sp_releaseapplock")) >= 1           # khóa luôn nhả


def test_khoa_ghi_ban_409_va_khong_ghi_gi():
    c = FakeConn(hvs_oto(1), applock=-1)
    with pytest.raises(svc.LoiNghiepVu) as e:
        lap(c, ["D-0001"])
    assert e.value.ma == "dang_ghi" and e.value.http == 409 and c.sp_them == []


def test_ds_rong_qua_nhieu_va_so_bc2_trung():
    c = FakeConn(hvs_oto(1))
    with pytest.raises(svc.LoiNghiepVu) as e:
        lap(c, [])
    assert e.value.ma == "khong_co_hoc_vien"
    with pytest.raises(svc.LoiNghiepVu) as e:
        lap(c, [f"X{i}" for i in range(5001)])
    assert e.value.ma == "qua_nhieu_dong"
    with pytest.raises(svc.LoiNghiepVu) as e:
        lap(c, ["D-0001"], so="76/2026")                              # số trùng BC2 có sẵn → chặn, không tạo
    assert e.value.ma == "trung_so" and c.sp_them == []
    assert nk.gan_day(nk.THEM_HV)[0]["trang_thai"] == "that_bai"     # nhật ký được đóng, không treo bat_dau


# ── Đọc lại sát trước SP ──
def test_hv_bi_pm_cu_doi_giua_chung_bi_bo_qua_khong_ghi_de():
    c = FakeConn(hvs_oto(3))
    c.doi_truoc_sp["D-0002"] = {"tt": "11", "ma_bc2": "75/2026"}     # PM cũ vừa đưa vào BC2 khác
    kq = lap(c, ["D-0001", "D-0002", "D-0003"], ma_bc2="76/2026")
    assert kq["da_them"] == ["D-0001", "D-0003"]
    assert kq["bo_qua"] == [{"ma_dk": "D-0002", "ma_ly_do": "doi_giua_chung",
                             "ly_do": "Phần mềm cũ vừa đổi học viên này — không ghi đè"}]
    assert c.hv["D-0002"]["ma_bc2"] == "75/2026"                      # nguyên vẹn


def test_canh_bao_trang_thai_cu_la_11_sau_ghi():
    c = FakeConn(hvs_oto(2))
    c.old_la_11.add("D-0002")
    kq = lap(c, ["D-0001", "D-0002"], ma_bc2="76/2026")
    assert [w["ma_dk"] for w in kq["canh_bao"]] == ["D-0002"] and kq["canh_bao"][0]["ma"] == "trang_thai_cu_la_11"


# ── Đứt giữa chừng + Làm tiếp + idempotent ──
def test_loi_giua_chung_tra_da_chua_ghi_roi_lam_tiep_khong_goi_lai_sp():
    c = FakeConn(hvs_oto(3))
    c.loi_sp.add("D-0002")
    k1 = lap(c, ["D-0001", "D-0002", "D-0003"])
    assert k1["trang_thai"] == "loi_giua_chung" and k1["da_them"] == ["D-0001"]
    assert k1["chua_ghi"] == ["D-0002", "D-0003"] and k1["loi"]["ma_dk"] == "D-0002"
    assert k1["da_tao_bc2"] is True and len(c.goi("EXEC usp_BaoCaoII_Insert")) == 1
    so_sp = len(c.sp_them)
    # nhật ký đã có D-0001 ngay sau SP thành công
    assert {h["ma_dk"]: h["ket_qua"] for h in nk.lo_hv("lo-0000001")}["D-0001"] == "da_them"
    # "Làm tiếp": cùng lo_id, KHÔNG truyền lại ma_bc2 (BC2 do lô này tạo), HV lỗi đã hết lỗi
    c.loi_sp.clear()
    k2 = lap(c, ["D-0001", "D-0002", "D-0003"])
    assert k2["trang_thai"] == "xong" and k2["da_tao_bc2"] is False and k2["ma_bc2"] == "81/2026"
    assert k2["da_them"] == ["D-0002", "D-0003"] and k2["da_co_tu_truoc"] == ["D-0001"]
    assert len(c.goi("EXEC usp_BaoCaoII_Insert")) == 1                # không tạo BC2 lần hai
    assert [p[0] for _s, p in c.sp_them[so_sp:]] == ["D-0002", "D-0003"]   # D-0001 KHÔNG bị gọi lại SP
    assert c.hv["D-0001"]["tt_cu"] == "09"                            # TT_XuLy_Old không bị ghi thành '11'


def test_khoi_chay_idempotent_theo_lo_id_va_tien_do():
    c = FakeConn(hvs_oto(2))
    doi_so = dict(lo_id="lo-0000002", ma_kh=KHOA, ma_bc2="76/2026", so_bao_cao="", ngay_bao_cao="", ghi_chu="",
                  ds_ma_dk=["D-0001", "D-0002"], nguoi="thu1", hom_nay=HOM_NAY, now=NOW)
    t1 = svc.khoi_chay("lo-0000002", svc.lap_bc2, doi_so, lambda: _ctx(c), dong_bo=True)
    assert t1["xong"] is True and t1["trang_thai"] == "xong" and t1["da_them"] == ["D-0001", "D-0002"]
    assert t1["xu_ly"] == 2 and t1["tong"] == 2
    n = len(c.sp_them)
    t2 = svc.khoi_chay("lo-0000002", svc.lap_bc2, doi_so, lambda: _ctx(c), dong_bo=True)   # cùng lo_id → không chạy lần hai
    assert t2["da_them"] == t1["da_them"] and len(c.sp_them) == n
    # tool khởi động lại (mất bộ nhớ): đọc từ sqlite, vẫn không chạy lại
    svc.quen_job("lo-0000002")
    t3 = svc.trang_thai_lo("lo-0000002")
    assert t3["xong"] is True and t3["da_them"] == ["D-0001", "D-0002"] and t3["ma_bc2"] == "76/2026"
    t4 = svc.khoi_chay("lo-0000002", svc.lap_bc2, doi_so, lambda: _ctx(c), dong_bo=True)
    assert t4["xong"] is True and len(c.sp_them) == n
    assert svc.trang_thai_lo("khong-co") is None


def test_job_loi_nghiep_vu_thanh_that_bai_co_ma_loi():
    c = FakeConn(hvs_oto(1))
    doi_so = dict(lo_id="lo-0000003", ma_kh=KHOA, ma_bc2="62/2025", so_bao_cao="", ngay_bao_cao="", ghi_chu="",
                  ds_ma_dk=["D-0001"], nguoi="thu1", hom_nay=HOM_NAY, now=NOW)
    t = svc.khoi_chay("lo-0000003", svc.lap_bc2, doi_so, lambda: _ctx(c), dong_bo=True)
    assert t["trang_thai"] == "that_bai" and t["xong"] is True and t["loi_nghiep_vu"]["ma"] == "bc2_khac_khoa"


# ── Hoàn tác ──
def _lap_roi_hoan_tac(c, ds, **kw):
    lap(c, ds, ma_bc2="76/2026", **kw)
    return svc.hoan_tac(c, ma_bc2="76/2026", lo_id="lo-hoantac1", nguoi="thu1")


def test_hoan_tac_go_dung_hv_cua_lo_va_chi_mot_lan():
    c = FakeConn(hvs_oto(3))
    kq = _lap_roi_hoan_tac(c, ["D-0001", "D-0002", "D-0003"])
    assert kq["trang_thai"] == "xong" and kq["da_go"] == ["D-0001", "D-0002", "D-0003"] and kq["bo_qua"] == []
    go = c.goi("EXEC usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2")
    assert [p for _s, p in go] == [(m, "12", "76/2026", 101) for m in ("D-0001", "D-0002", "D-0003")]
    assert all(c.hv[m]["tt"] == "09" and c.hv[m]["ma_bc2"] == "" for m in ("D-0001", "D-0002", "D-0003"))
    with pytest.raises(svc.LoiNghiepVu) as e:
        svc.hoan_tac(c, ma_bc2="76/2026", lo_id="lo-hoantac2", nguoi="thu1")
    assert e.value.ma == "da_hoan_tac" and e.value.http == 409
    assert len(c.goi("EXEC usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2")) == 3


def test_hoan_tac_bo_qua_hv_da_co_ket_qua_hoac_da_ra_khoi_bc2_va_khong_gom_hv_co_tu_truoc():
    hvs = hvs_oto(3)
    hvs["P-0001"] = hv("11", ma_bc2="76/2026", cu="09")               # PM cũ đã thêm từ trước — không thuộc lô
    c = FakeConn(hvs)
    lap(c, ["D-0001", "D-0002", "D-0003", "P-0001"], ma_bc2="76/2026")
    c.hv["D-0002"]["tt"] = "13"                                       # PM cũ đã nhập kết quả
    c.hv["D-0003"].update({"tt": "11", "ma_bc2": "75/2026"})          # sang BC2 khác
    kq = svc.hoan_tac(c, ma_bc2="76/2026", lo_id="lo-hoantac1", nguoi="thu1")
    assert kq["da_go"] == ["D-0001"]
    assert {b["ma_dk"]: b["ma_ly_do"] for b in kq["bo_qua"]} == {"D-0002": "khong_con_o_bc2", "D-0003": "khong_con_o_bc2"}
    assert c.hv["P-0001"]["tt"] == "11"                               # HV có từ trước KHÔNG bị gỡ


def test_hoan_tac_bc2_dong_khong_co_lo_va_thieu_tt_cu():
    c = FakeConn(hvs_oto(1))
    with pytest.raises(svc.LoiNghiepVu) as e:
        svc.hoan_tac(c, ma_bc2="62/2025", lo_id="lo-hoantac1", nguoi="thu1")
    assert e.value.ma == "bc2_da_dong"
    with pytest.raises(svc.LoiNghiepVu) as e:
        svc.hoan_tac(c, ma_bc2="76/2026", lo_id="lo-hoantac1", nguoi="thu1")
    assert e.value.ma == "khong_co_lo" and e.value.http == 404
    lap(c, ["D-0001"], ma_bc2="76/2026")
    c.hv["D-0001"]["tt_cu"] = ""                                      # mất trạng thái cũ → không ghi rỗng
    kq = svc.hoan_tac(c, ma_bc2="76/2026", lo_id="lo-hoantac2", nguoi="thu1")
    assert kq["da_go"] == [] and kq["bo_qua"][0]["ma_ly_do"] == "thieu_trang_thai_cu"


def test_hoan_tac_lay_lo_gan_nhat_cua_bc2_chu_khong_lo_cu_hon():
    c = FakeConn(hvs_oto(4))
    lap(c, ["D-0001", "D-0002"], lo_id="lo-aaaaaaa1", ma_bc2="76/2026")
    lap(c, ["D-0003", "D-0004"], lo_id="lo-aaaaaaa2", ma_bc2="76/2026")
    kq = svc.hoan_tac(c, ma_bc2="76/2026", lo_id="lo-hoantac1", nguoi="thu1")
    assert kq["lo_goc"] == "lo-aaaaaaa2" and kq["da_go"] == ["D-0003", "D-0004"]
    assert c.hv["D-0001"]["tt"] == "11" and c.hv["D-0002"]["tt"] == "11"


# ── Nhật ký ──
def test_nhat_ky_lo_khong_chua_pii_va_ghi_tung_hv():
    c = FakeConn(hvs_oto(2))
    lap(c, ["D-0001", "D-0002"], lo_id="lo-0000009")
    lo = nk.lo_lay("lo-0000009")
    assert lo["loai"] == "lap" and lo["trang_thai"] == "xong" and lo["ma_bc2"] == "81/2026" and lo["tong"] == 2
    assert [h["ket_qua"] for h in nk.lo_hv("lo-0000009")] == ["da_them", "da_them"]
    g = nk.gan_day(nk.THEM_HV)[0]
    assert g["lo_id"] == "lo-0000009" and g["trang_thai"] == "xong" and g["so_hv"] == 2
    blob = repr(g) + repr(lo)
    assert "cmt" not in blob.lower() and "ho_ten" not in blob.lower()


# ── Router ──
@pytest.fixture
def client(monkeypatch, auth_headers):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.routers import tn_bc2 as router

    conn = FakeConn(hvs_oto(3))

    @contextmanager
    def _conn(autocommit=True):
        yield conn

    @contextmanager
    def _cur(as_dict=True):
        yield conn.cursor()

    monkeypatch.setattr(router, "sqlserver_conn", _conn)
    monkeypatch.setattr(router, "sqlserver_cursor", _cur)
    monkeypatch.setattr(svc, "hom_nay_iso", lambda: HOM_NAY)
    # chạy nền thật bằng thread nhưng chờ xong: gói khoi_chay → dong_bo
    goc = svc.khoi_chay
    monkeypatch.setattr(svc, "khoi_chay", lambda *a, **k: goc(*a, **{**k, "dong_bo": True}))
    c = TestClient(app)

    class _C:
        def get(self, u, **kw):
            return c.get(u, headers=auth_headers, **kw)

        def post(self, u, **kw):
            return c.post(u, headers=auth_headers, **kw)
    return _C(), conn


def test_router_lap_tien_do_va_hoan_tac_voi_so_bc2_co_dau_gach_cheo(client):
    c, conn = client
    body = {"lo_id": "lo-router-01", "ma_kh": KHOA, "so_bao_cao": "81/2026", "ngay_bao_cao": "2026-10-11",
            "ds_ma_dk": ["D-0001", "D-0002"]}
    r = c.post("/local/tnbc2/bc2/lap", json=body)
    assert r.status_code == 400 and r.json()["detail"]["ma"] == "thieu_xac_nhan_csdl_that"
    assert conn.sp_them == []
    r = c.post("/local/tnbc2/bc2/lap", json=dict(body, xac_nhan_csdl_that=True))
    assert r.status_code == 200 and r.json()["xong"] is True and r.json()["da_them"] == ["D-0001", "D-0002"]
    assert conn.goi("EXEC usp_BaoCaoII_Insert")[0][1][8] == "op-test"
    r = c.get("/local/tnbc2/bc2/lo/lo-router-01")
    assert r.status_code == 200 and r.json()["trang_thai"] == "xong" and r.json()["ma_bc2"] == "81/2026"
    assert c.get("/local/tnbc2/bc2/lo/khong-co-lo").status_code == 404
    # gửi lại cùng lo_id → không chạy lần hai
    n = len(conn.sp_them)
    r = c.post("/local/tnbc2/bc2/lap", json=dict(body, xac_nhan_csdl_that=True))
    assert r.status_code == 200 and len(conn.sp_them) == n
    # hoàn tác: số BC2 "81/2026" có dấu "/" nên route dùng {ma:path}
    r = c.post("/local/tnbc2/bc2/81/2026/hoan-tac", json={"lo_id": "lo-ht-router1", "xac_nhan_csdl_that": True})
    assert r.status_code == 200 and r.json()["da_go"] == ["D-0001", "D-0002"]
    r = c.post("/local/tnbc2/bc2/81/2026/hoan-tac", json={"lo_id": "lo-ht-router2", "xac_nhan_csdl_that": True})
    assert r.status_code == 409 and r.json()["detail"]["ma"] == "da_hoan_tac"


def test_router_kiem_nhanh_tra_4xx_ngay_khong_chay_nen(client):
    c, conn = client
    ok = {"lo_id": "lo-router-02", "ma_kh": KHOA, "xac_nhan_csdl_that": True, "ds_ma_dk": ["D-0001"]}
    r = c.post("/local/tnbc2/bc2/lap", json=dict(ok, ma_bc2="62/2025"))
    assert r.status_code == 409 and r.json()["detail"]["ma"] == "bc2_khac_khoa"
    r = c.post("/local/tnbc2/bc2/lap", json=dict(ok, ma_bc2="999/2020"))
    assert r.status_code == 404
    r = c.post("/local/tnbc2/bc2/lap", json=dict(ok, ds_ma_dk=[]))
    assert r.status_code == 400 and r.json()["detail"]["ma"] == "khong_co_hoc_vien"
    r = c.post("/local/tnbc2/bc2/lap", json=dict(ok, lo_id="x"))
    assert r.status_code == 400 and r.json()["detail"]["ma"] == "lo_id_khong_hop_le"
    r = c.post("/local/tnbc2/bc2/lap", json=dict(ok, ds_ma_dk=[f"X{i}" for i in range(5001)]))
    assert r.status_code == 400 and r.json()["detail"]["ma"] == "qua_nhieu_dong"
    r = c.post("/local/tnbc2/bc2/lap", json=dict(ok, ma_kh="khong-co"))
    assert r.status_code == 404
    assert conn.sp_them == [] and conn.goi("EXEC usp_BaoCaoII_Insert") == []
    r = c.post("/local/tnbc2/bc2/76/2026/hoan-tac", json={"lo_id": "lo-ht-router3", "xac_nhan_csdl_that": True})
    assert r.status_code == 404 and r.json()["detail"]["ma"] == "khong_co_lo"
    r = c.post("/local/tnbc2/bc2/62/2025/hoan-tac", json={"lo_id": "lo-ht-router4", "xac_nhan_csdl_that": True})
    assert r.status_code == 409 and r.json()["detail"]["ma"] == "bc2_da_dong"


# ── Sau review nghiệp vụ task 99 ──
def test_doc_lai_sau_sp_loi_khong_lam_hv_thanh_chua_ghi():
    """SP đã chạy xong thì HV phải được ghi nhật ký "da_them" TRƯỚC khi đọc lại; lỗi đọc lại chỉ là cảnh báo."""
    c = FakeConn(hvs_oto(2))
    goc = FakeCur.execute
    dem = {"sp": 0}

    def execute(self, sql, params=()):
        s = " ".join(sql.split())
        if s.startswith("EXEC usp_NguoiLX_Update_ThemHSBC2"):
            dem["sp"] += 1
        # lệnh đọc 1 HV ngay SAU SP của D-0001 bị lỗi một lần
        if s.startswith("SELECT TT_XuLy, TT_XuLy_Old, MaBC2, SoHoSo FROM NguoiLX_HoSo WHERE MaDK") \
                and params[0] == "D-0001" and dem["sp"] == 1 and not dem.get("da_loi"):
            dem["da_loi"] = True
            raise RuntimeError("đứt khi đọc lại")
        return goc(self, sql, params)

    FakeCur.execute = execute
    try:
        kq = lap(c, ["D-0001", "D-0002"], ma_bc2="76/2026")
    finally:
        FakeCur.execute = goc
    assert kq["trang_thai"] == "xong" and kq["da_them"] == ["D-0001", "D-0002"] and kq["chua_ghi"] == []
    assert [w["ma"] for w in kq["canh_bao"]] == ["khong_doc_lai_duoc"]
    assert {h["ma_dk"]: h["ket_qua"] for h in nk.lo_hv("lo-0000001")} == {"D-0001": "da_them", "D-0002": "da_them"}
    assert len(c.sp_them) == 2


def test_hoan_tac_khong_go_hv_co_tt_cu_la_11():
    c = FakeConn(hvs_oto(2))
    c.old_la_11.add("D-0002")
    lap(c, ["D-0001", "D-0002"], ma_bc2="76/2026")
    kq = svc.hoan_tac(c, ma_bc2="76/2026", lo_id="lo-hoantac1", nguoi="thu1")
    assert kq["da_go"] == ["D-0001"]
    assert kq["bo_qua"][0]["ma_dk"] == "D-0002" and kq["bo_qua"][0]["ma_ly_do"] == "trang_thai_cu_la_11"
    assert c.hv["D-0002"]["tt"] == "11" and c.hv["D-0002"]["ma_bc2"] == "76/2026"      # không bị kéo thành 11 mồ côi


def test_lam_tiep_voi_so_trung_cua_bc2_da_dong_khong_them_hv():
    """Gửi lại cùng lo_id (thu_lai) nhưng đổi số sang số của một BC2 ĐÃ ĐÓNG cùng BC1 → chặn, không thêm HV."""
    bc2 = [{"MaBCII": "76/2026", "MaBCI": "858/26-TTTÐ", "SoBaoCao": "76/2026", "TrangThai": False, "TongSoThiSinh": 24},
           {"MaBCII": "77/2026", "MaBCI": "858/26-TTTÐ", "SoBaoCao": "77/2026", "TrangThai": True, "TongSoThiSinh": 10}]
    c = FakeConn(hvs_oto(2), bc2=bc2)
    nk.lo_bat_dau("lo-0000001", "thu1", nk.LO_LAP, KHOA, "", 2)        # lô này đã chạy dở trước đó
    with pytest.raises(svc.LoiNghiepVu) as e:
        lap(c, ["D-0001"], so="77/2026")
    assert e.value.ma == "bc2_da_dong" and c.sp_them == []


def test_hoan_tac_bo_qua_lo_khong_them_duoc_ai_va_lay_lo_that_truoc_do():
    c = FakeConn(hvs_oto(2))
    lap(c, ["D-0001", "D-0002"], lo_id="lo-aaaaaaa1", ma_bc2="76/2026")
    kq2 = lap(c, ["D-0001"], lo_id="lo-aaaaaaa2", ma_bc2="76/2026")      # D-0001 đã ở BC2 này → không thêm ai
    assert kq2["da_them"] == [] and kq2["da_co_tu_truoc"] == ["D-0001"]
    kq = svc.hoan_tac(c, ma_bc2="76/2026", lo_id="lo-hoantac1", nguoi="thu1")
    assert kq["lo_goc"] == "lo-aaaaaaa1" and kq["da_go"] == ["D-0001", "D-0002"]
