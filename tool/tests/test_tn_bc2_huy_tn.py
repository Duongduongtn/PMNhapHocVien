"""TNB-02 (1/2) — task 103: HỦY tốt nghiệp (`huy_tot_nghiep` + `POST /tot-nghiep/huy`).

Kết nối giả mô phỏng ĐÚNG `usp_NguoiLX_HoSo_Update_CNTN` (từ `test_tn_bc2_ghi_tn`): `@sSoCNTN=''` và
TT_XuLy='09' → ghi 6 cột và đặt '03'. Khóa các bất biến: giữ nguyên sổ/quyết định/ngày chỉ xóa số giấy,
`''` đúng chỗ, SP không kiểm trạng thái nên tool chặn HV đã vào BC2 / không còn 09, đọc lại sát trước SP,
làm tiếp không gọi lại SP, không dùng `Update_HSTotNghiep`, không ghi trực tiếp.
"""
from contextlib import contextmanager
from datetime import datetime

import pytest

from app import tn_bc2_nhat_ky as nk
from app import tn_bc2_service as svc
from tests.test_tn_bc2_ghi_tn import Conn
from tests.test_tn_bc2_tot_nghiep import HOM_NAY, KHOA, KHOA_MOTO, KHOA_TUONG_LAI, hv_row


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


def du_lieu():
    return [
        hv_row("H-0001", "Hủy Một", "09", giay="N1|7300", so="01/XNĐT/2026", qd="100/TTTĐ"),
        hv_row("H-0002", "Hủy Hai", "09", giay="N1|7301", so="01/XNĐT/2026", qd="100/TTTĐ"),
        hv_row("H-0003", "Chưa Tốt Nghiệp", "03"),
        hv_row("H-0004", "Đã Vào BC2", "11", ma_bc2="76/2026", giay="N1|7302", so="01/XNĐT/2026", qd="100/TTTĐ"),
        hv_row("H-0005", "Có Kết Quả", "16", ma_bc2="62/2025", giay="N1|7001", so="01/XNĐT/2026", qd="100/TTTĐ"),
        hv_row("H-0006", "Bất Thường", "09", ma_bc2="75/2026", giay="N1|7303", so="01/XNĐT/2026", qd="100/TTTĐ"),
        hv_row("H-0007", "Mô Tô", "09", hang="A1", giay="N1|7304", so="01/XNĐT/2026", qd="100/TTTĐ"),
        hv_row("H-0008", "09 Không Giấy", "09", giay="", so="01/XNĐT/2026", qd="100/TTTĐ"),
        hv_row("K-0001", "Khóa Khác", "09", ma_kh="70004K26B0107", giay="N1|7305", so="01/XNĐT/2026", qd="100/TTTĐ"),
    ]


def huy(c, ds, lo_id="lo-huy-00001", ma_kh=KHOA, **kw):
    return svc.huy_tot_nghiep(c, lo_id=lo_id, ma_kh=ma_kh, ds_ma_dk=ds, nguoi="thu1", hom_nay=HOM_NAY, **kw)


# ── Hủy đúng SP, giữ nguyên sổ ──
def test_huy_giu_nguyen_so_quyet_dinh_ngay_chi_xoa_so_giay_va_ve_03():
    c = Conn(hv=du_lieu())
    kq = huy(c, ["H-0001", "H-0002"])
    assert kq["trang_thai"] == "xong" and kq["bo_qua"] == [] and kq["chua_ghi"] == []
    assert kq["da_huy"] == [{"ma_dk": "H-0001", "so_giay_cu": "N1|7300"}, {"ma_dk": "H-0002", "so_giay_cu": "N1|7301"}]
    assert [p for _s, p in c.sp][0] == ("H-0001", "12", "01/XNĐT/2026", datetime(2026, 9, 30), "100/TTTĐ",
                                        datetime(2026, 9, 30), "", datetime(2026, 9, 30))
    assert c.sp[0][1][6] == "" and c.sp[0][1][6] is not None             # '' (không NULL), chỉ số giấy
    h = c.hv_cua("H-0001")
    assert h["TT_XuLy"] == "03" and h["SoGiayCNTN"] == ""
    assert h["SoSoTN"] == "01/XNĐT/2026" and h["SoQuyetDinhTN"] == "100/TTTĐ"      # giữ nguyên để nhập lại
    assert h["NgayVaoSoTN"] == datetime(2026, 9, 30) and h["NgayInGiayTN"] == datetime(2026, 9, 30)
    for s, _p in c.log:
        assert "HSTotNghiep" not in s                                      # không dùng Update_HSTotNghiep
        assert not any(k in s.upper() for k in ("INSERT INTO", "UPDATE ", "DELETE FROM")), s
    assert {x["ma_dk"]: x["ket_qua"] for x in nk.lo_hv("lo-huy-00001")} == {"H-0001": "da_huy", "H-0002": "da_huy"}
    g = nk.gan_day(nk.HUY_TOT_NGHIEP)[0]
    assert g["trang_thai"] == "xong" and "Hủy Một" not in repr(g)


