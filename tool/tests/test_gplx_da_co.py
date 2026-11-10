# -*- coding: utf-8 -*-
"""GPLX đã có (NAP-07): đổi danh sách bằng → 6 tham số SP, nháp + keo_ve bền. Không chạm SQL Server."""
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import nap
from app.main import app

client = TestClient(app)

_HV = {"ho_ten": "NGUYỄN VĂN AN", "ngay_sinh": "20000101", "gioi_tinh": "M", "so_cmt": "079200000001",
       "noi_tt_ma_dvhc": "00097"}
_TEN = {"HoVaTen": "NGUYỄN VĂN AN", "HoVaTenIn": "NGUYỄN VĂN AN"}
_KHOA = {"ma_kh": "K1", "hang_gplx": "A1", "hang_dt": "A1", "ma_so_gtvt": "70"}
B2 = {"nhom": "cu", "hang": "B2", "so": "790000000123", "ngay_tt": "20120815", "ngay_cap": "20180427",
      "ngay_hh": "20280427", "don_vi": "70"}
A1 = {"nhom": "moi", "hang": "A1m", "so": "790000000456", "ngay_tt": "20250905", "ngay_cap": "20250920",
      "ngay_hh": "", "don_vi": "79"}


def _params(ds):
    return dict(nap.build_params_sp_gop({**_HV, "gplx_da_co": ds}, _KHOA, "001", _TEN, "1,2,3,", "op"))


@pytest.mark.parametrize("ds", [None, []])
def test_khong_co_bang_ghi_chuoi_rong_nhu_phan_mem_cu(ds):
    """Phần mềm cũ không bao giờ để NULL 7 cột này (DB Nạp + DB đích 0 dòng NULL, tra 10/11/2026)."""
    p = _params(ds)
    for k in ("p_SoGPLXDaCo", "p_HangGPLXDaCo", "p_NgayTTGPLXDaCo", "p_NgayCapGPLXDaCo", "p_NgayHHGPLXDaCo",
              "p_DVCapGPLXDaCo", "p_NoiCapGPLXDaCo"):
        assert p[k] == ""


def test_mot_bang_ghi_thang():
    p = _params([B2])
    assert p["p_SoGPLXDaCo"] == "790000000123"
    assert p["p_HangGPLXDaCo"] == "B2"
    assert p["p_NgayCapGPLXDaCo"] == "20180427"
    assert p["p_DVCapGPLXDaCo"] == "70"
    assert p["p_NoiCapGPLXDaCo"] == ""  # quốc gia cấp: rỗng, không NULL — NULL làm phần mềm cũ không hiện nơi cấp


def test_quoc_gia_cap_rong_theo_so_bang():
    assert nap.noi_cap_gplx_rong(None) == "" and nap.noi_cap_gplx_rong([]) == ""
    assert nap.noi_cap_gplx_rong([B2]) == ""
    assert _params([B2, A1])["p_NoiCapGPLXDaCo"] == "|"   # cùng số phần với các cột khác, như "70|70"


def test_hai_bang_noi_doc_theo_cung_thu_tu_o_trong_giu_vi_tri():
    p = _params([B2, A1])
    assert p["p_HangGPLXDaCo"] == "B2|A1m"
    assert p["p_SoGPLXDaCo"] == "790000000123|790000000456"
    assert p["p_NgayHHGPLXDaCo"] == "20280427|"
    assert p["p_DVCapGPLXDaCo"] == "70|79"


def test_khong_doi_so_va_thu_tu_tham_so_sp():
    p = list(nap.build_params_sp_gop({**_HV, "gplx_da_co": [B2]}, _KHOA, "001", _TEN, "1,2,3,", "op"))
    assert len(p) == 30
    ten = [k for k, _ in p]
    i = ten.index("p_GiayTo")
    assert ten[i + 1:i + 8] == ["p_SoGPLXDaCo", "p_HangGPLXDaCo", "p_NgayTTGPLXDaCo", "p_NgayCapGPLXDaCo",
                                "p_NgayHHGPLXDaCo", "p_DVCapGPLXDaCo", "p_NoiCapGPLXDaCo"]


@pytest.mark.parametrize("sua,tu_khoa", [
    ({"hang": "Z9"}, "hạng"),
    ({"hang": ""}, "hạng"),
    ({"so": ""}, "số"),
    ({"so": "1" * 21}, "số"),
    ({"so": "79000000012"}, "12 chữ số"),     # CHANGES #101: 11 số — gõ thiếu
    ({"so": "7900000001234"}, "12 chữ số"),   # 13 số — gõ thừa
    ({"so": "ay123456"}, "12 chữ số"),        # chữ thường: app web/tool đã viết hoa, server không tự sửa
    ({"so": "12|3"}, "|"),
    ({"don_vi": "700"}, "nơi cấp"),
    ({"ngay_cap": "20181332"}, "ngày cấp"),
    ({"ngay_tt": "15/08/2012"}, "ngày trúng tuyển"),
])
def test_du_lieu_sai_bao_ro(sua, tu_khoa):
    with pytest.raises(ValueError, match=r"(?i)" + tu_khoa.replace("|", r"\|")):
        nap.dung_chuoi_gplx_da_co([{**B2, **sua}])


