# PCG-01 → PCG-04 — /kiemthu đóng Feature PCG (10/10/2026): bổ sung các ca sót sau khi soát độc lập.
"""Mức 2 bổ sung cho phân hệ Phân công GV – xe (backend, không DB thật).

Gồm: thứ tự ghi GIỮA các nhóm, luật "dữ liệu cũ" chỉ hạ mức dòng đã có sẵn (không để dòng mồ côi
hay dòng mới lọt qua), lỗi giữa chừng ở biên, sửa ghép xe giữ cột cũ, và các nhánh luật ghép xe
chưa có test. Dùng lại cursor giả của test_phancong_ghi.
"""
from datetime import datetime

import pytest

from app import phancong_nhat_ky as nk
from app import phancong_rules as r
from app import phancong_service as svc
from tests.test_phancong_ghi import _Db, _patch, client, hien_tai, khong_sp_xoa_lan, them_gv102
from tests.test_phancong_rules import P, _gh, _th, chay, ma_loi, xe

KHOA_MA = "75032K260010"


@pytest.fixture(autouse=True)
def _nhat_ky_tam(tmp_path, monkeypatch):
    monkeypatch.setattr(nk, "DB_PATH", tmp_path / "pc_nk_kt.sqlite")


def ghi(auth_headers, body, cb=True):
    return client.post("/local/phancong/ghi", headers=auth_headers,
                       json={**body, "xac_nhan_csdl_that": True, "da_xem_canh_bao": cb})


def loai(resp):
    return [x["loai"] for x in resp.json()["da_ghi"]]


# ── Ghi: thứ tự GIỮA các nhóm ──
def test_pcg04_ghi_tron_xoa_them_sua_dung_thu_tu_giua_cac_nhom(auth_headers, monkeypatch):
    db = _Db(); _patch(monkeypatch, db)
    d = them_gv102()
    d["ghep"] = [m for m in d["ghep"] if m["id"] != 11]         # bỏ ghép cũ (xóa)
    d["pc"][0]["den"] = "2026-12-10T00:00"                       # sửa phân công cũ
    resp = ghi(auth_headers, d)
    assert resp.status_code == 200, resp.text
    assert loai(resp) == ["gh_xoa", "gv_them", "xe_them", "pc_them", "gh_them", "pc_sua"]
    khong_sp_xoa_lan(db)


# ── Ghi: luật "dữ liệu cũ" — chặn đủ dòng mới / dòng mồ côi do chính bản nháp tạo ──
def test_pcg04_ghep_thu_hai_voi_xe_ngoai_khoa_van_bi_chan(auth_headers, monkeypatch):
    db = _Db(); _patch(monkeypatch, db)
    d = hien_tai()
    d["ghep"].append({"id": None, "ma": "75032101", "xe": "93C-9", "tu": "2026-10-15T00:00", "den": "2026-12-20T00:00"})
    resp = ghi(auth_headers, d)
    assert resp.status_code == 409 and resp.json()["detail"]["loi"] == "con_loi_chan", resp.text
    assert not db.execs


def test_pcg04_go_xe_khoi_khoa_nhung_giu_ghep_bi_chan(auth_headers, monkeypatch):
    db = _Db(); _patch(monkeypatch, db)
    d = hien_tai(); d["xe_khoa"] = []
    resp = ghi(auth_headers, d)
    assert resp.status_code == 409 and resp.json()["detail"]["loi"] == "con_loi_chan", resp.text
    assert not db.execs


def test_pcg04_xoa_thuc_hanh_cuoi_nhung_giu_ghep_bi_chan(auth_headers, monkeypatch):
    db = _Db(); _patch(monkeypatch, db)
    d = hien_tai(); d["pc"] = []
    resp = ghi(auth_headers, d)
    assert resp.status_code == 409 and resp.json()["detail"]["loi"] == "con_loi_chan", resp.text
    assert not db.execs


def test_pcg01_go_gv_khoi_khoa_nhung_giu_phan_cong_va_ghep_bi_chan(auth_headers, monkeypatch):
    db = _Db(); _patch(monkeypatch, db)
    d = hien_tai(); d["gv_khoa"] = []
    resp = ghi(auth_headers, d)
    assert resp.status_code == 409 and resp.json()["detail"]["loi"] == "con_loi_chan", resp.text
    assert not db.execs


