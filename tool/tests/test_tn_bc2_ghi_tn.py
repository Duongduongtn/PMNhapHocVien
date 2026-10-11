"""TNB-01 (2/3) — task 102: GHI tốt nghiệp ô tô (`ghi_tot_nghiep` + `POST /tot-nghiep/ghi`).

Kết nối giả mô phỏng ĐÚNG `usp_NguoiLX_HoSo_Update_CNTN` (đã đọc định nghĩa 11/10/2026): `@sSoCNTN` dài > 0
→ ghi 6 cột và `03→09`; `@sSoCNTN=''` → ghi 6 cột và `09→03` (hủy); các trạng thái khác giữ nguyên;
SP KHÔNG kiểm trạng thái. Khóa các bất biến: `''` (không `NULL`) cho "lưu sổ trước", 8 tham số, cổng
xác nhận, cảnh báo cần `da_xem_canh_bao`, dòng bị chặn không ghi, đọc lại sát trước SP, làm tiếp không gọi
lại SP, lỗi giữa chừng trả đã/chưa ghi, nhật ký không PII, chỉ gọi SP.
"""
from contextlib import contextmanager
from datetime import datetime

import pytest

from app import tn_bc2_nhat_ky as nk
from app import tn_bc2_service as svc
from tests.test_tn_bc2_tot_nghiep import CHUNG, HOM_NAY, KHOA, KHOA_MOTO, KHOA_TUONG_LAI, hv_row
from tests.test_tn_bc2_tot_nghiep import FakeCur as _Cur
from tests.test_tn_bc2_tot_nghiep import FakeDb as _Db


class Cur(_Cur):
    def execute(self, sql, params=()):
        st, s = self.st, " ".join(sql.split())
        if "sp_getapplock" in s:
            st.log.append((s, tuple(params)))
            self._rows = [{"r": st.applock}]
        elif "sp_releaseapplock" in s:
            st.log.append((s, tuple(params)))
            self._rows = []
        elif s.startswith("EXEC usp_NguoiLX_HoSo_Update_CNTN"):
            st.log.append((s, tuple(params)))
            ma, _so_hs, so_so, ngay_vao, qd, ngay_qd, giay, ngay_in = params
            if ma in st.loi_sp:
                raise RuntimeError("mất kết nối")
            h = next(x for x in st.hv if x["MaDK"] == ma)
            tt = h["TT_XuLy"]
            h.update({"SoSoTN": so_so, "NgayVaoSoTN": ngay_vao, "SoQuyetDinhTN": qd, "NgayRaQDTN": ngay_qd,
                      "SoGiayCNTN": giay, "NgayInGiayTN": ngay_in})
            if len(giay) > 0 and tt == "03":
                h["TT_XuLy"] = "09"
            elif len(giay) == 0 and tt == "09":
                h["TT_XuLy"] = "03"
            self._rows = []
        elif "FROM NguoiLX_HoSo h LEFT JOIN NguoiLX n ON n.MaDK = h.MaDK WHERE h.MaDK IN" in s:
            for m in params:                                   # đếm lần đọc để giả lập "PM cũ đổi giữa chừng"
                st.lan_doc[m] = st.lan_doc.get(m, 0) + 1
                if st.lan_doc[m] == 2 and m in st.doi_lan_hai:
                    next(x for x in st.hv if x["MaDK"] == m).update(st.doi_lan_hai.pop(m))
            super().execute(sql, params)
        else:
            super().execute(sql, params)


class Conn(_Db):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.applock, self.loi_sp = 0, set()
        self.lan_doc, self.doi_lan_hai = {}, {}

    def cursor(self, as_dict=True):
        return Cur(self)

    def goi(self, prefix):
        return [(s, p) for s, p in self.log if s.startswith(prefix)]

    @property
    def sp(self):
        return self.goi("EXEC usp_NguoiLX_HoSo_Update_CNTN")

    def hv_cua(self, ma):
        return next(x for x in self.hv if x["MaDK"] == ma)


@pytest.fixture(autouse=True)
def _co_lap(tmp_path, monkeypatch):
    monkeypatch.setattr(nk, "DB_PATH", tmp_path / "tnbc2_nhat_ky.sqlite")
    svc.bo_cache()
    yield
    svc.bo_cache()
    with svc._JOBS_KHOA:
        svc._JOBS.clear()


