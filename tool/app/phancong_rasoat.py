"""Phân công GV – xe (PCG-05) — rà soát mọi khóa của CSĐT. Chỉ ĐỌC.

Mỗi khóa: GV trong danh sách · GV chưa phân công · GV có phân công ngoài danh sách · xe trong danh sách ·
xe chưa ghép · xe ghép ngoài danh sách · kết luận Ổn / Cần xử lý. TDD §11E.7.
"""
from __future__ import annotations

from app import sync_helpers

_GIOI_HAN = 200


def ra_soat(conn, ma_csdt: str) -> list[dict]:
    cur = conn.cursor(as_dict=True)
    cur.execute(
        f"SELECT TOP {_GIOI_HAN} kh.MaKH, kh.TenKH, kh.HangGPLX, kh.HangDT, "
        "CONVERT(varchar(10), kh.NgayKG, 120) AS NgayKG, CONVERT(varchar(10), kh.NgayBG, 120) AS NgayBG, "
        f"{sync_helpers.dkkh_exists_sql('kh')} AS dkkh "
        "FROM dbo.KhoaHoc kh WHERE kh.MaCSDT = %s AND kh.TrangThai = 1 ORDER BY kh.NgayKG DESC, kh.MaKH DESC",
        (ma_csdt,),
    )
    khoa = cur.fetchall()

    gv_ds: dict[str, set[str]] = {}
    gv_pc: dict[str, set[str]] = {}
    cur.execute(
        "SELECT g.MaKH, g.MaGV, g.IsKhoaHocGiaoVien AS la_ds "
        "FROM dbo.KhoaHoc kh JOIN dbo.KhoaHoc_GiaoVien g ON g.MaKH = kh.MaKH "
        "WHERE kh.MaCSDT = %s AND kh.TrangThai = 1 AND g.TrangThai = 1",
        (ma_csdt,),
    )
    for r in cur.fetchall():
        d = gv_ds if r["la_ds"] else gv_pc
        d.setdefault(r["MaKH"], set()).add((r["MaGV"] or "").strip())

    xe_ds: dict[str, set[str]] = {}
    xe_gh: dict[str, set[str]] = {}
    cur.execute(
        "SELECT x.MaKH, x.BienSoXe, x.IsKhoaHocXeTap AS la_ds "
        "FROM dbo.KhoaHoc kh JOIN dbo.KhoaHoc_XeTap x ON x.MaKH = kh.MaKH "
        "WHERE kh.MaCSDT = %s AND kh.TrangThai = 1 AND x.TrangThai = 1",
        (ma_csdt,),
    )
    for r in cur.fetchall():
        d = xe_ds if r["la_ds"] else xe_gh
        d.setdefault(r["MaKH"], set()).add((r["BienSoXe"] or "").strip())

    out: list[dict] = []
    for k in khoa:
        ma = k["MaKH"]
        ds, pc = gv_ds.get(ma, set()), gv_pc.get(ma, set())
        xds, xgh = xe_ds.get(ma, set()), xe_gh.get(ma, set())
        r = {
            "ma_kh": ma, "ten_kh": k["TenKH"], "hang_dt": (k["HangDT"] or k["HangGPLX"] or "").strip(),
            "kg": k["NgayKG"], "bg": k["NgayBG"], "da_dkkh": bool(k["dkkh"]),
            "gv_ds": len(ds), "gv_chua_pc": len(ds - pc), "pc_ngoai_ds": len(pc - ds),
            "xe_ds": len(xds), "xe_chua_ghep": len(xds - xgh), "ghep_ngoai_ds": len(xgh - xds),
        }
        r["can_xu_ly"] = r["gv_ds"] == 0 or any(r[c] for c in ("gv_chua_pc", "pc_ngoai_ds", "ghep_ngoai_ds"))
        out.append(r)
    return out
