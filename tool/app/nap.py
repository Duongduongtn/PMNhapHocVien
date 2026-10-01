"""NAP-05 (1/2) — nạp 1 học viên vào GPLX_CSDT qua SP (lõi, chưa giấy tờ/lô).

Tách 2 lớp:
- Hàm THUẦN (sinh SoHoSo, tách họ tên, suy giá trị, validate cột, dựng tham số SP):
  unit-test được, không chạm DB.
- Orchestration nap_mot_hv(): applock → usp_NguoiLX_Insert → ghi .jp2 → usp_NguoiLX_HoSo_Insert
  → releaseapplock, kèm compensation + chống mồ côi. Chạy LIVE ở bước kiểm riêng (ghi production).

Mọi ghi DB chỉ qua SP (TDD §10, ❌ không INSERT trực tiếp).
"""
from __future__ import annotations
import sqlite3
from datetime import datetime
from pathlib import Path

# ===== Hằng suy ra (TDD §10.2) =====
MA_CSDT = "70004"
MA_HT_CAP = "CM_VN"
MAX_LEN = {"HoVaTen": 50, "HoDemNLX": 30, "TenNLX": 20, "HoVaTenIn": 25, "SoCMT": 20}

ORPHAN_DB = Path(__file__).resolve().parent.parent / "db" / "data" / "staging.sqlite"


# ---- Hàm thuần --------------------------------------------------------------
def sinh_so_ho_so(max_hien_tai: int) -> str:
    """SoHoSo = RIGHT('000' + (MAX+1), 3). Khóa 55 HV → '056' (memory §1, TDD §10.1)."""
    return f"{max_hien_tai + 1:03d}"


def tach_ho_ten(ho_ten: str) -> dict:
    """TenNLX = từ cuối; HoDemNLX = phần còn lại; HoVaTenIn = HoVaTen cắt ≤25 GIỮ DẤU (EC-030)."""
    ho_ten = " ".join((ho_ten or "").split())
    parts = ho_ten.split(" ")
    ten = parts[-1] if parts else ""
    ho_dem = " ".join(parts[:-1]) if len(parts) > 1 else ""
    return {
        "HoVaTen": ho_ten,
        "TenNLX": ten,
        "HoDemNLX": ho_dem,
        "HoVaTenIn": ho_ten[:MAX_LEN["HoVaTenIn"]],  # giữ dấu, KHÔNG hoa-bỏ-dấu
    }


def suy_tt_xuly(co_anh: bool) -> tuple[str, int | None]:
    """Có ảnh → ('03', 1); chưa ảnh → ('01', None) (TDD §10.2, BR-011)."""
    return ("03", 1) if co_anh else ("01", None)


def suy_ma_loai_hs(hang_gplx: str | None) -> int:
    return 1 if (hang_gplx or "").strip().upper().startswith("A") else 2


def validate_do_dai(ten: dict, so_cmt: str) -> list[str]:
    """Kiểm độ dài cột trước khi gọi SP (tránh SP lỗi); trả danh sách cảnh báo."""
    loi = []
    for col in ("HoVaTen", "HoDemNLX", "TenNLX", "HoVaTenIn"):
        if len(ten.get(col, "")) > MAX_LEN[col]:
            loi.append(f"{col} vượt {MAX_LEN[col]} ký tự")
    if len(so_cmt or "") > MAX_LEN["SoCMT"]:
        loi.append(f"SoCMT vượt {MAX_LEN['SoCMT']} ký tự")
    return loi


