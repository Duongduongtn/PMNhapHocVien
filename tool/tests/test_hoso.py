"""QLY-01 (tra cứu & sửa) + QLY-02 (đổi khóa) — test không cần DB thật.

QLY-01 lát 1 (đọc) + lát 2 (sửa): hàm thuần + gate + validate.
QLY-02 (đổi khóa): hàm thuần `di_chuyen_anh` (thư mục tạm) + gate + validate.
Ghi prod thật (UPDATE nhắm cột) + chặn BC1/GPLX/khác-hạng kiểm bằng tay/live (cần DB + khóa thật).
"""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.nap import di_chuyen_anh
from app.routers.hoso import (
    HoSoSua,
    dung_tham_so_update,
    gioi_tinh_hien,
    gioi_tinh_ma,
    ngay_sinh_hien,
    ngay_sinh_luu,
)

client = TestClient(app)


# ---- Lát 1: đọc lưới ----
def test_ds_ho_so_chua_dang_nhap_401():
    # Cổng HTG-01③: chưa đăng nhập → chặn trước khi tới DB.
    assert client.get("/local/ho-so?makh=70004K26B010").status_code == 401


def test_thieu_makh_422(auth_headers):
    r = client.get("/local/ho-so", headers=auth_headers)
    assert r.status_code == 422


def test_makh_rong_422(auth_headers):
    # min_length=1 → makh rỗng bị chặn ở validate, không chạm DB.
    r = client.get("/local/ho-so?makh=", headers=auth_headers)
    assert r.status_code == 422


# ---- Lát 2: hàm thuần đổi giới tính ----
def test_gioi_tinh_ma():
    assert gioi_tinh_ma("Nam") == "M"
    assert gioi_tinh_ma("Nữ") == "F"
    assert gioi_tinh_ma("M") == "M"
    assert gioi_tinh_ma("f") == "F"
    assert gioi_tinh_ma("") == "U"
    assert gioi_tinh_ma(None) == "U"
    assert gioi_tinh_ma("linh tinh") == "U"


def test_gioi_tinh_hien():
    assert gioi_tinh_hien("M") == "Nam"
    assert gioi_tinh_hien("F") == "Nữ"
    assert gioi_tinh_hien("U") == "Không xác định"
    assert gioi_tinh_hien(None) == "Không xác định"


# ---- Lát 2: hàm thuần đổi ngày sinh ----
def test_ngay_sinh_luu_ddmmyyyy():
    # Ô hiển thị dd/mm/yyyy → lưu yyyymmdd.
    assert ngay_sinh_luu("15/03/1990") == "19900315"
    assert ngay_sinh_luu("15031990") == "19900315"


def test_ngay_sinh_luu_chi_nam():
    assert ngay_sinh_luu("1990") == "1990"
    assert ngay_sinh_luu("") == ""


def test_ngay_sinh_hien_tu_luu():
    assert ngay_sinh_hien("19900315") == "15/03/1990"
    assert ngay_sinh_hien("1990") == "1990"
    assert ngay_sinh_hien("199003") == "03/1990"


def test_ngay_sinh_round_trip():
    # hiển thị → lưu → hiển thị không đổi (yyyymmdd).
    assert ngay_sinh_luu(ngay_sinh_hien("19900315")) == "19900315"


# ---- Lát 2: dựng tham số giữ nguyên cột không sửa ----
def _row():
    """Bản ghi NguoiLX hiện tại (đọc trước khi ghi) — mô phỏng SELECT."""
    return {
        "MaDK": "70004K26B010-056",
        "DonViNhanHSo": "700041",
        "HoDemNLX": "NGUYỄN VĂN",
        "TenNLX": "AN",
        "HoVaTen": "NGUYỄN VĂN AN",
        "MaQuocTich": "VNM",
        "NgaySinh": "19900101",
        "NoiTT": "Số 1 Thôn A",
        "NoiTT_MaDVHC": "12345",
        "NoiTT_MaDVQL": "12",
        "NoiCT": "Nơi A",
        "NoiCT_MaDVHC": "12345",
        "NoiCT_MaDVQL": "12",
        "SoCMT": "012345678901",
        "NgayCapCMT": datetime(2020, 5, 1),
        "NoiCapCMT": "Cục CS",
        "GhiChu": "ghi chú cũ",
        "TrangThai": True,
        "NguoiTao": "nv cũ",
        "NguoiSua": "nv cũ",
        "NgayTao": datetime(2024, 1, 1),
        "NgaySua": datetime(2024, 1, 1),
        "GioiTinh": "M",
        "HoVaTenIn": "NGUYỄN VĂN AN",
    }


