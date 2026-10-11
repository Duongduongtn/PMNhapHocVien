"""TNB-04 (1/6) + TNB-03 + TNB-06 — task 96: luật thuần `tn_bc2_rules` (không DB).

Khóa các bất biến của TDD §11F v6.8 (sau /reviewtdd 11/10/2026): thứ tự xét 4 nhóm,
HV ở BC2 mở khác → không đưa được (không "chuyển"), 14/17/18 bất kể khóa → thi lại,
ô tô 09 phải có số giấy, MaBC2 không tồn tại xử như rỗng, hoàn tác cứu miễn luật đích,
đánh số BC2, độ dài cột + giới hạn đầu vào.
"""
import pytest

from app import tn_bc2_rules as r

HOM_NAY = "2026-10-11"
KHOA = "75032K260007"
CTX = {"hom_nay": HOM_NAY, "ma_kh_chon": KHOA, "bc2_map": {"75/2026": 0, "62/2025": 1}, "ma_bc2_dang_them": ""}


def hv(tt="09", hang="B2", ma_kh=KHOA, ma_bc2="", so_giay="N1|7282", bg="2026-09-20", ma_dk="75032-001", ten_kh="B2-K007"):
    return {"ma_dk": ma_dk, "ten": "Nguyễn Văn A", "hang": hang, "ma_kh": ma_kh, "ten_kh": ten_kh,
            "tt": tt, "ma_bc2": ma_bc2, "so_giay": so_giay, "bg": bg}


def nhom(h, loai="oto", ctx=None):
    n = r.phan_nhom(h, loai, ctx or CTX)
    return None if n is None else n["nhom"]


# ── loại hạng: đúng điều kiện SP (chứa A hoặc B1m) ──
@pytest.mark.parametrize("hang,loai", [("A1", "moto"), ("A2", "moto"), ("B1m", "moto"), ("A", "moto"), ("a1", "moto"),
                                       ("B2", "oto"), ("B1", "oto"), ("B11", "oto"), ("C1", "oto"), ("D", "oto"), ("", "oto"), (None, "oto")])
def test_loai_hang(hang, loai):
    assert r.loai_hang(hang) == loai


# ── Sẵn sàng ──
def test_oto_09_co_so_giay_khoa_chon_la_san_sang_tich_san():
    n = r.phan_nhom(hv("09"), "oto", CTX)
    assert n["nhom"] == r.SAN_SANG and n["tich_san"] is True


def test_moto_03_khoa_chon_la_san_sang():
    assert nhom(hv("03", hang="A1", so_giay=""), "moto") == r.SAN_SANG


def test_ma_bc2_khong_ton_tai_xu_nhu_rong():
    """91 HV DB Nạp mang MaBC2 trỏ BC2 không còn tồn tại (không có FK) → vẫn sẵn sàng."""
    assert nhom(hv("09", ma_bc2="999/2020")) == r.SAN_SANG


def test_ma_bc2_da_dong_van_san_sang():
    assert nhom(hv("09", ma_bc2="62/2025")) == r.SAN_SANG


def test_oto_09_khoa_khac_khong_hien():
    assert nhom(hv("09", ma_kh="75032K260001")) is None


def test_moto_03_khoa_khac_khong_hien():
    assert nhom(hv("03", hang="A1", ma_kh="75032K260001"), "moto") is None


# ── Cần xem ──
def test_oto_03_la_can_xem_chua_tot_nghiep_goi_y_cap_nhat():
    n = r.phan_nhom(hv("03", so_giay=""), "oto", CTX)
    assert n["nhom"] == r.CAN_XEM and n["ma_ly_do"] == "chua_tot_nghiep" and n["goi_y_xu_ly"] == r.GOI_Y_TOT_NGHIEP
    assert n["tich_san"] is False


def test_oto_09_thieu_so_giay_la_can_xem_khong_chong_san_sang():
    n = r.phan_nhom(hv("09", so_giay=""), "oto", CTX)
    assert n["nhom"] == r.CAN_XEM and n["ma_ly_do"] == "thieu_so_giay"
    assert r.phan_nhom(hv("09", so_giay="   "), "oto", CTX)["nhom"] == r.CAN_XEM


def test_trang_thai_la_nguon_cuu_duoc_la_can_xem_goi_y_cuu():
    n = r.phan_nhom(hv("01", so_giay=""), "oto", CTX)
    assert n["nhom"] == r.CAN_XEM and n["goi_y_xu_ly"] == r.GOI_Y_CUU
    assert nhom(hv("01", ma_kh="75032K260001"), "oto") is None


def test_trang_thai_ngoai_tap_la_khong_duoc():
    n = r.phan_nhom(hv("05"), "oto", CTX)
    assert n["nhom"] == r.KHONG_DUOC and n["ma_ly_do"] == "trang_thai_ngoai_tap"


