"""NAP-05 — BUG giấy tờ trống (10/11/2026): khóa hạng mới tra danh mục giấy tờ bằng HangDT ra rỗng, hồ sơ nạp
vào không có giấy tờ nào (khóa A2/Am 70/70 hồ sơ). Dò HangDT → bỏ dấu chấm → HangGPLX."""
import pytest

from app import nap
from app.routers import khoahoc
from app.routers.nap import KHONG_CO_GIAY_TO, doc_giay_to, ma_hang_giay_to

# Bản rút gọn DM_LoaiHSo_GiayTo của DB Nạp: (MaLoaiHS, MaHangGPLX) → MaGT. Không có 'Am', 'B.01', 'A.03'.
_DM = {(1, "A2"): [1, 2, 3], (1, "A03"): [1, 2, 3], (1, "A1m"): [1, 2, 3],
       (2, "B"): [1, 2, 3], (2, "B01"): [1, 2, 3], (2, "C1"): [1, 2, 3], (3, "B2"): [1, 2, 3, 4, 5]}


class _Cur:
    def __init__(self):
        self.tra: list[str] = []
        self._kq: list = []

    def execute(self, sql, params):
        loai, ma = params
        self.tra.append(ma)
        self._kq = [{"MaGT": m, "TenGT": f"GT{m}"} for m in _DM.get((loai, ma), [])]

    def fetchall(self):
        return self._kq


@pytest.mark.parametrize("hang_gplx,hang_dt,ma_ra", [
    ("A2", "Am", "A2"),        # khóa ảnh 1: danh mục chỉ có mã hạng GPLX
    ("B11", "B.01", "B01"),    # danh mục ghi mã không dấu chấm
    ("A1", "A.03", "A03"),
    ("B1", "B", "B"),          # khóa cũ chạy đúng từ trước — vẫn tra HangDT trước
    ("C1", "C1", "C1"),
    ("A1m", "A1m", "A1m"),
])
def test_moi_hang_khoa_deu_ra_du_giay_to(hang_gplx, hang_dt, ma_ra):
    cur = _Cur()
    ds = doc_giay_to(cur, nap.suy_ma_loai_hs(hang_gplx, hang_dt), hang_dt, hang_gplx)
    assert [g["ma_gt"] for g in ds] == [1, 2, 3]
    assert cur.tra[-1] == ma_ra
    assert ds[0]["ten_gt"] == "GT1"


def test_thu_tu_do_va_bo_trung():
    assert ma_hang_giay_to("B.01", "B11") == ["B.01", "B01", "B11"]
    assert ma_hang_giay_to("C1", "C1") == ["C1"]          # không tra lặp
    assert ma_hang_giay_to(None, "A2") == ["A2"]
    assert ma_hang_giay_to(" Am ", "") == ["Am"]


def test_danh_muc_thieu_han_tra_rong():
    cur = _Cur()
    assert doc_giay_to(cur, 2, "D2", "D") == []
    assert cur.tra == ["D2", "D"]


def test_suy_loai_ho_so_nang_hang_khop_sp():
    """SP gộp: HangDT có '-' → 3 (nâng hạng) trước mọi luật khác."""
    for f in (nap.suy_ma_loai_hs, khoahoc.suy_ma_loai_hs):
        assert f("C", "B2-C") == 3
        assert f("A2", "Am") == 1
        assert f("B11", "B.01") == 2
        assert f("A1") == 1   # gọi kiểu cũ vẫn chạy
    assert [g["ma_gt"] for g in doc_giay_to(_Cur(), nap.suy_ma_loai_hs("C", "B2-C"), "B2-C", "B2")] == [1, 2, 3, 4, 5]


def test_nap_chan_khi_khoa_khong_co_danh_muc(monkeypatch):
    """Không nạp hồ sơ thiếu giấy tờ: danh mục rỗng → ValueError (nạp lô thành dòng lỗi, không ghi DB)."""
    from contextlib import contextmanager
    from app.routers import nap as r

    class Cur(_Cur):
        def execute(self, sql, params=None):
            if "FROM KhoaHoc" in sql:
                self._kq = [{"MaKH": "K1", "HangGPLX": "D", "HangDT": "D2", "MaSoGTVT": "70"}]
            elif "QTHT_ThamSoHT" in sql:
                self._kq = [{"GiaTriTS": r"D:\A"}]
            else:
                super().execute(sql, params)

        def fetchone(self):
            return self._kq[0] if self._kq else None

    class Conn:
        def cursor(self, as_dict=True):
            return Cur()

    @contextmanager
    def conn():
        yield Conn()

    goi = []
    monkeypatch.setattr(r, "sqlserver_conn", conn)
    monkeypatch.setattr(r.nap, "nap_mot_hv", lambda *a, **k: goi.append(a))
    body = r.NapIn(uuid="u1", ma_khoa_hoc="K1", ho_ten="A B", ngay_sinh="19900101", gioi_tinh="M", so_cmt="1",
                   noi_tt_ma_dvhc="1", noi_tt_ma_dvql="1", giay_to_tick=[1, 2, 3])
    with pytest.raises(ValueError, match="chưa có danh mục giấy tờ"):
        r._nap_mot(body)
    assert goi == []
    assert "scripts/bo_sung_giay_to_hang_moi.sql" in KHONG_CO_GIAY_TO
