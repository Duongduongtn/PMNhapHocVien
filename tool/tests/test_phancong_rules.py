"""PCG-04 (1/4) — task 85: luật thuần `phancong_rules` (không DB).

Khóa các bất biến của luật CDB đã verify 10/10/2026: datetime nửa mở (chạm đầu mút không
trùng, cùng ngày khác giờ được), phạm vi khóa (bd > 00:00 KG, kt < 23:59:59 BG), trùng so cả
cùng khóa, 1 GV–1 xe, hạn giấy phép, 3 mức.
"""
from app import phancong_rules as r

KHOA = {"ma": "75032K260010", "kg": "2026-10-01", "bg": "2026-12-20",
        "hang_nhom": "C1", "hang_xe": "C1", "da_dkkh": False}
HOM_NAY = "2026-10-10"


def gv(ma, loai="TH", active=True, hang=("B", "C1")):
    return {"ma": ma, "ten": f"GV {ma[-3:]}", "loai": loai, "active": active, "hang_duoc_day": list(hang)}


def xe(bs, hang="C1", active=True, het="2027-06-30"):
    return {"bs": bs, "hang": hang, "active": active, "gp_het": het}


def chay(pc=(), ghep=(), gv_khoa=("75032101",), xe_khoa=(), ban_gv=None, ban_xe=None, khoa=None, gvs=None, xes=None):
    gvm = {g["ma"]: g for g in (gvs or [gv("75032101"), gv("75032102"), gv("75032103")])}
    xem = {x["bs"]: x for x in (xes or [xe("93C-1"), xe("93C-2"), xe("60K-1", hang="B1")])}
    return r.kiem_tra_khoa(khoa or KHOA, gvm, xem, list(gv_khoa), [dict(p) for p in pc],
                           list(xe_khoa), [dict(m) for m in ghep], ban_gv, ban_xe, HOM_NAY,
                           {1: "Đạo đức", 4: "Luật", 6: "Thực hành lái xe"})


def ma_loi(vde, muc=r.CHAN):
    return sorted(v["ma"] for v in vde if v["muc"] == muc)


def P(i, ma, mon, tu, den):
    return {"id": i, "ma": ma, "mon": list(mon), "tu": tu, "den": den}


# ── Trùng thời gian: nửa mở, có xét giờ ──
def test_cham_dau_mut_khong_trung():
    pc = [P(1, "75032101", [4], "2026-10-04T00:00", "2026-10-06T00:00"),
          P(2, "75032101", [1], "2026-10-06T00:00", "2026-10-08T00:00")]
    assert r.CHAN not in {v["muc"] for v in chay(pc)}


def test_cung_ngay_sang_chieu_khong_trung():
    pc = [P(1, "75032101", [4], "2026-10-06T07:30", "2026-10-06T11:30"),
          P(2, "75032101", [1], "2026-10-06T13:30", "2026-10-06T17:30")]
    assert "gv_trung_cung_khoa" not in ma_loi(chay(pc))


def test_chong_gio_cung_khoa_chan_ca_hai_dong():
    pc = [P(1, "75032101", [4], "2026-10-06T07:30", "2026-10-06T11:30"),
          P(2, "75032101", [1], "2026-10-06T09:30", "2026-10-06T13:30")]
    v = chay(pc)
    assert ma_loi(v).count("gv_trung_cung_khoa") == 2          # mỗi dòng báo dòng kia
    assert {x["ref"] for x in v if x["ma"] == "gv_trung_cung_khoa"} == {"pc-1", "pc-2"}


def test_lich_ca_giai_doan_chiem_moi_gio():
    pc = [P(1, "75032101", [6], "2026-10-15T00:00", "2026-12-20T00:00"),
          P(2, "75032101", [4], "2026-10-20T07:30", "2026-10-20T11:30")]
    assert "gv_trung_cung_khoa" in ma_loi(chay(pc))


