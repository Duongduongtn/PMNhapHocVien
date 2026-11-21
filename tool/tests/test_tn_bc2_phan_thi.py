"""TNB-08 task 164 — luật phần thi In Báo cáo 2 (thuần, không DB)."""
from datetime import date

import pytest

from app import tn_bc2_phan_thi as pt

HOM_NAY = date(2026, 11, 21)
DM = [  # trích DM_DiemSatHach DB Nạp (B và C1 có 2 dòng trùng hạng)
    {"Hang": "A1", "LtDiemToiThieu": 21, "HiDiemToiThieu": 80, "DdDiemToiThieu": None},
    {"Hang": "B2", "LtDiemToiThieu": 32, "HiDiemToiThieu": 80, "DdDiemToiThieu": 80},
    {"Hang": "C1", "LtDiemToiThieu": 41, "HiDiemToiThieu": 80, "DdDiemToiThieu": 80},
    {"Hang": "C1", "LtDiemToiThieu": 32, "HiDiemToiThieu": 80, "DdDiemToiThieu": 80},
]


def test_nhom_hang_theo_ma_cu():
    assert pt.nhom_hang("A1") == pt.MOTO and pt.nhom_hang("A1m") == pt.MOTO and pt.nhom_hang("A2") == pt.MOTO
    assert pt.nhom_hang("A3") == pt.BA_BANH
    for h in ("B2", "B11", "B1", "C", "C1", "B", "", None):
        assert pt.nhom_hang(h) == pt.OTO


@pytest.mark.parametrize("phai, da_thi, ma", [
    ({"L", "H", "Đ"}, False, 1), ({"L", "H", "Đ"}, True, 4), ({"L", "H"}, True, 3), ({"L", "Đ"}, True, 18),
    ({"H", "Đ"}, True, 5), ({"Đ"}, True, 6), ({"L"}, True, 2), ({"H"}, True, 8), ({"H"}, False, 8),
])
def test_muc_o_to_du_7_to_hop(phai, da_thi, ma):
    assert pt.muc_tu_phan(pt.OTO, phai, da_thi) == ma


@pytest.mark.parametrize("phai, da_thi, ma", [
    ({"LT", "TH"}, False, 1), ({"LT", "TH"}, True, 3), ({"TH"}, False, 8), ({"TH"}, True, 7), ({"LT"}, True, 2),
])
def test_muc_mo_to(phai, da_thi, ma):
    assert pt.muc_tu_phan(pt.MOTO, phai, da_thi) == ma


def test_tat_het_phan_la_none():
    assert pt.muc_tu_phan(pt.OTO, set(), True) is None


def test_ten_in_mo_to_mien_lt_dung_chu_pm_cu():
    assert pt.ten_in(pt.MOTO, 8, "Sát hạch Hình") == "Sát hạch H (Miễn thi lý thuyết)"
    assert pt.ten_in(pt.OTO, 8, "Sát hạch Hình") == "Sát hạch Hình"


# Bảng quy đổi bỏ mô phỏng (PRD TNB-08, CHANGES #103) — 9 dòng
@pytest.mark.parametrize("ma_cu, ma_moi", [
    (11, 1), (12, 4), (13, 5), (20, 3), (19, 18), (17, 8), (15, 6), (14, 2), (16, None),
])
def test_quy_doi_bo_m(ma_cu, ma_moi):
    phan, da_thi = pt.phan_tu_ma_cu(pt.OTO, ma_cu)
    assert "M" not in phan
    assert pt.muc_tu_phan(pt.OTO, phan, da_thi) == ma_moi


@pytest.mark.parametrize("kq, dat", [
    ("RO", set()), ("VA", set()), ("RH", {"L"}), ("VH", {"L"}), ("RD", {"L", "H"}), ("VD", {"L", "H"}),
    ("DA", set()), ("1", set()), (None, set()),
])
def test_dat_tu_ket_qua_sh_o_to(kq, dat):
    assert pt.dat_tu_ket_qua(pt.OTO, kq) == dat


