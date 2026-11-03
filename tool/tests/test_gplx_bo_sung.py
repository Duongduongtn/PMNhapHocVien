"""QLY-10, TCB-05 — bổ sung GPLX đã có cho học viên đã nạp. Không cần DB thật."""
import re

import pytest
from fastapi.testclient import TestClient

from app import gplx_da_co as g
from app.main import app
from app.routers import hoso, sync_tracuu

client = TestClient(app)

B2 = {"hang": "B2", "so": "790000000123", "ngay_tt": "20120815", "ngay_cap": "20180427", "ngay_hh": "20280427", "don_vi": "70"}
A1 = {"hang": "A1", "so": "790000000456", "ngay_tt": "20100101", "ngay_cap": "20100201", "ngay_hh": "", "don_vi": "79"}
THO_TRONG = {c: "" for c in g.TEN_COT}


def dong(**kw):
    return {"MaKhoaHoc": "K1", "HangGPLX": "C1", "HoVaTen": "A", "NgaySinh": "19900501", **{c: None for c in g.TEN_COT}, **kw}


# ---- Tách chuỗi ----
def test_tach_rong():
    assert g.tach_chuoi_gplx(dong()) == ([], False)
    assert g.tach_chuoi_gplx(dong(SoGPLXDaCo="  ")) == ([], False)


def test_tach_hai_bang_giu_vi_tri_o_trong():
    ds, lech = g.tach_chuoi_gplx(dong(SoGPLXDaCo="1|2", HangGPLXDaCo="B2|A1m", NgayTTGPLXDaCo="20100101|20120101",
                                      NgayCapGPLXDaCo="20100201|20120201", NgayHHGPLXDaCo="20200201|", DonViCapGPLXDaCo="70|79"))
    assert not lech
    assert [(b["so"], b["hang"], b["ngay_hh"], b["nhom"]) for b in ds] == [("1", "B2", "20200201", "cu"), ("2", "A1m", "", "moi")]


def test_tach_cot_trong_han_khong_tinh_la_lech():
    ds, lech = g.tach_chuoi_gplx(dong(SoGPLXDaCo="1", HangGPLXDaCo="A1"))
    assert not lech and ds[0]["ngay_hh"] == ""


def test_tach_lech_so_phan_khong_mat_du_lieu():
    ds, lech = g.tach_chuoi_gplx(dong(SoGPLXDaCo="1|2", HangGPLXDaCo="B2"))
    assert lech
    assert [(b["so"], b["hang"]) for b in ds] == [("1", "B2"), ("2", "")]


def test_tach_roi_ghep_lai_y_nguyen():
    goc = {"SoGPLXDaCo": "790000000123|790000000456", "HangGPLXDaCo": "B2|A1", "NgayTTGPLXDaCo": "20120815|20100101",
           "NgayCapGPLXDaCo": "20180427|20100201", "NgayHHGPLXDaCo": "20280427|", "DonViCapGPLXDaCo": "70|79"}
    ds, _ = g.tach_chuoi_gplx(dong(**goc))
    assert g.gia_tri_ghi(ds, "C1", "19900501") == goc


def test_gia_tri_ghi_rong_thanh_null_va_kiem_nhu_nap():
    assert set(g.gia_tri_ghi([], "C1", None).values()) == {None}
    with pytest.raises(ValueError, match="trùng hạng"):
        g.gia_tri_ghi([B2], "B2", None)
    with pytest.raises(ValueError, match="18 tuổi"):
        g.gia_tri_ghi([B2], "C1", "20100101")


# ---- API, DB giả ----
class Cur:
    def __init__(self, row, bc1=0, dkkh=0, ma_bc1=None, rowcount=1):
        self.row, self.bc1, self.dkkh, self.ma_bc1, self.rowcount = row, bc1, dkkh, ma_bc1, rowcount
        self.sql, self._kq = [], None

    def execute(self, sql, params=None):
        self.sql.append((sql, params))
        if "UPDATE" in sql:
            return
        if "HoVaTen" in sql:
            self._kq = self.row
        else:
            self._kq = {"bc1": self.bc1, "dkkh": self.dkkh, "MaBC1": self.ma_bc1}

    def fetchone(self):
        return self._kq

    def updates(self):
        return [s for s in self.sql if "UPDATE" in s[0]]


