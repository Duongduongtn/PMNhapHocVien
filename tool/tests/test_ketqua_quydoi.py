"""Unit test quy đổi điểm + tính Đạt + tham số giờ/km (KQD-02, mức 2).

Bám "Sổ theo dõi KQ học tập TT17" + TT17/2026/TT-BXD + quyết định TDD-decisions §17.
"""
import pytest

from app import ketqua_quydoi as q


# ── Quy đổi 2 đoạn — khớp mẫu Sổ TT17 ──
def test_quy_doi_khop_so_tt17():
    assert q.lam_tron(q.quy_doi(28, 27, 30)) == 6.7   # LT 28/30 ngưỡng 27
    assert q.lam_tron(q.quy_doi(84, 80, 100)) == 6.0  # liên hoàn 84
    assert q.lam_tron(q.quy_doi(85, 80, 100)) == 6.3  # đường 85


def test_quy_doi_dung_nguong_bang_5():
    assert q.quy_doi(80, 80, 100) == 5.0
    assert q.quy_doi(27, 27, 30) == 5.0
    assert q.quy_doi(5, 5, 10) == 5.0


def test_quy_doi_mo_phong_chu_chi_nhap_thang_la_identity():
    for g in (0, 4, 5, 6.5, 10):
        assert q.quy_doi(g, 5, 10) == pytest.approx(g)


# ── Ranh giới làm tròn: xét Đạt trên điểm THÔ, không để 4,95 làm tròn thành Đạt ──
def test_ranh_gioi_lam_tron_duoi_nguong_la_truot():
    tho = q.quy_doi(79.2, 80, 100)  # 4,95
    assert tho < 5                  # thô: Trượt
    assert q.lam_tron(tho) == 5.0   # hiển thị/ghi: 5,0
    kq = q.tinh_ket_qua(
        {"ly_thuyet": 28, "mo_phong": 7, "hinh": 79.2, "tien_lui": 6, "duong": 84},
        "B01", "cu",
    )
    assert kq.ket_luan_csdt is False   # sa hình 4,95 < 5 → KHÔNG đạt (dù hiện 5,0)
    assert kq.kq_thuc_hanh is False


# ── Tham số Lý thuyết theo hạng × chương trình ──
@pytest.mark.parametrize("hang,ct,expect", [
    ("B", "cu", (27, 30)), ("B01", "cu", (27, 30)),
    ("B", "moi", (45, 50)), ("C1", "cu", (32, 35)), ("C1", "moi", (54, 60)),
])
def test_lt_param(hang, ct, expect):
    assert q.lt_param(hang, ct) == expect


def test_lt_param_hang_khong_xac_dinh():
    assert q.lt_param(None, "cu") is None


def test_cu_moi_doi_nguong_lt():
    # 28 câu: hạng B CŨ (/30 ng27) đạt 6,7 ; MỚI (/50 ng45) là Trượt
    assert q.quy_doi(28, 27, 30) >= 5
    assert q.quy_doi(28, 45, 50) < 5


# ── Kết luận per-môn ≥5 ──
def test_dat_tat_ca_mon():
    kq = q.tinh_ket_qua(
        {"ly_thuyet": 28, "mo_phong": 7, "hinh": 85, "tien_lui": 6, "duong": 84},
        "B01", "cu",
    )
    assert kq.ket_luan_csdt and kq.kq_ly_thuyet and kq.kq_thuc_hanh


def test_truot_mot_mon_ly_thuyet():
    kq = q.tinh_ket_qua(
        {"ly_thuyet": 20, "mo_phong": 7, "hinh": 85, "tien_lui": 6, "duong": 84},
        "B01", "cu",
    )
    assert kq.ket_luan_csdt is False
    assert kq.kq_ly_thuyet is False   # LT < 5
    assert kq.kq_thuc_hanh is True    # thực hành vẫn đạt


# ── Chặn điểm vượt khung ──
@pytest.mark.parametrize("diem", [
    {"ly_thuyet": 31, "mo_phong": 7, "hinh": 85, "tien_lui": 6, "duong": 84},   # câu > 30
    {"ly_thuyet": 28, "mo_phong": 11, "hinh": 85, "tien_lui": 6, "duong": 84},  # /10 > 10
    {"ly_thuyet": 28, "mo_phong": 7, "hinh": 101, "tien_lui": 6, "duong": 84},  # /100 > 100
    {"ly_thuyet": 28, "mo_phong": 7, "hinh": 85, "tien_lui": -1, "duong": 84},  # âm
])
def test_diem_vuot_khung_bao_loi(diem):
    with pytest.raises(q.LoiDiem):
        q.tinh_ket_qua(diem, "B01", "cu")


def test_thieu_mon_bao_loi():
    with pytest.raises(q.LoiDiem):
        q.tinh_ket_qua({"ly_thuyet": 28, "mo_phong": 7}, "B01", "cu")


# ── Phân loại hạng + giờ/km ──
@pytest.mark.parametrize("mm,mh,expect", [
    ("B.01", "B11", "B01"), ("B", "B1", "B"), ("B", "B2", "B"),
    ("C1", "C1", "C1"), ("", "", None),
])
def test_phan_loai_hang(mm, mh, expect):
    assert q.phan_loai_hang(mm, mh) == expect


def test_gio_km_theo_hang():
    assert q.gio_km("B01") == q.GioKm(34, 240, 12, 710)
    assert q.gio_km("B") == q.GioKm(34, 240, 20, 810)
    assert q.gio_km("C1") == q.GioKm(35, 225, 24, 825)
    assert q.gio_km(None) is None


# ── KQD-06 sửa lẻ: ket_qua_hon_hop (môn sửa từ gốc + môn giữ dùng quy-đổi đã lưu) ──
def test_hon_hop_giu_4_sua_1_van_dat():
    # Giữ 4 môn (quy-đổi ≥5) + sửa lại Lý thuyết (gốc 28/30 cũ → quy đổi 6,7) → vẫn Đạt
    kq = q.ket_qua_hon_hop(
        {"ly_thuyet": 28},
        {"mo_phong": 6.0, "hinh": 6.0, "tien_lui": 5.0, "duong": 7.0},
        "B01", "cu",
    )
    assert kq.ket_luan_csdt is True
    assert kq.quy_doi_tron["ly_thuyet"] == 6.7
    assert kq.quy_doi_tho["mo_phong"] == 6.0  # môn giữ dùng nguyên quy-đổi đã lưu


def test_hon_hop_mon_giu_duoi_5_la_khong_dat():
    kq = q.ket_qua_hon_hop(
        {"ly_thuyet": 28},
        {"mo_phong": 6.0, "hinh": 4.5, "tien_lui": 5.0, "duong": 7.0},  # sa hình 4,5 <5
        "B01", "cu",
    )
    assert kq.ket_luan_csdt is False
    assert kq.kq_thuc_hanh is False  # sa hình <5


def test_hon_hop_thieu_mon_bao_loi():
    with pytest.raises(q.LoiDiem):
        q.ket_qua_hon_hop({"ly_thuyet": 28}, {"mo_phong": 6.0, "hinh": 6.0}, "B01", "cu")  # thiếu tien_lui, duong


def test_hon_hop_mon_sua_vuot_khung_bao_loi():
    with pytest.raises(q.LoiDiem):
        q.ket_qua_hon_hop(
            {"hinh": 120},  # /100 vượt 100
            {"ly_thuyet": 6.0, "mo_phong": 6.0, "tien_lui": 5.0, "duong": 7.0},
            "B01", "cu",
        )
