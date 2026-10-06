"""Điểm vào bản đóng gói .exe (DGT-01/02) — khởi chạy tool như phần mềm thường.

Bản .exe phục vụ LUÔN giao diện (webui/dist) cùng cổng với API (xem app/main.py),
nên không cần Node / cổng dev 3011 riêng. DGT-02: chống chạy 2 bản → dò cổng trống →
chạy uvicorn ở luồng nền → tự mở trình duyệt → hiện khay hệ thống (thay console đen);
'Thoát' ở khay dừng server + xóa lock. Vòng đời/khay: xem app/launcher.py.

Chạy dev vẫn dùng `uvicorn app.main:app` như cũ (xem tool/README.md); file này cho bản gói.
"""
from __future__ import annotations

import multiprocessing
import os
import sys

HOST = os.environ.get("TOOL_HOST", "127.0.0.1")
PORT = int(os.environ.get("TOOL_PORT", "8000"))


def main() -> None:
    from app import launcher

    # 1. Chống chạy 2 bản: đã có bản đang chạy → chỉ mở lại trình duyệt vào đúng cổng, KHÔNG bật bản 2.
    cong_cu = launcher.ban_dang_chay()
    if cong_cu is not None:
        launcher.mo_trinh_duyet(f"http://127.0.0.1:{cong_cu}")
        return

    # 2. Chọn cổng: ưu tiên PORT, bận (app khác chiếm) → nhảy cổng trống.
    port = launcher.chon_cong(PORT)
    launcher.ghi_lock(port)

    # 3. Chạy uvicorn ở luồng nền (khay phải giữ luồng chính).
    import threading

    import uvicorn

    from app.main import app

    server = uvicorn.Server(uvicorn.Config(app, host=HOST, port=port, log_level="info"))
    threading.Thread(target=server.run, daemon=True).start()

    url = f"http://127.0.0.1:{port}"

    def _dung():
        server.should_exit = True
        launcher.xoa_lock()

    # 4. Chờ server sẵn sàng rồi mở trình duyệt; không mở được → báo địa chỉ để gõ tay.
    if launcher.cho_san_sang(port) and not launcher.mo_trinh_duyet(url):
        _bao_dia_chi(url)

    # 5. Khay hệ thống giữ luồng chính; 'Thoát' → _dung(). Không có khay (dev) → chạy nền tới Ctrl+C.
    try:
        launcher.chay_khay(url, _dung)
    except Exception:
        try:
            while not server.should_exit:
                import time

                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
    finally:
        _dung()


def _bao_dia_chi(url: str) -> None:
    """Trình duyệt không tự mở (bản --windowed không có console) → hiện hộp thoại địa chỉ để gõ tay."""
    print(f"Mở trình duyệt và truy cập: {url}")
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(
                0, f"Mở trình duyệt và truy cập:\n{url}", "Tool nạp hồ sơ học viên", 0x40
            )
        except Exception:
            pass


def selftest() -> int:
    """`pmcsdtlx-tool.exe --selftest` — kiểm nhanh bản đóng gói trên máy sạch (DGT-01):
    thư viện C có chạy không (pymssql/FreeTDS, rembg/onnxruntime + model u2net gói kèm).
    KHÔNG cần SQL Server / mạng — chỉ nạp module + xử lý 1 ảnh nhỏ. Trả 0 nếu đạt.
    Bản --windowed không có console → kết quả báo thêm bằng hộp thoại."""
    import io

    ok = True
    dong: list[str] = []

    try:
        import pymssql  # noqa: F401
        dong.append("[OK ] pymssql/FreeTDS nạp được")
    except Exception as e:  # pragma: no cover
        ok = False
        dong.append(f"[LOI] pymssql: {e}")

    try:
        from PIL import Image

        from app import image as img_mod

        buf = io.BytesIO()
        Image.new("RGB", (64, 80), (200, 150, 100)).save(buf, format="PNG")
        # doi_nen_anh: giải mã → ép 3:4 → rembg nền trắng → .jp2 (chạy đủ onnxruntime + model u2net).
        out = img_mod.doi_nen_anh(buf.getvalue())
        dong.append(f"[OK ] rembg/onnxruntime + model u2net xóa phông chạy được (.jp2 {len(out)} bytes)")
    except Exception as e:  # pragma: no cover
        ok = False
        dong.append(f"[LOI] rembg: {e}")

    dong.append("KET QUA: " + ("DAT" if ok else "CHUA DAT"))
    for d in dong:
        try:
            print(d)
        except Exception:
            pass
    if sys.platform == "win32":  # bản windowed không in ra đâu → hộp thoại
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(
                0, "\n".join(dong), "Tự kiểm tool (--selftest)", 0x40 if ok else 0x10
            )
        except Exception:
            pass
    return 0 if ok else 1


def _setup_output() -> None:
    """Console bản .exe Windows: không có (--windowed) → stdout/stderr=None, print/log sẽ sập;
    có → mặc định cp1252, in chữ Việt sập. Xử cả hai: không console thì trỏ log vào file
    trong thư mục dữ liệu (có log soi lỗi), có console thì ép UTF-8."""
    if sys.stdout is None or sys.stderr is None:
        try:
            from app import paths

            log = open(paths.DATA_DIR / "pmcsdtlx-tool.log", "a", encoding="utf-8", buffering=1)
            if sys.stdout is None:
                sys.stdout = log
            if sys.stderr is None:
                sys.stderr = log
        except Exception:
            pass
        return
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except Exception:
            pass


if __name__ == "__main__":
    # Bắt buộc cho bản đóng gói Windows nếu có tiến trình con (onnxruntime/rembg).
    multiprocessing.freeze_support()
    _setup_output()
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    main()