@contextmanager
def _ctx(c):
    yield c


def ghi(c, dong, chung=CHUNG, lo_id="lo-tn-000001", ma_kh=KHOA, **kw):
    return svc.ghi_tot_nghiep(c, lo_id=lo_id, ma_kh=ma_kh, dong=dong, chung=chung, nguoi="thu1", hom_nay=HOM_NAY, **kw)


# ── Ghi đúng SP, đúng tham số ──
def test_ghi_cac_loai_hv_dung_8_tham_so_va_trang_thai():
    c = Conn()
    kq = ghi(c, [{"ma_dk": "T-0001", "so_giay": "N1|7329"},       # 03 + giấy → 09
                 {"ma_dk": "T-0002", "so_giay": ""},               # 03 lưu sổ trước → ở lại 03, giấy ''
                 {"ma_dk": "T-0003", "so_giay": "N1|7330"},        # 09 đổi số giấy → giữ 09
                 {"ma_dk": "T-0004", "so_giay": "N1|7331"}],       # 11 thiếu giấy → ghi giấy, KHÔNG đổi trạng thái
             da_xem_canh_bao=True)
    assert kq["trang_thai"] == "xong" and kq["bo_qua"] == [] and kq["chua_ghi"] == []
    assert {g["ma_dk"]: g["ket_qua"] for g in kq["da_ghi"]} == {
        "T-0001": "se_len_09", "T-0002": "luu_so_truoc", "T-0003": "giu_09_sua_thong_tin",
        "T-0004": "khong_doi_trang_thai_da_vao_bc2"}
    assert len(c.sp) == 4
    p = {m: pr for (_s, pr) in c.sp for m in [pr[0]]}
    assert p["T-0001"] == ("T-0001", "12", "01/XNĐT/2026", datetime(2026, 9, 30), "100/TTTĐ", datetime(2026, 9, 30),
                           "N1|7329", datetime(2026, 9, 30))
    assert p["T-0002"][6] == "" and p["T-0002"][6] is not None      # '' chứ KHÔNG NULL
    assert c.hv_cua("T-0001")["TT_XuLy"] == "09" and c.hv_cua("T-0001")["SoGiayCNTN"] == "N1|7329"
    assert c.hv_cua("T-0002")["TT_XuLy"] == "03" and c.hv_cua("T-0002")["SoGiayCNTN"] == ""
    assert c.hv_cua("T-0003")["TT_XuLy"] == "09" and c.hv_cua("T-0003")["SoGiayCNTN"] == "N1|7330"
    assert c.hv_cua("T-0004")["TT_XuLy"] == "11" and c.hv_cua("T-0004")["SoGiayCNTN"] == "N1|7331"
    assert kq["dem"]["se_len_09"] == 1
    # thứ tự: khóa → SP → nhả khóa; không INSERT/UPDATE/DELETE trực tiếp
    ds = [s for s, _ in c.log]
    i_k = next(i for i, s in enumerate(ds) if "sp_getapplock" in s)
    i_s = next(i for i, s in enumerate(ds) if s.startswith("EXEC usp_NguoiLX_HoSo_Update_CNTN"))
    i_n = max(i for i, s in enumerate(ds) if "sp_releaseapplock" in s)
    assert i_k < i_s < i_n
    for s in ds:
        assert not any(k in s.upper() for k in ("INSERT INTO", "UPDATE ", "DELETE FROM")), s
    # nhật ký từng HV + không PII
    assert {h["ma_dk"]: h["ket_qua"] for h in nk.lo_hv("lo-tn-000001")} == {m: "da_ghi" for m in p}
    assert nk.lo_lay("lo-tn-000001")["loai"] == "tot_nghiep"
    g = nk.gan_day(nk.TOT_NGHIEP)[0]
    assert g["trang_thai"] == "xong" and "Nguyễn" not in repr(g)


