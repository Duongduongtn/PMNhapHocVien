"""In Báo cáo 2 — dựng PDF bằng mẫu Crystal của phần mềm cũ (TNB-08, task 166). TDD §11F.9, decisions §32.

Tool chỉ đưa dữ liệu; mẫu `rptBaoCao2.rpt` và dll Crystal đọc từ thư mục phần mềm cũ trên máy (không chép vào tool).
Gọi `in_bc2.ps1` bằng PowerShell 32-bit. Tệp tạm (có họ tên/số giấy) xóa ở mọi nhánh.
"""
from __future__ import annotations

import ctypes
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
from decimal import Decimal
from pathlib import Path

from app import config_store, paths
from app.tn_bc2_service import LoiNghiepVu

THOI_GIAN_TOI_DA = 60          # giây
CHO_LUOT_TOI_DA = 90           # giây chờ tới lượt dựng (một lần dựng mỗi lúc)
TUOI_TEP_TAM_TOI_DA = 300      # giây: thư mục tạm cũ hơn mức này bị quét khi bắt đầu dựng
MAU_REPORT = Path("PM1") / "Reports" / "rptBaoCao2.rpt"
DLL_BAT_BUOC = ("CrystalDecisions.CrystalReports.Engine.dll", "CrystalDecisions.Shared.dll",
                "CrystalDecisions.ReportSource.dll")
_KHOA = threading.Lock()       # một lần dựng mỗi lúc (Crystal nạp dll theo tiến trình, dựng song song tốn máy)


def _ps32() -> Path:
    return Path(os.environ.get("WINDIR", r"C:\Windows")) / "SysWOW64" / "WindowsPowerShell" / "v1.0" / "powershell.exe"


def _script() -> Path:
    return paths.BUNDLE_DIR / "app" / "scripts" / "in_bc2.ps1"


def kiem_thu_muc(thu_muc: str | Path) -> str:
    """Thư mục phần mềm cũ hợp lệ khi có mẫu BC2 + 3 dll Crystal. Trả '' nếu hợp lệ, ngược lại lý do."""
    d = Path(thu_muc)
    if not (d / MAU_REPORT).is_file():
        return f"Không thấy {MAU_REPORT} trong thư mục này"
    thieu = [x for x in DLL_BAT_BUOC if not (d / x).is_file()]
    return f"Thiếu {', '.join(thieu)}" if thieu else ""


def _o_co_dinh(o: str) -> bool:
    """Chỉ ổ đĩa cố định (loại USB/ổ mạng): dll trong thư mục được nạp và chạy với quyền người dùng."""
    try:
        return ctypes.windll.kernel32.GetDriveTypeW(f"{o}:\\") == 3   # DRIVE_FIXED
    except (AttributeError, OSError):
        return False


def duong_dan_an_toan(t: str) -> bool:
    """Đường dẫn tuyệt đối trên ổ cố định; không UNC (`\\\\máy\\…`), không tương đối."""
    t = (t or "").strip()
    if t.startswith(("\\\\", "//")) or not Path(t).is_absolute() or len(Path(t).drive) != 2:
        return False
    return _o_co_dinh(Path(t).drive[0])


def tu_do() -> list[str]:
    """Dò các thư mục phần mềm cũ phổ biến trên ổ cố định: `<ổ>:\\GPLX-*\\GPLX-*`, `<ổ>:\\GPLX-*`."""
    ung = []
    for o in "DCEFG":
        goc = Path(f"{o}:/")
        if not _o_co_dinh(o) or not goc.exists():
            continue
        try:
            for a in goc.glob("GPLX-*"):
                ung += [str(a)] + [str(b) for b in a.glob("GPLX-*") if b.is_dir()]
        except OSError:
            continue
    return [u for u in dict.fromkeys(ung) if not kiem_thu_muc(u)]


def doc_thu_muc() -> dict:
    """Thư mục phần mềm cũ đang dùng: cấu hình đã lưu (nếu còn hợp lệ) → dò tự động."""
    luu = (config_store.load_config().get("gplx_cu_dir") or "").strip()
    if luu and duong_dan_an_toan(luu) and not kiem_thu_muc(luu):
        return {"thu_muc": luu, "nguon": "da_luu", "ung_vien": []}
    ung = tu_do()
    return {"thu_muc": ung[0] if ung else "", "nguon": "tu_do" if ung else "khong_co", "ung_vien": ung,
            "luu_khong_hop_le": luu if luu else ""}


