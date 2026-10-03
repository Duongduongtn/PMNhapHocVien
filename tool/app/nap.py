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
import re
import shutil
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
def sinh_so_ho_so(da_co) -> str:
    """SoHoSo = số nhỏ nhất CHƯA dùng trong khóa (lấp khe trống), KHÔNG dùng MAX+1 (BUG-09).

    Vì sao đổi: lúc "gỡ về chờ nạp" (QLY-08) gọi usp_NguoiLX_Delete xóa CỨNG dòng NguoiLX_HoSo
    kèm SoHoSo; MAX+1 không thu hồi số đã xóa → nếu giữa các lần nạp-gỡ-nạp lại có HV khác chen
    vào (hoặc phantom BUG-01), MAX trèo cao hơn số HV thực → SoHoSo nhảy quá (ca Lê Thị Hồng:
    khóa 57 HV mà số 58). Lấp số nhỏ nhất chưa dùng → khớp số lượng HV, không trùng, tái dùng số đã gỡ.
    `da_co` = tập SoHoSo (int) đang có trong khóa. Trả 3 chữ số (TDD §10.1); khóa 55 HV liên tục → '056'.
    """
    da = set(da_co)
    n = 1
    while n in da:
        n += 1
    return f"{n:03d}"


def suy_noi_cap(so_cmt: str) -> str:
    """Nơi cấp = MÃ TỈNH 2 số, suy từ số căn cước (BUG-10, thống nhất 03/10).

    CCCD 12 số: 3 số đầu = mã tỉnh nơi ĐKKS dạng '0XY' → NoiCapCMT = 'XY' (vd 070…→'70' Đồng Nai,
    001…→'01', 038…→'38'). Khớp 7.941/14.437 bản ghi CCCD đang có trong GPLX_CSDT.
    QR không mang nơi cấp nhưng suy được từ chính số CCCD, nên khỏi cần nhập.
    Số không phải CCCD 12 số (CMND 9 số, số lạ) → trả '' để operator chọn tay (combobox tỉnh)."""
    s = (so_cmt or "").strip()
    return s[1:3] if len(s) == 12 and s.isdigit() else ""


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
        ("p_NoiCap", hv.get("noi_cap_cmt") or suy_noi_cap(hv.get("so_cmt", ""))),  # mã Sở GTVT suy từ CCCD (BUG-10)
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
    """Ghi file .jp2 (tên = MaDK) + UPDATE cột ảnh NguoiLX_HoSo (hướng A).

    Đường dẫn TUYỆT ĐỐI <IMG_PATH_CSDT>\\<MaKhoaHoc>\\<MaDK>.jp2 (verify DB thật 01/10).
    Dùng lại ở QLY-05 (nạp/thay ảnh cho HV đã có) và QLY-07 (đổi nền cả khóa).

    **TT_XuLy — KHÔNG BAO GIỜ HẠ (bug CHANGES #22):** chỉ nâng '01'/'02' → '03' khi HV CHƯA
    có ảnh; HV đã ở trạng thái khác ('03' hoặc mã Báo cáo '11'..'19') → GIỮ NGUYÊN TT_XuLy.
    Nếu hạ HV đã Báo cáo về '03' thì HV rơi khỏi usp_BaoCao2_DSHS (lọc TT_XuLy in '11'..'19').
    NAP-05 nạp HV mới (SP set '01') → vẫn lên '03' đúng. Trả đường dẫn đã ghi.

    Ghi file ATOMIC (temp → replace) để crash/mất điện giữa chừng không để lại .jp2 cụt.
    """
    folder = Path(img_path_base) / ma_kh
    folder.mkdir(parents=True, exist_ok=True)
    jp2_path = folder / f"{ma_dk}.jp2"
    # Ghi atomic: file tạm cùng thư mục → replace (nguyên tử, ghi đè nếu đã có — thay ảnh)
    tmp_path = folder / f"{ma_dk}.jp2.tmp"
    tmp_path.write_bytes(jp2_bytes)
    try:
        tmp_path.replace(jp2_path)   # app cũ khóa file đích → PermissionError (caller xử 409)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise
    duong_dan = str(jp2_path)

    # TT_XuLy: chỉ nâng khi HV CHƯA có ảnh ('01'/'02'); đã có ảnh/đã Báo cáo → giữ nguyên
    cur.execute("SELECT TT_XuLy FROM NguoiLX_HoSo WHERE MaDK=%s", (ma_dk,))
    r = cur.fetchone()
    tt_cu = ((r or {}).get("TT_XuLy") or "").strip()
    tt_moi = "03" if tt_cu in ("", "01", "02") else tt_cu

    cur.execute(
        "UPDATE NguoiLX_HoSo SET DuongDanAnh=%s, ChatLuongAnh=1, TT_XuLy=%s, "
        "NgayThuNhanAnh=%s, NguoiThuNhanAnh=%s WHERE MaDK=%s",
        (duong_dan, tt_moi, now, nguoi, ma_dk),
    )
    return duong_dan