class Conn:
    def __init__(self, cur):
        self._cur = cur

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def cursor(self, **kw):
        return self._cur


@pytest.fixture
def nap(monkeypatch):
    def lam(**kw):
        cur = Cur(kw.pop("row", dong()), **kw)
        monkeypatch.setattr(hoso, "sqlserver_conn", lambda **k: Conn(cur))
        monkeypatch.setattr(hoso, "sqlserver_cursor", lambda **k: Conn(cur).__enter__() and _Ctx(cur))
        monkeypatch.setattr(hoso.nap, "keo_ve_gan_gplx", lambda *a: None)
        return cur
    return lam


class _Ctx:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


@pytest.fixture
def dich(monkeypatch):
    def lam(**kw):
        cur = Cur(kw.pop("row", dong()), **kw)
        monkeypatch.setattr(sync_tracuu, "sqlserver_conn_dich", lambda db, **k: Conn(cur))
        monkeypatch.setattr(sync_tracuu, "_db_dich", lambda k: "DB_DICH")
        return cur
    return lam


def test_chua_dang_nhap_401():
    assert client.get("/local/ho-so/gplx?ma_dk=X").status_code == 401
    assert client.put("/local/ho-so/gplx?ma_dk=X", json={"gplx": [], "tho": THO_TRONG}).status_code == 401
    assert client.put("/local/sync/tra-cuu/gplx?ma_dk=X", json={"gplx": [], "tho": THO_TRONG}).status_code == 401


def test_thieu_chuoi_tho_422(auth_headers):
    r = client.put("/local/ho-so/gplx?ma_dk=X", headers=auth_headers, json={"gplx": [], "tho": {"SoGPLXDaCo": ""}})
    assert r.status_code == 422


def test_luu_chi_ghi_dung_6_cot_theo_ma_dk(auth_headers, nap):
    cur = nap()
    r = client.put("/local/ho-so/gplx?ma_dk=M1", headers=auth_headers, json={"gplx": [B2, A1], "tho": THO_TRONG})
    assert r.status_code == 200, r.text
    (sql, ts), = cur.updates()
    cot_ghi = re.findall(r"(\w+) = %s", sql.split(" WHERE ")[0].split(" SET ")[1])
    assert cot_ghi == list(g.TEN_COT)
    assert "NoiCapGPLXDaCo" not in sql and "TT_XuLy" not in sql
    assert " dbo.NguoiLX_HoSo " in sql and sql.count("UPDATE") == 1
    assert ts[0] == "790000000123|790000000456" and ts[1] == "B2|A1" and ts[6] == "M1"
    assert ts[7:] == ("",) * 6


def test_xoa_het_ghi_null_kem_dieu_kien_gia_tri_cu(auth_headers, nap):
    goc = dict(SoGPLXDaCo="1", HangGPLXDaCo="B2")
    cur = nap(row=dong(**goc))
    tho = {**THO_TRONG, **goc}
    assert client.put("/local/ho-so/gplx?ma_dk=M1", headers=auth_headers, json={"gplx": [], "tho": tho}).status_code == 200
    _, ts = cur.updates()[0]
    assert ts[:6] == (None,) * 6 and ts[7:9] == ("1", "B2")


def test_du_lieu_vua_doi_409(auth_headers, nap):
    nap(rowcount=0)
    r = client.put("/local/ho-so/gplx?ma_dk=M1", headers=auth_headers, json={"gplx": [B2], "tho": THO_TRONG})
    assert r.status_code == 409 and "vừa đổi" in r.json()["detail"]


def test_khoa_da_bc1_chan_khong_ghi(auth_headers, nap):
    cur = nap(bc1=1)
    r = client.put("/local/ho-so/gplx?ma_dk=M1", headers=auth_headers, json={"gplx": [B2], "tho": THO_TRONG})
    assert r.status_code == 409 and "Báo cáo 1" in r.json()["detail"]
    assert not cur.updates()
    d = client.get("/local/ho-so/gplx?ma_dk=M1", headers=auth_headers).json()
    assert "Báo cáo 1" in d["chan"]


def test_du_lieu_sai_400_khong_ghi(auth_headers, nap):
    cur = nap()
    bad = {**B2, "hang": "B2", "ngay_cap": "20100101"}
    r = client.put("/local/ho-so/gplx?ma_dk=M1", headers=auth_headers, json={"gplx": [bad], "tho": THO_TRONG})
    assert r.status_code == 400 and "ngày cấp" in r.json()["detail"]
    assert not cur.updates()