# ---- Dựng tham số SP (thứ tự đúng định nghĩa SP; unit-test giá trị MVP) ------
def build_params_nguoilx(hv: dict, ten: dict, now: datetime, nguoi: str) -> list[tuple]:
    """24 tham số usp_NguoiLX_Insert (bỏ @MaDK OUT — xử lý riêng trong EXEC)."""
    return [
        ("DonViNhanHSo", MA_CSDT),
        ("HoDemNLX", ten["HoDemNLX"]),
        ("TenNLX", ten["TenNLX"]),
        ("HoVaTen", ten["HoVaTen"]),
        ("MaQuocTich", "VNM"),           # chuẩn ISO alpha-3 (DM_QuocTich.Ma); "VN" vỡ FK — AS-003 01/10
        ("NgaySinh", hv.get("ngay_sinh", "")),           # varchar(8) yyyymmdd
        ("NoiTT", hv.get("noi_tt", "")),
        ("NoiTT_MaDVHC", hv["noi_tt_ma_dvhc"]),
        ("NoiTT_MaDVQL", hv["noi_tt_ma_dvql"]),
        ("NoiCT", hv.get("noi_ct", hv.get("noi_tt", ""))),
        ("NoiCT_MaDVHC", hv.get("noi_ct_ma_dvhc", hv["noi_tt_ma_dvhc"])),   # BR-004: NoiCT = NoiTT mặc định
        ("NoiCT_MaDVQL", hv.get("noi_ct_ma_dvql", hv["noi_tt_ma_dvql"])),
        ("SoCMT", hv.get("so_cmt", "")),
        ("NgayCapCMT", hv.get("ngay_cap_cmt")),
        ("NoiCapCMT", hv.get("noi_cap_cmt", "")),
        ("GhiChu", None),
        ("TrangThai", 1),                                 # TrangThai=1 khi tạo (§10.2)
        ("NguoiTao", nguoi),
        ("NguoiSua", nguoi),
        ("NgayTao", now),
        ("NgaySua", now),
        ("GioiTinh", hv.get("gioi_tinh", "")),            # 'M'/'F'
        ("HoVaTenIn", ten["HoVaTenIn"]),
    ]


def build_params_hoso(hv: dict, khoa: dict, so_ho_so: str, duong_dan_anh: str | None,
                      tt_xuly: str, chat_luong_anh: int | None, now: datetime, nguoi: str) -> list[tuple]:
    """69 tham số usp_NguoiLX_HoSo_Insert (bỏ @MaDK, @SoHoSo — xử lý trong EXEC).

    Field MVP có giá trị; field sát hạch/báo cáo = None (app cũ cho NULL khi mới thu nhận).
    """
    co_anh = bool(duong_dan_anh)
    return [
        ("MaCSDT", MA_CSDT),
        ("MaSoGTVT", khoa["ma_so_gtvt"]),
        ("MaDVNhanHSo", MA_CSDT),
        ("NgayNhanHSo", now),
        ("NguoiNhanHSo", nguoi),
        ("NgayHenTra", None),
        ("MaLoaiHs", suy_ma_loai_hs(khoa["hang_gplx"])),
        ("TT_XuLy", tt_xuly),
        ("DuongDanAnh", duong_dan_anh),
        ("ChatLuongAnh", chat_luong_anh),
        ("NgayThuNhanAnh", now if co_anh else None),
        ("NguoiThuNhanAnh", nguoi if co_anh else None),
        ("SoGPLXDaCo", None), ("HangGPLXDaCo", None), ("DonViCapGPLXDaCo", None),
        ("NoiCapGPLXDaCo", None), ("NgayCapGPLXDaCo", None), ("NgayHHGPLXDaCo", None),
        ("NgayTTGPLXDaCo", None),
        ("DonViHocLX", MA_CSDT),
        ("NamHocLX", now.year),
        ("HangGPLX", khoa["hang_gplx"]),
        ("SoNamLX", None), ("SoKmLXAnToan", None),
        ("GiayCNSK", 1),                                  # §10.2
        ("LyDoCapDoi", None), ("MucDichCapDoi", None), ("NoiDungSH", None),
        ("MaKhoaHoc", khoa["ma_kh"]),
        ("HangDaoTao", khoa.get("hang_dt") or khoa["hang_gplx"]),
        ("SoGiayCNTN", None), ("SoCCN", None), ("MaBC1", None),
        ("BC1_TuoiTS", None), ("BC1_ThamNien", None), ("MaBC2", None),
        ("KetQuaBC2", None), ("MaLyDoTCBC2", None), ("MaKySH", None),
        ("SoBD", None), ("LanSH", None), ("SoQDSH", None), ("NgayQDSH", None),
        ("KetQua_LyThuyet", None), ("NhanXet_LyThuyet", None),
        ("KetQua_Hinh", None), ("NhanXet_Hinh", None),
        ("KetQua_Duong", None), ("NhanXet_Duong", None),
        ("KetQuaSH", None), ("SoQDTT", None), ("NgayQDTT", None),
        ("GhiChu", None),
        ("NguoiTao", nguoi), ("NguoiSua", nguoi), ("NgayTao", now), ("NgaySua", now),
        ("SoGPLXTmp", None), ("NgayKTBC1", None), ("NguoiKTBC1", None),
        ("NgayKTBC2", None), ("NguoiKTBC2", None), ("MaIn", None),
        ("KetQuaDoiSanhTW", None), ("GhiChuKQDSTW", None), ("ChuKy", None),
        ("TrangThai", 1),                                 # TrangThai=1 khi tạo (§10.2)
        ("MaHTCap", MA_HT_CAP),                           # CM_VN
        ("NguoiKy", None),
    ]


