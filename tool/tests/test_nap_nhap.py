"""NAP-01 / CHANGES #32 — Nháp chuẩn bị BỀN (staging.sqlite): lưu/đọc/cờ 2 chip/xóa/reset địa chỉ.

E2E AN TOÀN: chỉ ghi staging.sqlite TẠM (fixture dời ORPHAN_DB sang tmp), KHÔNG chạm SQL Server/VPS.
Phủ TDD §9.3a + Checkpoint 11:
- Nháp sống qua "F5/đóng-mở tool" (round-trip qua API — mỗi request mở kết nối sqlite mới).
- 2 chip Địa chỉ/Ảnh/Tick (nhap_co) phản ánh đúng; mặc định ✗ khi chưa làm.
- Xóa nháp dọn cả ảnh PII; idempotent.
- BUG-04: reset RIÊNG địa chỉ, giữ ảnh/tick/nơi cấp.
"""
import pytest
from fastapi.testclient import TestClient

from app import nap
from app.main import app

client = TestClient(app)


@pytest.fixture
def staging_tmp(tmp_path, monkeypatch):
    """Dời staging.sqlite sang thư mục tạm — không đụng staging thật của máy."""
    monkeypatch.setattr(nap, "ORPHAN_DB", tmp_path / "staging.sqlite")


# ---- Hàm thuần: lưu / đọc (bền trên sqlite) ----
def test_nhap_luu_doc_round_trip(staging_tmp):
    nap.nhap_luu("u1", dia_chi_json='{"xa":"X"}', chi_tiet="Số 1", noi_cap="70",
                 tick_json="[1,2]", jp2_b64="JP2B64", anh_preview="PNGB64")
    d = nap.nhap_doc("u1")
    assert d["dia_chi_json"] == '{"xa":"X"}' and d["chi_tiet"] == "Số 1"
    assert d["noi_cap"] == "70" and d["tick_json"] == "[1,2]"
    assert d["jp2_b64"] == "JP2B64" and d["anh_preview"] == "PNGB64"
    assert d["updated_at"]                                    # có mốc thời gian


def test_nhap_doc_khong_co_tra_none(staging_tmp):
    assert nap.nhap_doc("khong-ton-tai") is None


def test_nhap_luu_upsert_ghi_de(staging_tmp):
    nap.nhap_luu("u1", chi_tiet="cũ")
    nap.nhap_luu("u1", chi_tiet="mới", noi_cap="75")         # upsert cùng uuid
    d = nap.nhap_doc("u1")
    assert d["chi_tiet"] == "mới" and d["noi_cap"] == "75"


# ---- 2 chip (nhap_co) — cờ nhẹ, không trả ảnh ----
def test_nhap_co_ba_co_dung(staging_tmp):
    nap.nhap_luu("u1", dia_chi_json='{"xa":"X"}', jp2_b64="JP2")   # có địa chỉ + ảnh, KHÔNG tick
    co = {r["uuid"]: r for r in nap.nhap_co(["u1"])}
    assert co["u1"]["co_dia_chi"] is True
    assert co["u1"]["co_anh"] is True
    assert co["u1"]["co_tick"] is False


def test_nhap_co_mac_dinh_false(staging_tmp):
    # uuid chưa có nháp → cả 3 cờ False (chip xám mặc định)
    assert nap.nhap_co(["chua-co"]) == [
        {"uuid": "chua-co", "co_dia_chi": False, "co_anh": False, "co_tick": False}
    ]


def test_nhap_co_json_rong_la_false(staging_tmp):
    # dia_chi_json '{}' và tick_json '[]' coi như CHƯA có → KHÔNG bật chip
    nap.nhap_luu("u1", dia_chi_json="{}", tick_json="[]")
    co = nap.nhap_co(["u1"])[0]
    assert co["co_dia_chi"] is False and co["co_tick"] is False


def test_nhap_co_rong_tra_rong(staging_tmp):
    assert nap.nhap_co([]) == []


# ---- Xóa nháp (nút "Xóa nháp" + 3 điểm kết thúc dòng) ----
def test_nhap_xoa_don_sach_va_idempotent(staging_tmp):
    nap.nhap_luu("u1", dia_chi_json='{"xa":"X"}', jp2_b64="JP2")
    nap.nhap_xoa("u1")
    assert nap.nhap_doc("u1") is None                        # hết nháp (gồm ảnh PII)
    assert nap.nhap_co(["u1"])[0]["co_anh"] is False
    nap.nhap_xoa("u1")                                        # gọi lại không lỗi (idempotent)


