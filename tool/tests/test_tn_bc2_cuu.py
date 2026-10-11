"""TNB-06 (1/2) — task 104: cứu trạng thái (`tim_hv_cuu`, `cuu_chuyen`, `cuu_hoan_tac` + router).

Kết nối giả mô phỏng ĐÚNG `usp_NguoiLX_HoSo_UpdateTTXLy` (đã đọc định nghĩa 11/10/2026): không kiểm điều kiện
nào, `TT_XuLy_Old = TT_XuLy hiện tại`, `TT_XuLy = mới`, `Transfer_flag = 1 nếu '04'`. Khóa các bất biến: nguồn
11/16/19 bị chặn, đích chỉ 09/14/17/18, 09 cần số giấy và là ô tô, lý do bắt buộc, hoàn tác dùng trạng thái cũ
TRONG NHẬT KÝ (SP ghi đè TT_XuLy_Old), miễn luật đích, chỉ khi chưa bị đổi tiếp, idempotent theo `lo_id`.
"""
from contextlib import contextmanager

import pytest

from app import tn_bc2_nhat_ky as nk
from app import tn_bc2_service as svc
from tests.test_tn_bc2_ghi_tn import Conn as _Conn
from tests.test_tn_bc2_ghi_tn import Cur as _Cur
from tests.test_tn_bc2_tot_nghiep import HOM_NAY, KHOA, hv_row


class Cur(_Cur):
    def execute(self, sql, params=()):
        st, s = self.st, " ".join(sql.split())
        if s.startswith("SELECT h.MaDK, h.SoHoSo, n.HoVaTen, n.NgaySinh, n.SoCMT, h.HangGPLX, h.TT_XuLy, h.MaBC2, h.MaKhoaHoc, "
                        "h.SoGiayCNTN, k.TenKH, k.NgayBG"):
            st.log.append((s, tuple(params)))
            st.dem_tim += 1
            ten_kh = {k["MaKH"]: k["TenKH"] for k in st.khoa}
            bg = {k["MaKH"]: k["NgayBG"] for k in st.khoa}
            self._rows = [dict(h, TenKH=ten_kh.get(h["MaKhoaHoc"], ""), NgayBG=bg.get(h["MaKhoaHoc"], None)) for h in st.hv]
        elif s.startswith("SELECT MaBCI, MaKH"):
            st.log.append((s, tuple(params)))
            self._rows = []
        elif s.startswith("SELECT MaBCII, MaBCI, SoBaoCao"):
            st.log.append((s, tuple(params)))
            self._rows = [{"MaBCII": "76/2026", "MaBCI": "x", "SoBaoCao": "76/2026", "TrangThai": 0, "TongSoThiSinh": 0}]
        elif s.startswith("EXEC usp_NguoiLX_HoSo_UpdateTTXLy"):
            st.log.append((s, tuple(params)))
            ma, _so_hs, moi = params
            if ma in st.loi_sp:
                raise RuntimeError("mất kết nối")
            h = next(x for x in st.hv if x["MaDK"] == ma)
            h["TT_XuLy_Old"], h["TT_XuLy"] = h["TT_XuLy"], moi
            h["Transfer_flag"] = 1 if moi == "04" else 0
            self._rows = []
        else:
            super().execute(sql, params)


class Conn(_Conn):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.dem_tim = 0

    def cursor(self, as_dict=True):
        return Cur(self)

    @property
    def sp_cuu(self):
        return self.goi("EXEC usp_NguoiLX_HoSo_UpdateTTXLy")


@pytest.fixture(autouse=True)
def _co_lap(tmp_path, monkeypatch):
    monkeypatch.setattr(nk, "DB_PATH", tmp_path / "tnbc2_nhat_ky.sqlite")
    svc.bo_cache()
    yield
    svc.bo_cache()
    with svc._JOBS_KHOA:
        svc._JOBS.clear()