def build_params_giayto(ma_gt: int, ma_dk: str, so_ho_so: str, ten_gt: str) -> list[tuple]:
    """5 tham số usp_NguoiLXHS_GiayTo_Insert (@MaGT,@MaDK,@SoHoSo,@TenGT,@TrangThai).

    TrangThai=1 vì chỉ ghi giấy tờ ĐÃ tick (nộp đủ); giấy tờ bỏ tick không tạo dòng
    (Done khi NAP-05: 'tab Giấy tờ có đủ dòng đã tick'). TenGT = tên đầy đủ từ DM_GiayTo.
    """
    return [
        ("MaGT", ma_gt),
        ("MaDK", ma_dk),
        ("SoHoSo", so_ho_so),
        ("TenGT", ten_gt),
        ("TrangThai", 1),
    ]


def _exec_sql(params: list[tuple], proc: str, head: str, out_select: str) -> tuple[str, list]:
    """Dựng câu EXEC proc với tham số đặt tên + OUTPUT, trả (sql, values)."""
    named = ", ".join(f"@{n}=%s" for n, _ in params)
    sql = f"{head}\nEXEC dbo.{proc} {out_select}{named};"
    return sql, [v for _, v in params]


# ---- Orchestration (chạy live ở bước kiểm riêng — GHI PRODUCTION) -----------
def _orphan_set(uuid: str, ma_dk: str) -> None:
    ORPHAN_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(ORPHAN_DB))
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS nap_dang_nap (uuid TEXT PRIMARY KEY, madk TEXT)")
        conn.execute("INSERT OR REPLACE INTO nap_dang_nap (uuid, madk) VALUES (?,?)", (uuid, ma_dk))
        conn.commit()
    finally:
        conn.close()


def _orphan_clear(uuid: str) -> None:
    if not ORPHAN_DB.exists():
        return
    conn = sqlite3.connect(str(ORPHAN_DB))
    try:
        conn.execute("DELETE FROM nap_dang_nap WHERE uuid=?", (uuid,))
        conn.commit()
    finally:
        conn.close()


_DONE_DDL = ("CREATE TABLE IF NOT EXISTS nap_xong "
             "(uuid TEXT PRIMARY KEY, ma_dk TEXT, so_ho_so TEXT, so_giay_to INT, duong_dan_anh TEXT)")