def test_pcg04_cong_400_di_truoc_409_khi_chua_tich_csdl_that(auth_headers, monkeypatch):
    db = _Db(); _patch(monkeypatch, db)
    d = hien_tai(); d["xe_khoa"] = []                            # còn lỗi chặn
    resp = client.post("/local/phancong/ghi", headers=auth_headers, json={**d, "xac_nhan_csdl_that": False})
    assert resp.status_code == 400 and resp.json()["detail"]["loi"] == "thieu_xac_nhan_csdl_that"


def test_pcg04_409_canh_bao_chi_chua_canh_bao_va_dem_dung(auth_headers, monkeypatch):
    db = _Db(); _patch(monkeypatch, db)
    d = hien_tai(); d["pc"][0]["den"] = "2026-12-10T00:00"       # ⚠ thực hành chưa tới bế giảng
    d["ghep"][0]["den"] = "2026-12-10T00:00"
    resp = ghi(auth_headers, d, cb=False)
    det = resp.json()["detail"]
    assert resp.status_code == 409 and det["loi"] == "thieu_xac_nhan_canh_bao"
    assert det["so_canh_bao"] == len(det["vande"]) >= 1 and all(v["muc"] == r.CANH_BAO for v in det["vande"])


# ── Ghi: Bỏ ghép, lỗi giữa chừng ở biên, sửa giữ cột cũ ──
def test_pcg03_bo_ghep_co_id_xoa_khong_id_khong_ghi(auth_headers, monkeypatch):
    db = _Db(); _patch(monkeypatch, db)
    d = hien_tai(); d["ghep"][0]["xe"] = ""                      # bỏ ghép dòng đã có trong CDB
    d["ghep"].append({"id": "n9", "ma": "75032101", "xe": "", "tu": "2026-10-15T00:00", "den": "2026-12-20T00:00"})
    resp = ghi(auth_headers, d)
    assert resp.status_code == 200, resp.text
    assert loai(resp) == ["gh_xoa"] and db.execs[0][1] == (11,)  # dòng rỗng không id: không sinh thao tác
    khong_sp_xoa_lan(db)


def test_pcg04_loi_ngay_dong_dau_khong_ghi_gi_va_nhat_ky_that_bai(auth_headers, monkeypatch):
    db = _Db(fail_at=0); _patch(monkeypatch, db)
    resp = ghi(auth_headers, them_gv102())
    j = resp.json()
    assert resp.status_code == 200 and j["ok"] is False and j["da_ghi"] == [] and len(j["chua_ghi"]) == 4
    assert nk.gan_day(KHOA_MA)[0]["trang_thai"] == "that_bai"


def test_pcg04_loi_o_dong_cuoi_chua_ghi_rong_nhung_van_bao_loi(auth_headers, monkeypatch):
    db = _Db(fail_at=3); _patch(monkeypatch, db)                 # 4 bước: bước thứ 4 lỗi
    j = ghi(auth_headers, them_gv102()).json()
    assert j["ok"] is False and len(j["da_ghi"]) == 3 and len(j["chua_ghi"]) == 1
    assert nk.gan_day(KHOA_MA)[0]["trang_thai"] == "loi_giua_chung"


def test_pcg03_sua_ghep_giu_dia_diem_va_nguoi_tao_cu(auth_headers, monkeypatch):
    db = _Db(); _patch(monkeypatch, db)
    d = hien_tai(); d["pc"][0]["den"] = "2026-12-10T00:00"; d["ghep"][0]["den"] = "2026-12-10T00:00"
    resp = ghi(auth_headers, d)
    assert resp.status_code == 200, resp.text
    sql, p = next((s, p) for s, p in db.execs if "usp_LichSD_KhoaHoc_XeTap_Update" in s)
    cols = [c.split("=")[0].lstrip("@") for c in sql.split("dbo.usp_LichSD_KhoaHoc_XeTap_Update ")[1].split(", ")]
    u = dict(zip(cols, p))
    assert u["DiaDiem"] == "tại trung tâm" and u["NguoiTao"] == "admin"      # không đè bằng mặc định
    assert u["NguoiSua"] == "op-test" and u["NgayKT"] == datetime(2026, 12, 10)