# ── Thi lại: 14/17/18 bất kể khóa, không tích sẵn ──
@pytest.mark.parametrize("tt", ["14", "17", "18"])
def test_thi_lai_cung_khoa_va_khac_khoa(tt):
    for ma_kh in (KHOA, "75032K250009"):
        n = r.phan_nhom(hv(tt, ma_kh=ma_kh, ma_bc2="62/2025", bg="2026-03-01"), "oto", CTX)
        assert n["nhom"] == r.THI_LAI and n["tich_san"] is False


def test_thi_lai_moto_cung_khoa_la_thi_lai_khong_phai_can_xem():
    assert nhom(hv("17", hang="A1"), "moto") == r.THI_LAI


def test_thi_lai_tra_du_ke_ca_qua_han_kem_tuoi_thang():
    n = r.phan_nhom(hv("18", ma_kh="75032K240001", bg="2024-10-01"), "oto", CTX)
    assert n["nhom"] == r.THI_LAI and n["tuoi_thang"] == 24
    assert r.trong_nguong_thi_lai(n, 12) is False and r.trong_nguong_thi_lai(n, 24) is True


def test_thi_lai_trong_nguong_12_thang():
    n = r.phan_nhom(hv("17", ma_kh="75032K250009", bg="2026-01-15"), "oto", CTX)
    assert n["tuoi_thang"] == 9 and r.trong_nguong_thi_lai(n) is True and n["trong_nguong"] is True
    n6 = r.phan_nhom(hv("17", ma_kh="75032K250009", bg="2026-01-15"), "oto", CTX, thi_lai_thang=6)
    assert n6["trong_nguong"] is False and n6["nhom"] == r.THI_LAI   # quá ngưỡng vẫn hiện, chỉ không được tích


# ── Không đưa được (và thứ tự xét) ──
def test_hv_o_bc2_mo_khac_la_khong_duoc_khong_chuyen():
    n = r.phan_nhom(hv("11", ma_bc2="75/2026"), "oto", CTX)
    assert n["nhom"] == r.KHONG_DUOC and n["ma_ly_do"] == "dang_o_bc2_mo" and n["goi_y_xu_ly"] == r.GOI_Y_GO_BC2
    assert "75/2026" in n["ly_do"]


def test_hv_11_o_bc2_da_dong_khong_duoc_mo_lai_o_pm_cu():
    n = r.phan_nhom(hv("11", ma_bc2="62/2025"), "oto", CTX)
    assert n["nhom"] == r.KHONG_DUOC and n["ma_ly_do"] == "da_vao_bc2_dong" and n["goi_y_xu_ly"] is None


def test_hv_da_o_chinh_bc2_dang_them_khong_hien_lai():
    ctx = dict(CTX, ma_bc2_dang_them="75/2026")
    assert nhom(hv("11", ma_bc2="75/2026"), "oto", ctx) is None


def test_14_17_18_mang_bc2_mo_khac_la_khong_duoc():
    assert nhom(hv("14", ma_bc2="75/2026")) == r.KHONG_DUOC


def test_03_09_mang_ma_bc2_dang_mo_khong_duoc_tich_san():
    """TDD §11F.4: san_sang chỉ khi MaBC2 rỗng / không tồn tại / BC2 đã đóng."""
    for h, loai in ((hv("09", ma_bc2="75/2026"), "oto"), (hv("03", hang="A1", ma_bc2="75/2026", so_giay=""), "moto")):
        n = r.phan_nhom(h, loai, CTX)
        assert n["nhom"] == r.KHONG_DUOC and n["ma_ly_do"] == "dang_o_bc2_mo" and n["goi_y_xu_ly"] == r.GOI_Y_GO_BC2


def test_khoa_chua_be_giang_khong_duoc_ke_ca_san_sang():
    n = r.phan_nhom(hv("09", bg="2026-12-20"), "oto", CTX)
    assert n["nhom"] == r.KHONG_DUOC and n["ma_ly_do"] == "khoa_chua_be_giang" and "20/12/2026" in n["ly_do"]
    assert nhom(hv("09", bg="")) == r.KHONG_DUOC  # thiếu NgayBG → coi như chưa bế giảng


def test_thu_tu_xet_khoa_chua_be_giang_truoc_can_xem():
    """Ô tô 03 của khóa chưa bế giảng phải là khong_duoc (không phải can_xem)."""
    assert nhom(hv("03", bg="2026-12-20", so_giay="")) == r.KHONG_DUOC


def test_sai_loai_la_khong_duoc_va_xet_truoc_het():
    n = r.phan_nhom(hv("09", hang="A1", bg="2026-12-20"), "oto", CTX)
    assert n["nhom"] == r.KHONG_DUOC and n["ma_ly_do"] == "sai_loai"


