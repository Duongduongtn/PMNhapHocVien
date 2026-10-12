"""TCB-02 (task 64) — thay ảnh HV ở CDB: ghi đè đúng file + sao lưu _BACKUP cùng thư mục.

Chỉ test hàm filesystem thuần `thay_anh_ghi_de` (không cần SQL Server/rembg). Phần UPDATE cột ảnh
đích + các mã lỗi HTTP (404/409) kiểm tay/live ở Checkpoint 14.
"""
from __future__ import annotations


import pytest

from app.routers.sync_tracuu import thay_anh_ghi_de


def test_ghi_de_giu_nguyen_ten_va_duong_dan(tmp_path):
    # Tên file gốc trỏ path nguồn (dùng chung 2 DB) — phải GIỮ NGUYÊN sau khi thay.
    f = tmp_path / "70004-2026K1.jp2"
    f.write_bytes(b"ANH-CU")
    kq = thay_anh_ghi_de(str(f), b"ANH-MOI")
    assert kq == str(f)                 # đường dẫn không đổi
    assert f.read_bytes() == b"ANH-MOI"  # đã ghi đè đúng file


def test_backup_canh_file_chi_neu_chua_co(tmp_path):
    f = tmp_path / "70004-2026K1.jp2"
    f.write_bytes(b"ANH-GOC")
    thay_anh_ghi_de(str(f), b"ANH-MOI-1")
    backup = tmp_path / "70004-2026K1_BACKUP.jp2"
    assert backup.exists()                      # backup nằm CÙNG thư mục
    assert backup.read_bytes() == b"ANH-GOC"    # giữ bản gốc đầu tiên
    # Thay lần 2 → KHÔNG đè backup (vẫn là bản gốc đầu tiên, không phải ANH-MOI-1)
    thay_anh_ghi_de(str(f), b"ANH-MOI-2")
    assert backup.read_bytes() == b"ANH-GOC"
    assert f.read_bytes() == b"ANH-MOI-2"


def test_khong_tao_file_anh_thu_2(tmp_path):
    # ❌ PRD: không tạo file ảnh thứ 2 — sau thay chỉ có file gốc + 1 backup, không thêm .jp2 khác.
    f = tmp_path / "70004-2026K1.jp2"
    f.write_bytes(b"ANH-GOC")
    thay_anh_ghi_de(str(f), b"ANH-MOI")
    jp2s = sorted(p.name for p in tmp_path.glob("*.jp2"))
    assert jp2s == ["70004-2026K1.jp2", "70004-2026K1_BACKUP.jp2"]
    # không để lại file .tmp cụt
    assert list(tmp_path.glob("*.tmp")) == []


def test_file_khong_con_raise(tmp_path):
    with pytest.raises(FileNotFoundError):
        thay_anh_ghi_de(str(tmp_path / "khong-ton-tai.jp2"), b"X")


# ---- TCB-02 bảo mật: validate_jp2 (size-cap + magic-byte) trước khi ghi đè ----
from app.image import validate_jp2, MAX_BYTES  # noqa: E402


def test_validate_jp2_box_format_ok():
    validate_jp2(b"\x00\x00\x00\x0cjP  \r\n\x87\n" + b"\x00" * 20)  # PIL sinh dạng này


def test_validate_jp2_codestream_ok():
    validate_jp2(b"\xff\x4f\xff\x51" + b"\x00" * 20)


def test_validate_jp2_khong_phai_anh_raise():
    with pytest.raises(ValueError, match="JPEG2000"):
        validate_jp2(b"PK\x03\x04 khong phai anh")  # zip/exe → chặn


def test_validate_jp2_qua_8mb_raise():
    with pytest.raises(ValueError, match="8 MB"):
        validate_jp2(b"\x00\x00\x00\x0cjP" + b"\x00" * (MAX_BYTES + 1))


# ---- TCB-03: sửa nhân thân ở CDB — chặn khi đã kết xuất DKKH (mock DB đích) ----
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)

