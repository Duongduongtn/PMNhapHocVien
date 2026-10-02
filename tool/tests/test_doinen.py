"""QLY-07 (task 39) — đổi nền trắng cả khóa: heuristic + backup + xử lý 1 HV + applock + endpoint.

Không cần rembg/SQL Server thật: mock image.doi_nen_anh + ghi_anh_update; heuristic chạy thật trên
ảnh PIL dựng tại chỗ.
"""
from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import doinen, image
from app.main import app

client = TestClient(app)


def _png(color: tuple[int, int, int]) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (40, 53), color).save(buf, format="PNG")
    return buf.getvalue()


# ---- heuristic 4 góc ---------------------------------------------------------
def test_anh_da_trang_nen_trang():
    assert image.anh_da_trang(_png((255, 255, 255))) is True


def test_anh_da_trang_nen_toi():
    assert image.anh_da_trang(_png((40, 40, 40))) is False


def test_anh_da_trang_file_hong_false():
    assert image.anh_da_trang(b"khong-phai-anh") is False  # hỏng → coi như chưa trắng


# ---- backup chỉ-nếu-chưa-có --------------------------------------------------
def test_backup_chi_neu_chua_co(tmp_path):
    src = tmp_path / "src.jp2"
    src.write_bytes(b"ANH-GOC")
    base = tmp_path / "img"
    base.mkdir()
    doinen._backup_neu_chua(src, "KX", "MDK1", str(base))
    dest = base / "KX" / "_BACKUP" / "MDK1.jp2"
    assert dest.read_bytes() == b"ANH-GOC"
    # chạy lần 2 với nguồn ĐÃ ĐỔI → KHÔNG đè backup gốc
    src.write_bytes(b"ANH-DA-DOI-NEN")
    doinen._backup_neu_chua(src, "KX", "MDK1", str(base))
    assert dest.read_bytes() == b"ANH-GOC"  # vẫn là bản gốc đầu tiên


# ---- xử lý 1 HV --------------------------------------------------------------
def test_xu_ly_mot_khong_file_bo_qua(tmp_path):
    td = doinen.TienDo()
    doinen.xu_ly_mot(None, "MDK1", "KX", str(tmp_path / "mat.jp2"), str(tmp_path),
                     "chua_trang", False, td)
    assert (td.bo_qua, td.xong, td.loi) == (1, 0, 0)


def test_xu_ly_mot_da_trang_bo_qua(tmp_path, monkeypatch):
    f = tmp_path / "a.jp2"
    f.write_bytes(b"x")
    monkeypatch.setattr(image, "anh_da_trang", lambda data: True)
    td = doinen.TienDo()
    doinen.xu_ly_mot(None, "MDK1", "KX", str(f), str(tmp_path), "chua_trang", False, td)
    assert (td.bo_qua, td.xong) == (1, 0)


def test_xu_ly_mot_tat_ca_khong_bo_qua_du_trang(tmp_path, monkeypatch):
    f = tmp_path / "a.jp2"
    f.write_bytes(b"x")
    monkeypatch.setattr(image, "anh_da_trang", lambda data: True)  # dù đã trắng
    monkeypatch.setattr(image, "doi_nen_anh", lambda data: b"JP2-MOI")
    ghi = []
    monkeypatch.setattr(doinen, "ghi_anh_update",
                        lambda cur, ma_dk, ma_kh, jp2, base, now: ghi.append((ma_dk, jp2)))
    td = doinen.TienDo()
    doinen.xu_ly_mot(object(), "MDK1", "KX", str(f), str(tmp_path), "tat_ca", False, td)
    assert td.xong == 1 and ghi == [("MDK1", b"JP2-MOI")]  # phạm vi 'tat_ca' bỏ qua heuristic


def test_xu_ly_mot_binh_thuong_ghi(tmp_path, monkeypatch):
    f = tmp_path / "a.jp2"
    f.write_bytes(b"x")
    monkeypatch.setattr(image, "anh_da_trang", lambda data: False)
    monkeypatch.setattr(image, "doi_nen_anh", lambda data: b"JP2-MOI")
    ghi = []
    monkeypatch.setattr(doinen, "ghi_anh_update",
                        lambda cur, ma_dk, ma_kh, jp2, base, now: ghi.append(ma_dk))
    td = doinen.TienDo()
    doinen.xu_ly_mot(object(), "MDK1", "KX", str(f), str(tmp_path), "chua_trang", True, td)
    assert td.xong == 1 and ghi == ["MDK1"]
    assert (tmp_path / "KX" / "_BACKUP" / "MDK1.jp2").exists()  # có backup (sao_luu=True)


# ---- applock -----------------------------------------------------------------
def test_bat_dau_applock_dang_chay():
    doinen._jobs["KLOCK"] = doinen.TienDo(dang_chay=True)
    try:
        with pytest.raises(RuntimeError):
            doinen.bat_dau("KLOCK", "chua_trang", True)
    finally:
        doinen._jobs.pop("KLOCK", None)


# ---- endpoint ----------------------------------------------------------------
def test_doi_nen_chua_dang_nhap_401():
    assert client.post("/local/khoa/KX/doi-nen", json={}).status_code in (401, 403)
    assert client.get("/local/khoa/KX/doi-nen").status_code in (401, 403)


def test_tien_do_chua_co_404(auth_headers):
    doinen._jobs.pop("KNONE", None)
    assert client.get("/local/khoa/KNONE/doi-nen", headers=auth_headers).status_code == 404


def test_bat_dau_dang_chay_409(auth_headers):
    doinen._jobs["KRUN"] = doinen.TienDo(dang_chay=True)
    try:
        r = client.post("/local/khoa/KRUN/doi-nen", headers=auth_headers, json={"pham_vi": "chua_trang"})
        assert r.status_code == 409
    finally:
        doinen._jobs.pop("KRUN", None)


def test_bat_dau_pham_vi_sai_422(auth_headers):
    r = client.post("/local/khoa/KX/doi-nen", headers=auth_headers, json={"pham_vi": "linh-tinh"})
    assert r.status_code == 422


def test_bat_dau_ok(auth_headers, monkeypatch):
    goi = {}
    monkeypatch.setattr(doinen, "bat_dau",
                        lambda ma_kh, pham_vi, sao_luu, nguoi="": goi.update(
                            ma_kh=ma_kh, pham_vi=pham_vi, sao_luu=sao_luu))
    r = client.post("/local/khoa/KX/doi-nen", headers=auth_headers,
                    json={"pham_vi": "tat_ca", "sao_luu": False})
    assert r.status_code == 200 and r.json()["ma_kh"] == "KX"
    assert goi == {"ma_kh": "KX", "pham_vi": "tat_ca", "sao_luu": False}
