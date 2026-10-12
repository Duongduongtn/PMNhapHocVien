"""QLY-07 (task 39, sửa task 118) — đổi nền trắng cả khóa: heuristic + ghi đè tại chỗ + backup +
xử lý 1 HV + applock + endpoint.

Không cần rembg/SQL Server thật: mock image.doi_nen_anh + cursor giả; file ghi thật vào tmp_path,
heuristic chạy thật trên ảnh PIL dựng tại chỗ.
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


# ---- xử lý 1 HV: ghi đè TẠI CHỖ (CHANGES #67) ------------------------------------
class _Cur:
    """Cursor giả: ghi lại các câu UPDATE để kiểm cột nào bị đụng."""

    def __init__(self):
        self.sql: list[tuple[str, tuple]] = []

    def execute(self, sql, params=()):
        self.sql.append((sql, params))


def _chay_mot(duong_dan, pham_vi="chua_trang", sao_luu=True, cur=None):
    td = doinen.TienDo()
    cur = cur if cur is not None else _Cur()
    doinen.xu_ly_mot(cur, "MDK1", str(duong_dan), pham_vi, sao_luu, "nv", td)
    return td, cur


def test_xu_ly_mot_khong_file_bo_qua(tmp_path):
    td, cur = _chay_mot(tmp_path / "mat.jp2")
    assert (td.bo_qua, td.xong, td.loi) == (1, 0, 0)
    assert cur.sql == []


def test_xu_ly_mot_da_trang_bo_qua(tmp_path, monkeypatch):
    f = tmp_path / "a.jp2"
    f.write_bytes(b"x")
    monkeypatch.setattr(image, "anh_da_trang", lambda data: True)
    td, cur = _chay_mot(f)
    assert (td.bo_qua, td.xong) == (1, 0)
    assert f.read_bytes() == b"x" and cur.sql == []


def test_xu_ly_mot_tat_ca_khong_bo_qua_du_trang(tmp_path, monkeypatch):
    f = tmp_path / "a.jp2"
    f.write_bytes(b"x")
    monkeypatch.setattr(image, "anh_da_trang", lambda data: True)  # dù đã trắng
    monkeypatch.setattr(image, "doi_nen_anh", lambda data: b"JP2-MOI")
    td, _ = _chay_mot(f, pham_vi="tat_ca")
    assert td.xong == 1 and f.read_bytes() == b"JP2-MOI"  # phạm vi 'tat_ca' bỏ qua heuristic


def test_xu_ly_mot_ghi_de_tai_cho_va_khong_doi_duong_dan(tmp_path, monkeypatch):
    # ảnh ở gốc KHÁC IMG_PATH_CSDT (vd UNC / Capmoi): vẫn ghi đè đúng chỗ, không sinh file chỗ khác
    goc_khac = tmp_path / "Capmoi" / "70004"
    goc_khac.mkdir(parents=True)
    f = goc_khac / "MDK1.jp2"
    f.write_bytes(b"ANH-GOC")
    monkeypatch.setattr(image, "anh_da_trang", lambda data: False)
    monkeypatch.setattr(image, "doi_nen_anh", lambda data: b"JP2-MOI")
    td, cur = _chay_mot(f)
    assert td.xong == 1
    assert f.read_bytes() == b"JP2-MOI"
    assert (goc_khac / "MDK1_BACKUP.jp2").read_bytes() == b"ANH-GOC"  # backup cùng thư mục
    assert sorted(x.name for x in goc_khac.iterdir()) == ["MDK1.jp2", "MDK1_BACKUP.jp2"]  # không .tmp, không thư mục _BACKUP
    assert not (tmp_path / "_BACKUP").exists()
    # UPDATE chỉ đụng cột chất lượng/ngày/người — KHÔNG DuongDanAnh, KHÔNG TT_XuLy
    assert len(cur.sql) == 1
    sql, params = cur.sql[0]
    assert "DuongDanAnh" not in sql and "TT_XuLy" not in sql
    assert "ChatLuongAnh" in sql and "NgayThuNhanAnh" in sql and "NguoiThuNhanAnh" in sql
    assert params[1:] == ("nv", "MDK1")


def test_xu_ly_mot_backup_chi_neu_chua_co(tmp_path, monkeypatch):
    f = tmp_path / "MDK1.jp2"
    f.write_bytes(b"ANH-GOC")
    monkeypatch.setattr(image, "anh_da_trang", lambda data: False)
    monkeypatch.setattr(image, "doi_nen_anh", lambda data: b"JP2-MOI-" + data)
    _chay_mot(f)
    _chay_mot(f)  # lần 2: nguồn đã đổi nền → backup VẪN là bản gốc thật
    assert (tmp_path / "MDK1_BACKUP.jp2").read_bytes() == b"ANH-GOC"


def test_xu_ly_mot_khong_sao_luu(tmp_path, monkeypatch):
    f = tmp_path / "MDK1.jp2"
    f.write_bytes(b"ANH-GOC")
    monkeypatch.setattr(image, "anh_da_trang", lambda data: False)
    monkeypatch.setattr(image, "doi_nen_anh", lambda data: b"JP2-MOI")
    td, _ = _chay_mot(f, sao_luu=False)
    assert td.xong == 1 and not (tmp_path / "MDK1_BACKUP.jp2").exists()


def test_xu_ly_mot_file_bi_khoa_khong_update(tmp_path, monkeypatch):
    f = tmp_path / "MDK1.jp2"
    f.write_bytes(b"ANH-GOC")
    monkeypatch.setattr(image, "anh_da_trang", lambda data: False)
    monkeypatch.setattr(image, "doi_nen_anh", lambda data: b"JP2-MOI")

    def _khoa(*a, **k):
        raise PermissionError("khoa")

    monkeypatch.setattr(doinen, "ghi_de_tai_cho", _khoa)
    cur = _Cur()
    with pytest.raises(PermissionError):
        _chay_mot(f, cur=cur)
    assert cur.sql == []  # ghi file lỗi → không UPDATE DB (ảnh/DB không lệch)


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
