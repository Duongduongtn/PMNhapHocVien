"""NAP-05 / NAP-06 — E2E LIVE (mức 3): nạp HV THẬT vào GPLX_CSDT khóa B-K149 rồi DỌN SẠCH.

⚠ GHI PRODUCTION — mark `live`, SKIP mặc định. Chỉ chạy có giám sát:
    pytest -m live
Mỗi test tạo HV với SoCMT test riêng, verify trên DB thật, rồi xóa HV + .jp2 ở teardown.
Lý do phải live (không mock): AS-003 chứng minh mock lọt lỗi (FK, field app cũ) — SP thật mới bắt được.
"""
import io
import uuid as uuidlib
from pathlib import Path

import pytest
from PIL import Image

from app import nap
from app.db import sqlserver_conn, sqlserver_cursor
from app.routers.nap import kiem_trung_cccd

pytestmark = pytest.mark.live

MA_KH = "70004K26B010"   # khóa B-K149


def _jp2() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (353, 471), (255, 255, 255)).save(
        buf, format="JPEG2000", quality_mode="rates", quality_layers=[10])
    return buf.getvalue()


def _uuid(p: str) -> str:
    return f"{p}-{uuidlib.uuid4().hex[:8]}"


def _don_cmt(cmt: str) -> None:
    """Xóa HV test sót cùng SoCMT trong khóa (tránh -2 trùng CMT khi chạy lại)."""
    with sqlserver_cursor() as cur:
        cur.execute("SELECT lx.MaDK FROM NguoiLX lx JOIN NguoiLX_HoSo hs ON hs.MaDK=lx.MaDK "
                    "WHERE lx.SoCMT=%s AND hs.MaKhoaHoc=%s", (cmt, MA_KH))
        ids = [r["MaDK"] for r in cur.fetchall()]
    for md in ids:
        with sqlserver_conn() as c:
            c.cursor().execute("EXEC dbo.usp_NguoiLX_Delete @MaDK=%s", (md,))


def _hv(cmt: str, dv: dict) -> dict:
    return {
        "ho_ten": "Nguyễn Văn Kiểm Thử",
        "ngay_sinh": "20000115", "gioi_tinh": "M", "so_cmt": cmt,
        "ngay_cap_cmt": "20180101", "noi_cap_cmt": "Cục CS QLHC",
        "noi_tt_ma_dvhc": dv["MaDvhc"], "noi_tt_ma_dvql": dv["MaDVQL"],
        "so_nam_lx": 10, "so_km_lx": 100000,
    }


@pytest.fixture(scope="module")
def ctx():
    with sqlserver_cursor() as cur:
        cur.execute("SELECT MaKH, HangGPLX, HangDT, MaSoGTVT FROM KhoaHoc WHERE MaKH=%s", (MA_KH,))
        k = cur.fetchone()
        cur.execute("SELECT TOP 1 MaDvhc, MaDVQL FROM DM_DVHC "
                    "WHERE TrangThai=1 AND MaDVQL IS NOT NULL ORDER BY MaDvhc")
        dv = cur.fetchone()
        cur.execute("SELECT GiaTriTS FROM QTHT_ThamSoHT WHERE TenTS='IMG_PATH_CSDT'")
        img = cur.fetchone()["GiaTriTS"]
    return {"khoa": {"ma_kh": k["MaKH"], "hang_gplx": k["HangGPLX"],
                     "hang_dt": k["HangDT"], "ma_so_gtvt": k["MaSoGTVT"]},
            "dv": dv, "img": img}


@pytest.fixture
def don(ctx):
    """Thu MaDK đã tạo → teardown xóa HV (cascade) + .jp2. Bảo đảm production sạch sau mỗi test."""
    rac: list[str] = []
    yield rac.append
    for ma_dk in rac:
        try:
            with sqlserver_conn() as c:
                c.cursor().execute("EXEC dbo.usp_NguoiLX_Delete @MaDK=%s", (ma_dk,))
        except Exception:
            pass
        try:
            (Path(ctx["img"]) / MA_KH / f"{ma_dk}.jp2").unlink()
        except OSError:
            pass


# ---- E-happy: NAP-05 nạp có ảnh → khớp app cũ (gồm field SP tự tính) ----
def test_e_happy_nap_co_anh_khop_app_cu(ctx, don):
    cmt = "000000000003"
    _don_cmt(cmt)
    gt = [{"ma_gt": i, "ten_gt": "x"} for i in (1, 2, 3)]
    with sqlserver_conn() as conn:
        r = nap.nap_mot_hv(conn, _hv(cmt, ctx["dv"]), ctx["khoa"], _jp2(),
                           ctx["img"], "", _uuid("ehappy"), gt)
    don(r["ma_dk"])
    with sqlserver_cursor() as cur:
        cur.execute("SELECT HoVaTen, HoVaTenIn, MaQuocTich, NoiTT, NoiCT FROM NguoiLX WHERE MaDK=%s",
                    (r["ma_dk"],))
        lx = cur.fetchone()
        cur.execute("SELECT TT_XuLy, DuongDanAnh, ChatLuongAnh, CHON_IN_GPLX, DonViHocLX, GiayCNSK, "
                    "MaHTCap, MaLoaiHs, TrangThai, MaCSDT FROM NguoiLX_HoSo WHERE MaDK=%s", (r["ma_dk"],))
        hs = cur.fetchone()
        cur.execute("SELECT MaGT FROM NguoiLXHS_GiayTo WHERE MaDK=%s ORDER BY MaGT", (r["ma_dk"],))
        gts = [x["MaGT"] for x in cur.fetchall()]
    # 5 field tới hạn
    assert lx["HoVaTen"] == "NGUYỄN VĂN KIỂM THỬ"
    assert lx["HoVaTenIn"] == "NGUYỄN VĂN KIỂM THỬ"[:25]
    assert lx["MaQuocTich"] == "VNM"
    assert (lx["NoiTT"] or "") == "" and (lx["NoiCT"] or "") == ""
    assert hs["CHON_IN_GPLX"] == 2 and hs["DonViHocLX"] is None
    # ảnh hướng A
    assert hs["TT_XuLy"] == "03" and hs["ChatLuongAnh"] == 1
    assert hs["DuongDanAnh"] and hs["DuongDanAnh"].endswith(f"{r['ma_dk']}.jp2")
    # field SP tự tính (chỉ verify được ở live)
    assert hs["GiayCNSK"] in (1, True) and hs["MaHTCap"] == "CM_VN"
    assert hs["MaLoaiHs"] == 2 and hs["TrangThai"] == 1 and hs["MaCSDT"] == "70004"
    # SoHoSo + giấy tờ
    assert r["so_ho_so"].isdigit() and len(r["so_ho_so"]) == 3
    assert gts == [1, 2, 3]