def test_pcg04_id_cdb_chi_nhan_so_nguyen_duong_khong_nhan_bool_va_id_tam():
    assert svc._id_cdb(12) == 12 and svc._id_cdb("12") == 12 and svc._id_cdb(" 7 ") == 7
    assert svc._id_cdb(True) is None and svc._id_cdb("n1") is None
    assert svc._id_cdb("") is None and svc._id_cdb(None) is None


# ── Luật ghép xe — các nhánh chưa có test ──
def test_pcg03_ghep_xe_ngoai_pham_vi_khoa_bi_chan():
    xk = ("93C-1",)
    kg_00 = {"ma": "75032101", "xe": "93C-1", "tu": "2026-10-01T00:00", "den": "2026-12-20T00:00"}
    bg_sau = {"ma": "75032101", "xe": "93C-1", "tu": "2026-10-15T00:00", "den": "2026-12-21T00:00"}
    ok = {"ma": "75032101", "xe": "93C-1", "tu": "2026-10-01T07:30", "den": "2026-12-20T00:00"}
    assert "ghep_ngoai_khoa" in ma_loi(chay([_th()], [kg_00], xe_khoa=xk))
    assert "ghep_ngoai_khoa" in ma_loi(chay([_th()], [bg_sau], xe_khoa=xk))
    assert "ghep_ngoai_khoa" not in ma_loi(chay([_th()], [ok], xe_khoa=xk))


def test_pcg03_ghep_xe_thieu_ngay_va_bat_dau_khong_truoc_ket_thuc():
    xk = ("93C-1",)
    thieu = {"ma": "75032101", "xe": "93C-1", "tu": "", "den": "2026-12-20T00:00"}
    bang = {"ma": "75032101", "xe": "93C-1", "tu": "2026-10-15T00:00", "den": "2026-10-15T00:00"}
    assert "thieu_ngay" in ma_loi(chay([_th()], [thieu], xe_khoa=xk))
    assert "bd_sau_kt" in ma_loi(chay([_th()], [bang], xe_khoa=xk))


def test_pcg03_xe_khong_co_trong_danh_muc_bi_chan_con_gv_ngoai_khoa_o_ghep():
    v = chay([_th()], [_gh("75032101", "99X-9")], xe_khoa=("99X-9",))
    assert "xe_khong_ton_tai" in ma_loi(v)
    v2 = chay([_th()], [_gh("75032102", "93C-1")], xe_khoa=("93C-1",))       # GV 102 chưa trong khóa
    assert "gv_ngoai_khoa" in ma_loi(v2)


def test_pcg03_hai_ghep_cham_dau_mut_hoac_cung_ngay_khac_gio_khong_bao_trung():
    a = {"ma": "75032101", "xe": "93C-1", "tu": "2026-10-15T00:00", "den": "2026-11-15T00:00"}
    b = {"ma": "75032102", "xe": "93C-1", "tu": "2026-11-15T00:00", "den": "2026-12-20T00:00"}
    pc = [_th("75032101", 1), _th("75032102", 2)]
    kw = dict(gv_khoa=("75032101", "75032102"), xe_khoa=("93C-1",))
    assert "xe_hai_gv" not in ma_loi(chay(pc, [a, b], **kw), r.CANH_BAO)     # chạm đầu mút
    sang = dict(a, tu="2026-10-20T07:30", den="2026-10-20T11:30")
    chieu = dict(b, tu="2026-10-20T13:30", den="2026-10-20T17:30")
    assert "xe_hai_gv" not in ma_loi(chay(pc, [sang, chieu], **kw), r.CANH_BAO)
    c1 = dict(a, ma="75032101", xe="93C-1"); c2 = dict(a, xe="93C-2")
    assert "gv_hai_xe" in ma_loi(chay([_th()], [c1, c2], xe_khoa=("93C-1", "93C-2")), r.CANH_BAO)
    c3 = dict(a, xe="93C-2", tu="2026-11-15T00:00", den="2026-12-20T00:00")
    assert "gv_hai_xe" not in ma_loi(chay([_th()], [a, c3], xe_khoa=("93C-1", "93C-2")), r.CANH_BAO)