# ---- Di chuyển ảnh khi đổi khóa (QLY-02) -----------------------------------
def di_chuyen_anh(duong_dan_cu: str | None, ma_kh_moi: str, ma_dk: str, img_path_base: str) -> str | None:
    """Di chuyển .jp2 sang folder khóa mới, giữ tên = MaDK (QLY-02). Trả đường dẫn mới.

    - DuongDanAnh trống (HV chưa có ảnh) → None (không có gì để chuyển).
    - File nguồn còn → di chuyển sang `<img_path_base>\\<ma_kh_moi>\\<MaDK>.jp2`.
    - File nguồn mất → vẫn trả đường dẫn mới (DB nhất quán với khóa mới; file thiếu như 'chưa ảnh').
    - File bị khóa (app cũ đang mở) → shutil.move ném PermissionError → caller báo đóng app cũ.
    """
    if not (duong_dan_cu or "").strip():
        return None
    folder = Path(img_path_base) / ma_kh_moi
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f"{ma_dk}.jp2"
    src = Path(duong_dan_cu)
    if src.exists() and src.resolve() != dest.resolve():
        shutil.move(str(src), str(dest))
    return str(dest)


# ---- Log xóa HV (QLY-03) — ghi vào staging SQLite để truy vết xóa mềm --------
_XOA_DDL = (
    "CREATE TABLE IF NOT EXISTS xoa_hv ("
    "ma_dk TEXT, ma_kh TEXT, duong_dan_cu TEXT, duong_dan_moi TEXT, nguoi TEXT, thoi_gian TEXT)"
)