def test_hv_09_khong_co_so_giay_van_huy_duoc():
    c = Conn(hv=du_lieu())
    kq = huy(c, ["H-0008"])
    assert kq["da_huy"] == [{"ma_dk": "H-0008", "so_giay_cu": ""}] and c.hv_cua("H-0008")["TT_XuLy"] == "03"


# ── Chặn ──
def test_bo_qua_hv_khong_hop_le_kem_ly_do_va_chi_huy_dung_hv():
    c = Conn(hv=du_lieu())
    kq = huy(c, ["H-0001", "H-0003", "H-0004", "H-0005", "H-0006", "H-0007", "K-0001", "KHONG-CO"])
    assert [d["ma_dk"] for d in kq["da_huy"]] == ["H-0001"]
    ly = {b["ma_dk"]: b["ma_ly_do"] for b in kq["bo_qua"]}
    assert ly == {"H-0003": "khong_con_o_09", "H-0004": "da_vao_bc2", "H-0005": "da_vao_bc2",
                  "H-0006": "da_vao_bc2", "H-0007": "sai_loai", "K-0001": "khac_khoa", "KHONG-CO": "hv_khong_ton_tai"}
    assert [p[0] for _s, p in c.sp] == ["H-0001"]
    for ma in ("H-0004", "H-0005", "H-0006"):                              # nguyên vẹn (SP sẽ ghi đè nếu bị gọi)
        assert c.hv_cua(ma)["TT_XuLy"] in ("11", "16", "09") and c.hv_cua(ma)["SoGiayCNTN"] != ""


def test_khong_co_hv_huy_duoc_409_khoa_chua_be_giang_va_khoa_mo_to():
    c = Conn(hv=du_lieu())
    with pytest.raises(svc.LoiNghiepVu) as e:
        huy(c, ["H-0003", "H-0004"])
    assert e.value.ma == "khong_co_hoc_vien_huy_duoc"
    assert {b["ma_ly_do"] for b in e.value.du_lieu["bo_qua"]} == {"khong_con_o_09", "da_vao_bc2"}
    c2 = Conn(hv=[hv_row("F-0001", "Tương Lai", "09", ma_kh=KHOA_TUONG_LAI, giay="N1|1", so="s", qd="q")])
    with pytest.raises(svc.LoiNghiepVu) as e:
        huy(c2, ["F-0001"], ma_kh=KHOA_TUONG_LAI)
    assert e.value.ma == "khoa_chua_be_giang"
    with pytest.raises(svc.LoiNghiepVu) as e:
        huy(c, ["H-0001"], ma_kh=KHOA_MOTO)
    assert e.value.ma == "chi_o_to"
    with pytest.raises(svc.LoiNghiepVu) as e:
        huy(c, [])
    assert e.value.ma == "khong_co_hoc_vien"
    assert c.sp == [] and c2.sp == []


def test_khoa_ghi_ban_409():
    c = Conn(hv=du_lieu())
    c.applock = -1
    with pytest.raises(svc.LoiNghiepVu) as e:
        huy(c, ["H-0001"])
    assert e.value.ma == "dang_ghi" and c.sp == []


# ── Đọc lại sát trước SP / lỗi / làm tiếp ──
def test_pm_cu_dua_hv_vao_bc2_giua_chung_bi_bo_qua():
    c = Conn(hv=du_lieu())
    c.doi_lan_hai["H-0002"] = {"TT_XuLy": "11", "MaBC2": "76/2026"}
    kq = huy(c, ["H-0001", "H-0002"])
    assert [d["ma_dk"] for d in kq["da_huy"]] == ["H-0001"]
    assert kq["bo_qua"][0]["ma_dk"] == "H-0002" and kq["bo_qua"][0]["ma_ly_do"] == "doi_giua_chung"
    assert c.hv_cua("H-0002")["SoGiayCNTN"] == "N1|7301"                  # không bị xóa số giấy


def test_loi_db_giua_chung_roi_lam_tiep_khong_goi_lai_sp():
    c = Conn(hv=du_lieu())
    c.loi_sp.add("H-0002")
    k1 = huy(c, ["H-0001", "H-0002"])
    assert k1["trang_thai"] == "loi_giua_chung" and [d["ma_dk"] for d in k1["da_huy"]] == ["H-0001"]
    assert k1["chua_ghi"] == ["H-0002"] and k1["loi"]["ma_dk"] == "H-0002"
    n = len(c.sp)
    c.loi_sp.clear()
    k2 = huy(c, ["H-0001", "H-0002"])
    assert k2["trang_thai"] == "xong" and [d["ma_dk"] for d in k2["da_huy"]] == ["H-0002"]
    assert k2["da_huy_truoc"] == [{"ma_dk": "H-0001", "so_giay_cu": "N1|7300"}]
    assert [p[0] for _s, p in c.sp[n:]] == ["H-0002"]                      # H-0001 KHÔNG bị gọi lại SP