def du_lieu():
    return [
        hv_row("C-0001", "Nguyễn Đức Anh", "03"),
        hv_row("C-0002", "Trần Thị Bích", "03", giay="N1|7300", so="01/XNĐT/2026", qd="100/TTTĐ"),   # 03 mà đã có số giấy
        hv_row("C-0003", "Lê Văn Cường", "13"),
        hv_row("C-0004", "Phạm Dũng", "11", ma_bc2="76/2026"),
        hv_row("C-0005", "Võ Em", "16", ma_bc2="62/2025", giay="N1|7001"),
        hv_row("C-0006", "Hồ Giang", "19", ma_bc2="62/2025", giay="N1|7002"),
        hv_row("C-0007", "Mô Tô Hùng", "03", hang="A1"),
        hv_row("C-0008", "Đỗ Khánh", "01"),
    ]


def hv_cua(c, ma):
    return next(x for x in c.hv if x["MaDK"] == ma)


def cuu(c, ma_dk, dich, ly_do="Vắng thi, nhập nhầm", loai="oto", lo_id="lo-cuu-0001"):
    return svc.cuu_chuyen(c, lo_id=lo_id, ma_dk=ma_dk, dich=dich, ly_do=ly_do, loai=loai, nguoi="thu1")


# ── Tìm ──
def test_tim_khong_dau_cmt_ma_dk_va_dich_cho_phep():
    c = Conn(hv=du_lieu())
    t = lambda q, **k: svc.tim_hv_cuu(c.cursor(), q, hom_nay=HOM_NAY, **k)  # noqa: E731
    assert [h["ma_dk"] for h in t("duc anh")["hoc_vien"]] == ["C-0001"]
    assert [h["ma_dk"] for h in t("do khanh")["hoc_vien"]] == ["C-0008"]            # đ → d
    assert [h["ma_dk"] for h in t("0790002")["hoc_vien"]] == ["C-0002"]             # CMT
    assert [h["ma_dk"] for h in t("c-0005")["hoc_vien"]] == ["C-0005"]              # mã đăng ký, không phân biệt hoa/thường
    h1 = t("duc anh")["hoc_vien"][0]
    d1 = {d["ma"]: d for d in h1["dich"]}
    assert d1["14"]["cho_phep"] and d1["17"]["cho_phep"] and d1["18"]["cho_phep"]
    assert d1["09"]["cho_phep"] is False and "số giấy" in d1["09"]["ly_do"]          # 09 cần số giấy
    assert h1["cuu_duoc"] is True and h1["khong_hien"]["ma"] == "chua_tot_nghiep"        # đang là 'cần xem', không phải ngoài tập
    h2 = t("tran thi bich")["hoc_vien"][0]
    assert {d["ma"]: d["cho_phep"] for d in h2["dich"]}["09"] is True                # đã có số giấy → được
    for ma in ("C-0004", "C-0005", "C-0006"):                                        # nguồn 11/16/19: không đích nào
        h = t(ma)["hoc_vien"][0]
        assert h["cuu_duoc"] is False and not any(d["cho_phep"] for d in h["dich"])
    hm = t("mo to hung")["hoc_vien"][0]
    assert {d["ma"]: d["cho_phep"] for d in hm["dich"]}["09"] is False               # mô tô không có 09
    assert t("duc anh", loai="moto")["hoc_vien"][0]["khac_loai"] is True
    assert t("duc anh", loai="moto")["hoc_vien"][0]["cuu_duoc"] is False


def test_tim_thieu_tu_khoa_va_cache_danh_sach():
    c = Conn(hv=du_lieu())
    with pytest.raises(svc.LoiNghiepVu) as e:
        svc.tim_hv_cuu(c.cursor(), "a", hom_nay=HOM_NAY)
    assert e.value.ma == "thieu_tu_khoa" and e.value.http == 400
    svc.tim_hv_cuu(c.cursor(), "anh", hom_nay=HOM_NAY)
    svc.tim_hv_cuu(c.cursor(), "bich", hom_nay=HOM_NAY)
    assert c.dem_tim == 1                                                             # danh sách giữ trong bộ nhớ
    svc.bo_cache()
    svc.tim_hv_cuu(c.cursor(), "bich", hom_nay=HOM_NAY)
    assert c.dem_tim == 2