def log_xoa_hv(ma_dk: str, ma_kh: str, duong_dan_cu: str | None,
               duong_dan_moi: str | None, nguoi: str) -> None:
    """Ghi 1 dòng log xóa HV (xóa mềm ảnh) để sau truy vết được ai xóa, file chuyển đi đâu."""
    ORPHAN_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(ORPHAN_DB))
    try:
        conn.execute(_XOA_DDL)
        conn.execute(
            "INSERT INTO xoa_hv (ma_dk, ma_kh, duong_dan_cu, duong_dan_moi, nguoi, thoi_gian) "
            "VALUES (?,?,?,?,?,?)",
            (ma_dk, ma_kh, duong_dan_cu, duong_dan_moi, nguoi, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
    finally:
        conn.close()


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


def lay_uuid_theo_ma_dk(ma_dk: str) -> str | None:
    """QLY-08 bước 2 — tra uuid gốc theo ma_dk từ staging nap_xong local (ưu tiên trước fallback
    VPS tra-uuid). Chưa từng nạp trên máy này / đã xóa SQLite → None → caller hỏi VPS."""
    if not ORPHAN_DB.exists():
        return None
    conn = sqlite3.connect(str(ORPHAN_DB))
    try:
        conn.execute(_DONE_DDL)
        row = conn.execute("SELECT uuid FROM nap_xong WHERE ma_dk=? LIMIT 1", (ma_dk,)).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


# ---- Hàng kéo về từ VPS (staging keo_ve) — NAP-01 ---------------------------
# Lưu METADATA hàng đợi kéo từ VPS (không lưu ảnh thô xuống đĩa — tránh để PII căn
# cước nằm lại máy tool; ảnh tải theo yêu cầu khi mở từng HV). Dedup theo uuid để
# kéo nhiều lần không nhân đôi (Done NAP-01). trang_thai cục bộ: 'cho'/'loi'/'xong'.
_KEO_DDL = (
    "CREATE TABLE IF NOT EXISTS keo_ve ("
    "uuid TEXT PRIMARY KEY, so_cccd TEXT, so_cmnd_cu TEXT, ho_ten TEXT, "
    "ngay_sinh TEXT, gioi_tinh TEXT, noi_tt_raw TEXT, ngay_cap TEXT, "
    "noi_cap_cccd TEXT, co_anh INT DEFAULT 0, created_at TEXT, "
    "trang_thai TEXT DEFAULT 'cho', loi TEXT, ma_dk TEXT, so_ho_so TEXT)"
)
_KEO_COLS = ("uuid", "so_cccd", "so_cmnd_cu", "ho_ten", "ngay_sinh", "gioi_tinh",
             "noi_tt_raw", "ngay_cap", "noi_cap_cccd", "co_anh", "created_at",
             "trang_thai", "loi", "ma_dk", "so_ho_so")


def iso_to_yyyymmdd(gia_tri: str | None) -> str:
    """Ngày cấp CCCD ISO 'yyyy-mm-dd' (cột VPS DATE) → 'yyyymmdd' (SP cần varchar(8),
    convert style 112). Rỗng/không đủ 8 số → '' (nạp thiếu ngày cấp, không chặn)."""
    so = re.sub(r"\D", "", gia_tri or "")
    return so[:8] if len(so) >= 8 else ""


def _keo_conn() -> sqlite3.Connection:
    ORPHAN_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(ORPHAN_DB))
    conn.execute(_KEO_DDL)
    return conn


def keo_ve_upsert(rows: list[dict]) -> tuple[int, int]:
    """Ghi các bản ghi kéo từ VPS vào staging. Dedup + LÀM TƯƠI theo uuid (CHANGES #11):
    - Chưa có → thêm mới (trạng thái 'cho').
    - Đã có + còn 'cho' → **cập nhật** thông tin/ảnh mới nhất từ VPS (collector sửa ở app web
      sau khi tool đã kéo → nhận bản mới). Giữ nguyên trạng thái cục bộ.
    - Đã có + 'xong'/'loi' → GIỮ nguyên, không đụng (đã nạp/đã xử lý).
    Trả (số thêm mới, số làm tươi).

    Mỗi row là KeoOut của VPS: uuid, so_cccd, so_cmnd_cu, ho_ten, ngay_sinh, gioi_tinh,
    noi_tt_raw, ngay_cap_cccd (ISO), noi_cap_cccd, co_anh, created_at.
    """
    conn = _keo_conn()
    try:
        moi = lam_tuoi = 0
        for r in rows:
            gt = (
                str(r.get("uuid")), r.get("so_cccd"), r.get("so_cmnd_cu"),
                r.get("ho_ten"), r.get("ngay_sinh"), r.get("gioi_tinh"),
                r.get("noi_tt_raw"), iso_to_yyyymmdd(r.get("ngay_cap_cccd")),
                r.get("noi_cap_cccd"), 1 if r.get("co_anh") else 0,
                str(r.get("created_at") or ""),
            )
            cot = ("uuid", "so_cccd", "so_cmnd_cu", "ho_ten", "ngay_sinh", "gioi_tinh",
                   "noi_tt_raw", "ngay_cap", "noi_cap_cccd", "co_anh", "created_at")
            hien = conn.execute("SELECT trang_thai FROM keo_ve WHERE uuid=?", (gt[0],)).fetchone()
            if hien is None:
                conn.execute(
                    f"INSERT INTO keo_ve ({', '.join(cot)}, trang_thai) "
                    f"VALUES ({', '.join('?' * len(cot))}, 'cho')",
                    gt,
                )
                moi += 1
            elif hien[0] == "cho":
                dat = ", ".join(f"{c}=?" for c in cot[1:])  # bỏ uuid (khóa)
                conn.execute(f"UPDATE keo_ve SET {dat} WHERE uuid=?", (*gt[1:], gt[0]))
                lam_tuoi += 1
            # 'xong'/'loi' → bỏ qua
        conn.commit()
        return moi, lam_tuoi
    finally:
        conn.close()


def keo_ve_danh_sach() -> list[dict]:
    """Toàn bộ hàng đã kéo về (lọc/sắp xếp để UI lo — CHANGES #6). Cũ trước cho ổn định."""
    conn = _keo_conn()
    try:
        rows = conn.execute(
            f"SELECT {', '.join(_KEO_COLS)} FROM keo_ve ORDER BY created_at ASC, uuid ASC"
        ).fetchall()
    finally:
        conn.close()
    return [dict(zip(_KEO_COLS, row)) for row in rows]


def keo_ve_cap_nhat(uuid: str, *, trang_thai: str, loi: str | None = None,
                    ma_dk: str | None = None, so_ho_so: str | None = None) -> None:
    """Cập nhật trạng thái cục bộ 1 bản ghi sau khi nạp (xong/lỗi)."""
    conn = _keo_conn()
    try:
        conn.execute(
            "UPDATE keo_ve SET trang_thai=?, loi=?, ma_dk=?, so_ho_so=? WHERE uuid=?",
            (trang_thai, loi, ma_dk, so_ho_so, str(uuid)),
        )
        conn.commit()
    finally:
        conn.close()


def keo_ve_trang_thai(uuid: str) -> str | None:
    """Trạng thái cục bộ 1 bản ghi staging (None nếu không có). NAP-01 task 38 — guard 'Bỏ khỏi hàng đợi'."""
    conn = _keo_conn()
    try:
        row = conn.execute("SELECT trang_thai FROM keo_ve WHERE uuid=?", (str(uuid),)).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


def keo_ve_xoa(uuid: str) -> None:
    """Xóa 1 bản ghi khỏi staging keo_ve (NAP-01 task 38 'Bỏ khỏi hàng đợi'). Chỉ đụng SQLite
    cục bộ của tool — KHÔNG chạm DB prod/VPS. Caller (router) tự guard chỉ xóa dòng đã nạp."""
    conn = _keo_conn()
    try:
        conn.execute("DELETE FROM keo_ve WHERE uuid=?", (str(uuid),))
        conn.commit()
    finally:
        conn.close()


def keo_ve_xoa_neu_cho(uuid: str) -> bool:
    """NAP-01 task 44 (đồng bộ xóa) — bỏ dòng staging CHỈ KHI còn 'cho' (chưa nạp). Dòng 'xong'/'loi'
    GIỮ nguyên (đã nạp/đã xử lý — collector không đụng tới được). Trả True nếu đã bỏ."""
    conn = _keo_conn()
    try:
        cur = conn.execute("DELETE FROM keo_ve WHERE uuid=? AND trang_thai='cho'", (str(uuid),))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ---- Mốc đồng bộ xóa (NAP-01 task 44) — created_at bản xóa gần nhất đã đồng bộ, để kéo incremental
_MOC_DDL = "CREATE TABLE IF NOT EXISTS keo_moc (ten TEXT PRIMARY KEY, gia_tri TEXT)"


def lay_moc_da_xoa() -> str | None:
    """Mốc da-xoa lần đồng bộ trước (None = chưa đồng bộ lần nào → lấy từ đầu)."""
    if not ORPHAN_DB.exists():
        return None
    conn = sqlite3.connect(str(ORPHAN_DB))
    try:
        conn.execute(_MOC_DDL)
        row = conn.execute("SELECT gia_tri FROM keo_moc WHERE ten='da_xoa'").fetchone()
    finally:
        conn.close()
    return row[0] if row else None


def luu_moc_da_xoa(moc: str) -> None:
    """Lưu mốc da-xoa mới nhất (VPS trả về) để lượt kéo sau chỉ lấy phần mới."""
    ORPHAN_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(ORPHAN_DB))
    try:
        conn.execute(_MOC_DDL)
        conn.execute("INSERT OR REPLACE INTO keo_moc (ten, gia_tri) VALUES ('da_xoa', ?)", (moc,))
        conn.commit()
    finally:
        conn.close()