# ---- BUG-04: reset RIÊNG địa chỉ, GIỮ ảnh/tick/nơi cấp ----
def test_nhap_reset_dia_chi_giu_anh_tick(staging_tmp):
    nap.nhap_luu("u1", dia_chi_json='{"xa":"cũ"}', chi_tiet="Số 1", noi_cap="70",
                 tick_json="[1]", jp2_b64="JP2", anh_preview="PNG")
    assert nap.nhap_reset_dia_chi("u1") is True
    d = nap.nhap_doc("u1")
    assert d["dia_chi_json"] is None and d["chi_tiet"] is None    # địa chỉ reset
    assert d["noi_cap"] == "70" and d["tick_json"] == "[1]"        # GIỮ
    assert d["jp2_b64"] == "JP2" and d["anh_preview"] == "PNG"     # GIỮ ảnh đã đổi nền


def test_nhap_reset_dia_chi_khong_co_tra_false(staging_tmp):
    nap.nhap_luu("other", chi_tiet="x")                      # DB tồn tại nhưng uuid khác
    assert nap.nhap_reset_dia_chi("khong-co") is False       # không có nháp → False (không toast)


# ---- E2E API: nháp BỀN qua "F5/đóng-mở tool" ----
def test_api_nhap_ben_qua_reload(staging_tmp, auth_headers):
    """PUT lưu nháp → GET đọc lại khớp. Mỗi request mở kết nối sqlite MỚI → mô phỏng F5/đóng-mở
    tool: nháp vẫn còn (bền trên đĩa), không phải chỉ ở RAM màn hình (gốc yêu cầu #32)."""
    body = {"dia_chi_json": '{"xa":"X"}', "chi_tiet": "Số 1", "noi_cap": "70",
            "tick_json": "[1,2]", "jp2_b64": "JP2", "anh_preview": "PNG"}
    r = client.put("/local/nap/nhap/u1", headers=auth_headers, json=body)
    assert r.status_code == 200 and r.json()["ok"] is True
    g = client.get("/local/nap/nhap/u1", headers=auth_headers)   # "mở lại tool"
    assert g.status_code == 200
    d = g.json()
    assert d["dia_chi_json"] == '{"xa":"X"}' and d["jp2_b64"] == "JP2"


def test_api_nhap_doc_chua_co_tra_rong_khong_404(staging_tmp, auth_headers):
    g = client.get("/local/nap/nhap/chua-chuan-bi", headers=auth_headers)
    assert g.status_code == 200                              # dòng mới chưa chuẩn bị là bình thường
    assert g.json()["dia_chi_json"] is None


def test_api_nhap_co_2_chip(staging_tmp, auth_headers):
    client.put("/local/nap/nhap/u1", headers=auth_headers, json={"dia_chi_json": '{"xa":"X"}'})
    r = client.get("/local/nap/nhap?uuids=u1,u2", headers=auth_headers)
    assert r.status_code == 200
    co = {x["uuid"]: x for x in r.json()}
    assert co["u1"]["co_dia_chi"] is True and co["u1"]["co_anh"] is False
    assert co["u2"] == {"uuid": "u2", "co_dia_chi": False, "co_anh": False, "co_tick": False}


def test_api_nhap_xoa(staging_tmp, auth_headers):
    client.put("/local/nap/nhap/u1", headers=auth_headers, json={"jp2_b64": "JP2"})
    d = client.delete("/local/nap/nhap/u1", headers=auth_headers)
    assert d.status_code == 200 and d.json()["ok"] is True
    g = client.get("/local/nap/nhap/u1", headers=auth_headers)
    assert g.json()["jp2_b64"] is None                      # đã dọn ảnh PII


def test_api_nhap_chua_dang_nhap_401(staging_tmp):
    # Cổng HTG-01③: mọi endpoint nháp cần đăng nhập
    assert client.get("/local/nap/nhap/u1").status_code == 401
    assert client.put("/local/nap/nhap/u1", json={}).status_code == 401
    assert client.delete("/local/nap/nhap/u1").status_code == 401
    assert client.get("/local/nap/nhap?uuids=u1").status_code == 401