def test_tim_toi_da_50_ket_qua():
    c = Conn(hv=[hv_row(f"X-{i:04d}", f"Nguyễn Văn {i}", "03") for i in range(120)])
    kq = svc.tim_hv_cuu(c.cursor(), "nguyen van", hom_nay=HOM_NAY)
    assert kq["tong_khop"] == 120 and len(kq["hoc_vien"]) == 50


# ── Chuyển ──
def test_cuu_03_ve_17_dung_sp_va_ghi_nhat_ky():
    c = Conn(hv=du_lieu())
    kq = cuu(c, "C-0001", "17")
    assert kq["tt_cu"] == "03" and kq["tt_moi"] == "17" and kq["da_ton_tai"] is False and kq["canh_bao"] == []
    assert kq["ten_trang_thai_moi"] == "Thi sát hạch chưa đạt"
    assert [p for _s, p in c.sp_cuu] == [("C-0001", "12", "17")]
    h = hv_cua(c, "C-0001")
    assert h["TT_XuLy"] == "17" and h["TT_XuLy_Old"] == "03" and h["Transfer_flag"] == 0
    for s, _p in c.log:
        assert not any(k in s.upper() for k in ("INSERT INTO", "UPDATE ", "DELETE FROM")), s
    ds = [s for s, _ in c.log]
    assert ds.index(next(s for s in ds if "sp_getapplock" in s)) < ds.index(next(s for s in ds if "UpdateTTXLy" in s))
    g = nk.gan_day(nk.CUU)[0]
    assert g["trang_thai"] == "xong" and g["chi_tiet"]["ly_do"] == "Vắng thi, nhập nhầm"
    assert "Nguyễn" not in repr(g)


def test_cuu_13_ve_14_va_03_co_so_giay_len_09_va_04_dat_transfer_flag():
    c = Conn(hv=du_lieu() + [hv_row("C-0009", "Bốn", "02")])
    assert cuu(c, "C-0003", "14", lo_id="lo-cuu-0002")["tt_moi"] == "14"
    assert cuu(c, "C-0002", "09", lo_id="lo-cuu-0003")["tt_moi"] == "09"
    assert hv_cua(c, "C-0002")["TT_XuLy"] == "09"


@pytest.mark.parametrize("ma,dich,ma_loi", [
    ("C-0004", "17", "nguon_bi_chan"),          # 11
    ("C-0005", "17", "nguon_bi_chan"),          # 16
    ("C-0006", "14", "nguon_bi_chan"),          # 19
    ("C-0001", "11", "dich_khong_hop_le"),      # đích ngoài tập
    ("C-0001", "03", "dich_khong_hop_le"),
    ("C-0001", "09", "dich_09_thieu_so_giay"),  # 09 thiếu số giấy
    ("C-0007", "09", "dich_09_chi_o_to"),       # mô tô không có 09
])
def test_cuu_chan(ma, dich, ma_loi):
    c = Conn(hv=du_lieu())
    loai = "moto" if ma == "C-0007" else "oto"
    with pytest.raises(svc.LoiNghiepVu) as e:
        cuu(c, ma, dich, loai=loai)
    assert e.value.ma == "khong_cuu_duoc" and e.value.http == 409
    assert ma_loi in {v["ma"] for v in e.value.du_lieu["chan"]}
    assert c.sp_cuu == []                                                             # không gọi SP
    assert len(c.goi("EXEC sp_releaseapplock")) == 1


def test_cuu_thieu_ly_do_khac_loai_va_khong_ton_tai():
    c = Conn(hv=du_lieu())
    with pytest.raises(svc.LoiNghiepVu) as e:
        cuu(c, "C-0001", "17", ly_do="   ")
    assert "thieu_ly_do" in {v["ma"] for v in e.value.du_lieu["chan"]}
    with pytest.raises(svc.LoiNghiepVu) as e:
        cuu(c, "C-0001", "17", loai="moto")                                          # HV ô tô, màn đang chọn mô tô
    assert "khac_loai" in {v["ma"] for v in e.value.du_lieu["chan"]}
    with pytest.raises(svc.LoiNghiepVu) as e:
        cuu(c, "KHONG-CO", "17")
    assert e.value.ma == "hv_khong_ton_tai" and e.value.http == 404
    assert c.sp_cuu == []


