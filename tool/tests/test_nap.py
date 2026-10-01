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
    assert p["MaQuocTich"] == "VNM"   # mã quốc tịch VN theo DM_QuocTich (FK), không phải "VN"
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


# ---- giấy tờ ----
def test_build_params_giayto():
    p = dict(nap.build_params_giayto(2, "70004-TEST", "056", "Bản sao CMND/hộ chiếu"))
    assert len(p) == 5                       # đúng 5 tham số SP
    assert p["MaGT"] == 2 and p["MaDK"] == "70004-TEST"
    assert p["SoHoSo"] == "056"
    assert p["TenGT"] == "Bản sao CMND/hộ chiếu"   # tên đầy đủ, giữ dấu
    assert p["TrangThai"] == 1                # chỉ ghi dòng đã tick → luôn 1


# ---- nạp lô: 1 HV lỗi không hỏng cả lô (EC-071) ----
def test_nap_lo_mot_loi_khong_hong_lo():
    items = [{"uuid": "a"}, {"uuid": "b"}, {"uuid": "c"}]

    def nap_fn(it):
        if it["uuid"] == "b":
            raise RuntimeError("SP lỗi giữa chừng")
        return {"ma_dk": "MK-" + it["uuid"], "so_ho_so": "056"}

    tien_do = []
    kq = nap.nap_lo(items, nap_fn, on_progress=lambda i, n: tien_do.append((i, n)))

    assert kq["tong"] == 3 and kq["thanh_cong"] == 2 and kq["that_bai"] == 1
    assert [r["ok"] for r in kq["ket_qua"]] == [True, False, True]  # b lỗi, a/c vẫn nạp
    assert kq["ket_qua"][1]["loi"] == "SP lỗi giữa chừng"
    assert tien_do == [(1, 3), (2, 3), (3, 3)]                      # tiến độ đủ từng bước


# ---- vòng ghi giấy tờ trong nap_mot_hv (mock cursor, không chạm DB) ----
class _FakeCursor:
    def __init__(self):
        self.calls = []
        self._fetch = [{"MaDK": "70004-TEST"}, {"m": 55}]  # MaDK OUT, rồi MAX(SoHoSo)

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._fetch.pop(0)


class _FakeConn:
    def __init__(self, cur):
        self._cur = cur

    def cursor(self, *a, **k):
        return self._cur


def _tat_staging(monkeypatch):
    """Cô lập test khỏi staging.sqlite thật (cờ mồ côi + chống trùng UUID)."""
    monkeypatch.setattr(nap, "_orphan_set", lambda *a, **k: None)
    monkeypatch.setattr(nap, "_orphan_clear", lambda *a, **k: None)
    monkeypatch.setattr(nap, "_done_get", lambda *a, **k: None)
    monkeypatch.setattr(nap, "_done_set", lambda *a, **k: None)


def test_nap_mot_hv_ghi_giay_to_theo_tick(monkeypatch):
    _tat_staging(monkeypatch)

    cur = _FakeCursor()
    giay_to = [
        {"ma_gt": 1, "ten_gt": "Đơn đề nghị học, sát hạch"},
        {"ma_gt": 2, "ten_gt": "Bản sao CMND/hộ chiếu"},
    ]
    r = nap.nap_mot_hv(_FakeConn(cur), _HV, _KHOA, None, r"D:\A", "op", "uuid-1", giay_to)

    assert r["ma_dk"] == "70004-TEST"
    assert r["so_ho_so"] == "056"            # MAX 55 + 1
    assert r["so_giay_to"] == 2
    gt_calls = [c for c in cur.calls if "usp_NguoiLXHS_GiayTo_Insert" in c[0]]
    assert len(gt_calls) == 2                # ghi đúng N dòng giấy tờ đã tick
    assert any("sp_releaseapplock" in c[0] for c in cur.calls)  # luôn nhả applock


def test_nap_mot_hv_khong_giay_to(monkeypatch):
    _tat_staging(monkeypatch)
    cur = _FakeCursor()
    r = nap.nap_mot_hv(_FakeConn(cur), _HV, _KHOA, None, r"D:\A", "op", "uuid-2")  # giay_to mặc định None
    assert r["so_giay_to"] == 0
    assert not [c for c in cur.calls if "usp_NguoiLXHS_GiayTo_Insert" in c[0]]


def test_nap_mot_hv_idempotent_uuid(monkeypatch):
    """Bấm lại cùng UUID (đã nạp xong) → trả kết quả cũ, KHÔNG gọi SP tạo HV thứ 2."""
    monkeypatch.setattr(nap, "_orphan_set", lambda *a, **k: None)
    monkeypatch.setattr(nap, "_orphan_clear", lambda *a, **k: None)
    monkeypatch.setattr(nap, "_done_set", lambda *a, **k: None)
    monkeypatch.setattr(
        nap, "_done_get",
        lambda uuid: {"ma_dk": "70004-CU", "so_ho_so": "056", "so_giay_to": 3,
                      "duong_dan_anh": None, "trung_uuid": True},
    )
    cur = _FakeCursor()
    r = nap.nap_mot_hv(_FakeConn(cur), _HV, _KHOA, None, r"D:\A", "op", "uuid-trung")
    assert r["ma_dk"] == "70004-CU" and r["trung_uuid"] is True
    assert cur.calls == []   # không chạm applock/SP nào — không tạo HV mới