def test_doc_tra_chuoi_tho_nguyen_van(auth_headers, nap):
    nap(row=dong(SoGPLXDaCo=" 1|2 ", HangGPLXDaCo="B2"))
    d = client.get("/local/ho-so/gplx?ma_dk=M1", headers=auth_headers).json()
    assert d["tho"]["SoGPLXDaCo"] == " 1|2 " and d["tho"]["NgayCapGPLXDaCo"] == ""
    assert d["lech"] and d["chan"] is None and d["hang_khoa"] == "C1"


def test_khong_tim_thay_404(auth_headers, nap):
    nap(row=None)
    assert client.get("/local/ho-so/gplx?ma_dk=M1", headers=auth_headers).status_code == 404


@pytest.mark.parametrize("kw, chu", [({"dkkh": 1}, "DKKH"), ({"bc1": 1}, "Báo cáo 1"), ({"ma_bc1": "BC"}, "Báo cáo 1")])
def test_dich_chan_dkkh_bc1(auth_headers, dich, kw, chu):
    cur = dich(**kw)
    r = client.put("/local/sync/tra-cuu/gplx?ma_dk=M1", headers=auth_headers, json={"gplx": [B2], "tho": THO_TRONG})
    assert r.status_code == 409 and chu in r.json()["detail"]
    assert not cur.updates()
    assert chu in client.get("/local/sync/tra-cuu/gplx?ma_dk=M1", headers=auth_headers).json()["chan"]


def test_dich_khong_doc_duoc_khoa_thi_chan(auth_headers, dich):
    cur = dich()
    goc = cur.fetchone
    cur.fetchone = lambda: None if cur._kq and "dkkh" in cur._kq else goc()
    r = client.put("/local/sync/tra-cuu/gplx?ma_dk=M1", headers=auth_headers, json={"gplx": [B2], "tho": THO_TRONG})
    assert r.status_code == 409 and not cur.updates()


def test_dich_luu_chi_6_cot(auth_headers, dich):
    cur = dich()
    assert client.put("/local/sync/tra-cuu/gplx?ma_dk=M1", headers=auth_headers, json={"gplx": [B2], "tho": THO_TRONG}).status_code == 200
    (sql, ts), = cur.updates()
    assert re.findall(r"(\w+) = %s", sql.split(" WHERE ")[0].split(" SET ")[1]) == list(g.TEN_COT)
    assert ts[6] == "M1"


def test_keo_ve_gan_gplx_loi_khong_lam_hong(monkeypatch):
    import sqlite3
    from app import nap as n

    def hong():
        raise sqlite3.OperationalError("x")
    monkeypatch.setattr(n, "_keo_conn", hong)
    n.keo_ve_gan_gplx("M1", [B2])


# ---- Cảnh báo bản app web (QLY-10) ----
from app import vps  # noqa: E402
from app.vps import VpsLoi  # noqa: E402


def _web(uuid="u1", ma_dk="M1", ds=None, luc="2026-11-03T09:00:00"):
    return {"uuid": uuid, "ma_dk": ma_dk, "gplx_da_co": [B2] if ds is None else ds, "nguoi_gui": "Thu nhận 1", "updated_at": luc}


def _dong_b2(**kw):
    return dong(MaDK="M1", TenKH="Khóa", SoGPLXDaCo=B2["so"], HangGPLXDaCo="B2", NgayTTGPLXDaCo=B2["ngay_tt"],
                NgayCapGPLXDaCo=B2["ngay_cap"], NgayHHGPLXDaCo=B2["ngay_hh"], DonViCapGPLXDaCo="70", **kw)


def test_loc_khac_db_thi_canh_bao_khong_tra_so_gplx():
    kq = g.loc_canh_bao([_web()], {"M1": dong(MaDK="M1", TenKH="Khóa")}, {})
    assert len(kq) == 1 and kq[0]["hang_web"] == [{"hang": "B2", "nhom": "cu"}] and kq[0]["hang_db"] == []
    assert B2["so"] not in str(kq)


def test_loc_giong_db_khong_canh_bao():
    assert g.loc_canh_bao([_web()], {"M1": _dong_b2()}, {}) == []