def test_cuu_idempotent_theo_lo_id_va_lo_id_khac_chay_lai_luat():
    c = Conn(hv=du_lieu())
    k1 = cuu(c, "C-0001", "17")
    k2 = cuu(c, "C-0001", "17")                                                      # cùng lo_id → không ghi lần hai
    assert k2["da_ton_tai"] is True and k2["tt_moi"] == "17" and len(c.sp_cuu) == 1
    with pytest.raises(svc.LoiNghiepVu):                                              # lo_id mới: HV đã 17 → khong_doi
        cuu(c, "C-0001", "17", lo_id="lo-cuu-0009")
    assert k1["lo_id"] == "lo-cuu-0001"


def test_gui_lai_sau_khi_tool_bi_ngat_giua_luc_cuu_hoan_tat_tu_nhat_ky_va_van_hoan_tac_duoc():
    """Tool chết SAU khi SP chạy nhưng TRƯỚC khi đóng lô: gửi lại cùng lo_id không bị `khong_doi`, lô được hoàn tất
    từ nhật ký (tt_cu ghi trước SP) nên nút Hoàn tác vẫn dùng được."""
    c = Conn(hv=du_lieu())
    cuu(c, "C-0001", "17")
    nk.lo_cap_nhat("lo-cuu-0001", trang_thai="dang_chay", ket_qua={})                 # giả lập: lô chưa kịp đóng
    k = cuu(c, "C-0001", "17")
    assert k["da_ton_tai"] is True and k["tt_cu"] == "03" and k["tt_moi"] == "17"
    assert [w["ma"] for w in k["canh_bao"]] == ["hoan_tat_tu_lan_truoc"]
    assert len(c.sp_cuu) == 1                                                        # KHÔNG gọi SP lần hai
    assert nk.lo_lay("lo-cuu-0001")["trang_thai"] == "xong"
    ht = svc.cuu_hoan_tac(c, lo_id_cuu="lo-cuu-0001", lo_id="lo-ht-0001", nguoi="thu1")
    assert ht["tt_moi"] == "03" and hv_cua(c, "C-0001")["TT_XuLy"] == "03"


def test_gui_lai_lo_do_khi_sp_chua_chay_thi_chay_binh_thuong_mot_lan():
    c = Conn(hv=du_lieu())
    c.loi_sp.add("C-0001")
    with pytest.raises(RuntimeError):
        cuu(c, "C-0001", "17")                                                        # SP lỗi: HV vẫn 03
    nk.lo_cap_nhat("lo-cuu-0001", trang_thai="dang_chay")                             # lô còn dở
    c.loi_sp.clear()
    k = cuu(c, "C-0001", "17")
    assert k["da_ton_tai"] is False and k["canh_bao"] == [] and hv_cua(c, "C-0001")["TT_XuLy"] == "17"


def test_lo_dang_chay_cua_thao_tac_khac_khong_bi_hoan_tat_nham():
    c = Conn(hv=du_lieu())
    cuu(c, "C-0001", "17")
    nk.lo_cap_nhat("lo-cuu-0001", trang_thai="dang_chay", ket_qua={})
    with pytest.raises(svc.LoiNghiepVu):                                              # đích khác với lần ghi trong nhật ký
        cuu(c, "C-0001", "18")
    assert len(c.sp_cuu) == 1


def test_cuu_loi_db_khong_danh_dau_xong():
    c = Conn(hv=du_lieu())
    c.loi_sp.add("C-0001")
    with pytest.raises(RuntimeError):
        cuu(c, "C-0001", "17")
    assert nk.lo_lay("lo-cuu-0001")["trang_thai"] == "that_bai"
    assert hv_cua(c, "C-0001")["TT_XuLy"] == "03"
    c.loi_sp.clear()
    assert cuu(c, "C-0001", "17")["tt_moi"] == "17"                                   # thử lại cùng lo_id được