def test_dat_cong_diem_theo_nguong():
    ng = pt.nguong_theo_hang(DM, "B2")
    assert ng == {"L": 32, "H": 80, "Đ": 80}
    # RO nhưng điểm L 35 ≥ 32, H 100 ≥ 80, Đ 0 → đạt L, H
    assert pt.dat_tu_ket_qua(pt.OTO, "RO", {"L": 35, "H": 100, "Đ": 0}, ng) == {"L", "H"}
    # điểm dưới ngưỡng không tính
    assert pt.dat_tu_ket_qua(pt.OTO, "RO", {"L": 30, "H": 75, "Đ": 0}, ng) == set()


def test_nguong_trung_hang_lay_cao_nhat():
    assert pt.nguong_theo_hang(DM, "C1")["L"] == 41


def test_dat_gioi_han_trong_phan_da_thi():
    # kỳ đó chỉ thi Đ: điểm L/H = 0 không làm mất gì, Đ đạt
    assert pt.dat_tu_ket_qua(pt.OTO, "RO", {"L": 0, "H": 0, "Đ": 85}, {"L": 32, "H": 80, "Đ": 80}, {"Đ"}) == {"Đ"}


def test_cong_don_khong_xoa_dat_cu():
    assert pt.cong_don({"L", "H"}, set()) == {"L", "H"}
    assert pt.cong_don({"L"}, {"H"}) == {"L", "H"}


def test_mac_dinh_chua_thi_la_lan_dau():
    kq = pt.mac_dinh(hang="B2", hom_nay=HOM_NAY, ma_pm_cu=11)
    assert (kq["ma"], kq["dat"], kq["da_thi"]) == (1, [], False)


def test_mac_dinh_rot_duong_ra_sh_lai_d():
    kq = pt.mac_dinh(hang="B2", ket_qua_sh="RD", diem={"L": 33, "H": 90, "Đ": 0},
                     nguong=pt.nguong_theo_hang(DM, "B2"), hom_nay=HOM_NAY, ngay_qdtt=date(2026, 6, 1))
    assert (kq["ma"], kq["dat"], kq["nguon"]) == (6, ["L", "H"], "suy")


def test_mac_dinh_rot_ca_ky_ra_thi_lai_toan_bo():
    kq = pt.mac_dinh(hang="C", ket_qua_sh="VA", hom_nay=HOM_NAY)
    assert kq["ma"] == 4 and kq["da_thi"] is True


def test_mac_dinh_so_tool_uu_tien_hon_db():
    # thi lại chỉ Đ rồi rớt: DB chỉ còn kỳ gần nhất (L=H=0) nhưng sổ giữ L, H đã đạt
    so = {"dat": ["L", "H"], "da_thi": True, "nguon": "so"}
    kq = pt.mac_dinh(hang="B2", ket_qua_sh="RO", diem={"L": 0, "H": 0, "Đ": 10}, hom_nay=HOM_NAY, so=so)
    assert (kq["ma"], kq["nguon"]) == (6, "so")


def test_mac_dinh_anh_sua_duoc_dung_lan_sau():
    so = {"dat": ["H"], "da_thi": True, "nguon": "sua"}
    kq = pt.mac_dinh(hang="B2", hom_nay=HOM_NAY, so=so)
    assert (kq["ma"], kq["nguon"]) == (18, "sua")


def test_mac_dinh_qua_han_bao_luu_thi_lai_toan_bo():
    kq = pt.mac_dinh(hang="B2", ket_qua_sh="RD", hom_nay=HOM_NAY, ngay_qdtt=date(2025, 11, 1))
    assert (kq["ma"], kq["dat"], kq["nguon"]) == (4, [], "qua_han")


def test_mac_dinh_dung_365_ngay_chua_qua_han():
    kq = pt.mac_dinh(hang="B2", ket_qua_sh="RD", hom_nay=HOM_NAY, ngay_qdtt=date(2025, 11, 21))
    assert kq["ma"] == 6


def test_mo_to_mien_ly_thuyet_khi_co_gplx_o_to():
    kq = pt.mac_dinh(hang="A1", hang_gplx_da_co="B2", hom_nay=HOM_NAY)
    assert (kq["ma"], kq["dat"], kq["da_thi"]) == (8, ["LT"], False)
    # hạng B mới không nằm trong cách dò của phần mềm cũ → không miễn (giữ đúng phần mềm cũ)
    assert pt.mac_dinh(hang="A1", hang_gplx_da_co="B", hom_nay=HOM_NAY)["ma"] == 1


