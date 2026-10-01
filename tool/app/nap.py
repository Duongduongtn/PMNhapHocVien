"""NAP-05 — nạp 1 học viên vào GPLX_CSDT qua 1 SP GỘP app cũ (hướng A).

Đổi 01/10/2026 (CHANGES #4/#5, TDD §10): bỏ 3 SP rời + compensation, dùng
`usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat` — chính SP màn "Thu nhận Hồ sơ cấp mới".

Tách 2 lớp:
- Hàm THUẦN (sinh SoHoSo, tách họ tên IN HOA, validate cột, dựng chuỗi giấy tờ,
  dựng 30 tham số @p_* của SP gộp): unit-test được, không chạm DB.
- Orchestration nap_mot_hv(): applock → SoHoSo → EXEC SP gộp (@p_MaDK=NULL OUT, @p_out)
  → ghi ảnh hướng A (ghi .jp2 + UPDATE 5 cột ảnh) → releaseapplock. Chạy LIVE (ghi production).

SP gộp tự lo: MaLoaiHs, MaCSDT, MaSoGTVT, MaHTCap, GiayCNSK, tách họ tên, transaction.
Tool chỉ UPDATE thẳng 5 cột ẢNH (ngoại lệ ❌ PRD, CHANGES #5) — SP không ghi ảnh.
"""
from __future__ import annotations
import sqlite3
from datetime import datetime
from pathlib import Path

# ===== Hằng (TDD §10.2) =====
MAX_LEN = {"HoVaTen": 50, "HoDemNLX": 30, "TenNLX": 20, "HoVaTenIn": 25, "SoCMT": 20}

# Mã lỗi nghiệp vụ SP trả qua @p_out (SP KHÔNG raiserror — phải đọc @p_out, TDD §10.3).
OUT_LOI = {
    -1: "Số hồ sơ đã tồn tại trong khóa",
    -2: "CCCD/CMND đã có học viên trong khóa",
    -3: "Thâm niên lái xe không đủ theo hạng",
    -4: "Số km lái xe an toàn không đủ theo hạng",
}

ORPHAN_DB = Path(__file__).resolve().parent.parent / "db" / "data" / "staging.sqlite"


# ---- Hàm thuần --------------------------------------------------------------
def sinh_so_ho_so(max_hien_tai: int) -> str:
    """SoHoSo = RIGHT('000' + (MAX+1), 3). Khóa 55 HV → '056' (TDD §10.1)."""
    return f"{max_hien_tai + 1:03d}"


def tach_ho_ten(ho_ten: str) -> dict:
    """IN HOA GIỮ DẤU (AS-003: 55/55 HV HoVaTen in hoa). SP gộp tự tách Ho/Ten từ @p_HoVaTen;
    hàm này chủ yếu để KIỂM ĐỘ DÀI cột + dựng HoVaTenIn (cắt ≤25, cũng in hoa giữ dấu)."""
    ho_ten = " ".join((ho_ten or "").split()).upper()   # IN HOA, KHÔNG bỏ dấu
    parts = ho_ten.split(" ")
    ten = parts[-1] if parts else ""
    ho_dem = " ".join(parts[:-1]) if len(parts) > 1 else ""
    return {
        "HoVaTen": ho_ten,
        "TenNLX": ten,
        "HoDemNLX": ho_dem,
        "HoVaTenIn": ho_ten[:MAX_LEN["HoVaTenIn"]],
    }


def suy_ma_loai_hs(hang_gplx: str | None) -> int:
    """Cho việc chọn giấy tờ mặc định theo loại HS (route). A* → 1 (mô tô), còn lại → 2 (ô tô).
    SP gộp TỰ tính MaLoaiHs khi ghi — tool không truyền."""
    return 1 if (hang_gplx or "").strip().upper().startswith("A") else 2


def validate_do_dai(ten: dict, so_cmt: str) -> list[str]:
    """Kiểm độ dài cột trước khi gọi SP (SP tự tách nên Ho/Ten có thể vượt); trả danh sách lỗi."""
    loi = []
    for col in ("HoVaTen", "HoDemNLX", "TenNLX", "HoVaTenIn"):
        if len(ten.get(col, "")) > MAX_LEN[col]:
            loi.append(f"{col} vượt {MAX_LEN[col]} ký tự")
    if len(so_cmt or "") > MAX_LEN["SoCMT"]:
        loi.append(f"SoCMT vượt {MAX_LEN['SoCMT']} ký tự")
    return loi


def dung_chuoi_giay_to(ma_gts: list[int]) -> str:
    """Chuỗi @p_GiayTo cho SP gộp: [1,2,3] → '1,2,3,'. SP parse bằng charindex(MaGT+',', ...)
    và tự insert từ DM_GiayTo. Chuỗi rỗng = không nộp giấy tờ nào."""
    return "".join(f"{int(m)}," for m in sorted({int(x) for x in ma_gts}))