# Bản ghi NguoiLX đầy đủ 24 cột (cho dung_tham_so_update đọc cột không sửa).
_ROW_NLX = {
    "MaDK": "75032-20260928-000001", "DonViNhanHSo": "75032", "HoDemNLX": "NGUYỄN VĂN",
    "TenNLX": "A", "HoVaTen": "NGUYỄN VĂN A", "MaQuocTich": "VNM", "NgaySinh": "19850923",
    "NoiTT": "Thôn 1", "NoiTT_MaDVHC": "12345", "NoiTT_MaDVQL": "01", "NoiCT": "Thôn 1",
    "NoiCT_MaDVHC": "12345", "NoiCT_MaDVQL": "01", "SoCMT": "012345678901",
    "NgayCapCMT": None, "NoiCapCMT": "079", "GhiChu": None, "TrangThai": 1,
    "NguoiTao": "admin", "NguoiSua": "admin", "NgayTao": None, "NgaySua": None,
    "GioiTinh": "M", "HoVaTenIn": "NGUYEN VAN A",
}
_BODY = {"ho_ten": "Nguyễn Văn B", "ngay_sinh": "23/09/1985", "gioi_tinh": "M",
         "so_cccd": "012345678901", "noi_tt": "Thôn 2"}


class _FakeCur:
    """Hàng đợi kết quả theo thứ tự truy vấn: fetchone pop 1 dict, fetchall pop 1 list."""
    def __init__(self, rows, executed):
        self._rows = list(rows)
        self._executed = executed

    def execute(self, sql, params=None):
        self._executed.append(sql)

    def fetchone(self):
        return self._rows.pop(0)

    def fetchall(self):
        return self._rows.pop(0)


class _FakeConn:
    def __init__(self, rows, executed):
        self._cur = _FakeCur(rows, executed)

    def cursor(self, as_dict=False):
        return self._cur

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _patch(monkeypatch, rows, executed):
    monkeypatch.setattr("app.routers.sync_tracuu._db_dich", lambda tk: "GPLX_CDB_CSDT")
    monkeypatch.setattr("app.routers.sync_tracuu.sqlserver_conn_dich",
                        lambda db, autocommit=False: _FakeConn(rows, executed))


def test_sua_khoa_da_dkkh_chan_409(auth_headers, monkeypatch):
    """Khóa đã kết xuất DKKH → 409 TRƯỚC khi gọi usp_NguoiLX_Update."""
    executed = []
    _patch(monkeypatch, [{"MaKhoaHoc": "75032K26B01", "dkkh": 1}], executed)
    r = client.post("/local/sync/tra-cuu/sua?ma_dk=MADK-1", headers=auth_headers, json=_BODY)
    assert r.status_code == 409
    assert "DKKH" in r.json()["detail"]
    assert not any("usp_NguoiLX_Update" in s for s in executed)  # KHÔNG ghi khi đã DKKH


def test_sua_chua_dkkh_goi_sp_update(auth_headers, monkeypatch):
    """Khóa chưa DKKH + CCCD không trùng → qua guard, chạy usp_NguoiLX_Update, không cảnh báo."""
    executed = []
    # thứ tự fetchone: meta (dkkh=0) → đếm trùng CCCD (n=0) → full row NguoiLX
    _patch(monkeypatch, [{"MaKhoaHoc": "75032K26B01", "dkkh": 0}, {"n": 0}, dict(_ROW_NLX)], executed)
    r = client.post("/local/sync/tra-cuu/sua?ma_dk=MADK-2", headers=auth_headers, json=_BODY)
    assert r.status_code == 200
    assert any("usp_NguoiLX_Update" in s for s in executed)
    assert r.json()["canh_bao"] == ""


def test_sua_cccd_trung_hv_khac_canh_bao(auth_headers, monkeypatch):
    """CCCD trùng HV khác trong khóa → vẫn lưu (gọi SP) nhưng kèm cảnh báo (mềm, PRD EC2)."""
    executed = []
    _patch(monkeypatch, [{"MaKhoaHoc": "75032K26B01", "dkkh": 0}, {"n": 1}, dict(_ROW_NLX)], executed)
    r = client.post("/local/sync/tra-cuu/sua?ma_dk=MADK-3", headers=auth_headers, json=_BODY)
    assert r.status_code == 200
    assert any("usp_NguoiLX_Update" in s for s in executed)  # vẫn lưu
    assert "trùng" in r.json()["canh_bao"]