@pytest.mark.parametrize("tt,co_goi_y_cuu", [("13", True), ("16", False), ("19", False)])
def test_co_ket_qua_cuoi_khong_duoc(tt, co_goi_y_cuu):
    n = r.phan_nhom(hv(tt), "oto", CTX)
    assert n["nhom"] == r.KHONG_DUOC and n["ma_ly_do"] == "co_ket_qua_cuoi"
    assert (n["goi_y_xu_ly"] == r.GOI_Y_CUU) is co_goi_y_cuu


def test_ten_trang_thai_nghiep_vu():
    assert r.ten_trang_thai("03", "oto") == "Đã học xong, chưa tốt nghiệp"
    assert r.ten_trang_thai("03", "moto") == "Đã học xong, chờ lập BC2"
    assert r.ten_trang_thai("09") == "Đã tốt nghiệp, chờ lập BC2"
    assert r.ten_trang_thai("11") == "Đã vào BC2, chờ kết quả"
    assert r.ten_trang_thai("17") == "Thi sát hạch chưa đạt"
    assert r.ten_trang_thai("99") == "Trạng thái 99"


# ── giai_thich_khong_hien ──
def test_giai_thich_khong_hien():
    g = r.giai_thich_khong_hien(hv("11", ma_bc2="75/2026"), "oto", CTX)
    assert g["ma"] == "dang_o_bc2_mo" and "75/2026" in g["noi_dung"]
    assert r.giai_thich_khong_hien(hv("09", ma_kh="75032K260001"), "oto", CTX)["ma"] == "khac_khoa"
    assert r.giai_thich_khong_hien(hv("09", bg="2026-12-20"), "oto", CTX)["ma"] == "khoa_chua_be_giang"
    assert r.giai_thich_khong_hien(hv("09", hang="A1"), "oto", CTX)["ma"] == "sai_loai"
    assert r.giai_thich_khong_hien(hv("16"), "oto", CTX)["ma"] == "co_ket_qua_cuoi"
    assert r.giai_thich_khong_hien(hv("05"), "oto", CTX)["ma"] == "trang_thai_ngoai_tap"
    # trạng thái ngoài tập của HV KHÁC khóa (hoặc chưa chọn khóa) vẫn được gọi đúng tên, kèm gợi ý cứu
    for tt in ("01", "02", "04", "10", "12"):
        for ma_kh in (KHOA, "75032K260001"):
            g = r.giai_thich_khong_hien(hv(tt, ma_kh=ma_kh, so_giay=""), "oto", CTX)
            assert g["ma"] == "trang_thai_ngoai_tap" and g["goi_y_xu_ly"] == r.GOI_Y_CUU
    g = r.giai_thich_khong_hien(hv("12", so_giay=""), "oto", dict(CTX, ma_kh_chon=""))
    assert g["ma"] == "trang_thai_ngoai_tap"
    assert r.giai_thich_khong_hien(hv("09"), "oto", CTX)["ma"] == "dang_hien"
    ctx = dict(CTX, ma_bc2_dang_them="75/2026")
    assert r.giai_thich_khong_hien(hv("11", ma_bc2="75/2026"), "oto", ctx)["ma"] == "da_trong_bc2_nay"


# ── Cứu trạng thái ──
def ma_loi(vde):
    return {v["ma"] for v in vde}


def test_cuu_hop_le_oto_ve_17_va_09():
    assert r.kiem_cuu(hv("03", so_giay=""), "17", "oto", "Vắng thi, nhập nhầm") == []
    assert r.kiem_cuu(hv("12"), "09", "oto", "Khôi phục") == []


@pytest.mark.parametrize("tt", ["11", "16", "19"])
def test_cuu_nguon_bi_chan(tt):
    assert "nguon_bi_chan" in ma_loi(r.kiem_cuu(hv(tt), "17", "oto", "lý do"))


def test_cuu_nguon_ngoai_tap_va_dich_khong_hop_le():
    assert "nguon_ngoai_tap" in ma_loi(r.kiem_cuu(hv("05"), "17", "oto", "x"))
    assert "dich_khong_hop_le" in ma_loi(r.kiem_cuu(hv("03"), "11", "oto", "x"))
    assert "dich_khong_hop_le" in ma_loi(r.kiem_cuu(hv("03"), "03", "oto", "x"))


def test_cuu_dich_09_can_so_giay_va_chi_oto():
    assert "dich_09_thieu_so_giay" in ma_loi(r.kiem_cuu(hv("03", so_giay=""), "09", "oto", "x"))
    assert "dich_09_chi_o_to" in ma_loi(r.kiem_cuu(hv("03", hang="A1", so_giay="N1|1"), "09", "moto", "x"))


