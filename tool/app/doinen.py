"""QLY-07 (task 39) — đổi nền trắng ảnh cho CẢ KHÓA, chạy nền + theo dõi tiến độ.

Chạy bằng thread (rembg nặng, không chẹn event loop). Tiến độ giữ trong bộ nhớ theo MaKH
(tool localhost 1 tiến trình). Applock theo khóa: mỗi khóa chỉ 1 job chạy cùng lúc.

Quy tắc nghiệp vụ (PRD/TDD §11.6):
- Ghi đè **TẠI `DuongDanAnh` hiện có** (2 DB dùng chung 1 file; CHANGES #67), atomic — KHÔNG tạo file
  ở thư mục khác, KHÔNG đổi `DuongDanAnh`, KHÔNG dùng `ghi_anh_update`. Chỉ UPDATE
  ChatLuongAnh/NgayThuNhanAnh/NguoiThuNhanAnh → **giữ TT_XuLy** (KHÔNG hạ '03' cho HV đã Báo cáo).
- Sao lưu `<tên>_BACKUP.jp2` CÙNG thư mục, **chỉ chép nếu CHƯA có** → chạy lần 2 không đè bản gốc thật.
- Phạm vi mặc định 'chua_trang' (heuristic 4 góc); 'tat_ca' xử mọi HV có ảnh.
- HV không có file ảnh → bỏ qua, KHÔNG tính lỗi. File khóa/hỏng → ghi lỗi, chạy tiếp.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app import image
from app.anh_file import ghi_de_tai_cho
from app.db import sqlserver_conn


@dataclass
class TienDo:
    tong: int = 0           # tổng HV có ảnh trong khóa
    xong: int = 0           # đã đổi nền
    bo_qua: int = 0         # không file / đã trắng (phạm vi chua_trang)
    loi: int = 0
    ds_loi: list[dict] = field(default_factory=list)  # [{ma_dk, ly_do}]
    dang_chay: bool = True
    xong_het: bool = False
    thong_bao: str = ""


_jobs: dict[str, TienDo] = {}
_lock = threading.Lock()


def tien_do(ma_kh: str) -> TienDo | None:
    return _jobs.get(ma_kh)


def xu_ly_mot(cur, ma_dk: str, duong_dan: str, pham_vi: str, sao_luu: bool,
              nguoi: str, td: TienDo) -> None:
    """Xử lý 1 HV: bỏ qua nếu không file / đã trắng (phạm vi chua_trang); còn lại đổi nền →
    ghi đè tại `duong_dan` (kèm backup nếu bật) + UPDATE cột ảnh (giữ TT_XuLy, giữ DuongDanAnh).
    Raise để caller gom vào danh sách lỗi."""
    p = Path(duong_dan)
    if not p.exists():
        td.bo_qua += 1
        return
    data = p.read_bytes()
    if pham_vi == "chua_trang" and image.anh_da_trang(data):
        td.bo_qua += 1
        return
    jp2 = image.doi_nen_anh(data)
    ghi_de_tai_cho(duong_dan, jp2, sao_luu)
    cur.execute(
        "UPDATE NguoiLX_HoSo SET ChatLuongAnh=1, NgayThuNhanAnh=%s, NguoiThuNhanAnh=%s WHERE MaDK=%s",
        (datetime.now(), nguoi, ma_dk),
    )
    td.xong += 1


def _chay(ma_kh: str, pham_vi: str, sao_luu: bool, nguoi: str, td: TienDo) -> None:
    try:
        with sqlserver_conn(autocommit=True) as conn:
            cur = conn.cursor(as_dict=True)
            # Chống chạy trùng cross-process (TDD §11.6): applock theo khóa như nạp lô §10.3.
            # LockTimeout=0 → khóa đang bị tiến trình tool khác giữ thì BỎ, không chờ (hiếm,
            # thường 1 máy CSDT). In-process đã chặn ở bat_dau; đây là tầng DB cho 2 tiến trình.
            cur.execute(
                "SET NOCOUNT ON; DECLARE @r int; "
                "EXEC @r = sp_getapplock @Resource=%s, @LockMode='Exclusive', @LockTimeout=0; "
                "SELECT @r AS r",
                (ma_kh,),
            )
            got = cur.fetchone()
            if not got or got["r"] < 0:
                td.thong_bao = "Khóa đang được xử lý ở tiến trình khác — thử lại sau."
                return
            try:
                cur.execute(
                    "SELECT MaDK, DuongDanAnh FROM NguoiLX_HoSo "
                    "WHERE MaKhoaHoc=%s AND DuongDanAnh IS NOT NULL AND LTRIM(RTRIM(DuongDanAnh))<>''",
                    (ma_kh,),
                )
                rows = cur.fetchall()
                td.tong = len(rows)
                for row in rows:
                    ma_dk = row["MaDK"]
                    try:
                        xu_ly_mot(cur, ma_dk, (row["DuongDanAnh"] or "").strip(),
                                  pham_vi, sao_luu, nguoi, td)
                    except Exception as e:  # noqa: BLE001 — 1 HV lỗi KHÔNG hỏng cả lô
                        td.loi += 1
                        td.ds_loi.append({"ma_dk": ma_dk, "ly_do": str(e)})
            finally:
                cur.execute("EXEC sp_releaseapplock @Resource=%s", (ma_kh,))
    except Exception as e:  # noqa: BLE001 — lỗi kết nối/truy vấn đầu job
        td.thong_bao = f"Không chạy được đổi nền: {e}"
    finally:
        td.dang_chay = False
        td.xong_het = True


def bat_dau(ma_kh: str, pham_vi: str, sao_luu: bool, nguoi: str = "") -> TienDo:
    """Khởi động job đổi nền cho 1 khóa (applock). Khóa đang chạy → RuntimeError (caller 409)."""
    with _lock:
        cu = _jobs.get(ma_kh)
        if cu and cu.dang_chay:
            raise RuntimeError("Khóa đang đổi nền.")
        td = TienDo()
        _jobs[ma_kh] = td
    threading.Thread(target=_chay, args=(ma_kh, pham_vi, sao_luu, nguoi, td), daemon=True).start()
    return td