def test_sua_chua_dang_nhap_401():
    assert client.post("/local/sync/tra-cuu/sua?ma_dk=X", json=_BODY).status_code == 401


# ---- TCB-04: xóa / đổi khóa — chặn theo DKKH (gửi Sở) + MaBC1 (per-HV) ----
def test_xoa_khoa_da_dkkh_chan_409(auth_headers, monkeypatch):
    """Khóa đã kết xuất DKKH → 409 TRƯỚC khi kiểm BC1 / gọi Delete (CHANGES #36)."""
    executed = []
    _patch(monkeypatch, [{"MaKhoaHoc": "KCU", "dkkh": 1}], executed)
    r = client.post("/local/sync/tra-cuu/xoa?ma_dk=MADK-0", headers=auth_headers)
    assert r.status_code == 409
    assert "DKKH" in r.json()["detail"]
    assert not any("usp_NguoiLX_Delete" in s for s in executed)


def test_xoa_hv_da_bc1_chan_409(auth_headers, monkeypatch):
    """Khóa chưa DKKH nhưng HV có MaBC1 → 409, KHÔNG gọi usp_NguoiLX_Delete."""
    executed = []
    # fetchone: _da_dkkh (dkkh=0) → _da_bc1 (MaBC1)
    _patch(monkeypatch, [{"MaKhoaHoc": "KCU", "dkkh": 0}, {"MaBC1": "BC1-001"}], executed)
    r = client.post("/local/sync/tra-cuu/xoa?ma_dk=MADK-1", headers=auth_headers)
    assert r.status_code == 409
    assert "Báo cáo 1" in r.json()["detail"]
    assert not any("usp_NguoiLX_Delete" in s for s in executed)


def test_xoa_hv_chua_bc1_goi_delete(auth_headers, monkeypatch):
    """Khóa chưa DKKH + HV chưa BC1 → gọi usp_NguoiLX_Delete, verify count=0 → ok."""
    executed = []
    _patch(monkeypatch, [{"MaKhoaHoc": "KCU", "dkkh": 0}, {"MaBC1": None}, {"n": 0}], executed)
    r = client.post("/local/sync/tra-cuu/xoa?ma_dk=MADK-2", headers=auth_headers)
    assert r.status_code == 200
    assert any("usp_NguoiLX_Delete" in s for s in executed)
    assert not any("DuongDanAnh" in s for s in executed)  # KHÔNG đụng cột/file ảnh (dùng chung với Nạp)


def test_doi_khoa_da_bc1_chan_409(auth_headers, monkeypatch):
    """Đổi khóa khi HV đã BC1 → 409, không UPDATE."""
    executed = []
    _patch(monkeypatch, [{"MaKhoaHoc": "KCU", "MaBC1": "BC1-001"}], executed)
    r = client.post("/local/sync/tra-cuu/doi-khoa?ma_dk=MADK-3", headers=auth_headers, json={"ma_kh_dich": "KMOI"})
    assert r.status_code == 409
    assert not any("UPDATE" in s.upper() for s in executed)


def test_doi_khoa_khac_hang_400(auth_headers, monkeypatch):
    """Khóa đích khác hạng → 400."""
    executed = []
    _patch(monkeypatch, [
        {"MaKhoaHoc": "KCU", "MaBC1": None},
        [{"MaKH": "KCU", "HangGPLX": "B11", "bc1": 0}, {"MaKH": "KMOI", "HangGPLX": "A1", "bc1": 0}],
    ], executed)
    r = client.post("/local/sync/tra-cuu/doi-khoa?ma_dk=MADK-4", headers=auth_headers, json={"ma_kh_dich": "KMOI"})
    assert r.status_code == 400
    assert "hạng" in r.json()["detail"]