def _body(**kw):
    d = dict(ho_ten="Trần Thị Bình", ngay_sinh="20/12/1992", gioi_tinh="Nữ",
             so_cccd="098765432109", noi_tt="Số 9 Thôn B")
    d.update(kw)
    return HoSoSua(**d)


def test_dung_tham_so_update_chong_truong_sua():
    p = dung_tham_so_update(_row(), _body(), "NV Nạp")
    assert len(p) == 24
    assert p[0] == "70004K26B010-056"            # MaDK giữ nguyên (khóa WHERE)
    assert p[2] == "TRẦN THỊ" and p[3] == "BÌNH"  # Ho/Ten tách IN HOA giữ dấu
    assert p[4] == "TRẦN THỊ BÌNH"                # HoVaTen
    assert p[6] == "19921220"                     # NgaySinh ddmmyyyy → yyyymmdd
    assert p[7] == "Số 9 Thôn B"                  # NoiTT
    assert p[13] == "098765432109"               # SoCMT
    assert p[19] == "NV Nạp"                      # NguoiSua ← người đăng nhập
    assert p[22] == "F"                           # GioiTinh Nữ → F
    assert p[23] == "TRẦN THỊ BÌNH"               # HoVaTenIn


def test_dung_tham_so_update_giu_cot_khong_sua():
    r = _row()
    p = dung_tham_so_update(r, _body(), "NV Nạp")
    # Cột không nằm trong 5 trường sửa phải y hệt bản ghi cũ (không bị NULL/đổi).
    assert p[1] == r["DonViNhanHSo"]
    assert p[5] == r["MaQuocTich"]
    assert p[8] == r["NoiTT_MaDVHC"] and p[9] == r["NoiTT_MaDVQL"]
    assert p[10] == r["NoiCT"] and p[11] == r["NoiCT_MaDVHC"] and p[12] == r["NoiCT_MaDVQL"]
    assert p[14] == r["NgayCapCMT"] and p[15] == r["NoiCapCMT"]
    assert p[16] == r["GhiChu"]
    assert p[17] == r["TrangThai"]
    assert p[18] == r["NguoiTao"]                 # NguoiTao giữ nguyên
    assert p[20] == r["NgayTao"]                  # NgayTao giữ nguyên


# ---- Lát 2: validate input ----
def test_validate_cccd_khong_phai_so():
    with pytest.raises(ValidationError):
        _body(so_cccd="12A456")


def test_validate_ho_ten_rong():
    with pytest.raises(ValidationError):
        _body(ho_ten="   ")


def test_validate_noi_tt_qua_dai():
    with pytest.raises(ValidationError):
        _body(noi_tt="x" * 51)


def test_validate_ngay_sinh_sai():
    with pytest.raises(ValidationError):
        _body(ngay_sinh="123")  # 3 số — không phải yyyy/ddmmyyyy


# ---- Lát 2: gate + validate tầng API (không chạm DB) ----
def test_chi_tiet_chua_dang_nhap_401():
    assert client.get("/local/ho-so/chi-tiet?ma_dk=X").status_code == 401


def test_sua_chua_dang_nhap_401():
    assert client.post("/local/ho-so/sua?ma_dk=X", json={}).status_code == 401


def test_sua_thieu_ma_dk_422(auth_headers):
    r = client.post("/local/ho-so/sua", headers=auth_headers,
                    json={"ho_ten": "A", "so_cccd": "012345678901"})
    assert r.status_code == 422


