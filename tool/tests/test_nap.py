"""NAP-05 — test hàm thuần + dựng tham số SP GỘP + orchestration (mock, không chạm DB).

Nạp thật vào production (applock + SP gộp + ghi ảnh) kiểm LIVE ở bước riêng (AS-003).
"""
from datetime import datetime

import pytest

from app import nap


# ---- sinh SoHoSo ----
def test_sinh_so_ho_so():
    assert nap.sinh_so_ho_so(55) == "056"   # khóa 55 HV → HV mới 056
    assert nap.sinh_so_ho_so(0) == "001"
    assert nap.sinh_so_ho_so(9) == "010"
    assert nap.sinh_so_ho_so(99) == "100"


# ---- tách họ tên (IN HOA giữ dấu — AS-003) ----
def test_tach_ho_ten_in_hoa():
    t = nap.tach_ho_ten("Nguyễn Văn An")
    assert t["TenNLX"] == "AN"
    assert t["HoDemNLX"] == "NGUYỄN VĂN"
    assert t["HoVaTen"] == "NGUYỄN VĂN AN"       # IN HOA giữ dấu
    assert t["HoVaTenIn"] == "NGUYỄN VĂN AN"


def test_tach_ho_ten_mot_tu():
    t = nap.tach_ho_ten("An")
    assert t["TenNLX"] == "AN" and t["HoDemNLX"] == ""


def test_hovatenin_cat_25_giu_dau():
    t = nap.tach_ho_ten("Nguyễn Thị Hoàng Yến Nhi Phương Thảo")
    assert len(t["HoVaTenIn"]) <= 25
    assert "Ễ" in t["HoVaTenIn"]   # còn giữ dấu (in hoa), không bỏ dấu


# ---- suy giá trị / chuỗi giấy tờ ----
def test_suy_ma_loai_hs():
    assert nap.suy_ma_loai_hs("A1") == 1
    assert nap.suy_ma_loai_hs("B1") == 2


def test_validate_do_dai():
    ten = nap.tach_ho_ten("A" * 60)
    assert any("HoVaTen" in e for e in nap.validate_do_dai(ten, "123"))
    assert nap.validate_do_dai(nap.tach_ho_ten("Trần Văn B"), "012345678901") == []


def test_dung_chuoi_giay_to():
    assert nap.dung_chuoi_giay_to([1, 2, 3]) == "1,2,3,"
    assert nap.dung_chuoi_giay_to([3, 1]) == "1,3,"      # sắp xếp + mỗi mã kèm dấu phẩy
    assert nap.dung_chuoi_giay_to([]) == ""              # không giấy tờ → chuỗi rỗng


# ---- dựng 30 tham số SP gộp ----
_HV = {
    "ho_ten": "Nguyễn Văn An",
    "ngay_sinh": "20000101",
    "gioi_tinh": "M",
    "so_cmt": "012345678901",
    "ngay_cap_cmt": "20180101",
    "noi_cap_cmt": "Cục CS QLHC",
    "noi_tt": "Phường Hồng Hà, Thành phố Hà Nội",   # tên xã — SP gộp BỎ QUA (NoiTT phải trống)
    "noi_tt_ma_dvhc": "00097",
    "noi_tt_ma_dvql": "01",
}
_KHOA = {"ma_kh": "70004K26B010", "hang_gplx": "B1", "hang_dt": "B", "ma_so_gtvt": "70"}
_NOW = datetime(2026, 10, 1, 9, 0, 0)


def test_build_params_sp_gop():
    ten = nap.tach_ho_ten(_HV["ho_ten"])
    p = dict(nap.build_params_sp_gop(_HV, _KHOA, "056", ten, "1,2,3,", "op"))
    assert len(p) == 30                          # 32 tham số SP trừ @p_out + @p_MaDK
    assert p["p_MaKH"] == "70004K26B010"
    assert p["p_SoHoSo"] == "056"
    assert p["p_HoVaTen"] == "NGUYỄN VĂN AN"      # IN HOA
    assert p["p_MaQuocTich"] == "VNM"             # không "VN" (vỡ FK)
    assert p["p_CHON_IN_GPLX"] == 2               # "Chọn in GPLX" bắt buộc
    assert p["p_ChiTiet_TT"] == ""                # NoiTT trống — không nhét tên xã
    assert p["p_MaDVHC_TT"] == "00097"
    assert p["p_MaDVHC_CT"] == "00097"            # mặc định = TT khi không có CT riêng
    assert p["p_GiayTo"] == "1,2,3,"


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
    assert [r["ok"] for r in kq["ket_qua"]] == [True, False, True]
    assert kq["ket_qua"][1]["loi"] == "SP lỗi giữa chừng"
    assert tien_do == [(1, 3), (2, 3), (3, 3)]