def test_giu_nguyen_gia_tri_hv_khi_khong_dien_chung():
    c = Conn()
    with pytest.raises(svc.LoiNghiepVu) as e:                            # 09, giữ nguyên mọi thứ → không có gì để ghi
        ghi(c, [{"ma_dk": "T-0003", "so_giay": "N1|7300"}], chung={})
    assert e.value.ma == "khong_co_dong_hop_le" and e.value.du_lieu["bo_qua"][0]["ma_ly_do"] == "khong_doi"
    assert c.sp == []                                                    # khong_doi → không gọi SP
    kq = ghi(c, [{"ma_dk": "T-0003", "so_giay": "N1|7399"}], chung={}, lo_id="lo-tn-000002")
    assert c.sp[0][1][2] == "01/XNĐT/2026" and c.sp[0][1][4] == "100/TTTĐ"  # sổ/QĐ giữ của HV


# ── Cổng, cảnh báo, chặn ──
def test_canh_bao_phai_xac_nhan_truoc_khi_ghi_bat_ky_dong_nao():
    c = Conn()
    with pytest.raises(svc.LoiNghiepVu) as e:
        ghi(c, [{"ma_dk": "T-0001", "so_giay": "N1|7329"}, {"ma_dk": "T-0004", "so_giay": "N1|7331"}])
    assert e.value.ma == "can_xac_nhan_canh_bao" and e.value.http == 409
    assert "bao_cao_da_lap_khong_doi_theo" in {w["ma"] for w in e.value.du_lieu["canh_bao"]}
    assert c.sp == []                                                    # chưa ghi gì, kể cả T-0001
    assert nk.gan_day(nk.TOT_NGHIEP)[0]["trang_thai"] == "that_bai"       # nhật ký được đóng


def test_dong_bi_chan_bo_qua_con_lai_van_ghi():
    c = Conn()
    c.giu = [{"MaDK": "X-0001", "SoGiayCNTN": "N1|7329"}]               # số 7329 đã thuộc HV khác
    kq = ghi(c, [{"ma_dk": "T-0001", "so_giay": "N1|7329"},             # trùng DB → chặn
                 {"ma_dk": "T-0002", "so_giay": "N1|7340"},             # ok
                 {"ma_dk": "T-0005", "so_giay": "N1|7500"},             # 16 đã có giấy → chặn sửa
                 {"ma_dk": "T-0006", "so_giay": "N1|7501"},             # 01 → chưa tới bước tốt nghiệp
                 {"ma_dk": "M-0001", "so_giay": "N1|7502"}])            # mô tô → sai loại
    assert [g["ma_dk"] for g in kq["da_ghi"]] == ["T-0002"]
    ly = {b["ma_dk"]: b["ma_ly_do"] for b in kq["bo_qua"]}
    assert ly == {"T-0001": "trung_db", "T-0005": "da_vao_bc2_khong_sua", "T-0006": "trang_thai_khong_hop_le",
                  "M-0001": "sai_loai"}
    assert [p[0] for _s, p in c.sp] == ["T-0002"]
    assert c.hv_cua("T-0001")["TT_XuLy"] == "03"                          # nguyên vẹn


def test_khong_co_dong_hop_le_va_khoa_chua_be_giang_va_khoa_mo_to():
    c = Conn()
    with pytest.raises(svc.LoiNghiepVu) as e:
        ghi(c, [{"ma_dk": "T-0006", "so_giay": "N1|7501"}])
    assert e.value.ma == "khong_co_dong_hop_le" and e.value.du_lieu["bo_qua"][0]["ma_ly_do"] == "trang_thai_khong_hop_le"
    c2 = Conn(hv=[hv_row("F-0001", "Tương Lai", "03", ma_kh=KHOA_TUONG_LAI)])
    with pytest.raises(svc.LoiNghiepVu) as e:
        ghi(c2, [{"ma_dk": "F-0001", "so_giay": "N1|7329"}], ma_kh=KHOA_TUONG_LAI)
    assert e.value.ma == "khoa_chua_be_giang" and c2.sp == []
    with pytest.raises(svc.LoiNghiepVu) as e:
        ghi(c, [{"ma_dk": "T-0001", "so_giay": "N1|7329"}], ma_kh=KHOA_MOTO)
    assert e.value.ma == "chi_o_to" and c.sp == []


def test_khoa_ghi_ban_409_khong_ghi_gi():
    c = Conn()
    c.applock = -1
    with pytest.raises(svc.LoiNghiepVu) as e:
        ghi(c, [{"ma_dk": "T-0001", "so_giay": "N1|7329"}])
    assert e.value.ma == "dang_ghi" and e.value.http == 409 and c.sp == []