def test_cuu_khong_doi_khac_loai_va_ly_do():
    assert "khong_doi" in ma_loi(r.kiem_cuu(hv("17"), "17", "oto", "x"))
    assert "khac_loai" in ma_loi(r.kiem_cuu(hv("03", hang="A1"), "17", "oto", "x"))
    assert "thieu_ly_do" in ma_loi(r.kiem_cuu(hv("03"), "17", "oto", "   "))
    assert "ly_do_qua_dai" in ma_loi(r.kiem_cuu(hv("03"), "17", "oto", "x" * 256))
    assert r.kiem_cuu(hv("03"), "17", "oto", "x" * 255) == []


def test_hoan_tac_cuu_mien_luat_dich():
    """Cứu 03→14 rồi hoàn tác về 03: đích 03 không thuộc DICH_CUU nhưng vẫn hợp lệ."""
    assert "03" not in r.DICH_CUU
    assert r.kiem_hoan_tac_cuu("14", "14", "03") == []


def test_hoan_tac_cuu_chan_khi_hv_da_bi_doi_tiep():
    assert ma_loi(r.kiem_hoan_tac_cuu("11", "14", "03")) == {"da_bi_doi"}
    assert ma_loi(r.kiem_hoan_tac_cuu("14", "14", "")) == {"khong_co_trang_thai_cu"}


# ── Đánh số BC2 ──
def test_goi_y_so_oto_max_cong_mot_trong_nam():
    ds = ["79/2026", "80/2026", "5/2025", "868/26-TTTĐ", "81/2026X", "100/2025"]
    assert r.goi_y_so_bc2("oto", ds, 2026) == "81/2026"
    assert r.goi_y_so_bc2("oto", [], 2026) == "1/2026"
    assert r.goi_y_so_bc2("oto", ["9/2026", "10/2026"], 2026) == "11/2026"  # so số, không so chuỗi


def test_goi_y_so_moto_bo_tien_to_a1a2():
    assert r.goi_y_so_bc2("moto", ["868/26-TTTĐ"], 2026, "A1A2870/26-TTTĐ") == "870/26-TTTĐ"
    assert r.goi_y_so_bc2("moto", [], 2026, "870/26-TTTĐ") == "870/26-TTTĐ"
    assert r.goi_y_so_bc2("moto", [], 2026, None) == ""


def test_kiem_so_bc2():
    assert r.kiem_so_bc2("81/2026", ["80/2026"]) == []
    assert ma_loi(r.kiem_so_bc2("", [])) == {"thieu_so"}
    assert ma_loi(r.kiem_so_bc2("80/2026", ["80/2026"])) == {"trung_so"}
    assert ma_loi(r.kiem_so_bc2("870/26-ttđ", ["870/26-TTĐ"])) == {"trung_so"}   # không phân biệt hoa/thường
    assert ma_loi(r.kiem_so_bc2("1234567890/2026", [])) == {"so_qua_dai"}      # > 13 (MaBCII varchar 13)
    assert r.kiem_so_bc2("A1A2870/26-TT", []) == []                              # đúng 13 ký tự


# ── Độ dài cột + giới hạn đầu vào ──
def test_do_dai_cot_theo_db_that():
    assert r.DO_DAI_COT["so_so_tn"] == 50 and r.DO_DAI_COT["so_giay_cntn"] == 20
    assert r.kiem_do_dai("so_giay_cntn", "N1|7282") == []
    assert r.kiem_do_dai("so_giay_cntn", "x" * 20) == []
    v = r.kiem_do_dai("so_giay_cntn", "x" * 21)
    assert ma_loi(v) == {"vuot_do_dai"} and v[0]["muc"] == r.CHAN and v[0]["ref"] == "so_giay_cntn"
    assert r.kiem_do_dai("so_so_tn", "x" * 51) and not r.kiem_do_dai("so_so_tn", "x" * 50)
    assert r.kiem_do_dai("ghi_chu", "x" * 256) and not r.kiem_do_dai("ghi_chu", "x" * 255)
    assert r.kiem_do_dai("so_giay_cntn", None) == []
    with pytest.raises(KeyError):
        r.kiem_do_dai("khong_co_cot", "x")


def test_gioi_han_danh_sach_dan():
    assert r.kiem_danh_sach_dan(["012345678901"] * 5000) == []
    assert ma_loi(r.kiem_danh_sach_dan(["1"] * 5001)) == {"qua_nhieu_dong"}
    assert ma_loi(r.kiem_danh_sach_dan(["x" * 41])) == {"dong_qua_dai"}
    assert r.kiem_danh_sach_dan(["x" * 40, "", "  "]) == []
    assert r.kiem_danh_sach_dan(None) == []


def test_co_chan():
    assert r.co_chan(r.kiem_so_bc2("", [])) is True
    assert r.co_chan([]) is False
