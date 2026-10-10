"""Phân công GV – xe (PCG, task 85) — LUẬT THUẦN, không đụng DB.

Nguồn luật: schema CDB không ràng buộc gì (không UNIQUE/CHECK/trigger); chỉ SP
`usp_CheckWarning*` do UI phần mềm CDB gọi mới kiểm. SP Insert/Update KHÔNG tự kiểm →
tool phải tự áp đúng công thức. TDD §11E.7, TDD-decisions §22, PRD PCG-04.

Thời gian: chuỗi ISO `YYYY-MM-DDTHH:MM` (so sánh từ điển = so sánh thời gian). Khoảng là
**nửa mở** `[bd, kt)`: trùng ⇔ `NOT (kt <= bd_cũ OR bd >= kt_cũ)` — kết thúc đúng lúc bắt đầu
kế tiếp KHÔNG trùng; cùng ngày khác giờ KHÔNG trùng (đúng CDB).

Module này chỉ NHẬN dữ liệu đã đọc (khóa, danh mục GV/xe, "bận" ở khóa khác, bản nháp) và
TRẢ danh sách vấn đề. Đọc DB nằm ở `phancong_service.py` (task 86).
"""
from __future__ import annotations

from typing import Any, Iterable

CHAN = "chan"            # ⛔ không lưu/ghi được
CANH_BAO = "canh_bao"    # ⚠ ghi được sau khi xác nhận
THONG_TIN = "thong_tin"  # ℹ chỉ báo

MON_THUC_HANH = 6        # DM_MonHoc.MaMH = "Thực hành lái xe"

# Hạng xe chấp nhận được cho hạng xe của khóa — theo dữ liệu thật (10/10/2026): khóa B01
# (`B11`, số tự động) dùng cả xe `B11` (10 lượt) lẫn xe `B1` (29 lượt) → coi là bình thường.
XE_HOP_HANG: dict[str, set[str]] = {"B11": {"B11", "B1"}, "B1": {"B1"}, "C1": {"C1"}}


# ── Tiện ích thời gian ──
def _chuan(dt: str | None) -> str:
    """'2026-10-01T07:30' → '2026-10-01T07:30:00' (so khớp biên 23:59:59 của CDB)."""
    if not dt:
        return ""
    dt = dt.replace(" ", "T")
    return dt + ":00" if len(dt) == 16 else dt


def ngay(dt: str | None) -> str:
    return (dt or "")[:10]


def gio(dt: str | None) -> str:
    return (dt or "")[11:16]


def chong_nhau(a_bd: str, a_kt: str, b_bd: str, b_kt: str) -> bool:
    """Hai khoảng nửa mở giao nhau thật (đúng công thức CDB). Chạm đầu mút → False."""
    return not (_chuan(a_kt) <= _chuan(b_bd) or _chuan(a_bd) >= _chuan(b_kt))


def _fmt_ngay(d: str) -> str:
    """'2026-10-20' → '20/10/2026'."""
    p = (d or "")[:10].split("-")
    return f"{p[2]}/{p[1]}/{p[0]}" if len(p) == 3 else (d or "—")


def fmt_khoang(bd: str, kt: str) -> str:
    """Hiển thị VN: 00:00 → chỉ ngày; có giờ → kèm giờ (24h)."""
    if not bd or not kt:
        return "—"
    g1, g2 = gio(bd), gio(kt)
    if g1 == "00:00" and g2 == "00:00":
        return f"{_fmt_ngay(bd)} → {_fmt_ngay(kt)}"
    if ngay(bd) == ngay(kt):
        return f"{_fmt_ngay(bd)} {g1} → {g2}"
    return f"{_fmt_ngay(bd)} {g1} → {_fmt_ngay(kt)} {g2}"


# ── Vấn đề ──
def _vd(muc: str, ma: str, buoc: int, ref: str, ai: str, nd: str) -> dict:
    return {"muc": muc, "ma": ma, "buoc": buoc, "ref": ref, "ai": ai, "noi_dung": nd}


def _ten_mon(ids: Iterable[int], ds_mon: dict[int, str] | None) -> str:
    ids = list(ids)
    if ds_mon:
        return " + ".join(ds_mon.get(i, str(i)) for i in ids)
    return ",".join(str(i) for i in ids)