@pytest.mark.parametrize("sua,tu_khoa", [
    ({"ngay_cap": ""}, "bắt buộc"),
    ({"ngay_tt": ""}, "bắt buộc"),
    ({"ngay_cap": "20100101"}, "sau ngày trúng tuyển"),
    ({"ngay_cap": "20990101"}, "sau hôm nay"),
    ({"ngay_hh": "20180427"}, "hết hạn"),
])
def test_quy_tac_ngay_khop_form_cu(sua, tu_khoa):
    with pytest.raises(ValueError, match=tu_khoa):
        nap.dung_chuoi_gplx_da_co([{**B2, **sua}])


def test_trung_hang_dang_ky_bi_chan():
    with pytest.raises(ValueError, match="trùng hạng"):
        nap.dung_chuoi_gplx_da_co([B2], "B2")
    assert nap.dung_chuoi_gplx_da_co([B2], "A1m")["p_HangGPLXDaCo"] == "B2"


def test_chua_du_18_tuoi_khi_cap_bi_chan():
    with pytest.raises(ValueError, match="18 tuổi"):
        nap.dung_chuoi_gplx_da_co([B2], ngay_sinh="20050101")
    assert nap.dung_chuoi_gplx_da_co([B2], ngay_sinh="20000427")["p_HangGPLXDaCo"] == "B2"
    assert nap.dung_chuoi_gplx_da_co([B2], ngay_sinh="20000000")["p_HangGPLXDaCo"] == "B2"  # chỉ có năm sinh


def test_qua_nhieu_bang_va_vuot_100_ky_tu():
    with pytest.raises(ValueError, match="tối đa"):
        nap.dung_chuoi_gplx_da_co([B2] * 9)
    with pytest.raises(ValueError, match="100 ký tự"):
        nap.dung_chuoi_gplx_da_co([{**B2, "so": "1" * 12}] * 8)  # 8 × 12 số + 7 dấu | = 103 > 100


@pytest.fixture
def staging_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(nap, "ORPHAN_DB", tmp_path / "staging.sqlite")
    return tmp_path / "staging.sqlite"


def test_nhap_luu_doc_va_co(staging_tmp):
    nap.nhap_luu("u1", gplx_da_co_json='[{"hang":"B2"}]', gplx_goc_json="goc")
    d = nap.nhap_doc("u1")
    assert d["gplx_da_co_json"] == '[{"hang":"B2"}]'
    assert d["gplx_goc_json"] == "goc"
    c = nap.nhap_co(["u1", "khong"])
    assert c[0]["gplx_da_co_json"] == '[{"hang":"B2"}]'
    assert c[1]["gplx_da_co_json"] is None


def test_nhap_phan_biet_chua_sua_va_da_xoa_het(staging_tmp):
    nap.nhap_luu("a", chi_tiet="x")
    nap.nhap_luu("b", gplx_da_co_json="[]")
    assert nap.nhap_doc("a")["gplx_da_co_json"] is None
    assert nap.nhap_doc("b")["gplx_da_co_json"] == "[]"


def test_migrate_bang_cu_chua_co_cot(staging_tmp):
    c = sqlite3.connect(str(staging_tmp))
    c.execute("CREATE TABLE nhap_chuan_bi (uuid TEXT PRIMARY KEY, dia_chi_json TEXT, chi_tiet TEXT, noi_cap TEXT, "
              "ngay_cap TEXT, tick_json TEXT, jp2_b64 TEXT, anh_preview TEXT, updated_at TEXT, chon_in_gplx INTEGER)")
    c.execute("CREATE TABLE keo_ve (uuid TEXT PRIMARY KEY, so_cccd TEXT, so_cmnd_cu TEXT, ho_ten TEXT, ngay_sinh TEXT, "
              "gioi_tinh TEXT, noi_tt_raw TEXT, ngay_cap TEXT, noi_cap_cccd TEXT, co_anh INT DEFAULT 0, created_at TEXT, "
              "trang_thai TEXT DEFAULT 'cho', loi TEXT, ma_dk TEXT, so_ho_so TEXT)")
    c.execute("INSERT INTO keo_ve (uuid, ho_ten) VALUES ('cu', 'A')")
    c.commit()
    c.close()
    assert nap.keo_ve_danh_sach()[0]["gplx_da_co_json"] is None
    nap.nhap_luu("moi", gplx_da_co_json="[]")
    assert nap.nhap_doc("moi")["gplx_da_co_json"] == "[]"


def _dong(**over):
    return {"uuid": "u1", "so_cccd": "079", "ho_ten": "A", "noi_tt_raw": "X", "created_at": "2026", **over}