def keo_ve_ve_cho(uuid: str) -> bool:
    """QLY-08 bước 5 — đưa dòng staging keo_ve về 'cho' (gỡ ma_dk/so_ho_so/lỗi) sau khi gỡ HV
    về chờ nạp. Chỉ đụng SQLite cục bộ. Dòng không còn trong staging (đã 'Bỏ khỏi hàng đợi' sau
    khi nạp) → trả False để UI gợi ý bấm 'Kéo về' lấy lại từ VPS (giờ đã pending).

    BUG-01 (03/10): PHẢI gỡ luôn vé 'đã nạp' trong nap_xong của uuid. HV đã bị xóa khỏi CSDT khi
    gỡ về chờ nạp nên vé cũ (uuid→MaDK) không còn hiệu lực; không gỡ thì lần nạp lại cùng uuid bị
    `nap_mot_hv` → `_done_get` short-circuit, trả kết quả cũ với MaDK đã xóa → HV KHÔNG vào DB mà
    tool vẫn báo thành công. Xóa vé KHÔNG phụ thuộc dòng keo_ve còn hay không (dòng có thể đã bị
    'Bỏ khỏi hàng đợi' nhưng vé vẫn kẹt lại)."""
    conn = _keo_conn()
    try:
        conn.execute(_DONE_DDL)  # đảm bảo bảng nap_xong tồn tại trước khi xóa vé
        conn.execute("DELETE FROM nap_xong WHERE uuid=?", (str(uuid),))
        cur = conn.execute(
            "UPDATE keo_ve SET trang_thai='cho', loi=NULL, ma_dk=NULL, so_ho_so=NULL WHERE uuid=?",
            (str(uuid),),
        )
        conn.commit()
        return cur.rowcount > 0
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
        # 0) NAP-06: kiểm trùng CMT trong khóa (SP gộp KHÔNG bắt khi nạp MỚI vì
        #    `lx.MaDK <> @p_MaDK` với @p_MaDK=NULL → UNKNOWN → đếm 0). Kiểm trong applock
        #    theo khóa nên chống được cả đua 2 máy (EC-012/BR-005).
        cur.execute("SELECT COUNT(*) AS n FROM NguoiLX lx JOIN NguoiLX_HoSo hs ON hs.MaDK = lx.MaDK "
                    "WHERE lx.SoCMT = %s AND hs.MaKhoaHoc = %s",
                    (hv.get("so_cmt", ""), khoa["ma_kh"]))
        if cur.fetchone()["n"] > 0:
            raise ValueError("CCCD/CMND đã có học viên trong khóa")

        # 1) SoHoSo = số nhỏ nhất chưa dùng trong khóa (lấp khe do nạp→gỡ→nạp lại — BUG-09).
        #    Đọc TOÀN BỘ SoHoSo trong khóa (trong applock → không đua với insert sau).
        cur.execute("SELECT CAST(SoHoSo AS INT) AS n FROM NguoiLX_HoSo WHERE MaKhoaHoc=%s",
                    (khoa["ma_kh"],))
        da_co = {r["n"] for r in cur.fetchall() if r["n"] is not None}
        so_ho_so = sinh_so_ho_so(da_co)

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