# ── Luật cơ bản của một khoảng thời gian trong khóa ──
def kiem_khoang_khoa(khoa: dict, bd: str, kt: str, ma_loi: str = "ngoai_khoa") -> list[tuple[str, str, str]]:
    """Trả [(mức, mã, nội dung)] cho riêng quan hệ khoảng-thời-gian ↔ khóa."""
    out: list[tuple[str, str, str]] = []
    if not bd or not kt:
        out.append((CHAN, "thieu_ngay", "Chưa nhập đủ từ ngày – đến ngày."))
        return out
    if _chuan(bd) >= _chuan(kt):
        out.append((CHAN, "bd_sau_kt",
                    "Thời điểm bắt đầu phải trước thời điểm kết thúc. Dạy trong 1 ngày: "
                    "tích \"Chỉnh giờ\" và chọn giờ bắt đầu < giờ kết thúc."))
    kg, bg = khoa["kg"], khoa["bg"]
    if _chuan(bd) <= _chuan(kg + "T00:00"):
        out.append((CHAN, ma_loi, f"Phải bắt đầu SAU 00:00 ngày khai giảng {_fmt_ngay(kg)} "
                                  "(chọn ngày sau, hoặc chỉnh giờ)."))
    if _chuan(kt) >= _chuan(bg + "T23:59:59"):
        out.append((CHAN, ma_loi, f"Phải kết thúc TRƯỚC hết ngày bế giảng {_fmt_ngay(bg)} (23:59)."))
    return out


# ── Kiểm một phân công (cờ=0 của GV) ──
def kiem_phan_cong(p: dict, ctx: dict) -> list[dict]:
    """`ctx`: khoa, gv_master{ma→dict}, gv_khoa[list ma], pc[list toàn bộ bản nháp],
    ban_gv{ma→[{khoa,tu,den,bg}]}, hom_nay 'YYYY-MM-DD', ds_mon{id→tên}."""
    khoa, gvm, ma = ctx["khoa"], ctx["gv_master"], p["ma"]
    g = gvm.get(ma)
    ten = (g or {}).get("ten") or ma
    ref = f"pc-{p.get('id')}"
    ai = f"{ten} · {_ten_mon(p.get('mon') or [], ctx.get('ds_mon'))}"
    out: list[dict] = []
    add = lambda muc, code, nd: out.append(_vd(muc, code, 2, ref, ai, nd))  # noqa: E731

    if not p.get("mon"):
        add(CHAN, "thieu_mon", "Chưa chọn môn dạy.")
    for muc, code, nd in kiem_khoang_khoa(khoa, p.get("tu", ""), p.get("den", "")):
        add(muc, code, nd)
    if ma not in ctx["gv_khoa"]:
        add(CHAN, "gv_ngoai_khoa", "Giáo viên chưa thuộc danh sách GV của khóa — thêm ở bước ① trước.")
    if g is None:
        add(CHAN, "gv_khong_ton_tai", "Không tìm thấy giáo viên trong danh mục của cơ sở.")
    elif not g.get("active", True):
        add(CHAN, "gv_ngung", "Giáo viên đã ngừng hoạt động.")

    hop_le_tg = p.get("tu") and p.get("den") and _chuan(p["tu"]) < _chuan(p["den"])
    if hop_le_tg:
        for b in ctx.get("ban_gv", {}).get(ma, []):
            if chong_nhau(p["tu"], p["den"], b["tu"], b["den"]):
                add(CHAN, "gv_trung_khoa_khac",
                    f"Trùng thời gian với khóa {b['khoa']} ({fmt_khoang(b['tu'], b['den'])}).")
        for q in ctx["pc"]:
            if q is p or q.get("id") == p.get("id") or q["ma"] != ma or not (q.get("tu") and q.get("den")):
                continue
            if chong_nhau(p["tu"], p["den"], q["tu"], q["den"]):
                add(CHAN, "gv_trung_cung_khoa",
                    "Chồng thời gian với phân công khác của GV này trong cùng khóa: "
                    f"{_ten_mon(q.get('mon') or [], ctx.get('ds_mon'))} ({fmt_khoang(q['tu'], q['den'])}).")
    if MON_THUC_HANH in (p.get("mon") or []) and p.get("den") and ngay(p["den"]) < khoa["bg"]:
        add(CANH_BAO, "th_chua_toi_be_giang",
            f"Thực hành mới kéo đến {_fmt_ngay(ngay(p['den']))}, chưa tới ngày bế giảng {_fmt_ngay(khoa['bg'])}.")
    return out


# ── Kiểm một ghép xe (cờ=0 của xe) ──
def co_phan_cong_thuc_hanh(ma_gv: str, pc: list[dict]) -> bool:
    return any(p["ma"] == ma_gv and MON_THUC_HANH in (p.get("mon") or []) for p in pc)