def test_mo_to_mien_lt_da_thi_rot_van_mien_lt():
    kq = pt.mac_dinh(hang="A1", ket_qua_sh="RO", hang_gplx_da_co="B2", hom_nay=HOM_NAY)
    assert (kq["ma"], kq["dat"], kq["da_thi"]) == (7, ["LT"], True)


def test_ket_qua_1_la_chua_co_ket_qua():
    assert pt.mac_dinh(hang="B2", ket_qua_sh="1", hom_nay=HOM_NAY)["ma"] == 1


def test_mo_to_rot_thuc_hanh_ra_sh_lai_th():
    kq = pt.mac_dinh(hang="A1", ket_qua_sh="RH", hom_nay=HOM_NAY)
    assert (kq["ma"], kq["dat"]) == (7, ["LT"])


def test_pm_cu_sh_lai_m_khong_con_phan_nao():
    kq = pt.mac_dinh(hang="B2", ket_qua_sh="XX", hom_nay=HOM_NAY, ma_pm_cu=16)
    assert kq["ma"] is None and kq["phai_thi"] == []


def test_diem_theo_nhom():
    assert pt.diem_theo_nhom(pt.MOTO, 23, 85, 0) == {"LT": 23, "TH": 85}
    assert pt.diem_theo_nhom(pt.OTO, 33, 90, 0) == {"L": 33, "H": 90, "Đ": 0}


# ── Bổ sung từ review code (21/11/2026) ──
@pytest.mark.parametrize("phai, da_thi, ma", [
    ({"LT", "TH", "Đ"}, False, 1), ({"LT", "TH", "Đ"}, True, 4), ({"LT", "TH"}, True, 3), ({"TH", "Đ"}, True, 5),
    ({"LT", "Đ"}, True, 18), ({"Đ"}, True, 6), ({"LT"}, True, 2), ({"TH"}, True, 7),
])
def test_muc_a3_a4(phai, da_thi, ma):
    assert pt.muc_tu_phan(pt.BA_BANH, phai, da_thi) == ma


def test_a3_a4_mac_dinh_nguong_va_diem():
    ng = pt.nguong_theo_hang([{"Hang": "A3", "LtDiemToiThieu": 23, "HiDiemToiThieu": 80, "DdDiemToiThieu": None}], "A3")
    assert ng == {"LT": 23, "TH": 80}
    assert pt.diem_theo_nhom(pt.BA_BANH, 24, 90, 0) == {"LT": 24, "TH": 90, "Đ": 0}
    kq = pt.mac_dinh(hang="A3", ket_qua_sh="RD", diem=pt.diem_theo_nhom(pt.BA_BANH, 24, 90, 0), nguong={"LT": 23, "TH": 80},
                     hom_nay=HOM_NAY)
    assert (kq["nhom"], kq["dat"], kq["ma"]) == (pt.BA_BANH, ["LT", "TH"], 6)
    assert pt.phan_tu_ma_cu(pt.BA_BANH, 12) == ({"LT", "TH", "Đ"}, True)


def test_mo_to_mien_ly_thuyet_van_giu_khi_qua_han_bao_luu():
    # phần mềm cũ áp miễn lý thuyết SAU luật quá hạn → vẫn "SH lại TH", không bắt thi lại lý thuyết
    kq = pt.mac_dinh(hang="A1", ket_qua_sh="RO", hang_gplx_da_co="B2", ngay_qdtt=date(2025, 1, 1), hom_nay=HOM_NAY)
    assert (kq["ma"], kq["dat"], kq["nguon"]) == (7, ["LT"], "qua_han")
    # mô tô thường (không miễn) quá hạn → thi lại toàn bộ
    assert pt.mac_dinh(hang="A1", ket_qua_sh="RO", ngay_qdtt=date(2025, 1, 1), hom_nay=HOM_NAY)["ma"] == 3