# ---- orchestration nap_mot_hv (mock cursor, không chạm DB) ----
class _FakeCursor:
    def __init__(self, fetches):
        self.calls = []
        self._fetch = list(fetches)

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
    monkeypatch.setattr(nap, "_orphan_set", lambda *a, **k: None)
    monkeypatch.setattr(nap, "_orphan_clear", lambda *a, **k: None)
    monkeypatch.setattr(nap, "_done_get", lambda *a, **k: None)
    monkeypatch.setattr(nap, "_done_set", lambda *a, **k: None)


def _ok_fetches():
    # thứ tự fetchone: COUNT trùng CMT (NAP-06) → MAX(SoHoSo) → kết quả SP gộp (@p_out, @p_MaDK)
    return [{"n": 0}, {"m": 55}, {"@p_out": 0, "@p_MaDK": "70004-TEST"}]


def test_nap_mot_hv_khong_anh_truyen_giay_to_qua_sp(monkeypatch):
    _tat_staging(monkeypatch)
    cur = _FakeCursor(_ok_fetches())
    giay_to = [{"ma_gt": 1, "ten_gt": "Đơn đề nghị"}, {"ma_gt": 2, "ten_gt": "Bản sao CMND"}]

    r = nap.nap_mot_hv(_FakeConn(cur), _HV, _KHOA, None, r"D:\A", "op", "uuid-1", giay_to)

    assert r["ma_dk"] == "70004-TEST"
    assert r["so_ho_so"] == "056"               # MAX 55 + 1
    assert r["so_giay_to"] == 2
    assert r["duong_dan_anh"] is None
    # giấy tờ đi qua @p_GiayTo của SP gộp (KHÔNG còn usp_NguoiLXHS_GiayTo_Insert rời)
    sp_call = [c for c in cur.calls if "ThemMoiCapNhat" in c[0]][0]
    assert "1,2," in sp_call[1]                  # chuỗi giấy tờ nằm trong tham số
    assert not [c for c in cur.calls if "GiayTo_Insert" in c[0]]
    # KHÔNG UPDATE cột ảnh khi không có ảnh (giữ TT_XuLy='01')
    assert not [c for c in cur.calls if "UPDATE NguoiLX_HoSo" in c[0]]
    assert any("sp_releaseapplock" in c[0] for c in cur.calls)   # luôn nhả applock


def test_nap_mot_hv_co_anh_update_5_cot(monkeypatch, tmp_path):
    _tat_staging(monkeypatch)
    cur = _FakeCursor(_ok_fetches())

    r = nap.nap_mot_hv(_FakeConn(cur), _HV, _KHOA, b"JP2DATA", str(tmp_path), "op", "uuid-2")

    # ghi .jp2 tên = MaDK, đường dẫn tuyệt đối <base>\<MaKhoaHoc>\<MaDK>.jp2
    jp2 = tmp_path / "70004K26B010" / "70004-TEST.jp2"
    assert jp2.read_bytes() == b"JP2DATA"
    assert r["duong_dan_anh"] == str(jp2)
    # UPDATE 5 cột ảnh, nâng TT_XuLy='03' (hướng A)
    upd = [c for c in cur.calls if "UPDATE NguoiLX_HoSo" in c[0]]
    assert len(upd) == 1 and "TT_XuLy='03'" in upd[0][0]
    assert upd[0][1][3] == "70004-TEST"         # WHERE MaDK


def test_nap_mot_hv_loi_nghiep_vu_pout(monkeypatch):
    """@p_out ≠ 0 → lỗi nghiệp vụ, raise (SP không insert, không raiserror)."""
    _tat_staging(monkeypatch)
    cur = _FakeCursor([{"n": 0}, {"m": 55}, {"@p_out": -2, "@p_MaDK": None}])

    with pytest.raises(ValueError, match="CCCD"):
        nap.nap_mot_hv(_FakeConn(cur), _HV, _KHOA, None, r"D:\A", "op", "uuid-3")
    assert any("sp_releaseapplock" in c[0] for c in cur.calls)   # vẫn nhả applock


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
    cur = _FakeCursor([])
    r = nap.nap_mot_hv(_FakeConn(cur), _HV, _KHOA, None, r"D:\A", "op", "uuid-trung")
    assert r["ma_dk"] == "70004-CU" and r["trung_uuid"] is True
    assert cur.calls == []   # không chạm applock/SP nào