# ── Hoàn tác ──
def test_hoan_tac_ve_03_mien_luat_dich_dung_tt_cu_trong_nhat_ky_va_chi_mot_lan():
    c = Conn(hv=du_lieu())
    cuu(c, "C-0001", "17")
    assert hv_cua(c, "C-0001")["TT_XuLy_Old"] == "03"
    kq = svc.cuu_hoan_tac(c, lo_id_cuu="lo-cuu-0001", lo_id="lo-ht-0001", nguoi="thu1")
    assert kq["tt_moi"] == "03" and kq["da_ton_tai"] is False
    assert hv_cua(c, "C-0001")["TT_XuLy"] == "03"                                    # 03 ∉ {09,14,17,18} nhưng hợp lệ
    assert [p for _s, p in c.sp_cuu][-1] == ("C-0001", "12", "03")
    with pytest.raises(svc.LoiNghiepVu) as e:
        svc.cuu_hoan_tac(c, lo_id_cuu="lo-cuu-0001", lo_id="lo-ht-0002", nguoi="thu1")
    assert e.value.ma == "da_hoan_tac" and e.value.http == 409
    k2 = svc.cuu_hoan_tac(c, lo_id_cuu="lo-cuu-0001", lo_id="lo-ht-0001", nguoi="thu1")   # cùng lo_id → trả cũ
    assert k2["da_ton_tai"] is True and len(c.sp_cuu) == 2


def test_hoan_tac_chan_khi_hv_da_bi_pm_cu_doi_tiep_va_khi_khong_co_lan_cuu():
    c = Conn(hv=du_lieu())
    cuu(c, "C-0001", "17")
    hv_cua(c, "C-0001")["TT_XuLy"] = "11"                                             # PM cũ đưa vào BC2
    with pytest.raises(svc.LoiNghiepVu) as e:
        svc.cuu_hoan_tac(c, lo_id_cuu="lo-cuu-0001", lo_id="lo-ht-0003", nguoi="thu1")
    assert e.value.ma == "da_bi_doi" and e.value.http == 409
    assert len(c.sp_cuu) == 1
    with pytest.raises(svc.LoiNghiepVu) as e:
        svc.cuu_hoan_tac(c, lo_id_cuu="khong-co-lo", lo_id="lo-ht-0004", nguoi="thu1")
    assert e.value.ma == "khong_co_lan_cuu" and e.value.http == 404


# ── Router ──
@pytest.fixture
def client(monkeypatch, auth_headers):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.routers import tn_bc2 as router

    conn = Conn(hv=du_lieu())

    @contextmanager
    def _conn(autocommit=True):
        yield conn

    @contextmanager
    def _cur(as_dict=True):
        yield conn.cursor()

    monkeypatch.setattr(router, "sqlserver_conn", _conn)
    monkeypatch.setattr(router, "sqlserver_cursor", _cur)
    monkeypatch.setattr(svc, "hom_nay_iso", lambda: HOM_NAY)
    c = TestClient(app)

    class _C:
        def get(self, u, **kw):
            return c.get(u, headers=auth_headers, **kw)

        def post(self, u, **kw):
            return c.post(u, headers=auth_headers, **kw)
    return _C(), conn


