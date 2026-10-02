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