def test_sua_cccd_sai_422(auth_headers):
    # CCCD chữ → chặn ở validate body, không chạm DB.
    r = client.post("/local/ho-so/sua?ma_dk=X", headers=auth_headers,
                    json={"ho_ten": "A", "so_cccd": "ABC"})
    assert r.status_code == 422


# ---- QLY-02: di chuyển ảnh (hàm thuần, dùng thư mục tạm) ----
def test_di_chuyen_anh_khong_co_anh():
    assert di_chuyen_anh("", "70004K26B099", "MADK1", "/bất kỳ") is None
    assert di_chuyen_anh(None, "70004K26B099", "MADK1", "/bất kỳ") is None


def test_di_chuyen_anh_di_chuyen_file(tmp_path):
    base = tmp_path / "ANH"
    cu = base / "KHOACU"
    cu.mkdir(parents=True)
    f = cu / "MADK1.jp2"
    f.write_bytes(b"jp2-data")
    moi = di_chuyen_anh(str(f), "KHOAMOI", "MADK1", str(base))
    assert moi == str(base / "KHOAMOI" / "MADK1.jp2")
    assert (base / "KHOAMOI" / "MADK1.jp2").read_bytes() == b"jp2-data"  # đã chuyển
    assert not f.exists()  # file cũ không còn


def test_di_chuyen_anh_file_mat_van_tra_duong_dan_moi(tmp_path):
    base = tmp_path / "ANH"
    # DuongDanAnh trỏ file không tồn tại → vẫn trả đường dẫn mới theo khóa mới
    moi = di_chuyen_anh(str(base / "KHOACU" / "MADK9.jp2"), "KHOAMOI", "MADK9", str(base))
    assert moi == str(base / "KHOAMOI" / "MADK9.jp2")


# ---- QLY-02: gate + validate tầng API (không chạm DB) ----
def test_doi_khoa_chua_dang_nhap_401():
    assert client.post("/local/ho-so/doi-khoa?ma_dk=X", json={"ma_kh_dich": "Y"}).status_code == 401


def test_doi_khoa_thieu_ma_dk_422(auth_headers):
    r = client.post("/local/ho-so/doi-khoa", headers=auth_headers, json={"ma_kh_dich": "Y"})
    assert r.status_code == 422


def test_doi_khoa_thieu_khoa_dich_422(auth_headers):
    r = client.post("/local/ho-so/doi-khoa?ma_dk=X", headers=auth_headers, json={})
    assert r.status_code == 422


# ---- QLY-03: gate + validate (xóa thật kiểm live) ----
def test_xoa_chua_dang_nhap_401():
    assert client.post("/local/ho-so/xoa?ma_dk=X").status_code == 401


def test_xoa_thieu_ma_dk_422(auth_headers):
    assert client.post("/local/ho-so/xoa", headers=auth_headers).status_code == 422


# ---- QLY-03 task 37 (CHANGES #22): chặn xóa HV khóa đã BC1 ở BACKEND (mock DB) ----
class _FakeCurXoa:
    """Ghi lại SQL đã chạy; fetchone trả sẵn các dòng theo thứ tự truy vấn của xoa_ho_so."""

    def __init__(self, rows, executed):
        self._rows = list(rows)
        self._executed = executed

    def execute(self, sql, params=None):
        self._executed.append(sql)

    def fetchone(self):
        return self._rows.pop(0)


class _FakeConnXoa:
    def __init__(self, rows, executed):
        self._cur = _FakeCurXoa(rows, executed)

    def cursor(self, as_dict=False):
        return self._cur

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_xoa_khoa_da_bc1_chan_409(auth_headers, monkeypatch):
    """Khóa đã lập BC1 → 409 TRƯỚC khi gọi usp_NguoiLX_Delete (bảo toàn Báo cáo 1/2)."""
    executed = []
    rows = [{"MaKhoaHoc": "70004K26B010", "DuongDanAnh": "D:/ANH/x.jp2", "bc1": 1}]
    monkeypatch.setattr("app.routers.hoso.sqlserver_conn", lambda **k: _FakeConnXoa(rows, executed))
    r = client.post("/local/ho-so/xoa?ma_dk=MADK-1", headers=auth_headers)
    assert r.status_code == 409
    assert "Báo cáo 1" in r.json()["detail"]
    assert not any("usp_NguoiLX_Delete" in s for s in executed)  # KHÔNG xóa khi đã BC1