def test_trung_trong_lo_va_do_dai_chan_ca_dong_va_khong_ghi_gi():
    c = Conn()
    with pytest.raises(svc.LoiNghiepVu) as e:
        ghi(c, [{"ma_dk": "T-0001", "so_giay": "N1|7329"}, {"ma_dk": "T-0002", "so_giay": "n1|7329"},   # trùng trong lô
                {"ma_dk": "T-0003", "so_giay": "x" * 21}])                                            # quá 20 ký tự
    assert e.value.ma == "khong_co_dong_hop_le"
    ly = {b["ma_dk"]: b["ma_ly_do"] for b in e.value.du_lieu["bo_qua"]}
    assert ly == {"T-0001": "trung_trong_lo", "T-0002": "trung_trong_lo", "T-0003": "vuot_do_dai"}
    assert c.sp == []


# ── Đọc lại sát trước SP / lỗi giữa chừng / làm tiếp ──
def test_pm_cu_doi_giua_chung_bi_bo_qua_khong_ghi_de():
    c = Conn()
    c.doi_lan_hai["T-0002"] = {"TT_XuLy": "11", "MaBC2": "76/2026"}      # PM cũ vừa đưa T-0002 vào BC2
    kq = ghi(c, [{"ma_dk": "T-0001", "so_giay": "N1|7329"}, {"ma_dk": "T-0002", "so_giay": "N1|7330"}])
    assert [g["ma_dk"] for g in kq["da_ghi"]] == ["T-0001"]
    assert kq["bo_qua"] == [{"ma_dk": "T-0002", "ma_ly_do": "doi_giua_chung",
                             "ly_do": "Phần mềm cũ vừa đổi học viên này — không ghi đè"}]
    assert c.hv_cua("T-0002")["SoGiayCNTN"] == "" and c.hv_cua("T-0002")["MaBC2"] == "76/2026"


def test_loi_db_giua_chung_tra_da_chua_ghi_roi_lam_tiep_khong_goi_lai_sp():
    c = Conn()
    c.loi_sp.add("T-0002")
    dong = [{"ma_dk": "T-0001", "so_giay": "N1|7329"}, {"ma_dk": "T-0002", "so_giay": "N1|7330"}]
    k1 = ghi(c, dong)
    assert k1["trang_thai"] == "loi_giua_chung" and [g["ma_dk"] for g in k1["da_ghi"]] == ["T-0001"]
    assert k1["chua_ghi"] == ["T-0002"] and k1["loi"]["ma_dk"] == "T-0002"
    n = len(c.sp)
    c.loi_sp.clear()
    k2 = ghi(c, dong)                                                    # cùng lo_id = Làm tiếp
    assert k2["trang_thai"] == "xong" and [g["ma_dk"] for g in k2["da_ghi"]] == ["T-0002"]
    assert k2["da_ghi_truoc"] == ["T-0001"]
    assert [p[0] for _s, p in c.sp[n:]] == ["T-0002"]                    # T-0001 KHÔNG bị gọi lại SP
    assert c.hv_cua("T-0001")["SoGiayCNTN"] == "N1|7329" and c.hv_cua("T-0002")["TT_XuLy"] == "09"


def test_khoi_chay_idempotent_theo_lo_id_va_tien_do():
    c = Conn()
    doi_so = dict(lo_id="lo-tn-000009", ma_kh=KHOA, dong=[{"ma_dk": "T-0001", "so_giay": "N1|7329"},
                                                         {"ma_dk": "T-0002", "so_giay": "N1|7330"}],
                  chung=CHUNG, nguoi="thu1", da_xem_canh_bao=False, hom_nay=HOM_NAY)
    t1 = svc.khoi_chay("lo-tn-000009", svc.ghi_tot_nghiep, doi_so, lambda: _ctx(c), dong_bo=True)
    assert t1["xong"] is True and t1["xu_ly"] == 2 and t1["tong"] == 2 and len(t1["da_ghi"]) == 2
    n = len(c.sp)
    t2 = svc.khoi_chay("lo-tn-000009", svc.ghi_tot_nghiep, doi_so, lambda: _ctx(c), dong_bo=True)
    assert t2["da_ghi"] == t1["da_ghi"] and len(c.sp) == n
    svc.quen_job("lo-tn-000009")
    t3 = svc.trang_thai_lo("lo-tn-000009")                               # tool khởi động lại: đọc từ sqlite
    assert t3["xong"] is True and [g["ma_dk"] for g in t3["da_ghi"]] == ["T-0001", "T-0002"]