# ---- case bổ sung (Checkpoint 2 /kiemthu) ----
def test_suy_ma_loai_hs_nang_hang():
    """U-01: HangGPLX bắt đầu 'A' → mô tô (1); còn lại → ô tô (2). (MaLoaiHs=3 nâng hạng do SP tự tính
    theo HangDT chứa '-', tool không truyền — verify ở E2E live, không ở hàm này.)"""
    assert nap.suy_ma_loai_hs("A2") == 1
    assert nap.suy_ma_loai_hs("C") == 2
    assert nap.suy_ma_loai_hs("") == 2


def test_validate_do_dai_ho_dem_vuot():
    """U-05: HoDemNLX > 30 ký tự → báo lỗi riêng cột HoDemNLX (SP tự tách nên phải kiểm trước)."""
    ten = nap.tach_ho_ten("A" * 31 + " B")   # HoDem 31 ký tự, Ten 'B'
    loi = nap.validate_do_dai(ten, "012345678901")
    assert any("HoDemNLX" in e for e in loi)


def test_nap_mot_hv_khoa_moi_sohoso_001(monkeypatch):
    """U-06: khóa mới (MAX(SoHoSo) trả NULL) → SoHoSo '001' (nhánh `m or 0`)."""
    _tat_staging(monkeypatch)
    cur = _FakeCursor([{"n": 0}, {"m": None}, {"@p_out": 0, "@p_MaDK": "70004-MOI"}])
    r = nap.nap_mot_hv(_FakeConn(cur), _HV, _KHOA, None, r"D:\A", "op", "uuid-moi")
    assert r["so_ho_so"] == "001"


def test_nap_mot_hv_pout_trung_sohoso(monkeypatch):
    """U-07: @p_out=-1 (trùng SoHoSo) → ValueError, vẫn nhả applock."""
    _tat_staging(monkeypatch)
    cur = _FakeCursor([{"n": 0}, {"m": 55}, {"@p_out": -1, "@p_MaDK": None}])
    with pytest.raises(ValueError, match="Số hồ sơ"):
        nap.nap_mot_hv(_FakeConn(cur), _HV, _KHOA, None, r"D:\A", "op", "uuid-7")
    assert any("sp_releaseapplock" in c[0] for c in cur.calls)


def test_nap_mot_hv_trung_cmt_server_side(monkeypatch):
    """U-09: trùng CMT trong khóa (COUNT>0) → ValueError, KHÔNG gọi SP gộp (SP không bắt khi
    nạp mới). Chốt chặn cuối server-side trong applock (NAP-06)."""
    _tat_staging(monkeypatch)
    cur = _FakeCursor([{"n": 1}])   # COUNT trùng = 1
    with pytest.raises(ValueError, match="CCCD"):
        nap.nap_mot_hv(_FakeConn(cur), _HV, _KHOA, None, r"D:\A", "op", "uuid-trung-cmt")
    assert not [c for c in cur.calls if "ThemMoiCapNhat" in c[0]]   # không gọi SP
    assert any("sp_releaseapplock" in c[0] for c in cur.calls)      # vẫn nhả applock


class _FakeCursorUpdateFail(_FakeCursor):
    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        if "UPDATE NguoiLX_HoSo" in sql:
            raise RuntimeError("DB rớt giữa UPDATE ảnh")


def test_nap_mot_hv_ghi_anh_update_loi_giu_hv(monkeypatch, tmp_path):
    """U-08: ghi .jp2 OK nhưng UPDATE 5 cột ảnh lỗi → HV VẪN tạo (giữ '01'), trả cờ anh_loi,
    .jp2 KHÔNG bị xóa (để retry UPDATE, §10.3), applock vẫn nhả — khác EC-022 (SP lỗi → dọn)."""
    _tat_staging(monkeypatch)
    cur = _FakeCursorUpdateFail([{"n": 0}, {"m": 55}, {"@p_out": 0, "@p_MaDK": "70004-TEST"}])
    r = nap.nap_mot_hv(_FakeConn(cur), _HV, _KHOA, b"JP2DATA", str(tmp_path), "op", "uuid-8")
    assert r["ma_dk"] == "70004-TEST"          # HV đã tạo, không xóa
    assert "anh_loi" in r and r["duong_dan_anh"] is None
    assert (tmp_path / "70004K26B010" / "70004-TEST.jp2").exists()   # .jp2 giữ lại để retry
    assert any("sp_releaseapplock" in c[0] for c in cur.calls)