def test_router_tim_chuyen_hoan_tac_va_cong_xac_nhan(client):
    c, conn = client
    r = c.get("/local/tnbc2/cuu/tim", params={"q": "duc anh"})
    assert r.status_code == 200 and r.json()["hoc_vien"][0]["ma_dk"] == "C-0001"
    assert c.get("/local/tnbc2/cuu/tim", params={"q": "a"}).status_code == 422
    assert c.get("/local/tnbc2/cuu/tim", params={"q": "duc anh", "loai": "xe"}).status_code == 422
    body = {"lo_id": "lo-router-c1", "ma_dk": "C-0001", "dich": "17", "ly_do": "Vắng thi", "loai": "oto"}
    r = c.post("/local/tnbc2/cuu/chuyen", json=body)
    assert r.status_code == 400 and r.json()["detail"]["ma"] == "thieu_xac_nhan_csdl_that" and conn.sp_cuu == []
    r = c.post("/local/tnbc2/cuu/chuyen", json=dict(body, dich="11", lo_id="lo-router-c0", xac_nhan_csdl_that=True))
    assert r.status_code == 409 and r.json()["detail"]["ma"] == "khong_cuu_duoc"
    assert r.json()["detail"]["chan"][0]["ma"] == "dich_khong_hop_le"
    r = c.post("/local/tnbc2/cuu/chuyen", json=dict(body, xac_nhan_csdl_that=True))
    assert r.status_code == 200 and r.json()["tt_moi"] == "17" and len(conn.sp_cuu) == 1
    r = c.post("/local/tnbc2/cuu/hoan-tac", json={"lo_id_cuu": "lo-router-c1", "lo_id": "lo-router-h1"})
    assert r.status_code == 400
    r = c.post("/local/tnbc2/cuu/hoan-tac",
               json={"lo_id_cuu": "lo-router-c1", "lo_id": "lo-router-h1", "xac_nhan_csdl_that": True})
    assert r.status_code == 200 and r.json()["tt_moi"] == "03"
    r = c.post("/local/tnbc2/cuu/hoan-tac",
               json={"lo_id_cuu": "lo-router-c1", "lo_id": "lo-router-h2", "xac_nhan_csdl_that": True})
    assert r.status_code == 409 and r.json()["detail"]["ma"] == "da_hoan_tac"


# ── Sau review nghiệp vụ task 104 ──
def test_lo_id_da_dung_cho_thao_tac_khac_bi_chan_khong_tra_ket_qua_sai():
    c = Conn(hv=du_lieu())
    cuu(c, "C-0001", "17")
    with pytest.raises(svc.LoiNghiepVu) as e:                                        # cùng lo_id nhưng HV/đích khác
        cuu(c, "C-0003", "14")
    assert e.value.ma == "lo_id_khong_khop" and e.value.http == 409 and len(c.sp_cuu) == 1
    with pytest.raises(svc.LoiNghiepVu) as e:                                        # dùng lo_id của lần cứu làm lo_id hoàn tác
        svc.cuu_hoan_tac(c, lo_id_cuu="lo-cuu-0001", lo_id="lo-cuu-0001", nguoi="thu1")
    assert e.value.ma == "lo_id_khong_khop"


def test_hoan_tac_doc_lai_sau_sp_va_loi_nhat_ky_chi_la_canh_bao(monkeypatch):
    c = Conn(hv=du_lieu())
    cuu(c, "C-0001", "17")
    kq = svc.cuu_hoan_tac(c, lo_id_cuu="lo-cuu-0001", lo_id="lo-ht-0010", nguoi="thu1")
    assert kq["canh_bao"] == [] and hv_cua(c, "C-0001")["TT_XuLy"] == "03"
    c2 = Conn(hv=du_lieu())
    goc = nk.lo_ghi_hv

    def hong(lo_id, ma_dk, ket_qua, ma_ly_do="", db_path=None):
        raise RuntimeError("sqlite hỏng")

    monkeypatch.setattr(nk, "lo_ghi_hv", hong)
    k = cuu(c2, "C-0003", "14", lo_id="lo-cuu-0020")
    assert k["tt_moi"] == "14" and [w["ma"] for w in k["canh_bao"]] == ["khong_ghi_duoc_nhat_ky"]
    assert hv_cua(c2, "C-0003")["TT_XuLy"] == "14"                                     # thao tác vẫn là "đã làm"
    monkeypatch.setattr(nk, "lo_ghi_hv", goc)


def test_tim_khac_loai_bao_ly_do_khac_loai_trong_khong_hien():
    c = Conn(hv=du_lieu())
    h = svc.tim_hv_cuu(c.cursor(), "duc anh", loai="moto", hom_nay=HOM_NAY)["hoc_vien"][0]
    assert h["khac_loai"] is True and h["khong_hien"]["ma"] == "khac_loai"