def test_doi_khoa_dich_bc1_chan_409(auth_headers, monkeypatch):
    """Khóa đích đã BC1 → 409."""
    executed = []
    _patch(monkeypatch, [
        {"MaKhoaHoc": "KCU", "MaBC1": None},
        [{"MaKH": "KCU", "HangGPLX": "B11", "bc1": 0, "dkkh": 0}, {"MaKH": "KMOI", "HangGPLX": "B11", "bc1": 1, "dkkh": 0}],
    ], executed)
    r = client.post("/local/sync/tra-cuu/doi-khoa?ma_dk=MADK-5", headers=auth_headers, json={"ma_kh_dich": "KMOI"})
    assert r.status_code == 409
    assert "đích" in r.json()["detail"]


def test_doi_khoa_cu_da_dkkh_chan_409(auth_headers, monkeypatch):
    """Khóa HIỆN TẠI của HV đã DKKH → 409 (không chuyển ra khỏi khóa đã gửi Sở) — CHANGES #36."""
    executed = []
    _patch(monkeypatch, [
        {"MaKhoaHoc": "KCU", "MaBC1": None},
        [{"MaKH": "KCU", "HangGPLX": "B11", "bc1": 0, "dkkh": 1}, {"MaKH": "KMOI", "HangGPLX": "B11", "bc1": 0, "dkkh": 0}],
    ], executed)
    r = client.post("/local/sync/tra-cuu/doi-khoa?ma_dk=MADK-5b", headers=auth_headers, json={"ma_kh_dich": "KMOI"})
    assert r.status_code == 409
    assert "DKKH" in r.json()["detail"]
    assert not any("UPDATE" in s.upper() for s in executed)


def test_doi_khoa_dich_da_dkkh_chan_409(auth_headers, monkeypatch):
    """Khóa ĐÍCH đã DKKH → 409 (không nhận thêm HV vào khóa đã gửi Sở) — CHANGES #36."""
    executed = []
    _patch(monkeypatch, [
        {"MaKhoaHoc": "KCU", "MaBC1": None},
        [{"MaKH": "KCU", "HangGPLX": "B11", "bc1": 0, "dkkh": 0}, {"MaKH": "KMOI", "HangGPLX": "B11", "bc1": 0, "dkkh": 1}],
    ], executed)
    r = client.post("/local/sync/tra-cuu/doi-khoa?ma_dk=MADK-5c", headers=auth_headers, json={"ma_kh_dich": "KMOI"})
    assert r.status_code == 409
    assert "DKKH" in r.json()["detail"]
    assert not any("UPDATE" in s.upper() for s in executed)


def test_doi_khoa_happy_update_giu_duongdananh(auth_headers, monkeypatch):
    """Cùng hạng, cả hai chưa DKKH & chưa BC1 → UPDATE MaKhoaHoc+SoHoSo, KHÔNG đụng DuongDanAnh."""
    executed = []
    _patch(monkeypatch, [
        {"MaKhoaHoc": "KCU", "MaBC1": None},
        [{"MaKH": "KCU", "HangGPLX": "B11", "bc1": 0, "dkkh": 0}, {"MaKH": "KMOI", "HangGPLX": "B11", "bc1": 0, "dkkh": 0}],
        [{"n": 1}, {"n": 2}],  # SoHoSo đang dùng ở khóa đích
    ], executed)
    r = client.post("/local/sync/tra-cuu/doi-khoa?ma_dk=MADK-6", headers=auth_headers, json={"ma_kh_dich": "KMOI"})
    assert r.status_code == 200
    upd = [s for s in executed if s.upper().startswith("UPDATE")]
    assert upd and "MaKhoaHoc" in upd[0] and "SoHoSo" in upd[0]
    assert "DuongDanAnh" not in upd[0]  # giữ nguyên đường dẫn ảnh dùng chung


def test_xoa_chua_dang_nhap_401():
    assert client.post("/local/sync/tra-cuu/xoa?ma_dk=X").status_code == 401