def test_loc_da_xu_ly_dung_ban_thi_an_ban_khac_hien_lai():
    dv = g.dau_van("u1", [B2])
    db = {"M1": dong(MaDK="M1")}
    assert g.loc_canh_bao([_web()], db, {"u1": dv}) == []
    moi = [{**B2, "so": "790000000999"}]
    assert len(g.loc_canh_bao([_web(ds=moi)], db, {"u1": dv})) == 1


def test_loc_khong_thay_trong_db():
    kq = g.loc_canh_bao([_web()], {}, {})
    assert kq[0]["khong_thay"] is True


def test_dau_van_khac_theo_uuid():
    assert g.dau_van("u1", [B2]) != g.dau_van("u2", [B2])


def test_lay_ban_web_du_trang_va_lay_moi_nhat(monkeypatch):
    trang = [
        {"items": [_web("u1", "M1", luc="2026-11-01T00:00:00")], "co_tiep": True, "cursor": "c"},
        {"items": [_web("u2", "M1", luc="2026-11-02T00:00:00"), _web("u3", "M2")], "co_tiep": False, "cursor": None},
    ]
    goi = []
    monkeypatch.setattr(vps, "gplx_bo_sung", lambda tok, cur: (goi.append(cur), trang[len(goi) - 1])[1])
    ds = g.lay_ban_web("t")
    assert goi == [None, "c"]
    assert sorted(x["uuid"] for x in ds) == ["u2", "u3"]


def test_doc_lo_db_chia_lo_500():
    class C:
        def __init__(self):
            self.lo = []

        def execute(self, sql, p):
            self.lo.append(len(p))

        def fetchall(self):
            return []
    c = C()
    g.doc_lo_db(c, [f"M{i}" for i in range(1201)])
    assert c.lo == [500, 500, 201]


def test_xu_ly_luu_va_don_30_ngay(tmp_path, monkeypatch):
    from app import nap as n
    monkeypatch.setattr(n, "ORPHAN_DB", tmp_path / "s.sqlite")
    g.danh_dau_xu_ly("u1", "dv")
    assert g.da_xu_ly() == {"u1": "dv"}
    c = g._conn_xu_ly()
    c.execute("UPDATE gplx_da_xu_ly SET luc = datetime('now', '-31 day')")
    c.commit()
    c.close()
    assert g.da_xu_ly() == {}


def test_ds_vps_loi_la_chua_kiem_duoc_khong_phai_0(auth_headers, monkeypatch):
    def hong(*a, **k):
        raise VpsLoi("x", 502)
    monkeypatch.setattr(vps, "gplx_bo_sung", hong)
    d = client.get("/local/ho-so/gplx-bo-sung", headers=auth_headers).json()
    assert d == {"kiem_duoc": False, "items": []}


def test_luu_tu_ban_web_ghi_dau_van_sau_khi_ghi_db(auth_headers, nap, monkeypatch):
    nap()
    goi = []
    monkeypatch.setattr(g, "danh_dau_sau_luu", lambda u, d: goi.append((u, d)))
    monkeypatch.setattr(hoso, "_hv_co_o_dich", lambda c: True)
    r = client.put("/local/ho-so/gplx?ma_dk=M1", headers=auth_headers,
                   json={"gplx": [B2], "tho": THO_TRONG, "ban_web": {"uuid": "u1", "dau_van": "dv"}})
    assert r.status_code == 200 and r.json()["co_o_dich"] is True
    assert goi == [("u1", "dv")]


def test_luu_loi_khong_ghi_dau_van(auth_headers, nap, monkeypatch):
    nap(rowcount=0)
    goi = []
    monkeypatch.setattr(g, "danh_dau_sau_luu", lambda u, d: goi.append(u))
    r = client.put("/local/ho-so/gplx?ma_dk=M1", headers=auth_headers,
                   json={"gplx": [B2], "tho": THO_TRONG, "ban_web": {"uuid": "u1", "dau_van": "dv"}})
    assert r.status_code == 409 and goi == []


def test_bo_qua_ghi_dau_van(auth_headers, tmp_path, monkeypatch):
    from app import nap as n
    monkeypatch.setattr(n, "ORPHAN_DB", tmp_path / "s.sqlite")
    assert client.post("/local/ho-so/gplx/bo-qua", headers=auth_headers, json={"uuid": "u1", "dau_van": "dv"}).status_code == 200
    assert g.da_xu_ly() == {"u1": "dv"}