# ── Router ──
@pytest.fixture
def client(monkeypatch, auth_headers):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.routers import tn_bc2 as router

    conn = Conn()

    @contextmanager
    def _conn(autocommit=True):
        yield conn

    @contextmanager
    def _cur(as_dict=True):
        yield conn.cursor()

    monkeypatch.setattr(router, "sqlserver_conn", _conn)
    monkeypatch.setattr(router, "sqlserver_cursor", _cur)
    monkeypatch.setattr(svc, "hom_nay_iso", lambda: HOM_NAY)
    goc = svc.khoi_chay
    monkeypatch.setattr(svc, "khoi_chay", lambda *a, **k: goc(*a, **{**k, "dong_bo": True}))
    c = TestClient(app)

    class _C:
        def get(self, u, **kw):
            return c.get(u, headers=auth_headers, **kw)

        def post(self, u, **kw):
            return c.post(u, headers=auth_headers, **kw)
    return _C(), conn


def test_router_ghi_cong_xac_nhan_canh_bao_va_idempotent(client):
    c, conn = client
    body = {"lo_id": "lo-router-tn1", "ma_kh": KHOA, "dong": [{"ma_dk": "T-0001", "so_giay": "N1|7329"}], "chung": CHUNG}
    r = c.post("/local/tnbc2/tot-nghiep/ghi", json=body)
    assert r.status_code == 400 and r.json()["detail"]["ma"] == "thieu_xac_nhan_csdl_that" and conn.sp == []
    r = c.post("/local/tnbc2/tot-nghiep/ghi", json=dict(body, xac_nhan_csdl_that=True))
    assert r.status_code == 200 and r.json()["xong"] is True and r.json()["da_ghi"][0]["ma_dk"] == "T-0001"
    assert c.get("/local/tnbc2/bc2/lo/lo-router-tn1").json()["trang_thai"] == "xong"
    n = len(conn.sp)
    r = c.post("/local/tnbc2/tot-nghiep/ghi", json=dict(body, xac_nhan_csdl_that=True))      # cùng lo_id
    assert r.status_code == 200 and len(conn.sp) == n


def test_router_kiem_nhanh_tra_4xx_ngay(client):
    c, conn = client
    ok = {"lo_id": "lo-router-tn2", "ma_kh": KHOA, "chung": CHUNG, "xac_nhan_csdl_that": True,
          "dong": [{"ma_dk": "T-0004", "so_giay": "N1|7331"}]}
    r = c.post("/local/tnbc2/tot-nghiep/ghi", json=ok)                                      # cảnh báo chưa xác nhận
    assert r.status_code == 409 and r.json()["detail"]["ma"] == "can_xac_nhan_canh_bao"
    assert r.json()["detail"]["canh_bao"][0]["ma"] == "bao_cao_da_lap_khong_doi_theo"
    r = c.post("/local/tnbc2/tot-nghiep/ghi", json=dict(ok, lo_id="lo-router-tn3", ma_kh=KHOA_MOTO))
    assert r.status_code == 400 and r.json()["detail"]["ma"] == "chi_o_to"
    r = c.post("/local/tnbc2/tot-nghiep/ghi", json=dict(ok, lo_id="lo-router-tn4", dong=[]))
    assert r.status_code == 400 and r.json()["detail"]["ma"] == "khong_co_hoc_vien"
    r = c.post("/local/tnbc2/tot-nghiep/ghi", json=dict(ok, lo_id="x"))
    assert r.status_code == 400 and r.json()["detail"]["ma"] == "lo_id_khong_hop_le"
    r = c.post("/local/tnbc2/tot-nghiep/ghi", json=dict(ok, lo_id="lo-router-tn5", da_xem_canh_bao=True))
    assert r.status_code == 200 and r.json()["da_ghi"][0]["ket_qua"] == "khong_doi_trang_thai_da_vao_bc2"
    assert len(conn.sp) == 1