def test_pcg04_thuc_hanh_toi_be_giang_khong_canh_bao_chua_toi_thi_co():
    het = P(1, "75032101", [6], "2026-10-15T00:00", "2026-12-20T00:00")
    gan = P(1, "75032101", [6], "2026-10-15T00:00", "2026-12-19T00:00")
    lt = P(1, "75032101", [4], "2026-10-15T00:00", "2026-12-10T00:00")
    assert "th_chua_toi_be_giang" not in ma_loi(chay([het]), r.CANH_BAO)
    assert "th_chua_toi_be_giang" in ma_loi(chay([gan]), r.CANH_BAO)
    assert "th_chua_toi_be_giang" not in ma_loi(chay([lt]), r.CANH_BAO)      # chỉ môn Thực hành


@pytest.mark.parametrize("hang_gv", ["D1", "D2", "E"])
def test_pcg01_khoa_c1_nhan_gv_hang_d1_d2_e_day_thuc_hanh(hang_gv):
    from tests.test_phancong_rules import gv
    v = chay([_th()], gvs=[gv("75032101", hang=(hang_gv,))])
    assert "gv_lech_hang" not in {x["ma"] for x in v}


def test_pcg01_khoa_c1_gv_hang_a1_day_thuc_hanh_bi_canh_bao():
    from tests.test_phancong_rules import gv
    v = chay([_th()], gvs=[gv("75032101", hang=("A1",))])
    assert "gv_lech_hang" in ma_loi(v, r.CANH_BAO) and not r.co_chan(v)


def test_pcg04_xe_het_han_chi_bi_chan_khi_ghep_khong_chan_khi_chi_o_danh_sach():
    ds = chay([_th()], [], xe_khoa=("93C-9",), xes=[xe("93C-9", het="2026-11-30")])
    assert "xe_het_han" not in ma_loi(ds)                                    # PRD: thêm được, chỉ chặn khi ghép
    gh = chay([_th()], [_gh("75032101", "93C-9")], xe_khoa=("93C-9",), xes=[xe("93C-9", het="2026-11-30")])
    assert "xe_het_han" in ma_loi(gh)


# ── CHANGES #58 — chốt 9 điểm mơ hồ (10/10/2026) ──
def test_pcg02_gv_ly_thuyet_nhan_mon_thuc_hanh_canh_bao_khong_chan():            # E-2
    from tests.test_phancong_rules import gv
    v = chay([_th()], gvs=[gv("75032101", loai="LT")])
    assert "gv_lt_day_thuc_hanh" in ma_loi(v, r.CANH_BAO) and not r.co_chan(v)
    lt = P(1, "75032101", [4], "2026-10-06T00:00", "2026-10-08T00:00")
    assert "gv_lt_day_thuc_hanh" not in ma_loi(chay([lt], gvs=[gv("75032101", loai="LT")]), r.CANH_BAO)
    assert "gv_lt_day_thuc_hanh" not in ma_loi(chay([_th()], gvs=[gv("75032101", loai="AL")]), r.CANH_BAO)


def test_pcg04_khoa_dkkh_khong_doi_gi_ghi_tra_khong_co_thay_doi_khong_hoi_canh_bao(auth_headers, monkeypatch):   # E-6
    db = _Db(warn_dkkh=True); _patch(monkeypatch, db)
    resp = client.post("/local/phancong/ghi", headers=auth_headers,
                       json={**hien_tai(), "xac_nhan_csdl_that": True, "da_xem_canh_bao": False})
    assert resp.status_code == 200 and resp.json()["da_ghi"] == [] and not db.execs
    assert resp.json()["thong_bao"] == "Không có thay đổi để ghi."


def test_pcg04_khoa_dkkh_co_thay_doi_van_doi_xac_nhan_canh_bao(auth_headers, monkeypatch):
    db = _Db(warn_dkkh=True); _patch(monkeypatch, db)
    resp = client.post("/local/phancong/ghi", headers=auth_headers,
                       json={**them_gv102(), "xac_nhan_csdl_that": True, "da_xem_canh_bao": False})
    assert resp.status_code == 409 and resp.json()["detail"]["loi"] == "thieu_xac_nhan_canh_bao"


def test_pcg02_chua_toi_be_giang_tinh_theo_ca_gv_nhieu_dot_noi_tiep_khong_bao_oan():   # E-9
    dot1 = P(1, "75032101", [6], "2026-10-15T00:00", "2026-11-30T00:00")
    dot2 = P(2, "75032101", [6], "2026-11-30T00:00", "2026-12-20T00:00")
    assert "th_chua_toi_be_giang" not in ma_loi(chay([dot1, dot2]), r.CANH_BAO)
    dot2_ngan = P(2, "75032101", [6], "2026-11-30T00:00", "2026-12-10T00:00")
    v = chay([dot1, dot2_ngan])
    bao = [x for x in v if x["ma"] == "th_chua_toi_be_giang"]
    assert len(bao) == 1 and bao[0]["ref"] == "pc-2"                          # 1 cảnh báo/GV, ở đợt cuối