def test_lam_tiep_bi_409_giu_danh_sach_da_huy():
    c = Conn(hv=du_lieu())
    c.loi_sp.add("H-0002")
    doi_so = dict(lo_id="lo-huy-00020", ma_kh=KHOA, ds_ma_dk=["H-0001", "H-0002"], nguoi="thu1", hom_nay=HOM_NAY)
    t1 = svc.khoi_chay("lo-huy-00020", svc.huy_tot_nghiep, doi_so, lambda: _ctx(c), dong_bo=True)
    assert t1["trang_thai"] == "loi_giua_chung" and [d["ma_dk"] for d in t1["da_huy"]] == ["H-0001"]
    svc.quen_job("lo-huy-00020")
    c.loi_sp.clear()
    c.hv_cua("H-0002").update({"TT_XuLy": "11", "MaBC2": "76/2026"})        # PM cũ đưa vào BC2 giữa hai lần
    t2 = svc.khoi_chay("lo-huy-00020", svc.huy_tot_nghiep, doi_so, lambda: _ctx(c), dong_bo=True)
    assert t2["trang_thai"] == "loi_giua_chung" and [d["ma_dk"] for d in t2["da_huy"]] == ["H-0001"]
    assert t2["loi_nghiep_vu"]["ma"] == "khong_co_hoc_vien_huy_duoc"


def test_khoi_chay_idempotent():
    c = Conn(hv=du_lieu())
    doi_so = dict(lo_id="lo-huy-00009", ma_kh=KHOA, ds_ma_dk=["H-0001"], nguoi="thu1", hom_nay=HOM_NAY)
    t1 = svc.khoi_chay("lo-huy-00009", svc.huy_tot_nghiep, doi_so, lambda: _ctx(c), dong_bo=True)
    assert t1["xong"] is True and t1["xu_ly"] == 1
    n = len(c.sp)
    t2 = svc.khoi_chay("lo-huy-00009", svc.huy_tot_nghiep, doi_so, lambda: _ctx(c), dong_bo=True)
    assert t2["da_huy"] == t1["da_huy"] and len(c.sp) == n


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
    goc = svc.khoi_chay
    monkeypatch.setattr(svc, "khoi_chay", lambda *a, **k: goc(*a, **{**k, "dong_bo": True}))
    c = TestClient(app)

    class _C:
        def get(self, u, **kw):
            return c.get(u, headers=auth_headers, **kw)

        def post(self, u, **kw):
            return c.post(u, headers=auth_headers, **kw)
    return _C(), conn


def test_router_huy_cong_xac_nhan_kiem_nhanh_va_idempotent(client):
    c, conn = client
    body = {"lo_id": "lo-router-huy1", "ma_kh": KHOA, "ds_ma_dk": ["H-0001"]}
    r = c.post("/local/tnbc2/tot-nghiep/huy", json=body)
    assert r.status_code == 400 and r.json()["detail"]["ma"] == "thieu_xac_nhan_csdl_that" and conn.sp == []
    r = c.post("/local/tnbc2/tot-nghiep/huy", json=dict(body, lo_id="lo-router-huy0", ds_ma_dk=["H-0004"],
                                                        xac_nhan_csdl_that=True))
    assert r.status_code == 409 and r.json()["detail"]["ma"] == "khong_co_hoc_vien_huy_duoc"
    assert r.json()["detail"]["bo_qua"][0]["ma_ly_do"] == "da_vao_bc2" and conn.sp == []
    r = c.post("/local/tnbc2/tot-nghiep/huy", json=dict(body, xac_nhan_csdl_that=True))
    assert r.status_code == 200 and r.json()["xong"] is True and r.json()["da_huy"][0]["so_giay_cu"] == "N1|7300"
    assert c.get("/local/tnbc2/bc2/lo/lo-router-huy1").json()["trang_thai"] == "xong"
    n = len(conn.sp)
    r = c.post("/local/tnbc2/tot-nghiep/huy", json=dict(body, xac_nhan_csdl_that=True))      # cùng lo_id
    assert r.status_code == 200 and len(conn.sp) == n
    r = c.post("/local/tnbc2/tot-nghiep/huy", json=dict(body, lo_id="lo-router-huy2", ma_kh=KHOA_MOTO,
                                                        xac_nhan_csdl_that=True))
    assert r.status_code == 400 and r.json()["detail"]["ma"] == "chi_o_to"
    r = c.post("/local/tnbc2/tot-nghiep/huy", json=dict(body, lo_id="x", xac_nhan_csdl_that=True))
    assert r.status_code == 400 and r.json()["detail"]["ma"] == "lo_id_khong_hop_le"