# ── Sau review nghiệp vụ task 102 ──
def test_lam_tiep_bi_409_giu_ket_qua_da_ghi_cua_lan_truoc():
    c = Conn()
    c.loi_sp.add("T-0002")
    dong = [{"ma_dk": "T-0001", "so_giay": "N1|7329"}, {"ma_dk": "T-0002", "so_giay": "N1|7330"}]
    doi_so = dict(lo_id="lo-tn-000020", ma_kh=KHOA, dong=dong, chung=CHUNG, nguoi="thu1", da_xem_canh_bao=False,
                  hom_nay=HOM_NAY)
    t1 = svc.khoi_chay("lo-tn-000020", svc.ghi_tot_nghiep, doi_so, lambda: _ctx(c), dong_bo=True)
    assert t1["trang_thai"] == "loi_giua_chung" and [g["ma_dk"] for g in t1["da_ghi"]] == ["T-0001"]
    svc.quen_job("lo-tn-000020")
    # lần Làm tiếp: T-0002 giờ đã bị PM cũ đưa vào BC2 → mọi dòng còn lại bị chặn → 409
    c.loi_sp.clear()
    c.hv_cua("T-0002").update({"TT_XuLy": "16", "MaBC2": "62/2025", "SoGiayCNTN": "N1|7001"})
    t2 = svc.khoi_chay("lo-tn-000020", svc.ghi_tot_nghiep, doi_so, lambda: _ctx(c), dong_bo=True)
    assert t2["xong"] is True and t2["trang_thai"] == "loi_giua_chung"
    assert [g["ma_dk"] for g in t2["da_ghi"]] == ["T-0001"]                 # KHÔNG mất danh sách đã ghi
    assert t2["loi_nghiep_vu"]["ma"] == "khong_co_dong_hop_le"
    svc.quen_job("lo-tn-000020")
    t3 = svc.trang_thai_lo("lo-tn-000020")                                  # sau khi khởi động lại: đọc từ sqlite
    assert [g["ma_dk"] for g in t3["da_ghi"]] == ["T-0001"] and t3["trang_thai"] == "loi_giua_chung"


def test_hv_03_gan_ma_bc2_bat_thuong_bi_chan_khong_de_sp_doi_09():
    c = Conn(hv=[hv_row("B-0001", "Bất Thường", "03", ma_bc2="75/2026")])
    with pytest.raises(svc.LoiNghiepVu) as e:
        ghi(c, [{"ma_dk": "B-0001", "so_giay": "N1|7329"}])
    assert e.value.ma == "khong_co_dong_hop_le"
    assert e.value.du_lieu["bo_qua"][0]["ma_ly_do"] == "trang_thai_bc2_bat_thuong" and c.sp == []


def test_dong_trung_ma_dk_voi_so_giay_khac_nhau_la_loi_khong_am_tham_bo():
    c = Conn()
    with pytest.raises(svc.LoiNghiepVu) as e:
        ghi(c, [{"ma_dk": "T-0001", "so_giay": "N1|7329"}, {"ma_dk": "T-0001", "so_giay": "N1|7330"}])
    assert e.value.ma == "dong_trung_hoc_vien" and e.value.http == 400 and c.sp == []
    kq = ghi(c, [{"ma_dk": "T-0001", "so_giay": "N1|7329"}, {"ma_dk": "T-0001", "so_giay": "N1|7329"}],
             lo_id="lo-tn-000021")                                           # trùng y hệt → gộp
    assert [g["ma_dk"] for g in kq["da_ghi"]] == ["T-0001"] and len(c.sp) == 1


def test_loi_ghi_nhat_ky_sau_sp_khong_bien_hv_da_ghi_thanh_chua_ghi(monkeypatch):
    c = Conn()
    goc = nk.lo_ghi_hv

    def hong(lo_id, ma_dk, ket_qua, ma_ly_do="", db_path=None):
        if ket_qua == "da_ghi":
            raise RuntimeError("sqlite hỏng")
        return goc(lo_id, ma_dk, ket_qua, ma_ly_do, db_path)

    monkeypatch.setattr(nk, "lo_ghi_hv", hong)
    kq = ghi(c, [{"ma_dk": "T-0001", "so_giay": "N1|7329"}])
    assert [g["ma_dk"] for g in kq["da_ghi"]] == ["T-0001"] and kq["chua_ghi"] == []
    assert [w["ma"] for w in kq["canh_bao"]] == ["khong_ghi_duoc_nhat_ky"] and c.hv_cua("T-0001")["TT_XuLy"] == "09"