def test_xoa_khoa_chua_bc1_qua_guard(auth_headers, monkeypatch):
    """Khóa chưa BC1 → qua guard BC1, tiếp tục kiểm GPLX (ở đây có GPLX → 409 GPLX, không phải BC1)."""
    executed = []
    rows = [
        {"MaKhoaHoc": "70004K26B010", "DuongDanAnh": None, "bc1": 0},  # step 1: chưa BC1
        {"n": 1},  # step 2: có GPLX → chặn ở nhánh khác
    ]
    monkeypatch.setattr("app.routers.hoso.sqlserver_conn", lambda **k: _FakeConnXoa(rows, executed))
    r = client.post("/local/ho-so/xoa?ma_dk=MADK-2", headers=auth_headers)
    assert r.status_code == 409
    assert "GPLX" in r.json()["detail"]  # guard BC1 cho qua, dừng ở guard GPLX
    assert not any("usp_NguoiLX_Delete" in s for s in executed)


# ---- QLY-06: đọc đủ dữ liệu để điền sẵn (gate; đọc thật + nạp mới kiểm live qua NAP-05) ----
def test_day_du_chua_dang_nhap_401():
    assert client.get("/local/ho-so/day-du?ma_dk=X").status_code == 401


def test_day_du_thieu_ma_dk_422(auth_headers):
    assert client.get("/local/ho-so/day-du", headers=auth_headers).status_code == 422


# ---- QLY-08: gỡ HV về chờ nạp (task 43) — mock DB + VPS + staging ----
from app import nap as _nap_mod          # noqa: E402
from app import session as _session_mod  # noqa: E402
from app import vps as _vps_mod          # noqa: E402
from app.vps import VpsLoi as _VpsLoi    # noqa: E402


@pytest.fixture
def op_vps_headers():
    """Phiên operator CÓ vps_token (gỡ về chờ nạp gọi VPS — auth_headers mặc định không có)."""
    token = "test-go-ve-token"
    _session_mod._phien_theo_token[token] = _session_mod.Phien(
        username="op-test", ho_ten="NV Nạp", vai_tro="operator", vps_token="jwt-vps-gia"
    )
    yield {"Authorization": f"Bearer {token}"}
    _session_mod._phien_theo_token.pop(token, None)


def test_go_ve_chua_dang_nhap_401():
    assert client.post("/local/ho-so/go-ve-cho-nap?ma_dk=X").status_code == 401


def test_go_ve_thieu_ma_dk_422(op_vps_headers):
    assert client.post("/local/ho-so/go-ve-cho-nap", headers=op_vps_headers).status_code == 422


def test_go_ve_phien_khong_co_vps_token_409(auth_headers):
    """auth_headers không có vps_token → chặn trước khi đụng CSDT (không gỡ nửa vời)."""
    r = client.post("/local/ho-so/go-ve-cho-nap?ma_dk=X", headers=auth_headers)
    assert r.status_code == 409
    assert "máy chủ" in r.json()["detail"]


def test_go_ve_khong_tra_duoc_uuid_khong_xoa_409(op_vps_headers, monkeypatch):
    """Không tra được uuid gốc (staging trống + VPS 404) → 409 TRƯỚC khi xóa CSDT (không mất HV)."""
    executed = []
    monkeypatch.setattr(_nap_mod, "lay_uuid_theo_ma_dk", lambda ma_dk: None)
    monkeypatch.setattr(_vps_mod, "tra_uuid", lambda token, ma_dk: None)
    monkeypatch.setattr("app.routers.hoso.sqlserver_conn",
                        lambda **k: _FakeConnXoa([], executed))
    r = client.post("/local/ho-so/go-ve-cho-nap?ma_dk=MADK-9", headers=op_vps_headers)
    assert r.status_code == 409
    assert "Xóa hẳn" in r.json()["detail"]
    assert executed == []  # chưa đụng CSDT