# ---- Dựng 30 tham số SP gộp (trừ @p_out + @p_MaDK — xử lý riêng ở EXEC) ------
def build_params_sp_gop(hv: dict, khoa: dict, so_ho_so: str, ten: dict,
                        giay_to_str: str, nguoi: str = "") -> list[tuple]:
    """30 tham số @p_* của usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat (khớp 1:1 form app cũ).

    Field map khớp app cũ (AS-003 01/10): MaQuocTich='VNM', CHON_IN_GPLX=2, NoiTT=ChiTiet
    (mặc định trống — KHÔNG nhét tên xã), DonViHocLX NULL (SP không có tham số → tự NULL).
    """
    return [
        ("p_MaKH", khoa["ma_kh"]),
        ("p_MaHangGPLX", khoa["hang_gplx"]),
        ("p_HangDaoTao", khoa.get("hang_dt") or khoa["hang_gplx"]),
        ("p_SoHoSo", so_ho_so),
        ("p_NguoiNhanHSo", nguoi),
        ("p_HoVaTen", ten["HoVaTen"]),        # IN HOA — SP tự tách Ho/Ten
        ("p_HoVaTenIn", ten["HoVaTenIn"]),    # IN HOA ≤25
        ("p_NgaySinh", hv.get("ngay_sinh", "")),              # varchar(8) yyyymmdd
        ("p_GioiTinh", hv.get("gioi_tinh", "")),              # 'M'/'F'
        ("p_MaQuocTich", "VNM"),                              # ISO alpha-3 (DM_QuocTich.Ma); 'VN' vỡ FK
        ("p_SoCMT", hv.get("so_cmt", "")),
        ("p_NgayCap", hv.get("ngay_cap_cmt") or ""),          # varchar(8); SP convert 112 nếu len=8
        ("p_NoiCap", hv.get("noi_cap_cmt") or ""),
        ("p_MaDVHC_TT", hv["noi_tt_ma_dvhc"]),
        ("p_ChiTiet_TT", hv.get("chi_tiet_tt") or ""),        # chi tiết (số nhà/thôn); mặc định TRỐNG
        ("p_MaDVHC_CT", hv.get("noi_ct_ma_dvhc") or hv["noi_tt_ma_dvhc"]),
        ("p_ChiTiet_CT", hv.get("chi_tiet_ct") or ""),
        ("p_SoNamLX", hv.get("so_nam_lx")),                   # None → không vỡ check thâm niên
        ("p_SoKmLX", hv.get("so_km_lx")),
        ("p_GiayTo", giay_to_str),                            # '1,2,3,'
        ("p_SoGPLXDaCo", None),
        ("p_HangGPLXDaCo", None),
        ("p_NgayTTGPLXDaCo", None),
        ("p_NgayCapGPLXDaCo", None),
        ("p_NgayHHGPLXDaCo", None),
        ("p_DVCapGPLXDaCo", None),
        ("p_NoiCapGPLXDaCo", None),
        ("p_GhiChu", None),
        ("p_SO_CMND_CU", None),
        ("p_CHON_IN_GPLX", 2),                                # "Chọn in GPLX" bắt buộc = 2 (AS-003)
    ]


# ---- Ghi ảnh (hướng A) — DÙNG CHUNG cho NAP-05 và QLY-05 --------------------
def ghi_anh_update(cur, ma_dk: str, ma_kh: str, jp2_bytes: bytes,
                   img_path_base: str, now: datetime, nguoi: str = "") -> str:
    """Ghi file .jp2 (tên = MaDK) + UPDATE 5 cột ảnh NguoiLX_HoSo, nâng TT_XuLy='03' (hướng A).

    Đường dẫn TUYỆT ĐỐI <IMG_PATH_CSDT>\\<MaKhoaHoc>\\<MaDK>.jp2 (verify DB thật 01/10).
    Dùng lại ở QLY-05 (nạp/thay ảnh cho HV đã có). Trả đường dẫn đã ghi.
    """
    folder = Path(img_path_base) / ma_kh
    folder.mkdir(parents=True, exist_ok=True)
    jp2_path = folder / f"{ma_dk}.jp2"
    jp2_path.write_bytes(jp2_bytes)          # ghi đè nếu đã có (thay ảnh — QLY-05)
    duong_dan = str(jp2_path)
    cur.execute(
        "UPDATE NguoiLX_HoSo SET DuongDanAnh=%s, ChatLuongAnh=1, TT_XuLy='03', "
        "NgayThuNhanAnh=%s, NguoiThuNhanAnh=%s WHERE MaDK=%s",
        (duong_dan, now, nguoi, ma_dk),
    )
    return duong_dan


