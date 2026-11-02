"""NAP-01 (phần ①) — kéo hàng đợi VPS → staging + nạp lô (mức 2).

Phủ:
- iso_to_yyyymmdd: đổi ngày cấp CCCD ISO → yyyymmdd (SP cần varchar(8)).
- staging keo_ve: upsert dedup theo uuid, danh sách, cập nhật trạng thái.
- /local/nap/keo: gọi VPS (mock) → ghi staging; VPS lỗi → 502.
- /local/nap/keo/{uuid}/anh: proxy ảnh từ VPS (mock); chưa có ảnh → 404.
- /local/nap/nap-lo: lock→nạp→da-nap mỗi HV; 1 HV lỗi không hỏng lô + mở khóa lại.

Mock lớp VPS (app.vps) và lõi nạp (_nap_mot) để không cần VPS/SQL Server thật.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import nap, session
from app import vps as vps_mod
from app.main import app
from app.routers import nap as nap_router
from app.vps import VpsLoi

client = TestClient(app)


# ---- Fixtures ----------------------------------------------------------------
@pytest.fixture
def staging_tmp(tmp_path, monkeypatch):
    """Dời staging.sqlite sang thư mục tạm — không đụng staging thật của máy."""
    monkeypatch.setattr(nap, "ORPHAN_DB", tmp_path / "staging.sqlite")


@pytest.fixture
def op_headers(monkeypatch):
    """Phiên operator có vps_token (khác auth_headers mặc định — cần cho /keo, /nap-lo)."""
    token = "test-keo-token"
    session._phien_theo_token[token] = session.Phien(
        username="op-test", ho_ten="NV Nạp", vai_tro="operator", vps_token="jwt-vps-gia"
    )
    yield {"Authorization": f"Bearer {token}"}
    session._phien_theo_token.pop(token, None)


def _keo_row(uuid: str, **kw) -> dict:
    row = {
        "uuid": uuid, "so_cccd": "012345678901", "so_cmnd_cu": None,
        "ho_ten": "nguyễn văn a", "ngay_sinh": "20000101", "gioi_tinh": "M",
        "noi_tt_raw": "Xã X, Tỉnh Y", "ngay_cap_cccd": "2021-03-10",
        "noi_cap_cccd": "Cục CS", "co_anh": True, "created_at": "2026-10-01T08:00:00+00:00",
    }
    row.update(kw)
    return row


def _nap_item(uuid: str) -> dict:
    """1 HV đã được UI chuẩn bị đủ (payload NapIn)."""
    return {
        "uuid": uuid, "ma_khoa_hoc": "70004K26B010", "ho_ten": "NGUYỄN VĂN A",
        "ngay_sinh": "20000101", "gioi_tinh": "M", "so_cmt": "012345678901",
        "noi_tt_ma_dvhc": "26998", "noi_tt_ma_dvql": "26",
    }


# ---- Hàm thuần ---------------------------------------------------------------
def test_iso_to_yyyymmdd():
    assert nap.iso_to_yyyymmdd("2021-03-10") == "20210310"
    assert nap.iso_to_yyyymmdd("20210310") == "20210310"
    assert nap.iso_to_yyyymmdd(None) == ""
    assert nap.iso_to_yyyymmdd("") == ""
    assert nap.iso_to_yyyymmdd("2021") == ""  # thiếu ngày/tháng → bỏ, không đoán


# ---- staging keo_ve ----------------------------------------------------------
def test_keo_ve_upsert_them_moi(staging_tmp):
    moi, tuoi, reset = nap.keo_ve_upsert([_keo_row("u1"), _keo_row("u2")])
    assert (moi, tuoi, reset) == (2, 0, 0)
    moi2, tuoi2, reset2 = nap.keo_ve_upsert([_keo_row("u2"), _keo_row("u3")])  # u2 còn 'cho' → làm tươi; u3 mới
    assert (moi2, tuoi2, reset2) == (1, 1, 0)
    assert {r["uuid"] for r in nap.keo_ve_danh_sach()} == {"u1", "u2", "u3"}


def test_keo_ve_lam_tuoi_ban_cho(staging_tmp):
    # CHANGES #11: kéo lại cập nhật bản còn 'cho' (collector sửa ở app web sau khi đã kéo).
    nap.keo_ve_upsert([_keo_row("u1", ho_ten="Tên Cũ")])
    moi, tuoi, reset = nap.keo_ve_upsert([_keo_row("u1", ho_ten="Tên Mới")])
    assert (moi, tuoi, reset) == (0, 1, 0)
    assert nap.keo_ve_danh_sach()[0]["ho_ten"] == "Tên Mới"


def test_keo_ve_khong_dung_ban_da_nap(staging_tmp):
    # Bản 'xong'/'loi' GIỮ nguyên, kéo lại không làm tươi.
    nap.keo_ve_upsert([_keo_row("u1", ho_ten="Tên Cũ")])
    nap.keo_ve_cap_nhat("u1", trang_thai="xong", ma_dk="M1", so_ho_so="056")
    moi, tuoi, reset = nap.keo_ve_upsert([_keo_row("u1", ho_ten="Tên Mới")])
    assert (moi, tuoi, reset) == (0, 0, 0)
    r = nap.keo_ve_danh_sach()[0]
    assert r["ho_ten"] == "Tên Cũ" and r["trang_thai"] == "xong"


def test_keo_ve_upsert_doi_ngay_cap(staging_tmp):
    nap.keo_ve_upsert([_keo_row("u1", ngay_cap_cccd="2021-03-10")])
    r = nap.keo_ve_danh_sach()[0]
    assert r["ngay_cap"] == "20210310"  # đã đổi ISO → yyyymmdd
    assert r["trang_thai"] == "cho"


def test_keo_ve_cap_nhat(staging_tmp):
    nap.keo_ve_upsert([_keo_row("u1")])
    nap.keo_ve_cap_nhat("u1", trang_thai="xong", ma_dk="70004K26B010001", so_ho_so="056")
    r = nap.keo_ve_danh_sach()[0]
    assert r["trang_thai"] == "xong"
    assert r["ma_dk"] == "70004K26B010001"
    assert r["so_ho_so"] == "056"


# ---- /local/nap/keo ----------------------------------------------------------
def test_keo_ghi_staging(staging_tmp, op_headers, monkeypatch):
    goi = {"n": 0}

    def fake_keo(token, limit=200, cursor=None):
        goi["n"] += 1
        return [_keo_row("u1"), _keo_row("u2")] if goi["n"] == 1 else []

    monkeypatch.setattr(vps_mod, "keo", fake_keo)
    monkeypatch.setattr(vps_mod, "da_xoa", lambda token, since=None: {"uuids": [], "moc": None})
    r = client.post("/local/nap/keo", headers=op_headers)
    assert r.status_code == 200
    assert r.json() == {"keo_ve": 2, "lam_tuoi": 0, "bo_da_xoa": 0, "dia_chi_reset": 0, "tong": 2}
    assert len(nap.keo_ve_danh_sach()) == 2


def test_keo_vps_loi_502(staging_tmp, op_headers, monkeypatch):
    def fake_keo(token, limit=200, cursor=None):
        raise VpsLoi("VPS sập", 500)

    monkeypatch.setattr(vps_mod, "keo", fake_keo)
    assert client.post("/local/nap/keo", headers=op_headers).status_code == 502


def test_keo_chua_dang_nhap_401(staging_tmp):
    assert client.post("/local/nap/keo").status_code in (401, 403)


def test_danh_sach(staging_tmp, op_headers):
    nap.keo_ve_upsert([_keo_row("u1")])
    r = client.get("/local/nap/danh-sach", headers=op_headers)
    assert r.status_code == 200
    assert r.json()[0]["uuid"] == "u1"


# ---- /local/nap/keo/{uuid}/anh ----------------------------------------------
def test_tai_anh_proxy(op_headers, monkeypatch):
    monkeypatch.setattr(vps_mod, "tai_anh", lambda token, uuid: b"\xff\xd8\xff\xe0abc")
    r = client.get("/local/nap/keo/u1/anh", headers=op_headers)
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/jpeg"
    assert r.content[:3] == b"\xff\xd8\xff"


def test_tai_anh_chua_co_404(op_headers, monkeypatch):
    monkeypatch.setattr(vps_mod, "tai_anh", lambda token, uuid: None)
    assert client.get("/local/nap/keo/u1/anh", headers=op_headers).status_code == 404


# ---- /local/nap/nap-lo -------------------------------------------------------
def test_nap_lo_thanh_cong(staging_tmp, op_headers, monkeypatch):
    nap.keo_ve_upsert([_keo_row("u1"), _keo_row("u2")])
    monkeypatch.setattr(vps_mod, "lock", lambda t, u: None)
    monkeypatch.setattr(vps_mod, "da_nap", lambda t, u, ma_dk: None)
    monkeypatch.setattr(vps_mod, "unlock", lambda t, u: None)
    monkeypatch.setattr(
        nap_router, "_nap_mot",
        lambda body: {"ma_dk": f"MDK-{body.uuid}", "so_ho_so": "056", "so_giay_to": 3},
    )
    r = client.post("/local/nap/nap-lo", headers=op_headers,
                    json={"items": [_nap_item("u1"), _nap_item("u2")]})
    assert r.status_code == 200
    kq = r.json()
    assert kq["tong"] == 2 and kq["thanh_cong"] == 2 and kq["that_bai"] == 0
    # staging cập nhật 'xong'
    tt = {x["uuid"]: x["trang_thai"] for x in nap.keo_ve_danh_sach()}
    assert tt == {"u1": "xong", "u2": "xong"}


def test_nap_lo_mot_loi_khong_hong_lo(staging_tmp, op_headers, monkeypatch):
    nap.keo_ve_upsert([_keo_row("u1"), _keo_row("u2")])
    mo_khoa = []
    monkeypatch.setattr(vps_mod, "lock", lambda t, u: None)
    monkeypatch.setattr(vps_mod, "da_nap", lambda t, u, ma_dk: None)
    monkeypatch.setattr(vps_mod, "unlock", lambda t, u: mo_khoa.append(u))

    def fake_nap(body):
        if body.uuid == "u1":
            raise ValueError("CCCD/CMND đã có học viên trong khóa")
        return {"ma_dk": "MDK-u2", "so_ho_so": "056", "so_giay_to": 3}

    monkeypatch.setattr(nap_router, "_nap_mot", fake_nap)
    r = client.post("/local/nap/nap-lo", headers=op_headers,
                    json={"items": [_nap_item("u1"), _nap_item("u2")]})
    kq = r.json()
    assert kq["thanh_cong"] == 1 and kq["that_bai"] == 1
    tt = {x["uuid"]: x for x in nap.keo_ve_danh_sach()}
    assert tt["u1"]["trang_thai"] == "loi"
    assert "đã có học viên" in tt["u1"]["loi"]
    assert tt["u2"]["trang_thai"] == "xong"
    assert mo_khoa == ["u1"]  # HV lỗi được mở khóa lại trên VPS


def test_nap_lo_trung_uuid_khong_goi_da_nap(staging_tmp, op_headers, monkeypatch):
    """Phòng tuyến 2 (QLY-09, chặn phantom BUG-01): `_nap_mot` trả VÉ CŨ (`trung_uuid`, không INSERT)
    → `nap_fn` KHÔNG gọi `vps.da_nap` (không đánh dấu imported cho bản không thực vào CSDT)."""
    nap.keo_ve_upsert([_keo_row("u1")])
    da_nap_goi = []
    monkeypatch.setattr(vps_mod, "lock", lambda t, u: None)
    monkeypatch.setattr(vps_mod, "da_nap", lambda t, u, ma_dk: da_nap_goi.append(u))
    monkeypatch.setattr(vps_mod, "unlock", lambda t, u: None)
    monkeypatch.setattr(
        nap_router, "_nap_mot",
        lambda body: {"ma_dk": "MDK-u1", "so_ho_so": "056", "so_giay_to": 3, "trung_uuid": True},
    )
    r = client.post("/local/nap/nap-lo", headers=op_headers, json={"items": [_nap_item("u1")]})
    assert r.status_code == 200 and r.json()["thanh_cong"] == 1
    assert da_nap_goi == []  # vé cũ → KHÔNG da_nap


def test_nap_lo_nap_moi_van_goi_da_nap(staging_tmp, op_headers, monkeypatch):
    """Đối chứng: nạp MỚI (không `trung_uuid`) → vẫn gọi `da_nap` như thường."""
    nap.keo_ve_upsert([_keo_row("u1")])
    da_nap_goi = []
    monkeypatch.setattr(vps_mod, "lock", lambda t, u: None)
    monkeypatch.setattr(vps_mod, "da_nap", lambda t, u, ma_dk: da_nap_goi.append(u))
    monkeypatch.setattr(vps_mod, "unlock", lambda t, u: None)
    monkeypatch.setattr(nap_router, "_nap_mot",
                        lambda body: {"ma_dk": "MDK-u1", "so_ho_so": "056", "so_giay_to": 3})
    client.post("/local/nap/nap-lo", headers=op_headers, json={"items": [_nap_item("u1")]})
    assert da_nap_goi == ["u1"]


def test_nap_lo_lock_409_ghi_loi(staging_tmp, op_headers, monkeypatch):
    nap.keo_ve_upsert([_keo_row("u1")])
    monkeypatch.setattr(vps_mod, "lock", lambda t, u: (_ for _ in ()).throw(VpsLoi("đang nạp", 409)))
    monkeypatch.setattr(vps_mod, "da_nap", lambda t, u, ma_dk: None)
    unlock_goi = []
    monkeypatch.setattr(vps_mod, "unlock", lambda t, u: unlock_goi.append(u))
    monkeypatch.setattr(nap_router, "_nap_mot", lambda body: {"ma_dk": "X", "so_ho_so": "1", "so_giay_to": 0})
    r = client.post("/local/nap/nap-lo", headers=op_headers, json={"items": [_nap_item("u1")]})
    kq = r.json()
    assert kq["that_bai"] == 1
    assert unlock_goi == []  # lock thất bại → KHÔNG mở khóa (không phải mình khóa)
    assert nap.keo_ve_danh_sach()[0]["trang_thai"] == "loi"


# ---- NAP-01 #51: "Bỏ khỏi hàng đợi" + tombstone (POST /local/nap/bo-qua) -----
def test_keo_ve_xoa_va_trang_thai(staging_tmp):
    nap.keo_ve_upsert([_keo_row("u1"), _keo_row("u2")])
    assert nap.keo_ve_trang_thai("u1") == "cho"
    assert nap.keo_ve_trang_thai("khong-co") is None
    nap.keo_ve_xoa("u1")
    assert nap.keo_ve_trang_thai("u1") is None
    assert {r["uuid"] for r in nap.keo_ve_danh_sach()} == {"u2"}


def test_bo_qua_chua_dang_nhap_401(staging_tmp):
    assert client.post("/local/nap/bo-qua", json={"uuids": ["u1"]}).status_code in (401, 403)


def test_bo_qua_dong_cho_ghi_tombstone(staging_tmp, op_headers):
    """Dòng 'cho' → bỏ được + ghi tombstone (kéo lại không về). Khác hẳn hành vi cũ chặn 409."""
    nap.keo_ve_upsert([_keo_row("u1")])
    r = client.post("/local/nap/bo-qua", headers=op_headers, json={"uuids": ["u1"]})
    assert r.status_code == 200 and r.json() == {"bo": 1, "tombstone": 1}
    assert nap.keo_ve_trang_thai("u1") is None       # đã khỏi hàng đợi
    assert "u1" in nap._bo_qua_uuids()               # tombstone ghi


def test_bo_qua_uuid_khong_co_van_ghi_tombstone(staging_tmp, op_headers):
    """uuid đã trôi khỏi keo_ve (kéo trôi / gọi lại) → None → vẫn ghi tombstone (chặn kéo lại)."""
    r = client.post("/local/nap/bo-qua", headers=op_headers, json={"uuids": ["khong-co"]})
    assert r.status_code == 200 and r.json() == {"bo": 1, "tombstone": 1}


def test_bo_qua_dong_xong_khong_tombstone(staging_tmp, op_headers):
    """Dòng 'xong' (đã nạp) → xóa khỏi staging nhưng KHÔNG tombstone (QLY-08 cần kéo lại được)."""
    nap.keo_ve_upsert([_keo_row("u1")])
    nap.keo_ve_cap_nhat("u1", trang_thai="xong", ma_dk="M1", so_ho_so="056")
    r = client.post("/local/nap/bo-qua", headers=op_headers, json={"uuids": ["u1"]})
    assert r.status_code == 200 and r.json() == {"bo": 1, "tombstone": 0}
    assert nap.keo_ve_trang_thai("u1") is None
    assert "u1" not in nap._bo_qua_uuids()


def test_bo_qua_nhieu_mot_luot(staging_tmp, op_headers):
    """Bỏ nhiều một lượt: 'cho'+'loi' ghi tombstone, 'xong' không; tất cả rời hàng đợi."""
    nap.keo_ve_upsert([_keo_row("u1"), _keo_row("u2"), _keo_row("u3")])
    nap.keo_ve_cap_nhat("u2", trang_thai="loi", loi="trùng CCCD")
    nap.keo_ve_cap_nhat("u3", trang_thai="xong", ma_dk="M3", so_ho_so="056")
    r = client.post("/local/nap/bo-qua", headers=op_headers, json={"uuids": ["u1", "u2", "u3"]})
    assert r.status_code == 200 and r.json() == {"bo": 3, "tombstone": 2}  # u1 cho + u2 loi
    assert nap.keo_ve_danh_sach() == []
    assert nap._bo_qua_uuids() == {"u1", "u2"}


def test_bo_qua_don_nhap_ben(staging_tmp, op_headers):
    """Bỏ qua dòng 'cho' có nháp bền (ảnh PII) → nháp bị dọn (nhap_xoa) đầu-cuối."""
    nap.keo_ve_upsert([_keo_row("u1")])
    nap.nhap_luu("u1", jp2_b64="anh-pii", chi_tiet="123 Lê Lợi")
    assert nap.nhap_doc("u1") is not None               # tiền đề: có nháp
    client.post("/local/nap/bo-qua", headers=op_headers, json={"uuids": ["u1"]})
    assert nap.nhap_doc("u1") is None                   # nháp (gồm ảnh) đã dọn


def test_bo_qua_lo_rong_noop(staging_tmp, op_headers):
    r = client.post("/local/nap/bo-qua", headers=op_headers, json={"uuids": []})
    assert r.status_code == 200 and r.json() == {"bo": 0, "tombstone": 0}


def test_bo_qua_vuot_tran_422(staging_tmp, op_headers):
    body = {"uuids": [f"u{i}" for i in range(1001)]}
    assert client.post("/local/nap/bo-qua", headers=op_headers, json=body).status_code == 422


def test_bo_qua_idempotent(staging_tmp, op_headers):
    """Gọi lại cùng uuid → tombstone đã có nên ghi mới = 0 (INSERT OR IGNORE)."""
    nap.keo_ve_upsert([_keo_row("u1")])
    client.post("/local/nap/bo-qua", headers=op_headers, json={"uuids": ["u1"]})
    r = client.post("/local/nap/bo-qua", headers=op_headers, json={"uuids": ["u1"]})
    assert r.json() == {"bo": 1, "tombstone": 0}


def test_keo_ve_upsert_loc_bo_tombstone(staging_tmp, op_headers):
    """keo_ve_upsert lọc bỏ uuid đã bỏ qua → kéo lại KHÔNG mang về (dù VPS còn gửi)."""
    nap.keo_ve_upsert([_keo_row("u1")])
    client.post("/local/nap/bo-qua", headers=op_headers, json={"uuids": ["u1"]})
    moi, tuoi, _ = nap.keo_ve_upsert([_keo_row("u1")])  # VPS vẫn gửi u1 (còn pending)
    assert (moi, tuoi) == (0, 0)                        # bị lọc: không thêm, không làm tươi
    assert nap.keo_ve_danh_sach() == []


def test_tombstone_khong_chan_uuid_moi(staging_tmp, op_headers):
    """Gửi lại = uuid mới → không khớp tombstone → hiện lại bình thường (PRD edge #51)."""
    nap.keo_ve_upsert([_keo_row("u1")])
    client.post("/local/nap/bo-qua", headers=op_headers, json={"uuids": ["u1"]})
    moi, _, _ = nap.keo_ve_upsert([_keo_row("u2")])     # hồ sơ gửi lại mang uuid mới
    assert moi == 1
    assert {r["uuid"] for r in nap.keo_ve_danh_sach()} == {"u2"}


# ---- QLY-08: staging helper tra uuid theo ma_dk + đưa dòng về 'cho' ----
def test_lay_uuid_theo_ma_dk(staging_tmp):
    nap._done_set("uuid-A", {"ma_dk": "MADK-A", "so_ho_so": "056", "so_giay_to": 3})
    assert nap.lay_uuid_theo_ma_dk("MADK-A") == "uuid-A"
    assert nap.lay_uuid_theo_ma_dk("MADK-KHONG-CO") is None


def test_keo_ve_ve_cho_dua_dong_da_nap_ve_cho(staging_tmp):
    """Dòng đã 'xong' (nạp) → về 'cho', gỡ ma_dk/so_ho_so → UI thấy lại như HV chờ nạp."""
    nap.keo_ve_upsert([_keo_row("u1")])
    nap.keo_ve_cap_nhat("u1", trang_thai="xong", ma_dk="M1", so_ho_so="056")
    assert nap.keo_ve_ve_cho("u1") is True
    assert nap.keo_ve_trang_thai("u1") == "cho"
    row = next(r for r in nap.keo_ve_danh_sach() if r["uuid"] == "u1")
    assert row["ma_dk"] is None and row["so_ho_so"] is None


def test_keo_ve_ve_cho_dong_da_bo_khoi_hang_doi(staging_tmp):
    """Dòng không còn trong staging (đã 'Bỏ khỏi hàng đợi') → False để UI gợi ý Kéo về."""
    assert nap.keo_ve_ve_cho("khong-co") is False


def test_keo_ve_ve_cho_go_ve_khoi_nap_xong(staging_tmp):
    """BUG-01: gỡ về chờ nạp PHẢI xóa vé 'đã nạp' (nap_xong). Không xóa thì nạp lại cùng uuid bị
    _done_get short-circuit → trả MaDK đã xóa, HV KHÔNG vào DB. (Fail trên code cũ.)"""
    nap.keo_ve_upsert([_keo_row("u1")])
    nap.keo_ve_cap_nhat("u1", trang_thai="xong", ma_dk="M1", so_ho_so="056")
    nap._done_set("u1", {"ma_dk": "M1", "so_ho_so": "056", "so_giay_to": 3})
    assert nap._done_get("u1") is not None            # tiền đề: vé đã nạp tồn tại
    nap.keo_ve_ve_cho("u1")
    assert nap._done_get("u1") is None                # vé bị gỡ → nạp lại sẽ INSERT thật


def test_keo_ve_ve_cho_go_ve_nap_xong_du_da_bo_khoi_hang_doi(staging_tmp):
    """BUG-01 biên: dòng keo_ve đã bị 'Bỏ khỏi hàng đợi' (chỉ còn vé nap_xong) → vẫn phải gỡ vé."""
    nap._done_set("u1", {"ma_dk": "M1", "so_ho_so": "056", "so_giay_to": 3})
    assert nap.keo_ve_ve_cho("u1") is False           # không còn dòng keo_ve → False
    assert nap._done_get("u1") is None                # nhưng vé vẫn phải bị gỡ


# ---- NAP-01 task 44: đồng bộ xóa (keo bỏ dòng 'cho' đã xóa ở app web) ----
def test_keo_ve_xoa_neu_cho_chi_bo_dong_cho(staging_tmp):
    nap.keo_ve_upsert([_keo_row("u1"), _keo_row("u2")])
    nap.keo_ve_cap_nhat("u2", trang_thai="xong", ma_dk="M2", so_ho_so="056")  # đã nạp
    assert nap.keo_ve_xoa_neu_cho("u1") is True    # 'cho' → bỏ
    assert nap.keo_ve_xoa_neu_cho("u2") is False   # 'xong' → GIỮ
    uuids = {r["uuid"] for r in nap.keo_ve_danh_sach()}
    assert uuids == {"u2"}


def test_moc_da_xoa_luu_doc(staging_tmp):
    assert nap.lay_moc_da_xoa() is None
    nap.luu_moc_da_xoa("2026-10-03T08:00:00+00:00")
    assert nap.lay_moc_da_xoa() == "2026-10-03T08:00:00+00:00"


def test_keo_dong_bo_bo_dong_da_xoa(staging_tmp, op_headers, monkeypatch):
    """Kéo về: dòng 'cho' nằm trong da-xoa → bị bỏ; dòng 'xong' đã xóa ở app → GIỮ (đã nạp rồi)."""
    # u1 'cho', u2 đã nạp 'xong' (từ trước)
    nap.keo_ve_upsert([_keo_row("u1")])
    nap.keo_ve_upsert([_keo_row("u2")])
    nap.keo_ve_cap_nhat("u2", trang_thai="xong", ma_dk="M2", so_ho_so="056")

    monkeypatch.setattr(vps_mod, "keo", lambda token, limit=200, cursor=None: [])  # không kéo thêm
    monkeypatch.setattr(vps_mod, "da_xoa",
                        lambda token, since=None: {"uuids": ["u1", "u2"], "moc": "2026-10-03T09:00:00+00:00"})
    r = client.post("/local/nap/keo", headers=op_headers)
    assert r.status_code == 200
    assert r.json()["bo_da_xoa"] == 1  # chỉ bỏ u1 ('cho'); u2 'xong' giữ
    uuids = {x["uuid"] for x in nap.keo_ve_danh_sach()}
    assert uuids == {"u2"}
    assert nap.lay_moc_da_xoa() == "2026-10-03T09:00:00+00:00"  # mốc đã tiến


def test_keo_dong_bo_vps_loi_khong_hong_keo(staging_tmp, op_headers, monkeypatch):
    """da-xoa lỗi → kéo vẫn thành công (bo_da_xoa=0), đồng bộ để lượt sau."""
    nap.keo_ve_upsert([_keo_row("u1")])
    monkeypatch.setattr(vps_mod, "keo", lambda token, limit=200, cursor=None: [])
    monkeypatch.setattr(vps_mod, "da_xoa",
                        lambda token, since=None: (_ for _ in ()).throw(VpsLoi("mất kết nối", None)))
    r = client.post("/local/nap/keo", headers=op_headers)
    assert r.status_code == 200 and r.json()["bo_da_xoa"] == 0
    assert {x["uuid"] for x in nap.keo_ve_danh_sach()} == {"u1"}  # KHÔNG bỏ nhầm khi da-xoa lỗi


# ---- NAP-01 task 50: nháp chuẩn bị BỀN (CHANGES #32, TDD §9.3a) --------------
def test_nhap_luu_doc_round_trip(staging_tmp):
    nap.nhap_luu("u1", dia_chi_json='{"xa":"X"}', chi_tiet="Số 1 Thôn A",
                 noi_cap="Cục CS", tick_json="[1,3]", jp2_b64="IMG64", anh_preview="PNG64")
    d = nap.nhap_doc("u1")
    assert d["dia_chi_json"] == '{"xa":"X"}' and d["chi_tiet"] == "Số 1 Thôn A"
    assert d["noi_cap"] == "Cục CS" and d["tick_json"] == "[1,3]"
    assert d["jp2_b64"] == "IMG64" and d["anh_preview"] == "PNG64"
    assert d["updated_at"]  # có mốc thời gian
    assert nap.nhap_doc("khong-co") is None


def test_nhap_luu_ghi_de(staging_tmp):
    nap.nhap_luu("u1", chi_tiet="cũ", jp2_b64="A")
    nap.nhap_luu("u1", chi_tiet="mới", jp2_b64="B", dia_chi_json="{}")
    d = nap.nhap_doc("u1")
    assert d["chi_tiet"] == "mới" and d["jp2_b64"] == "B" and d["dia_chi_json"] == "{}"


def test_nhap_co_cac_co(staging_tmp):
    nap.nhap_luu("u1", dia_chi_json='{"xa":"X"}', jp2_b64="IMG", tick_json="[3]")
    nap.nhap_luu("u2", dia_chi_json=None, jp2_b64=None, tick_json="[]")  # rỗng → False hết
    co = nap.nhap_co(["u1", "u2", "u3"])  # u3 chưa có nháp
    assert co == [
        {"uuid": "u1", "co_dia_chi": True, "co_anh": True, "co_tick": True, "gplx_da_co_json": None, "gplx_goc_json": None},
        {"uuid": "u2", "co_dia_chi": False, "co_anh": False, "co_tick": False, "gplx_da_co_json": None, "gplx_goc_json": None},
        {"uuid": "u3", "co_dia_chi": False, "co_anh": False, "co_tick": False, "gplx_da_co_json": None, "gplx_goc_json": None},
    ]
    assert nap.nhap_co([]) == []


def test_nhap_xoa_don_ca_anh(staging_tmp):
    nap.nhap_luu("u1", jp2_b64="IMG", dia_chi_json="{}")
    nap.nhap_xoa("u1")
    assert nap.nhap_doc("u1") is None
    nap.nhap_xoa("u1")  # idempotent — không lỗi khi gọi lại


def test_bug04_reset_dia_chi_khi_raw_doi(staging_tmp):
    """BUG-04: noi_tt_raw đổi khi làm tươi → reset địa chỉ nháp, GIỮ ảnh/tick/nơi cấp."""
    nap.keo_ve_upsert([_keo_row("u1", noi_tt_raw="Xã X, Tỉnh Y")])
    nap.nhap_luu("u1", dia_chi_json='{"xa":"X"}', chi_tiet="Số 1", noi_cap="Cục",
                 tick_json="[3]", jp2_b64="IMG", anh_preview="PNG")
    moi, tuoi, reset = nap.keo_ve_upsert([_keo_row("u1", noi_tt_raw="Xã Z, Tỉnh W")])
    assert (moi, tuoi, reset) == (0, 1, 1)
    d = nap.nhap_doc("u1")
    assert d["dia_chi_json"] is None and d["chi_tiet"] is None   # địa chỉ reset
    assert d["jp2_b64"] == "IMG" and d["anh_preview"] == "PNG"   # ảnh giữ
    assert d["tick_json"] == "[3]" and d["noi_cap"] == "Cục"     # tick/nơi cấp giữ


def test_bug04_khong_reset_khi_raw_khong_doi(staging_tmp):
    nap.keo_ve_upsert([_keo_row("u1", noi_tt_raw="Xã X, Tỉnh Y")])
    nap.nhap_luu("u1", dia_chi_json='{"xa":"X"}', chi_tiet="Số 1")
    _, tuoi, reset = nap.keo_ve_upsert([_keo_row("u1", noi_tt_raw="Xã X, Tỉnh Y")])
    assert (tuoi, reset) == (1, 0)  # làm tươi nhưng KHÔNG reset
    d = nap.nhap_doc("u1")
    assert d["dia_chi_json"] == '{"xa":"X"}' and d["chi_tiet"] == "Số 1"


def test_bug04_raw_doi_nhung_khong_co_nhap(staging_tmp):
    """raw đổi nhưng dòng chưa có nháp → reset=0 (không có gì để reset)."""
    nap.keo_ve_upsert([_keo_row("u1", noi_tt_raw="Xã X, Tỉnh Y")])
    _, tuoi, reset = nap.keo_ve_upsert([_keo_row("u1", noi_tt_raw="Xã Z, Tỉnh W")])
    assert (tuoi, reset) == (1, 0)


def test_nhap_xoa_khi_dong_bo_xoa(staging_tmp):
    """Đồng bộ xóa (keo_ve_xoa_neu_cho) bỏ dòng 'cho' → dọn luôn nháp bền (ảnh PII)."""
    nap.keo_ve_upsert([_keo_row("u1")])
    nap.nhap_luu("u1", jp2_b64="IMG")
    assert nap.keo_ve_xoa_neu_cho("u1") is True
    assert nap.nhap_doc("u1") is None


def test_nhap_don_khi_nap_xong(staging_tmp, op_headers, monkeypatch):
    """Nạp xong qua nap-lo → nháp bền (ảnh PII) tự xóa."""
    nap.keo_ve_upsert([_keo_row("u1")])
    nap.nhap_luu("u1", jp2_b64="IMG", dia_chi_json="{}")
    monkeypatch.setattr(vps_mod, "lock", lambda t, u: None)
    monkeypatch.setattr(vps_mod, "da_nap", lambda t, u, ma_dk: None)
    monkeypatch.setattr(vps_mod, "unlock", lambda t, u: None)
    monkeypatch.setattr(nap_router, "_nap_mot",
                        lambda body: {"ma_dk": "MDK-u1", "so_ho_so": "056", "so_giay_to": 3})
    r = client.post("/local/nap/nap-lo", headers=op_headers, json={"items": [_nap_item("u1")]})
    assert r.status_code == 200 and r.json()["thanh_cong"] == 1
    assert nap.nhap_doc("u1") is None  # nháp đã dọn


# ---- NAP-01 task 50: endpoint nháp bền --------------------------------------
def test_nhap_endpoints_401(staging_tmp):
    assert client.get("/local/nap/nhap?uuids=u1").status_code in (401, 403)
    assert client.get("/local/nap/nhap/u1").status_code in (401, 403)
    assert client.put("/local/nap/nhap/u1", json={}).status_code in (401, 403)
    assert client.delete("/local/nap/nhap/u1").status_code in (401, 403)


def test_nhap_put_get_co_delete_qua_endpoint(staging_tmp, op_headers):
    r = client.put("/local/nap/nhap/u1", headers=op_headers, json={
        "dia_chi_json": '{"xa":"X"}', "chi_tiet": "Số 1", "noi_cap": "Cục",
        "tick_json": "[3]", "jp2_b64": "IMG", "anh_preview": "PNG"})
    assert r.status_code == 200 and r.json()["ok"] is True
    full = client.get("/local/nap/nhap/u1", headers=op_headers).json()
    assert full["jp2_b64"] == "IMG" and full["anh_preview"] == "PNG" and full["chi_tiet"] == "Số 1"
    co = client.get("/local/nap/nhap", headers=op_headers, params={"uuids": "u1,u2"}).json()
    assert co == [
        {"uuid": "u1", "co_dia_chi": True, "co_anh": True, "co_tick": True, "gplx_da_co_json": None, "gplx_goc_json": None},
        {"uuid": "u2", "co_dia_chi": False, "co_anh": False, "co_tick": False, "gplx_da_co_json": None, "gplx_goc_json": None},
    ]
    # nút "Xóa nháp"
    assert client.delete("/local/nap/nhap/u1", headers=op_headers).status_code == 200
    assert client.get("/local/nap/nhap/u1", headers=op_headers).json()["jp2_b64"] is None


def test_nhap_get_chua_co_tra_rong_khong_404(staging_tmp, op_headers):
    full = client.get("/local/nap/nhap/moi-toanh", headers=op_headers).json()
    assert full["uuid"] == "moi-toanh" and full["dia_chi_json"] is None and full["jp2_b64"] is None