# ---- E-01: NAP-05 bỏ tick giấy KSK (MaGT=3) → GiayCNSK=0, chỉ 2 dòng ----
def test_e01_bo_tick_giay_ksk(ctx, don):
    cmt = "000000000004"
    _don_cmt(cmt)
    gt = [{"ma_gt": 1, "ten_gt": "x"}, {"ma_gt": 2, "ten_gt": "y"}]   # bỏ giấy 3
    with sqlserver_conn() as conn:
        r = nap.nap_mot_hv(conn, _hv(cmt, ctx["dv"]), ctx["khoa"], None,
                           ctx["img"], "", _uuid("e01"), gt)
    don(r["ma_dk"])
    with sqlserver_cursor() as cur:
        cur.execute("SELECT GiayCNSK FROM NguoiLX_HoSo WHERE MaDK=%s", (r["ma_dk"],))
        giay_cnsk = cur.fetchone()["GiayCNSK"]
        cur.execute("SELECT MaGT FROM NguoiLXHS_GiayTo WHERE MaDK=%s ORDER BY MaGT", (r["ma_dk"],))
        gts = [x["MaGT"] for x in cur.fetchall()]
    assert gts == [1, 2]                     # bỏ tick được tôn trọng
    assert giay_cnsk in (0, False)           # không giấy 3 → GiayCNSK=0


# ---- E-04: NAP-05 nạp KHÔNG ảnh → TT_XuLy=01, không .jp2 (BR-011) ----
def test_e04_nap_khong_anh(ctx, don):
    cmt = "000000000005"
    _don_cmt(cmt)
    with sqlserver_conn() as conn:
        r = nap.nap_mot_hv(conn, _hv(cmt, ctx["dv"]), ctx["khoa"], None,
                           ctx["img"], "", _uuid("e04"), [{"ma_gt": 1, "ten_gt": "x"}])
    don(r["ma_dk"])
    assert r["duong_dan_anh"] is None
    with sqlserver_cursor() as cur:
        cur.execute("SELECT TT_XuLy, DuongDanAnh, ChatLuongAnh FROM NguoiLX_HoSo WHERE MaDK=%s",
                    (r["ma_dk"],))
        hs = cur.fetchone()
    assert hs["TT_XuLy"] == "01"
    assert hs["DuongDanAnh"] is None and hs["ChatLuongAnh"] is None
    assert not (Path(ctx["img"]) / MA_KH / f"{r['ma_dk']}.jp2").exists()


# ---- E-trùng: NAP-06 nạp lại cùng CMT cùng khóa → SP @p_out=-2, không tạo HV 2 ----
def test_e_trung_cccd_cung_khoa(ctx, don):
    cmt = "000000000006"
    _don_cmt(cmt)
    with sqlserver_conn() as conn:
        r = nap.nap_mot_hv(conn, _hv(cmt, ctx["dv"]), ctx["khoa"], None,
                           ctx["img"], "", _uuid("etr1"), [{"ma_gt": 1, "ten_gt": "x"}])
    don(r["ma_dk"])
    with sqlserver_conn() as conn:
        with pytest.raises(ValueError, match="CCCD"):
            nap.nap_mot_hv(conn, _hv(cmt, ctx["dv"]), ctx["khoa"], None,
                           ctx["img"], "", _uuid("etr2"), [{"ma_gt": 1, "ten_gt": "x"}])
    with sqlserver_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM NguoiLX lx JOIN NguoiLX_HoSo hs ON hs.MaDK=lx.MaDK "
                    "WHERE lx.SoCMT=%s AND hs.MaKhoaHoc=%s", (cmt, MA_KH))
        assert cur.fetchone()["n"] == 1      # vẫn chỉ 1 HV, không tạo thứ 2


# ---- E-03: NAP-06 cùng CMT khác khóa → cho phép (kiểm sớm) ----
def test_e03_kiem_trung_khac_khoa_cho_phep(ctx, don):
    cmt = "000000000007"
    _don_cmt(cmt)
    with sqlserver_conn() as conn:
        r = nap.nap_mot_hv(conn, _hv(cmt, ctx["dv"]), ctx["khoa"], None,
                           ctx["img"], "", _uuid("e03"), [{"ma_gt": 1, "ten_gt": "x"}])
    don(r["ma_dk"])
    assert kiem_trung_cccd(ma_kh=MA_KH, so_cmt=cmt)["trung"] is True            # cùng khóa → trùng
    assert kiem_trung_cccd(ma_kh="70004K26B999", so_cmt=cmt)["trung"] is False  # khác khóa → cho phép
