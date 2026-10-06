"""Điểm vào bản đóng gói .exe (DGT-01) — chạy FastAPI bằng uvicorn trên localhost.

Bản .exe phục vụ LUÔN giao diện (webui/dist) cùng cổng với API (xem app/main.py),
nên không cần Node / cổng dev 3011 riêng. DGT-02 (task 67) sẽ bổ sung: tự mở trình
duyệt + khay hệ thống + chống chạy 2 bản + dò cổng trống.

Chạy dev vẫn dùng `uvicorn app.main:app` như cũ (xem tool/README.md); file này cho bản gói.
"""
from __future__ import annotations

import multiprocessing
import os
import sys

HOST = os.environ.get("TOOL_HOST", "127.0.0.1")
PORT = int(os.environ.get("TOOL_PORT", "8000"))


def main() -> None:
    import uvicorn

    from app.main import app

    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


def selftest() -> int:
    """`pmcsdtlx-tool.exe --selftest` — kiểm nhanh bản đóng gói trên máy sạch (DGT-01):
    thư viện C có chạy không (pymssql/FreeTDS, rembg/onnxruntime + model u2net gói kèm).
    KHÔNG cần SQL Server / mạng — chỉ nạp module + xử lý 1 ảnh nhỏ. Trả 0 nếu đạt."""
    import io

    ok = True

    try:
        import pymssql  # noqa: F401
        print("[OK ] pymssql/FreeTDS nạp được")
    except Exception as e:  # pragma: no cover
        ok = False
        print(f"[LOI] pymssql: {e}")

    try:
        from PIL import Image

        from app import image as img_mod

        buf = io.BytesIO()
        Image.new("RGB", (64, 80), (200, 150, 100)).save(buf, format="PNG")
        # doi_nen_anh: giải mã → ép 3:4 → rembg nền trắng → .jp2 (chạy đủ onnxruntime + model u2net).
        out = img_mod.doi_nen_anh(buf.getvalue())
        print(f"[OK ] rembg/onnxruntime + model u2net xóa phông chạy được (.jp2 {len(out)} bytes)")
    except Exception as e:  # pragma: no cover
        ok = False
        print(f"[LOI] rembg: {e}")

    print("KET QUA: " + ("DAT" if ok else "CHUA DAT"))
    return 0 if ok else 1


def _force_utf8() -> None:
    """Console bản .exe Windows mặc định cp1252 → in chữ Việt (log/selftest) sẽ sập.
    Ép stdout/stderr sang UTF-8 để an toàn."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except Exception:
            pass


if __name__ == "__main__":
    # Bắt buộc cho bản đóng gói Windows nếu có tiến trình con (onnxruntime/rembg).
    multiprocessing.freeze_support()
    _force_utf8()
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    main()