# ── CHANGES #59 — /reviewtdd §11E: dấu vân tay hiện trạng, khóa ghi, giới hạn đầu vào ──
def test_pcg04_ghi_dau_van_tay_khop_thi_ghi_lech_thi_409_khoa_da_doi(auth_headers, monkeypatch):   # 3.1
    db = _Db(); _patch(monkeypatch, db)
    r0 = client.post("/local/phancong/ghi", headers=auth_headers,
                     json={**hien_tai(), "xac_nhan_csdl_that": True}).json()
    dvt = r0["hien_trang"]["dau_van_tay"]
    assert isinstance(dvt, str) and len(dvt) == 20
    resp = ghi(auth_headers, {**them_gv102(), "dau_van_tay": dvt})
    assert resp.status_code == 200 and resp.json()["ok"] is True
    db2 = _Db(); _patch(monkeypatch, db2)
    resp = ghi(auth_headers, {**them_gv102(), "dau_van_tay": "0" * 20})              # CDB đã khác lúc mở
    assert resp.status_code == 409 and resp.json()["detail"]["loi"] == "khoa_da_doi" and not db2.execs


def test_pcg04_dau_van_tay_doi_khi_cdb_co_them_dong(auth_headers, monkeypatch):
    db = _Db(); _patch(monkeypatch, db)
    a = client.post("/local/phancong/ghi", headers=auth_headers,
                    json={**hien_tai(), "xac_nhan_csdl_that": True}).json()["hien_trang"]["dau_van_tay"]
    db.cur_gv.append({"MaLichLV": 3, "MaGV": "75032101", "la_ds": 0, "NgayBD": datetime(2026, 10, 2),
                      "NgayKT": datetime(2026, 10, 3), "MaMonHoc": None, "TenMonHoc": "4"})   # người khác vừa thêm
    b = client.post("/local/phancong/ghi", headers=auth_headers,
                    json={**hien_tai(), "xac_nhan_csdl_that": True}).json()["hien_trang"]["dau_van_tay"]
    assert a != b


def test_pcg04_ghi_dang_ghi_o_khoa_nay_thi_409_dang_ghi(auth_headers, monkeypatch):               # 3.2
    db = _Db(); _patch(monkeypatch, db)
    khoa = svc._khoa_ghi(KHOA_MA)
    assert khoa.acquire(blocking=False)
    try:
        resp = ghi(auth_headers, them_gv102())
        assert resp.status_code == 409 and resp.json()["detail"]["loi"] == "dang_ghi" and not db.execs
    finally:
        khoa.release()
    assert ghi(auth_headers, them_gv102()).status_code == 200                                      # nhả khóa thì ghi được


def test_pcg04_khoa_duoc_nha_ca_khi_ghi_loi(auth_headers, monkeypatch):
    db = _Db(fail_at=0); _patch(monkeypatch, db)
    ghi(auth_headers, them_gv102())
    khoa = svc._khoa_ghi(KHOA_MA)
    assert khoa.acquire(blocking=False)
    khoa.release()


def test_pcg03_dia_diem_qua_255_ky_tu_bi_tu_choi_truoc_khi_ghi(auth_headers, monkeypatch):         # 4.1
    db = _Db(); _patch(monkeypatch, db)
    d = them_gv102(); d["ghep"][-1]["dia_diem"] = "x" * 256
    resp = ghi(auth_headers, d)
    assert resp.status_code == 422 and not db.execs
    d["ghep"][-1]["dia_diem"] = "y" * 255
    assert ghi(auth_headers, d).status_code == 200


def test_pcg02_mon_khong_co_trong_danh_muc_bi_chan_o_buoc_kiem_tra():                               # 4.1
    v = chay([P(1, "75032101", [6, 99], "2026-10-15T00:00", "2026-12-20T00:00")])
    assert "mon_khong_ton_tai" in ma_loi(v)
    assert "mon_khong_ton_tai" not in ma_loi(chay([_th()]))