def kiem_ghep_xe(m: dict, ctx: dict) -> list[dict]:
    khoa, gvm, xem = ctx["khoa"], ctx["gv_master"], ctx["xe_master"]
    ma, bs = m["ma"], m.get("xe")
    if not bs:
        return []
    ten = (gvm.get(ma) or {}).get("ten") or ma
    ref, ai = f"gh-{ma}", f"{ten} ↔ {bs}"
    out: list[dict] = []
    add = lambda muc, code, nd: out.append(_vd(muc, code, 3, ref, ai, nd))  # noqa: E731
    x = xem.get(bs)

    if ma not in ctx["gv_khoa"]:
        add(CHAN, "gv_ngoai_khoa", "Giáo viên chưa thuộc danh sách GV của khóa.")
    if not co_phan_cong_thuc_hanh(ma, ctx["pc"]):
        add(CHAN, "gv_khong_day_th", "Chỉ ghép xe cho giáo viên có phân công \"Thực hành lái xe\".")
    if bs not in ctx["xe_khoa"]:
        add(CHAN, "xe_ngoai_khoa", "Xe chưa thuộc danh sách xe của khóa — thêm xe vào khóa trước.")
    if x is None:
        add(CHAN, "xe_khong_ton_tai", "Không tìm thấy xe trong danh mục của cơ sở.")
    else:
        if not x.get("active", True):
            add(CHAN, "xe_ngung", "Xe đã ngừng hoạt động.")
        het = x.get("gp_het")  # ngày hết hạn sớm nhất của GPXTL / GCNKD
        if het and ngay(het) < khoa["bg"]:
            add(CHAN, "xe_het_han",
                f"Giấy phép xe tập lái hết hạn {_fmt_ngay(ngay(het))} — trước ngày bế giảng {_fmt_ngay(khoa['bg'])}.")
    tu, den = m.get("tu", ""), m.get("den", "")
    for muc, code, nd in kiem_khoang_khoa(khoa, tu, den):
        add(muc, code if code != "ngoai_khoa" else "ghep_ngoai_khoa", nd)
    if tu and den and _chuan(tu) < _chuan(den):
        for b in ctx.get("ban_xe", {}).get(bs, []):
            if chong_nhau(tu, den, b["tu"], b["den"]):
                add(CHAN, "xe_trung_khoa_khac",
                    f"Xe trùng thời gian với khóa {b['khoa']} ({fmt_khoang(b['tu'], b['den'])}).")
        for o in ctx["ghep"]:
            if o is m or not o.get("xe") or not (o.get("tu") and o.get("den")):
                continue
            if not chong_nhau(tu, den, o["tu"], o["den"]):
                continue
            if o["xe"] == bs and o["ma"] != ma:
                add(CHAN, "xe_hai_gv",
                    f"Xe này đã ghép cho GV {(gvm.get(o['ma']) or {}).get('ten') or o['ma']} trong khóa (1 xe chỉ 1 GV).")
            if o["ma"] == ma and o["xe"] != bs:
                add(CHAN, "gv_hai_xe", "Giáo viên này đã có xe khác trong cùng khoảng thời gian (1 GV chỉ 1 xe).")
    return out