def test_go_ve_khoa_da_bc1_chan_409(op_vps_headers, monkeypatch):
    """Khóa đã BC1 → 409, KHÔNG xóa CSDT (uuid đã tra được nhưng guard BC1 chặn trước xóa)."""
    executed = []
    monkeypatch.setattr(_nap_mod, "lay_uuid_theo_ma_dk", lambda ma_dk: "uuid-1")
    rows = [{"MaKhoaHoc": "70004K26B010", "DuongDanAnh": "D:/ANH/x.jp2", "bc1": 1}]
    monkeypatch.setattr("app.routers.hoso.sqlserver_conn",
                        lambda **k: _FakeConnXoa(rows, executed))
    r = client.post("/local/ho-so/go-ve-cho-nap?ma_dk=MADK-1", headers=op_vps_headers)
    assert r.status_code == 409
    assert "Báo cáo 1" in r.json()["detail"]
    assert not any("usp_NguoiLX_Delete" in s for s in executed)


def test_go_ve_thanh_cong_xoa_csdt_roi_tra_ve(op_vps_headers, monkeypatch):
    """Luồng thuận: tra uuid (staging) → xóa CSDT → VPS trả về chờ nạp → staging về 'cho'."""
    executed = []
    goi_vps = {}
    monkeypatch.setattr(_nap_mod, "lay_uuid_theo_ma_dk", lambda ma_dk: "uuid-2")
    rows = [
        {"MaKhoaHoc": "70004K26B010", "DuongDanAnh": None, "bc1": 0},  # step 1: chưa BC1
        {"n": 0},                     # step 2: không có GPLX
        {"GiaTriTS": "D:/ANH"},       # step 3: đường dẫn ảnh
        {"n": 0},                     # step 4: verify đã xóa (NguoiLX còn 0)
    ]
    monkeypatch.setattr("app.routers.hoso.sqlserver_conn",
                        lambda **k: _FakeConnXoa(rows, executed))
    monkeypatch.setattr(_vps_mod, "tra_ve_cho_nap",
                        lambda token, uuid: goi_vps.update(uuid=uuid))
    monkeypatch.setattr(_nap_mod, "keo_ve_ve_cho", lambda uuid: True)
    r = client.post("/local/ho-so/go-ve-cho-nap?ma_dk=MADK-2", headers=op_vps_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] and body["ve_cho_nap"] and body["trong_hang_doi"]
    assert goi_vps["uuid"] == "uuid-2"
    assert any("usp_NguoiLX_Delete" in s for s in executed)  # ĐÃ xóa CSDT


def test_go_ve_vps_loi_mang_da_xoa_cho_thu_lai(op_vps_headers, monkeypatch):
    """VPS lỗi mạng SAU khi đã xóa CSDT → ok=True + dong_bo_loi + co_the_thu_lai (banner 'Thử lại')."""
    executed = []
    monkeypatch.setattr(_nap_mod, "lay_uuid_theo_ma_dk", lambda ma_dk: "uuid-3")
    rows = [
        {"MaKhoaHoc": "70004K26B010", "DuongDanAnh": None, "bc1": 0},
        {"n": 0}, {"GiaTriTS": "D:/ANH"}, {"n": 0},
    ]
    monkeypatch.setattr("app.routers.hoso.sqlserver_conn",
                        lambda **k: _FakeConnXoa(rows, executed))
    monkeypatch.setattr(_vps_mod, "tra_ve_cho_nap",
                        lambda token, uuid: (_ for _ in ()).throw(_VpsLoi("mất kết nối", None)))
    r = client.post("/local/ho-so/go-ve-cho-nap?ma_dk=MADK-3", headers=op_vps_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] and body["da_xoa_csdt"] and body["co_the_thu_lai"] is True
    assert "dong_bo_loi" in body
    assert any("usp_NguoiLX_Delete" in s for s in executed)  # CSDT đã xóa (không hoàn tác)


