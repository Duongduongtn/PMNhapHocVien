"""NAP-05 (1/2) — test hàm thuần + dựng tham số SP (không chạm DB).

Nạp thật vào production (applock + SP + compensation) kiểm LIVE ở bước riêng (AS-003).
"""
from datetime import datetime

from app import nap


# ---- sinh SoHoSo ----
def test_sinh_so_ho_so():
    assert nap.sinh_so_ho_so(55) == "056"   # khóa 55 HV → HV mới 056
    assert nap.sinh_so_ho_so(0) == "001"
    assert nap.sinh_so_ho_so(9) == "010"
    assert nap.sinh_so_ho_so(99) == "100"


# ---- tách họ tên ----
def test_tach_ho_ten():
    t = nap.tach_ho_ten("Nguyễn Văn An")
    assert t["TenNLX"] == "An"
    assert t["HoDemNLX"] == "Nguyễn Văn"
    assert t["HoVaTen"] == "Nguyễn Văn An"
    assert t["HoVaTenIn"] == "Nguyễn Văn An"


def test_tach_ho_ten_mot_tu():
    t = nap.tach_ho_ten("An")
    assert t["TenNLX"] == "An" and t["HoDemNLX"] == ""


def test_hovatenin_cat_25_giu_dau():
    t = nap.tach_ho_ten("Nguyễn Thị Hoàng Yến Nhi Phương Thảo")
    assert len(t["HoVaTenIn"]) <= 25
    assert "ễ" in t["HoVaTenIn"]  # còn giữ dấu, không hoa-bỏ-dấu


# ---- suy giá trị ----
def test_suy_tt_xuly():
    assert nap.suy_tt_xuly(True) == ("03", 1)
    assert nap.suy_tt_xuly(False) == ("01", None)


def test_suy_ma_loai_hs():
    assert nap.suy_ma_loai_hs("A1") == 1
    assert nap.suy_ma_loai_hs("B1") == 2


def test_validate_do_dai():
    ten = nap.tach_ho_ten("A" * 60)
    assert any("HoVaTen" in e for e in nap.validate_do_dai(ten, "123"))
    assert nap.validate_do_dai(nap.tach_ho_ten("Trần Văn B"), "012345678901") == []


# ---- dựng tham số SP ----
_HV = {
    "ho_ten": "Nguyễn Văn An",
    "ngay_sinh": "20000101",
    "gioi_tinh": "M",
    "so_cmt": "012345678901",
    "noi_tt": "Phường Hồng Hà, Thành phố Hà Nội",
    "noi_tt_ma_dvhc": "00097",
    "noi_tt_ma_dvql": "01",
}
_KHOA = {"ma_kh": "70004K26B010", "hang_gplx": "B1", "hang_dt": "B", "ma_so_gtvt": "70"}
_NOW = datetime(2026, 10, 1, 9, 0, 0)


def test_params_nguoilx_gia_tri_mvp():
    p = dict(nap.build_params_nguoilx(_HV, nap.tach_ho_ten(_HV["ho_ten"]), _NOW, "operator"))
    assert len(p) == 23  # 24 tham số SP trừ @MaDK OUT
    assert p["DonViNhanHSo"] == "70004"
    assert p["MaQuocTich"] == "VN"
    assert p["TrangThai"] == 1
    assert p["NoiTT_MaDVHC"] == "00097" and p["NoiTT_MaDVQL"] == "01"
    assert p["NoiCT_MaDVHC"] == "00097"  # BR-004: NoiCT = NoiTT mặc định
    assert p["HoVaTenIn"] == "Nguyễn Văn An"


def test_params_hoso_co_anh():
    p = dict(nap.build_params_hoso(_HV, _KHOA, "056", r"D:\A\70004K26B010\x.jp2", "03", 1, _NOW, "op"))
    assert len(p) == 69  # 71 tham số SP trừ @MaDK, @SoHoSo
    assert p["MaCSDT"] == "70004" and p["MaSoGTVT"] == "70"
    assert p["MaLoaiHs"] == 2            # B1 → ô tô
    assert p["TT_XuLy"] == "03" and p["ChatLuongAnh"] == 1
    assert p["GiayCNSK"] == 1 and p["TrangThai"] == 1 and p["MaHTCap"] == "CM_VN"
    assert p["MaKhoaHoc"] == "70004K26B010" and p["HangDaoTao"] == "B"
    assert p["NguoiThuNhanAnh"] == "op"


def test_params_hoso_khong_anh():
    p = dict(nap.build_params_hoso(_HV, _KHOA, "056", None, "01", None, _NOW, "op"))
    assert p["DuongDanAnh"] is None and p["ChatLuongAnh"] is None
    assert p["NgayThuNhanAnh"] is None and p["NguoiThuNhanAnh"] is None
    assert p["TT_XuLy"] == "01"