def luu_thu_muc(thu_muc: str) -> dict:
    t = (thu_muc or "").strip().strip('"')
    if not t or len(t) > 400 or not duong_dan_an_toan(t):
        raise LoiNghiepVu("thu_muc_khong_hop_le",
                          "Chỉ nhận đường dẫn đầy đủ trên ổ đĩa cố định của máy (vd D:\\GPLX-…), không nhận ổ mạng hay USB", 400)
    if not Path(t).is_dir():
        raise LoiNghiepVu("thu_muc_khong_hop_le", "Không thấy thư mục này", 400)
    ly_do = kiem_thu_muc(t)
    if ly_do:
        raise LoiNghiepVu("thu_muc_khong_hop_le", ly_do, 400)
    config_store.sua_config(lambda data: data.update({"gplx_cu_dir": t}))
    return doc_thu_muc()


def _xoa(*duong_dan: Path) -> None:
    """Xóa tệp/thư mục tạm; thử lại vài lần (antivirus/Crystal có thể còn giữ tay cầm sau khi bị dừng)."""
    for p in duong_dan:
        for lan in range(4):
            try:
                if p.is_dir():
                    shutil.rmtree(p)
                elif p.exists():
                    p.unlink()
                break
            except OSError:
                time.sleep(0.3)
        else:
            shutil.rmtree(p, ignore_errors=True)


def quet_tep_tam_cu() -> None:
    """Xóa các thư mục `bc2_*` (có họ tên/CMT) bị bỏ lại do lần trước hỏng giữa chừng."""
    han = time.time() - TUOI_TEP_TAM_TOI_DA
    try:
        for d in paths.DATA_DIR.glob("bc2_*"):
            if d.is_dir() and d.stat().st_mtime < han:
                _xoa(d)
    except OSError:
        pass


def _mac_dinh_json(v):
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    return str(v)


def dung_pdf(du_lieu: dict, *, thu_muc_pm_cu: str | None = None, thoi_gian: int = THOI_GIAN_TOI_DA,
             cho_luot: int = CHO_LUOT_TOI_DA) -> bytes:
    """Dựng PDF Báo cáo 2 từ dữ liệu `tn_bc2_in.du_lieu_crystal`. Trả nội dung PDF.

    Lỗi: 409 `chua_co_phan_mem_cu` (thiếu/không an toàn thư mục, mẫu, dll, PowerShell 32-bit), 409 `ban_in_dang_ban`
    (quá `cho_luot` giây chưa tới lượt), 504 `dung_ban_in_qua_lau`, 502 `dung_ban_in_loi`.
    Thông báo lỗi KHÔNG chép đầu ra của Crystal (có thể chứa họ tên, đường dẫn nội bộ). Tệp tạm xóa trong `finally`."""
    tm = thu_muc_pm_cu or doc_thu_muc()["thu_muc"]
    if not tm or not duong_dan_an_toan(tm) or kiem_thu_muc(tm) or not _ps32().is_file() or not _script().is_file():
        raise LoiNghiepVu("chua_co_phan_mem_cu",
                          "Máy này chưa dựng được bản in: không tìm thấy mẫu in và bộ Crystal của phần mềm cũ. "
                          "Chọn đúng thư mục cài phần mềm cũ.", 409)
    if not _KHOA.acquire(timeout=cho_luot):
        raise LoiNghiepVu("ban_in_dang_ban", "Đang dựng một bản in khác — chờ ít phút rồi thử lại.", 409)
    tam: Path | None = None
    try:
        quet_tep_tam_cu()
        tam = Path(tempfile.mkdtemp(prefix="bc2_", dir=str(paths.DATA_DIR)))
        json_p, pdf_p = tam / "du_lieu.json", tam / "ban_in.pdf"
        json_p.write_text(json.dumps(du_lieu, ensure_ascii=False, default=_mac_dinh_json), encoding="utf-8")
        cmd = [str(_ps32()), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(_script()),
               "-Rpt", str(Path(tm) / MAU_REPORT), "-Json", str(json_p), "-Pdf", str(pdf_p), "-CrystalDir", tm]
        try:
            kq = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                stdin=subprocess.DEVNULL, timeout=thoi_gian,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except subprocess.TimeoutExpired:
            raise LoiNghiepVu("dung_ban_in_qua_lau", f"Dựng bản in quá {thoi_gian} giây — thử lại.", 504)
        if kq.returncode != 0 or not pdf_p.is_file() or pdf_p.stat().st_size == 0:
            raise LoiNghiepVu("dung_ban_in_loi", "Bộ Crystal của phần mềm cũ báo lỗi khi dựng bản in. "
                              "Kiểm lại thư mục phần mềm cũ rồi thử lại; nếu vẫn lỗi, báo người hỗ trợ.", 502,
                              {"ma_thoat": kq.returncode})
        return pdf_p.read_bytes()
    finally:
        if tam is not None:
            _xoa(tam)
        _KHOA.release()
