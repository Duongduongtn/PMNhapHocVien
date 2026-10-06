# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — DGT-01: đóng gói tool nạp thành .exe one-folder.
#
# Build (từ thư mục tool/, trong venv đã cài pyinstaller):
#   .venv/Scripts/python.exe -m PyInstaller tool.spec --noconfirm
# Kết quả: dist/pmcsdtlx-tool/pmcsdtlx-tool.exe (+ _internal/ kèm Python, thư viện, dữ liệu).
#
# Trước khi build phải có: webui/dist (pnpm build) và db/data/dvhc_map.sqlite.
import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

SPEC_DIR = Path(os.getcwd())

# ── Dữ liệu gói kèm (chỉ đọc) ──────────────────────────────────────────────
datas = [
    ("webui/dist", "webui/dist"),                      # giao diện build tĩnh (FastAPI phục vụ)
    ("db/data/dvhc_map.sqlite", "db/data"),            # map DVHC cũ→mới (NAP-03)
]
binaries = []
hiddenimports = []

# Model rembg (xóa phông ảnh) — gói kèm để máy sạch chạy offline, khớp U2NET_HOME ở app/paths.py.
_u2net = Path(os.path.expanduser("~/.u2net/u2net.onnx"))
if _u2net.is_file():
    datas.append((str(_u2net), "models"))

# rembg + onnxruntime: kéo đủ submodule + native lib + metadata.
for _pkg in ("rembg", "onnxruntime"):
    _d, _b, _h = collect_all(_pkg)
    datas += _d
    binaries += _b
    hiddenimports += _h

# rembg tra version qua importlib.metadata → phải nhét dist-info của rembg + pymatting
# (nếu thiếu: "No package metadata was found for pymatting" lúc xóa phông — DGT-01).
for _pkg in ("rembg", "pymatting", "numpy", "onnxruntime"):
    try:
        datas += copy_metadata(_pkg)
    except Exception:
        pass

# pymssql có phần biên dịch C (FreeTDS) — thường tự bắt, khai thêm cho chắc (gotcha máy sạch).
hiddenimports += collect_submodules("pymssql")
hiddenimports += ["pymssql", "_mssql", "uvicorn", "uvicorn.loops.auto",
                  "uvicorn.protocols.http.auto", "uvicorn.protocols.websockets.auto",
                  "uvicorn.lifespan.on"]

# pystray chọn backend theo nền tảng lúc chạy → PyInstaller dễ sót backend win32 (DGT-02).
hiddenimports += collect_submodules("pystray")
hiddenimports += ["pystray._win32", "PIL.ImageDraw"]

a = Analysis(
    ["run_tool.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,       # one-folder: nhanh khởi động hơn one-file
    name="pmcsdtlx-tool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                   # không UPX: tránh antivirus báo nhầm
    console=False,               # DGT-02: windowed (không cửa sổ console đen) — dùng khay hệ thống
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="pmcsdtlx-tool",
)