def _done_get(uuid: str) -> dict | None:
    """UUID đã nạp thành công trước đó? → trả kết quả cũ (idempotent, không tạo HV thứ 2)."""
    if not ORPHAN_DB.exists():
        return None
    conn = sqlite3.connect(str(ORPHAN_DB))
    try:
        conn.execute(_DONE_DDL)
        row = conn.execute(
            "SELECT ma_dk, so_ho_so, so_giay_to, duong_dan_anh FROM nap_xong WHERE uuid=?",
            (uuid,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return {"ma_dk": row[0], "so_ho_so": row[1], "so_giay_to": row[2],
            "duong_dan_anh": row[3], "trung_uuid": True}


def _done_set(uuid: str, r: dict) -> None:
    ORPHAN_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(ORPHAN_DB))
    try:
        conn.execute(_DONE_DDL)
        conn.execute(
            "INSERT OR IGNORE INTO nap_xong (uuid, ma_dk, so_ho_so, so_giay_to, duong_dan_anh) "
            "VALUES (?,?,?,?,?)",
            (uuid, r["ma_dk"], r["so_ho_so"], r.get("so_giay_to", 0), r.get("duong_dan_anh")),
        )
        conn.commit()
    finally:
        conn.close()


def nap_mot_hv(conn, hv: dict, khoa: dict, jp2_bytes: bytes | None,
               img_path_base: str, nguoi: str, uuid: str,
               giay_to: list[dict] | None = None) -> dict:
    """Nạp 1 HV (GHI PRODUCTION). conn: pymssql connection (autocommit, 1 connection giữ applock).

    giay_to: danh sách giấy tờ ĐÃ tick, mỗi phần tử {"ma_gt": int, "ten_gt": str}
    (TenGT tên đầy đủ từ DM_GiayTo) → ghi N dòng usp_NguoiLXHS_GiayTo_Insert, TrangThai=1.

    Trả {"ma_dk","so_ho_so","duong_dan_anh","so_giay_to"}.
    Lỗi bất kỳ (kể cả giấy tờ) → compensation (xóa NguoiLX cascade → cuốn luôn HoSo+GiayTo + .jp2) + raise.
    """
    import pymssql  # noqa: F401 (đảm bảo driver có)

    da_nap = _done_get(uuid)   # bấm lại cùng UUID (mạng timeout) → trả kết quả cũ, không tạo HV 2
    if da_nap:
        return da_nap

    now = datetime.now()
    ten = tach_ho_ten(hv.get("ho_ten", ""))
    loi = validate_do_dai(ten, hv.get("so_cmt", ""))
    if loi:
        raise ValueError("Dữ liệu vượt độ dài cột: " + "; ".join(loi))

    cur = conn.cursor(as_dict=True)   # cần dict để đọc fetchone()["MaDK"]/["m"] (pymssql mặc định trả tuple)
    ma_dk = None
    jp2_path: Path | None = None
    cur.execute("EXEC sp_getapplock @Resource=%s, @LockMode='Exclusive', @LockTimeout=15000",
                (khoa["ma_kh"],))
    try:
        # 1) usp_NguoiLX_Insert → MaDK (OUT)
        p = build_params_nguoilx(hv, ten, now, nguoi)
        sql, vals = _exec_sql(p, "usp_NguoiLX_Insert", "DECLARE @MaDK varchar(25);\n",
                              "@MaDK=@MaDK OUTPUT, ")
        cur.execute(sql + "\nSELECT @MaDK AS MaDK;", tuple(vals))
        ma_dk = cur.fetchone()["MaDK"]
        _orphan_set(uuid, ma_dk)  # chống mồ côi nếu tool chết (PH-3.2)

        # 2) SoHoSo = MAX+1 trong khóa (đọc trong applock)
        cur.execute("SELECT MAX(CAST(SoHoSo AS INT)) AS m FROM NguoiLX_HoSo WHERE MaKhoaHoc=%s",
                    (khoa["ma_kh"],))
        so_ho_so = sinh_so_ho_so(cur.fetchone()["m"] or 0)

        # 3) Ghi .jp2 (tên = MaDK) nếu có ảnh
        duong_dan_anh = None
        chat_luong = None
        tt_xuly, chat_luong = suy_tt_xuly(bool(jp2_bytes))
        if jp2_bytes:
            folder = Path(img_path_base) / khoa["ma_kh"]
            folder.mkdir(parents=True, exist_ok=True)
            jp2_path = folder / f"{ma_dk}.jp2"
            jp2_path.write_bytes(jp2_bytes)
            duong_dan_anh = str(jp2_path)

        # 4) usp_NguoiLX_HoSo_Insert (truyền SoHoSo tự sinh)
        p = build_params_hoso(hv, khoa, so_ho_so, duong_dan_anh, tt_xuly, chat_luong, now, nguoi)
        sql, vals = _exec_sql(
            p, "usp_NguoiLX_HoSo_Insert",
            f"DECLARE @SoHoSo varchar(18)=%s; DECLARE @MaDK varchar(25)=%s;\n",
            "@MaDK=@MaDK, @SoHoSo=@SoHoSo OUTPUT, ",
        )
        cur.execute(sql, tuple([so_ho_so, ma_dk] + vals))

        # 5) Giấy tờ kèm theo × N (theo tick cuối — chỉ ghi dòng đã tick, TrangThai=1)
        for gt in (giay_to or []):
            pg = build_params_giayto(gt["ma_gt"], ma_dk, so_ho_so, gt["ten_gt"])
            sql_gt, vals_gt = _exec_sql(pg, "usp_NguoiLXHS_GiayTo_Insert", "", "")
            cur.execute(sql_gt, tuple(vals_gt))

        _orphan_clear(uuid)
        ket_qua = {"ma_dk": ma_dk, "so_ho_so": so_ho_so, "duong_dan_anh": duong_dan_anh,
                   "so_giay_to": len(giay_to or [])}
        _done_set(uuid, ket_qua)   # chốt UUID đã nạp xong → chống bấm lại tạo trùng
        return ket_qua
    except Exception:
        # compensation: xóa NguoiLX (cascade) + .jp2 vừa ghi, giữ pending (§10.3)
        if ma_dk:
            try:
                conn.cursor().execute("EXEC dbo.usp_NguoiLX_Delete @MaDK=%s", (ma_dk,))
            except Exception:
                pass
        if jp2_path and jp2_path.exists():
            try:
                jp2_path.unlink()
            except OSError:
                pass
        _orphan_clear(uuid)
        raise
    finally:
        try:
            cur.execute("EXEC sp_releaseapplock @Resource=%s", (khoa["ma_kh"],))
        except Exception:
            pass


def nap_lo(items: list[dict], nap_fn, on_progress=None) -> dict:
    """Nạp lô nhiều HV TUẦN TỰ — 1 HV lỗi KHÔNG hỏng cả lô (EC-071).

    items: danh sách HV (mỗi phần tử tuỳ ý, có "uuid" để truy vết).
    nap_fn(item) -> dict: nạp 1 HV, raise khi lỗi (mỗi HV một connection/applock riêng).
    on_progress(da_xong, tong): gọi sau mỗi HV để UI cập nhật tiến độ (tuỳ chọn).

    Trả {"tong", "thanh_cong", "that_bai", "ket_qua": [{uuid, ok, ...}]}.
    HV lỗi giữ pending (nap_fn tự compensation) + ghi dòng lỗi; lô vẫn chạy tiếp.
    """
    ket_qua: list[dict] = []
    tong = len(items)
    for i, it in enumerate(items):
        uuid = it.get("uuid")
        try:
            r = nap_fn(it)
            ket_qua.append({"uuid": uuid, "ok": True, **r})
        except Exception as e:  # noqa: BLE001 — gom lỗi từng dòng, không dừng lô
            ket_qua.append({"uuid": uuid, "ok": False, "loi": str(e)})
        if on_progress:
            on_progress(i + 1, tong)
    thanh_cong = sum(1 for r in ket_qua if r["ok"])
    return {"tong": tong, "thanh_cong": thanh_cong,
            "that_bai": tong - thanh_cong, "ket_qua": ket_qua}