def test_keo_ve_nhan_gplx_tu_vps_va_lam_tuoi_dong_cho(staging_tmp):
    nap.keo_ve_upsert([_dong(gplx_da_co=[B2])])
    assert json.loads(nap.keo_ve_danh_sach()[0]["gplx_da_co_json"])[0]["hang"] == "B2"
    nap.keo_ve_upsert([_dong(gplx_da_co=[A1])])
    assert json.loads(nap.keo_ve_danh_sach()[0]["gplx_da_co_json"])[0]["hang"] == "A1m"
    nap.keo_ve_upsert([_dong()])                       # VPS bỏ hết bằng
    assert nap.keo_ve_danh_sach()[0]["gplx_da_co_json"] is None


def test_lam_tuoi_khong_dung_vao_ban_nhan_vien_da_sua(staging_tmp):
    nap.keo_ve_upsert([_dong(gplx_da_co=[B2])])
    nap.nhap_luu("u1", gplx_da_co_json='[{"hang":"C"}]')
    nap.keo_ve_upsert([_dong(gplx_da_co=[A1])])
    assert nap.nhap_doc("u1")["gplx_da_co_json"] == '[{"hang":"C"}]'


def test_nap_xong_ghi_danh_sach_cuoi_va_dong_xong_khong_bi_de(staging_tmp):
    nap.keo_ve_upsert([_dong(gplx_da_co=[B2])])
    nap.keo_ve_cap_nhat("u1", trang_thai="xong", ma_dk="M", so_ho_so="001", gplx_da_co=[A1])
    assert json.loads(nap.keo_ve_danh_sach()[0]["gplx_da_co_json"])[0]["hang"] == "A1m"
    nap.keo_ve_upsert([_dong(gplx_da_co=[B2])])
    assert json.loads(nap.keo_ve_danh_sach()[0]["gplx_da_co_json"])[0]["hang"] == "A1m"


def test_nap_loi_khong_doi_gplx_keo_ve(staging_tmp):
    nap.keo_ve_upsert([_dong(gplx_da_co=[B2])])
    nap.keo_ve_cap_nhat("u1", trang_thai="loi", loi="x")
    assert json.loads(nap.keo_ve_danh_sach()[0]["gplx_da_co_json"])[0]["hang"] == "B2"


def test_api_nhap_round_trip(auth_headers, staging_tmp):
    assert client.put("/local/nap/nhap/u9", headers=auth_headers, json={"gplx_da_co_json": "[]"}).status_code == 200
    assert client.get("/local/nap/nhap/u9", headers=auth_headers).json()["gplx_da_co_json"] == "[]"
    assert client.get("/local/nap/nhap/chua", headers=auth_headers).json()["gplx_da_co_json"] is None


def test_api_nhap_qua_dai_422(auth_headers, staging_tmp):
    r = client.put("/local/nap/nhap/u9", headers=auth_headers, json={"gplx_da_co_json": "x" * 8001})
    assert r.status_code == 422


def test_nap_don_sai_gplx_tra_400_truoc_khi_dung_db(auth_headers):
    r = client.post("/local/nap", headers=auth_headers, json={
        "uuid": "u1", "ma_khoa_hoc": "K1", "ho_ten": "A", "ngay_sinh": "20000101", "gioi_tinh": "M",
        "so_cmt": "079200000001", "noi_tt_ma_dvhc": "00097", "noi_tt_ma_dvql": "00097",
        "gplx_da_co": [{"hang": "Z9", "so": "1", "ngay_tt": "20100101", "ngay_cap": "20180101"}]})
    assert r.status_code == 400
    assert "hạng" in r.json()["detail"]


def test_so_gplx_bang_giay_cu_hop_le():
    """CHANGES #101: bằng giấy bìa cũ 2 chữ cái + 6 số vẫn nạp được (có/không dấu cách)."""
    for so in ("AY 123456", "AH123456"):
        assert nap.dung_chuoi_gplx_da_co([{**B2, "so": so}], "A1m")["p_SoGPLXDaCo"] == so



def test_so_cu_sai_dang_giu_nguyen_thi_qua_so_moi_sai_thi_chan():
    """CHANGES #101: số đã lưu từ trước (DB/app web) giữ nguyên thì không chặn dạng; số mới sai dạng vẫn chặn."""
    cu = {**B2, "so": "79000000012"}
    assert nap.dung_chuoi_gplx_da_co([cu], "A1m", so_cu={"79000000012"})["p_SoGPLXDaCo"] == "79000000012"
    with pytest.raises(ValueError, match="12 chữ số"):
        nap.dung_chuoi_gplx_da_co([cu], "A1m")
    with pytest.raises(ValueError, match="12 chữ số"):
        nap.dung_chuoi_gplx_da_co([cu, {**B2, "hang": "C", "so": "7900000004"}], "A1m", so_cu={"79000000012"})