def test_go_ve_vps_409_da_don_pii_khong_thu_lai(op_vps_headers, monkeypatch):
    """VPS 409 (bản gốc đã dọn PII/đã xóa) sau khi xóa CSDT → co_the_thu_lai=False (thử lại vô ích)."""
    executed = []
    monkeypatch.setattr(_nap_mod, "lay_uuid_theo_ma_dk", lambda ma_dk: "uuid-4")
    rows = [
        {"MaKhoaHoc": "70004K26B010", "DuongDanAnh": None, "bc1": 0},
        {"n": 0}, {"GiaTriTS": "D:/ANH"}, {"n": 0},
    ]
    monkeypatch.setattr("app.routers.hoso.sqlserver_conn",
                        lambda **k: _FakeConnXoa(rows, executed))
    monkeypatch.setattr(_vps_mod, "tra_ve_cho_nap",
                        lambda token, uuid: (_ for _ in ()).throw(_VpsLoi("không còn bản gốc", 409)))
    r = client.post("/local/ho-so/go-ve-cho-nap?ma_dk=MADK-4", headers=op_vps_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] and body["da_xoa_csdt"] and body["co_the_thu_lai"] is False


def test_go_ve_fallback_vps_tra_uuid_khi_staging_trong(op_vps_headers, monkeypatch):
    """Staging local trống → fallback GET /api/nap/tra-uuid (VPS) ra uuid rồi xóa + trả về."""
    executed = []
    monkeypatch.setattr(_nap_mod, "lay_uuid_theo_ma_dk", lambda ma_dk: None)
    monkeypatch.setattr(_vps_mod, "tra_uuid", lambda token, ma_dk: "uuid-fb")
    rows = [
        {"MaKhoaHoc": "70004K26B010", "DuongDanAnh": None, "bc1": 0},
        {"n": 0}, {"GiaTriTS": "D:/ANH"}, {"n": 0},
    ]
    monkeypatch.setattr("app.routers.hoso.sqlserver_conn",
                        lambda **k: _FakeConnXoa(rows, executed))
    monkeypatch.setattr(_vps_mod, "tra_ve_cho_nap", lambda token, uuid: None)
    monkeypatch.setattr(_nap_mod, "keo_ve_ve_cho", lambda uuid: False)
    r = client.post("/local/ho-so/go-ve-cho-nap?ma_dk=MADK-FB", headers=op_vps_headers)
    assert r.status_code == 200
    assert r.json()["uuid"] == "uuid-fb"
    assert r.json()["trong_hang_doi"] is False  # dòng đã 'Bỏ khỏi hàng đợi' → UI gợi ý Kéo về


# ---- QLY-08: 'Thử lại đồng bộ' — chỉ chạy lại bước VPS, không xóa CSDT ----
def test_dong_bo_tra_ve_chua_dang_nhap_401():
    assert client.post("/local/ho-so/dong-bo-tra-ve?uuid=X").status_code == 401


def test_dong_bo_tra_ve_thanh_cong(op_vps_headers, monkeypatch):
    goi = {}
    monkeypatch.setattr(_vps_mod, "tra_ve_cho_nap", lambda token, uuid: goi.update(u=uuid))
    monkeypatch.setattr(_nap_mod, "keo_ve_ve_cho", lambda uuid: True)
    r = client.post("/local/ho-so/dong-bo-tra-ve?uuid=uuid-5", headers=op_vps_headers)
    assert r.status_code == 200
    assert r.json()["ve_cho_nap"] and goi["u"] == "uuid-5"


def test_dong_bo_tra_ve_vps_409(op_vps_headers, monkeypatch):
    """Thử lại mà VPS vẫn 409 → báo lỗi 409 cho UI (khác luồng gỡ: đây KHÔNG đụng CSDT)."""
    monkeypatch.setattr(_vps_mod, "tra_ve_cho_nap",
                        lambda token, uuid: (_ for _ in ()).throw(_VpsLoi("không còn bản gốc", 409)))
    r = client.post("/local/ho-so/dong-bo-tra-ve?uuid=uuid-6", headers=op_vps_headers)
    assert r.status_code == 409