def test_gv_khac_nhau_cung_gio_khong_trung():
    pc = [P(1, "75032101", [4], "2026-10-06T07:30", "2026-10-06T11:30"),
          P(2, "75032102", [4], "2026-10-06T07:30", "2026-10-06T11:30")]
    assert r.CHAN not in {v["muc"] for v in chay(pc, gv_khoa=("75032101", "75032102"))}


def test_trung_khoa_khac_chan_va_khoa_khac_chua_be_giang_canh_bao():
    p = P(1, "75032101", [6], "2026-10-15T00:00", "2026-12-20T00:00")
    ban = {"75032101": [{"khoa": "B-K149", "tu": "2026-08-28T00:00", "den": "2026-10-26T00:00", "bg": "2026-10-26"}]}
    v = chay([p], ban_gv=ban)
    assert "gv_trung_khoa_khac" in ma_loi(v)
    ban2 = {"75032101": [{"khoa": "B01-K41", "tu": "2026-09-26T00:00", "den": "2026-10-12T00:00", "bg": "2026-10-28"}]}
    v2 = chay([p], ban_gv=ban2)
    assert "gv_trung_khoa_khac" not in ma_loi(v2)
    assert "gv_dang_khoa_khac" in ma_loi(v2, r.CANH_BAO)


def test_cham_dau_mut_voi_khoa_khac_khong_trung():
    p = P(1, "75032101", [6], "2026-10-12T00:00", "2026-12-20T00:00")
    ban = {"75032101": [{"khoa": "B01-K41", "tu": "2026-09-26T00:00", "den": "2026-10-12T00:00", "bg": "2026-10-28"}]}
    assert "gv_trung_khoa_khac" not in ma_loi(chay([p], ban_gv=ban))


def test_gio_le_cu_van_so_dung():
    pc = [P(1, "75032101", [4], "2026-10-06T07:30", "2026-10-06T11:34"),
          P(2, "75032101", [1], "2026-10-06T11:30", "2026-10-06T13:30")]       # 11:30 < 11:34 → chồng
    assert "gv_trung_cung_khoa" in ma_loi(chay(pc))


# ── Phạm vi khóa & thứ tự ──
def test_bat_dau_dung_00_gio_ngay_khai_giang_bi_chan():
    v = chay([P(1, "75032101", [4], "2026-10-01T00:00", "2026-10-03T00:00")])
    assert "ngoai_khoa" in ma_loi(v)
    ok = chay([P(1, "75032101", [4], "2026-10-01T07:30", "2026-10-03T00:00")])
    assert "ngoai_khoa" not in ma_loi(ok)


def test_ket_thuc_00_gio_ngay_be_giang_hop_le_con_23_59_59_bi_chan():
    assert "ngoai_khoa" not in ma_loi(chay([P(1, "75032101", [6], "2026-10-15T00:00", "2026-12-20T00:00")]))
    assert "ngoai_khoa" not in ma_loi(chay([P(1, "75032101", [6], "2026-10-15T00:00", "2026-12-20T23:59")]))
    assert "ngoai_khoa" in ma_loi(chay([P(1, "75032101", [6], "2026-10-15T00:00", "2026-12-21T00:00")]))
    assert "ngoai_khoa" in ma_loi(chay([P(1, "75032101", [6], "2026-10-15T00:00", "2026-12-20T23:59:59")]))


def test_bd_phai_truoc_kt_va_1_ngay_can_gio():
    assert "bd_sau_kt" in ma_loi(chay([P(1, "75032101", [4], "2026-10-06T00:00", "2026-10-06T00:00")]))
    assert "bd_sau_kt" in ma_loi(chay([P(1, "75032101", [4], "2026-10-07T00:00", "2026-10-06T00:00")]))
    assert "bd_sau_kt" not in ma_loi(chay([P(1, "75032101", [4], "2026-10-06T07:30", "2026-10-06T11:30")]))


def test_thieu_mon_thieu_ngay():
    v = chay([P(1, "75032101", [], "", "")])
    assert {"thieu_mon", "thieu_ngay"} <= set(ma_loi(v))