# ── Kiểm cả khóa ──
def kiem_tra_khoa(
    khoa: dict,
    gv_master: dict[str, dict],
    xe_master: dict[str, dict],
    gv_khoa: list[str],
    pc: list[dict],
    xe_khoa: list[str],
    ghep: list[dict],
    ban_gv: dict[str, list[dict]] | None = None,
    ban_xe: dict[str, list[dict]] | None = None,
    hom_nay: str = "",
    ds_mon: dict[int, str] | None = None,
) -> list[dict]:
    """Chạy toàn bộ luật. `khoa`: {ma,kg,bg:'YYYY-MM-DD', hang_nhom, hang_xe, da_dkkh}.

    `ban_gv/ban_xe`: các dòng cờ=0 ở khóa KHÁC (+ dòng của chính khóa này mà bản nháp KHÔNG
    chứa) đã được tầng đọc lọc sẵn; luật này tự so các dòng trong bản nháp với nhau."""
    ctx = {
        "khoa": khoa, "gv_master": gv_master, "xe_master": xe_master, "gv_khoa": gv_khoa,
        "pc": pc, "xe_khoa": xe_khoa, "ghep": ghep, "ban_gv": ban_gv or {}, "ban_xe": ban_xe or {},
        "hom_nay": hom_nay or "9999-12-31", "ds_mon": ds_mon,
    }
    out: list[dict] = []
    for ma in gv_khoa:
        g = gv_master.get(ma)
        ten = (g or {}).get("ten") or ma
        if g is not None and not g.get("active", True):
            out.append(_vd(CHAN, "gv_ngung_trong_khoa", 1, f"gv-{ma}", ten,
                           "Giáo viên đã ngừng hoạt động nhưng còn trong danh sách khóa."))
        if not any(p["ma"] == ma for p in pc):
            out.append(_vd(CANH_BAO, "gv_chua_phan_cong", 2, f"gv-{ma}", ten, "Chưa có phân công dạy nào."))
    for p in pc:
        out += kiem_phan_cong(p, ctx)
    for m in ghep:
        out += kiem_ghep_xe(m, ctx)
    # Cảnh báo theo GV (MỘT lần/GV/khóa — không lặp theo từng dòng phân công)
    for ma in dict.fromkeys(gv_khoa):
        g = gv_master.get(ma)
        if g is None:
            continue
        ten = g.get("ten") or ma
        day_duoc = g.get("hang_duoc_day") or []
        if day_duoc and khoa.get("hang_nhom") and khoa["hang_nhom"] not in day_duoc:
            out.append(_vd(CANH_BAO, "gv_lech_hang", 1, f"gv-{ma}", ten,
                           f"Giáo viên chỉ được dạy hạng {', '.join(day_duoc)} — khóa này là hạng {khoa['hang_nhom']}."))
        khoa_khac: dict[str, str] = {}
        for b in ctx["ban_gv"].get(ma, []):
            if (b.get("bg") or "") < ctx["hom_nay"]:
                continue
            if any(q["ma"] == ma and q.get("tu") and q.get("den") and chong_nhau(q["tu"], q["den"], b["tu"], b["den"]) for q in pc):
                continue  # đã báo ⛔ trùng thời gian ở dòng phân công
            khoa_khac.setdefault(b["khoa"], b["bg"])
        if khoa_khac:   # MỘT dòng/GV, liệt kê các khóa
            ds = ", ".join(f"{k} (bế giảng {_fmt_ngay(bg)})" for k, bg in khoa_khac.items())
            out.append(_vd(CANH_BAO, "gv_dang_khoa_khac", 1, f"gv-{ma}", ten, f"Đang dạy khóa khác chưa kết thúc: {ds}."))
    # Cảnh báo theo xe (một lần/xe/khóa)
    for bs in dict.fromkeys(xe_khoa):
        x = xe_master.get(bs)
        if x is None:
            continue
        if not x.get("active", True):
            out.append(_vd(CHAN, "xe_ngung_trong_khoa", 3, f"xe-{bs}", bs,
                           "Xe đã ngừng hoạt động nhưng còn trong danh sách xe của khóa."))
        hang_xe = khoa.get("hang_xe")
        if hang_xe and x.get("hang") and x["hang"] not in XE_HOP_HANG.get(hang_xe, {hang_xe}):
            out.append(_vd(CANH_BAO, "xe_lech_hang", 3, f"xe-{bs}", bs,
                           f"Xe hạng {x['hang']} nhưng khóa dùng xe hạng {hang_xe}."))
        khoa_khac = {}
        for b in ctx["ban_xe"].get(bs, []):
            if (b.get("bg") or "") < ctx["hom_nay"]:
                continue
            if any(m.get("xe") == bs and m.get("tu") and m.get("den") and chong_nhau(m["tu"], m["den"], b["tu"], b["den"]) for m in ghep):
                continue
            khoa_khac.setdefault(b["khoa"], b["bg"])
        if khoa_khac:
            ds = ", ".join(f"{k} (bế giảng {_fmt_ngay(bg)})" for k, bg in khoa_khac.items())
            out.append(_vd(CANH_BAO, "xe_dang_khoa_khac", 3, f"xe-{bs}", bs, f"Xe đang chạy khóa khác chưa kết thúc: {ds}."))
    da_ghep_xe = {m["ma"] for m in ghep if m.get("xe")}
    for ma in gv_khoa:
        if co_phan_cong_thuc_hanh(ma, pc) and ma not in da_ghep_xe:
            ten = (gv_master.get(ma) or {}).get("ten") or ma
            out.append(_vd(CANH_BAO, "gv_th_chua_xe", 3, f"gh-{ma}", ten, "GV thực hành chưa được ghép xe."))
    xe_da_ghep = {m["xe"] for m in ghep if m.get("xe")}
    for bs in xe_khoa:
        if bs not in xe_da_ghep:
            out.append(_vd(THONG_TIN, "xe_chua_ghep", 3, f"xe-{bs}", bs, "Xe thuộc khóa nhưng chưa ghép cho GV nào."))
    if khoa.get("da_dkkh"):
        out.append(_vd(CANH_BAO, "khoa_da_dkkh", 0, "", "Khóa đã gửi DKKH",
                       "GV/xe thay đổi sau khi gửi có thể lệch với bản Sở đang giữ."))
    return out


def tom_tat(vde: list[dict]) -> dict[str, int]:
    """Đếm theo mức: {'chan': n, 'canh_bao': n, 'thong_tin': n}."""
    r = {CHAN: 0, CANH_BAO: 0, THONG_TIN: 0}
    for v in vde:
        r[v["muc"]] = r.get(v["muc"], 0) + 1
    return r


def co_chan(vde: list[dict]) -> bool:
    return any(v["muc"] == CHAN for v in vde)
