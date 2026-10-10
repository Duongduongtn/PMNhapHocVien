"""Chặn lỗi trắng màn hình khi F5/mở link sâu ở bản FastAPI phục vụ dist (DGT-01).

`base: "./"` khiến /ket-qua/cap-nhat xin /ket-qua/assets/*.js → catch-all SPA trả index.html
(text/html) → JS không chạy. Phải dùng base tuyệt đối "/" vì server phục vụ dist ở gốc.
"""
import re
from pathlib import Path

CFG = Path(__file__).resolve().parents[1] / "webui" / "vite.config.ts"


def test_vite_base_tuyet_doi():
    m = re.search(r'base:\s*"([^"]*)"', CFG.read_text(encoding="utf-8"))
    assert m, "vite.config.ts phải khai báo base"
    assert m.group(1) == "/", "base phải là '/' — './' làm trắng màn hình ở link sâu"