# ── GV ──
def test_gv_ngoai_khoa_ngung_khong_ton_tai():
    p = P(1, "75032102", [4], "2026-10-06T00:00", "2026-10-08T00:00")
    assert "gv_ngoai_khoa" in ma_loi(chay([p], gv_khoa=("75032101",)))
    v = chay([p], gv_khoa=("75032102",), gvs=[gv("75032102", active=False)])
    assert {"gv_ngung", "gv_ngung_trong_khoa"} <= set(ma_loi(v))
    assert "gv_khong_ton_tai" in ma_loi(chay([P(1, "75099999", [4], "2026-10-06T00:00", "2026-10-08T00:00")], gv_khoa=("75099999",)))


def test_gv_chua_phan_cong_va_lech_hang_la_canh_bao():
    v = chay([], gv_khoa=("75032101",))
    assert "gv_chua_phan_cong" in ma_loi(v, r.CANH_BAO)
    p = P(1, "75032103", [4], "2026-10-06T00:00", "2026-10-08T00:00")
    v2 = chay([p], gv_khoa=("75032103",), gvs=[gv("75032103", hang=("B",))])
    assert "gv_lech_hang" in ma_loi(v2, r.CANH_BAO) and r.CHAN not in {x["muc"] for x in v2}


def test_thuc_hanh_chua_toi_be_giang_canh_bao():
    v = chay([P(1, "75032101", [6], "2026-10-15T00:00", "2026-12-10T00:00")])
    assert "th_chua_toi_be_giang" in ma_loi(v, r.CANH_BAO)


# ── Ghép xe ──
def _th(ma="75032101", i=1):
    return P(i, ma, [6], "2026-10-15T00:00", "2026-12-20T00:00")


def _gh(ma, bs):
    return {"ma": ma, "xe": bs, "tu": "2026-10-15T00:00", "den": "2026-12-20T00:00"}


def test_ghep_hop_le_khong_loi():
    v = chay([_th()], [_gh("75032101", "93C-1")], xe_khoa=("93C-1",))
    assert ma_loi(v) == [] and ma_loi(v, r.CANH_BAO) == []


def test_ghep_xe_ngoai_khoa_ngung_het_han_khong_day_th():
    assert "xe_ngoai_khoa" in ma_loi(chay([_th()], [_gh("75032101", "93C-1")], xe_khoa=()))
    assert "xe_ngung" in ma_loi(chay([_th()], [_gh("75032101", "93C-9")], xe_khoa=("93C-9",), xes=[xe("93C-9", active=False)]))
    assert "xe_het_han" in ma_loi(chay([_th()], [_gh("75032101", "93C-9")], xe_khoa=("93C-9",), xes=[xe("93C-9", het="2026-11-30")]))
    assert "xe_het_han" not in ma_loi(chay([_th()], [_gh("75032101", "93C-9")], xe_khoa=("93C-9",), xes=[xe("93C-9", het="2026-12-20")]))
    assert "gv_khong_day_th" in ma_loi(chay([P(1, "75032101", [4], "2026-10-06T00:00", "2026-10-08T00:00")],
                                            [_gh("75032101", "93C-1")], xe_khoa=("93C-1",)))


def test_mot_xe_hai_gv_va_mot_gv_hai_xe_bi_chan():
    pc = [_th("75032101", 1), _th("75032102", 2)]
    v = chay(pc, [_gh("75032101", "93C-1"), _gh("75032102", "93C-1")],
             gv_khoa=("75032101", "75032102"), xe_khoa=("93C-1",))
    assert ma_loi(v).count("xe_hai_gv") == 2
    # ghép của cùng GV chỉ 1 dòng/GV trong UI, nhưng service có thể gửi 2 dòng → luật vẫn chặn
    v2 = chay([_th()], [_gh("75032101", "93C-1"), _gh("75032101", "93C-2")], xe_khoa=("93C-1", "93C-2"))
    assert "gv_hai_xe" in ma_loi(v2)


