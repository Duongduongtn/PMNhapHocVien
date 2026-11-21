"""In Báo cáo 2 — ghép dữ liệu bản in + lựa chọn phần thi (TNB-08, task 165). TDD §11F.9.

Chỉ ĐỌC DB Nạp (`GPLX_CSDT`): dữ liệu dòng giống `usp_BaoCao2_ViewRPT` (nhánh mọi HV trong BC2 — khớp danh sách gói
XML gửi Sở), đầu trang `usp_BaoCao_TieuDe`. Lựa chọn và sổ phần thi lưu SQLite (`tn_bc2_ban_in`).
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Iterable

from app import tn_bc2_ban_in as kho
from app import tn_bc2_phan_thi as pt
from app import tn_bc2_rules as rules
from app import tn_bc2_service as svc

# Cùng cột, điều kiện, thứ tự với usp_BaoCao2_ViewRPT (nhánh @Loai <> '1'), thêm cột cho luật phần thi.
_Q_DONG = """
SELECT A.MaDK, B.HoVaTen,
       (CASE WHEN LEN(B.NgaySinh) < 7 THEN B.NgaySinh
             ELSE SUBSTRING(B.NgaySinh,7,2) + '/' + SUBSTRING(B.NgaySinh,5,2) + '/' + SUBSTRING(B.NgaySinh,1,4) END) AS NgaySinh,
       B.SoCMT,
       (B.NoiCT + ' ' + (SELECT TenDayDu FROM DM_DVHC WHERE MaDVHC = B.NoiCT_MaDVHC AND MaDVQL = B.NoiCT_MaDVQL)) AS NoiCT,
       A.GiayCNSK, A.HangGPLXDaCo, A.SoNamLX, A.SoKmLXAnToan,
       dbo.usf_ToanPK_BoDauPhaiCuoi(A.SoGiayCNTN, A.SoCCN) AS CCTN,
       dbo.usf_BaBT_GetMaNoidungSathach(A.MaDK) AS MaNDCu,
       dbo.usf_BaBT_GetNoidungSathach(A.MaDK) AS TenNDCu,
       A.HangGPLX, A.KetQuaSH, A.KetQua_LyThuyet, A.KetQua_Hinh, A.KetQua_Duong, A.MaKySH, A.NgayQDTT, A.MaKhoaHoc