# ---- Chống mồ côi / chống trùng UUID (staging SQLite) ----------------------
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


# ---- Orchestration (chạy live — GHI PRODUCTION) ----------------------------
def nap_mot_hv(conn, hv: dict, khoa: dict, jp2_bytes: bytes | None,
               img_path_base: str, nguoi: str, uuid: str,
               giay_to: list[dict] | None = None) -> dict:
    """Nạp 1 HV qua SP gộp (GHI PRODUCTION). conn: pymssql connection (autocommit, giữ applock).

    giay_to: danh sách giấy tờ ĐÃ tick [{"ma_gt": int, "ten_gt": str}] → dựng chuỗi @p_GiayTo
    (SP tự insert từ DM_GiayTo; ten_gt chỉ để UI, SP không cần).

    Trả {"ma_dk","so_ho_so","duong_dan_anh","so_giay_to"} (+ "anh_loi" nếu ghi ảnh lỗi).
    - SP gộp atomic (SET XACT_ABORT ON) → lỗi SP tự rollback, KHÔNG để bản ghi nửa vời.
    - @p_out ≠ 0 → lỗi nghiệp vụ, SP không insert → raise (giữ pending).
    - Ghi ảnh lỗi SAU khi SP tạo xong → giữ TT_XuLy='01' (thiếu ảnh, BR-011), KHÔNG xóa HV.
    """
    import pymssql  # noqa: F401 (đảm bảo driver có)

    da_nap = _done_get(uuid)   # bấm lại cùng UUID → trả kết quả cũ, không tạo HV 2
    if da_nap:
        return da_nap

    now = datetime.now()
    ten = tach_ho_ten(hv.get("ho_ten", ""))
    loi = validate_do_dai(ten, hv.get("so_cmt", ""))
    if loi:
        raise ValueError("Dữ liệu vượt độ dài cột: " + "; ".join(loi))
    giay_to_str = dung_chuoi_giay_to([g["ma_gt"] for g in (giay_to or [])])

    cur = conn.cursor(as_dict=True)
    cur.execute("EXEC sp_getapplock @Resource=%s, @LockMode='Exclusive', @LockTimeout=15000",
                (khoa["ma_kh"],))
    try:
        # 1) SoHoSo = MAX+1 trong khóa (đọc trong applock)
        cur.execute("SELECT MAX(CAST(SoHoSo AS INT)) AS m FROM NguoiLX_HoSo WHERE MaKhoaHoc=%s",
                    (khoa["ma_kh"],))
        so_ho_so = sinh_so_ho_so(cur.fetchone()["m"] or 0)

        # 2) EXEC SP gộp — @p_MaDK=NULL OUT → SP tự sinh; @p_out OUT (lỗi nghiệp vụ)
        p = build_params_sp_gop(hv, khoa, so_ho_so, ten, giay_to_str, nguoi)
        named = ", ".join(f"@{n}=%s" for n, _ in p)
        sql = ("SET XACT_ABORT ON;\n"
               "DECLARE @out INT, @madk VARCHAR(25) = NULL;\n"
               "EXEC dbo.usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat "
               f"@p_out=@out OUTPUT, @p_MaDK=@madk OUTPUT, {named};")
        cur.execute(sql, tuple(v for _, v in p))
        row = cur.fetchone() or {}
        p_out = row.get("@p_out")
        ma_dk = row.get("@p_MaDK")
        if p_out != 0:
            raise ValueError("Nạp hồ sơ bị từ chối: " + OUT_LOI.get(p_out, f"SP trả mã {p_out}"))
        if not ma_dk:
            raise RuntimeError("SP không trả về MaDK dù @p_out=0")
        _orphan_set(uuid, ma_dk)   # chống mồ côi nếu tool chết trước khi chốt done

        # 3) Ghi ảnh hướng A (lỗi KHÔNG xóa HV — giữ '01' thiếu ảnh, BR-011)
        duong_dan_anh = None
        anh_loi = None
        if jp2_bytes:
            try:
                duong_dan_anh = ghi_anh_update(cur, ma_dk, khoa["ma_kh"], jp2_bytes,
                                               img_path_base, now, nguoi)
            except Exception as e:  # noqa: BLE001
                anh_loi = str(e)

        ket_qua = {"ma_dk": ma_dk, "so_ho_so": so_ho_so, "duong_dan_anh": duong_dan_anh,
                   "so_giay_to": len(giay_to or [])}
        if anh_loi:
            ket_qua["anh_loi"] = anh_loi
        _orphan_clear(uuid)
        _done_set(uuid, ket_qua)   # chốt UUID đã nạp xong → chống bấm lại tạo trùng
        return ket_qua
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
    HV lỗi: SP atomic tự rollback → giữ pending + ghi dòng lỗi; lô vẫn chạy tiếp.
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