def test_xe_trung_khoa_khac_va_lech_hang():
    ban = {"93C-1": [{"khoa": "C1-K14", "tu": "2026-08-26T00:00", "den": "2026-11-16T00:00", "bg": "2026-11-16"}]}
    assert "xe_trung_khoa_khac" in ma_loi(chay([_th()], [_gh("75032101", "93C-1")], xe_khoa=("93C-1",), ban_xe=ban))
    v = chay([_th()], [_gh("75032101", "60K-1")], xe_khoa=("60K-1",))
    assert "xe_lech_hang" in ma_loi(v, r.CANH_BAO) and r.CHAN not in {x["muc"] for x in v}


def test_gv_th_chua_xe_xe_chua_ghep_dkkh():
    khoa = dict(KHOA, da_dkkh=True)
    v = chay([_th()], [], xe_khoa=("93C-1",), khoa=khoa)
    assert "gv_th_chua_xe" in ma_loi(v, r.CANH_BAO)
    assert "khoa_da_dkkh" in ma_loi(v, r.CANH_BAO)
    assert "xe_chua_ghep" in ma_loi(v, r.THONG_TIN)


def test_tom_tat_va_co_chan():
    v = chay([P(1, "75032101", [], "", "")])
    t = r.tom_tat(v)
    assert t[r.CHAN] >= 2 and r.co_chan(v)
    assert not r.co_chan(chay([_th()], [_gh("75032101", "93C-1")], xe_khoa=("93C-1",)))


def test_fmt_khoang_vn():
    assert r.fmt_khoang("2026-10-15T00:00", "2026-12-20T00:00") == "15/10/2026 → 20/12/2026"
    assert r.fmt_khoang("2026-10-12T07:30", "2026-10-12T11:30") == "12/10/2026 07:30 → 11:30"
    assert r.fmt_khoang("2026-10-01T07:30", "2026-10-03T17:30") == "01/10/2026 07:30 → 03/10/2026 17:30"


# ── Tinh chỉnh sau thử trên dữ liệu thật (10/10/2026) ──
def test_canh_bao_gv_dang_khoa_khac_chi_mot_lan_moi_gv_khoa():
    pc = [P(i, "75032101", [4], f"2026-10-0{i + 1}T07:30", f"2026-10-0{i + 1}T11:30") for i in range(1, 5)]
    ban = {"75032101": [{"khoa": "B01-K41", "tu": "2026-09-26T00:00", "den": "2026-09-30T00:00", "bg": "2026-10-28"},
                        {"khoa": "B01-K41", "tu": "2026-09-20T00:00", "den": "2026-09-25T00:00", "bg": "2026-10-28"}]}
    v = chay(pc, ban_gv=ban)
    assert ma_loi(v, r.CANH_BAO).count("gv_dang_khoa_khac") == 1            # không lặp theo dòng/khóa


def test_lech_hang_gv_mot_lan_va_xe_b11_chap_nhan_xe_b1():
    pc = [P(i, "75032103", [4], f"2026-10-0{i + 1}T00:00", f"2026-10-0{i + 2}T00:00") for i in range(1, 4)]
    v = chay(pc, gv_khoa=("75032103",), gvs=[gv("75032103", hang=("B",))])
    assert ma_loi(v, r.CANH_BAO).count("gv_lech_hang") == 1
    khoa = dict(KHOA, hang_xe="B11", hang_nhom="B")
    ok = chay([_th()], [_gh("75032101", "60K-1")], xe_khoa=("60K-1",), khoa=khoa)           # xe B1 vào khóa B11
    assert "xe_lech_hang" not in ma_loi(ok, r.CANH_BAO)
    sai = chay([_th()], [_gh("75032101", "93C-1")], xe_khoa=("93C-1",), khoa=khoa)          # xe C1 vào khóa B11
    assert "xe_lech_hang" in ma_loi(sai, r.CANH_BAO)