FROM dbo.NguoiLX_HoSo A, dbo.NguoiLX B
WHERE A.MaBC2 = %s AND A.MaDK = B.MaDK AND A.TT_XuLy IN ('11','12','13','14','16','17','18','19')
ORDER BY B.TenNLX, B.HoDemNLX
"""
_Q_DM_ND = "SELECT MaNoiDungSH, TenNoiDungSH FROM dbo.DM_NoiDungSH"
_Q_DM_DIEM = "SELECT Hang, LtDiemToiThieu, HiDiemToiThieu, DdDiemToiThieu FROM dbo.DM_DiemSatHach"

_MA_CO_M = {11, 12, 13, 14, 15, 16, 17, 19, 20}
_COT_IN = ("HoVaTen", "NgaySinh", "SoCMT", "NoiCT", "GiayCNSK", "HangGPLXDaCo", "SoNamLX", "SoKmLXAnToan", "CCTN")
_TEN_NGUON = {"so": "Kết quả Sở", "sua": "User chỉnh sửa", "in": "Theo BC2 đã in", "suy": "Suy từ DB", "pm_cu": "Theo phần mềm cũ",
              "chua_thi": "Chưa thi", "qua_han": "Quá hạn bảo lưu — thi lại toàn bộ"}


def _s(v) -> str:
    return "" if v is None else str(v).strip()


def _ngay(v) -> date | None:
    if isinstance(v, datetime):
        return v.date()
    return v if isinstance(v, date) else None


def doc_dm_noi_dung(cur) -> dict[int, str]:
    cur.execute(_Q_DM_ND)
    return {int(r["MaNoiDungSH"]): _s(r["TenNoiDungSH"]) for r in cur.fetchall()}


def _doc_bc2(cur, ma_bc2: str) -> tuple[str, dict]:
    dang_db = rules.dang_luu_ma_bcii(ma_bc2)
    bc2 = svc._doc_bc2_mot(cur, dang_db)
    if bc2 is None:
        raise svc.LoiNghiepVu("bc2_khong_ton_tai", f"Không có BC2 số {ma_bc2}", 404)
    return dang_db, bc2


def _cong_ket_qua_moi(dong: list[dict], so: dict[str, dict], nguong_map: dict, ma_bc2: str) -> int:
    """Kết quả Sở kỳ mới (MaKySH/KetQuaSH ở DB khác lúc user chọn ở BC2 trước) → cộng phần vừa đạt vào sổ."""
    moi = []
    for r in dong:
        s = so.get(r["MaDK"])
        kq = _s(r["KetQuaSH"]).upper()
        if not s or s["nguon"] not in kho.NGUON_CHON or s["ma_bc2"] == ma_bc2 or kq not in pt.KQ_DA_THI:
            continue
        if (_s(r["MaKySH"]), kq) == (_s(s["ma_ky_sh"]), _s(s["ket_qua_sh"]).upper()):
            continue                                   # DB chưa có kết quả kỳ đã chọn
        nhom = pt.nhom_hang(r["HangGPLX"])
        dat_moi = pt.dat_tu_ket_qua(nhom, kq, pt.diem_theo_nhom(nhom, r["KetQua_LyThuyet"], r["KetQua_Hinh"],
                                                                r["KetQua_Duong"]),
                                    nguong_map.get(_s(r["HangGPLX"])), s["phan_thi"])
        moi.append({"ma_dk": r["MaDK"], "ma_bc2": s["ma_bc2"], "phan_thi": s["phan_thi"], "ket_qua_sh": kq,
                    "diem": [r["KetQua_LyThuyet"], r["KetQua_Hinh"], r["KetQua_Duong"]],
                    "ma_ky_sh": _s(r["MaKySH"]), "dat": pt.thu_tu(nhom, pt.cong_don(s["dat"], dat_moi))})
    return kho.ghi_ket_qua(moi) if moi else 0


def du_lieu_ban_in(cur, ma_bc2: str, *, hom_nay: date | None = None) -> dict:
    """Đầu trang + dòng HV (cột in + phần thi đã đạt/phải thi + ghi chú) cho màn In BC2 và bản in."""
    hom_nay = hom_nay or date.today()
    dang_db, bc2 = _doc_bc2(cur, ma_bc2)
    cur.execute(_Q_DONG, (dang_db,))
    dong = cur.fetchall()
    dm = doc_dm_noi_dung(cur)
    cur.execute(_Q_DM_DIEM)
    dm_diem = cur.fetchall()
    ma_kh = Counter(_s(r["MaKhoaHoc"]) for r in dong).most_common(1)[0][0] if dong else ""
    tieu_de = {}
    if ma_kh:
        cur.execute("EXEC dbo.usp_BaoCao_TieuDe @MaKH = %s", (ma_kh,))
        tieu_de = cur.fetchone() or {}
    nguong_map = {h: pt.nguong_theo_hang(dm_diem, h) for h in {_s(r["HangGPLX"]) for r in dong}}

    ds_dk = [r["MaDK"] for r in dong]
    _cong_ket_qua_moi(dong, kho.so_moi_nhat(ds_dk), nguong_map, dang_db)
    so = kho.so_moi_nhat(ds_dk, tru_ma_bc2=dang_db)
    lua_chon = kho.doc_lua_chon(dang_db)

    hv, n_lai, n_can = [], 0, 0
    for i, r in enumerate(dong, 1):
        hang = _s(r["HangGPLX"])
        nhom = pt.nhom_hang(hang)
        s = so.get(r["MaDK"])
        md = pt.mac_dinh(hang=hang, ket_qua_sh=r["KetQuaSH"],
                         diem=pt.diem_theo_nhom(nhom, r["KetQua_LyThuyet"], r["KetQua_Hinh"], r["KetQua_Duong"]),
                         nguong=nguong_map.get(hang), hang_gplx_da_co=r["HangGPLXDaCo"],
                         ngay_qdtt=_ngay(r["NgayQDTT"]), hom_nay=hom_nay,
                         so={"dat": s["dat"], "da_thi": s["da_thi"], "nguon": s["nguon"]} if s else None,
                         ma_pm_cu=r["MaNDCu"])
        ma_cu = int(r["MaNDCu"]) if r["MaNDCu"] is not None else None
        ten_cu = _s(r["TenNDCu"])

        lc = lua_chon.get(r["MaDK"])

        def ghi_chu(ma: int | None, dung_chu_cu: bool = True) -> str:
            if ma is None:
                return ""
            if dung_chu_cu and ma == ma_cu and ma_cu not in _MA_CO_M and ten_cu:
                return ten_cu                       # dòng chưa chọn lại: giữ đúng chữ phần mềm cũ khi trùng mục
            return pt.ten_in(nhom, ma, dm.get(ma, ""))

        if lc:
            phai, da_thi = pt.thu_tu(nhom, lc["phai_thi"]), lc["da_thi"]
            ma = pt.muc_tu_phan(nhom, phai, da_thi)
        else:
            phai, da_thi, ma = md["phai_thi"], md["da_thi"], md["ma"]
        da_sua = bool(lc) and phai != md["phai_thi"]
        n_lai += 1 if da_sua else 0
        n_can += 1 if ma is None else 0
        gc = ghi_chu(ma, dung_chu_cu=lc is None)
        hv.append({
            "stt": i, "ma_dk": r["MaDK"], "ho_ten": _s(r["HoVaTen"]), "ngay_sinh": _s(r["NgaySinh"]),
            "so_cmt": _s(r["SoCMT"]), "noi_ct": _s(r["NoiCT"]), "giay_cnsk": bool(r["GiayCNSK"]),
            "hang_gplx_da_co": _s(r["HangGPLXDaCo"]), "so_nam_lx": r["SoNamLX"], "so_km_lx": r["SoKmLXAnToan"],
            "cctn": _s(r["CCTN"]), "hang": hang, "nhom": nhom, "phan": list(pt.PHAN[nhom]),
            "phai_thi": phai, "dat": [p for p in pt.PHAN[nhom] if p not in phai], "da_thi": da_thi,
            "ma_nd": ma, "ghi_chu": gc, "da_sua": da_sua,
            "nguon": "sua" if da_sua else md["nguon"],
            "ten_nguon": _TEN_NGUON["sua" if da_sua else md["nguon"]],
            "nguon_luc": (lc["luc"] if da_sua else (s["luc"] if s else "")) or "",
            "ket_qua_sh": _s(r["KetQuaSH"]),
            "mac_dinh": {"phai_thi": md["phai_thi"], "dat": md["dat"], "ma_nd": md["ma"], "ghi_chu": ghi_chu(md["ma"]),
                         "da_thi": md["da_thi"]},
            "ma_ky_sh": _s(r["MaKySH"]),
            "pm_cu": ten_cu, "pm_cu_khac": bool(ten_cu) and ten_cu != gc,
            # nguyên giá trị SP cũ trả (không cắt khoảng trắng / không đổi None) để bản in giống tuyệt đối
            "cot_in": {k: r[k] for k in _COT_IN},
        })
    kho.ghi_tom_tat(dang_db, n_lai, n_can)
    return {
        "ma_bc2": dang_db, "so_bao_cao": bc2["so_bao_cao"], "ngay_bao_cao": bc2["ngay_bao_cao"],
        "dang_mo": bc2["trang_thai"] == 0, "ma_kh": ma_kh, "tieu_de": _tieu_de(tieu_de),
        "loai": rules.loai_hang(dong[0]["HangGPLX"]) if dong else "", "hoc_vien": hv,
        "so_chon_lai": n_lai, "so_can_chon": n_can,
    }


def _tieu_de(r: dict) -> dict:
    """Giữ nguyên tên cột usp_BaoCao_TieuDe (Crystal đọc đúng tên này); ngày → ISO cho JSON."""
    out = {}
    for k, v in (r or {}).items():
        out[k] = v.isoformat() if isinstance(v, (date, datetime)) else v
    return out


def luu_noi_dung_thi(cur, ma_bc2: str, ds: Iterable[dict], nguoi: str, *, hom_nay: date | None = None) -> dict:
    """Lưu lựa chọn phần thi (mỗi dòng {ma_dk, phai_thi: [..] | None}); None = về mặc định. Trả dữ liệu mới."""
    hien = du_lieu_ban_in(cur, ma_bc2, hom_nay=hom_nay)
    theo_dk = {h["ma_dk"]: h for h in hien["hoc_vien"]}
    ghi = []
    for d in ds:
        h = theo_dk.get(_s(d.get("ma_dk")))
        if h is None:
            raise svc.LoiNghiepVu("hv_khong_thuoc_bc2", f"Học viên {d.get('ma_dk')} không có trong BC2 này", 400)
        phai = d.get("phai_thi")
        if phai is None:
            ghi.append({"ma_dk": h["ma_dk"], "phai_thi": None})
            continue
        if not isinstance(phai, list) or any(p not in h["phan"] for p in phai):
            raise svc.LoiNghiepVu("phan_thi_khong_hop_le", f"Phần thi không hợp lệ cho hạng {h['hang']}", 400)
        phai = pt.thu_tu(h["nhom"], phai)
        da_thi = h["mac_dinh"]["da_thi"]
        ghi.append({"ma_dk": h["ma_dk"], "phai_thi": phai, "da_thi": da_thi,
                    "dat": [p for p in h["phan"] if p not in phai], "ma_nd": pt.muc_tu_phan(h["nhom"], phai, da_thi),
                    "mac_dinh": phai == h["mac_dinh"]["phai_thi"], "ket_qua_sh": h["ket_qua_sh"],
                    "ma_ky_sh": h["ma_ky_sh"]})
    kho.luu_lua_chon(hien["ma_bc2"], ghi, nguoi)
    return du_lieu_ban_in(cur, ma_bc2, hom_nay=hom_nay)


def ghi_da_in(cur, ma_bc2: str, nguoi: str, *, hom_nay: date | None = None) -> dict:
    """In… / Lưu PDF: chụp phần thi mọi HV có nội dung thi vào sổ + ghi một lần in (cột "Bản in")."""
    dl = du_lieu_ban_in(cur, ma_bc2, hom_nay=hom_nay)
    kho.chup_phan_thi(dl["ma_bc2"], [
        {"ma_dk": h["ma_dk"], "phai_thi": h["phai_thi"], "dat": h["dat"], "da_thi": h["da_thi"],
         "ket_qua_sh": h["ket_qua_sh"], "ma_ky_sh": h["ma_ky_sh"]} for h in dl["hoc_vien"] if h["ma_nd"] is not None], nguoi)
    kho.ghi_lan_in(dl["ma_bc2"], nguoi, len(dl["hoc_vien"]), dl["so_chon_lai"])
    return {"ok": True, "so_hv": len(dl["hoc_vien"]), "so_chon_lai": dl["so_chon_lai"]}


def du_lieu_crystal(dl: dict) -> dict:
    """Dữ liệu đưa vào mẫu rptBaoCao2.rpt: 2 bảng đúng tên cột của 2 SP cũ, Ghi chú = nội dung thi đã chọn."""
    rows = [{**h["cot_in"], "GhiChu": h["ghi_chu"]} for h in dl["hoc_vien"]]
    return {"ma_kh": dl["ma_kh"], "ma_bc2": dl["ma_bc2"].replace("Ð", "Đ").replace("ð", "đ"),
            "tieu_de": dl["tieu_de"], "dong": rows}
