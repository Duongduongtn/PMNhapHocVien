"""Mức 3 — integration toàn tuyến phía VPS (THU-02 → HTG-02 → NAP-01).

Mô phỏng cả luồng ở tầng API (TestClient, SQLite in-memory): collector gửi hồ sơ + ảnh →
operator kéo thấy đủ (ngày cấp + ảnh) → collector sửa khi còn chờ → operator kéo lại thấy
bản mới (nền của "làm tươi" NAP-01/CHANGES #11) → lock → da-nap → imported không kéo lại.

Ranh giới (TDD §14.3): nạp vào SQL Server + khớp app cũ (AS-003) có `test_nap_live.py`;
quét thẻ thật (AS-001) + nạp khớp app cũ là kiểm TAY — KHÔNG ở đây.
"""
import io
from uuid import uuid4

import pytest
from PIL import Image

from app.config import get_settings

TOOL_KEY = get_settings().tool_api_key


@pytest.fixture(autouse=True)
def _anh_tmp_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "anh_tho_dir", str(tmp_path / "anh-tho"))


def _login(api, username):
    pw = {"admin1": "admin-pass", "op1": "op-pass", "col1": "col-pass"}[username]
    token = api.post("/api/auth/login", json={"username": username, "password": pw}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _op(api):
    return {**_login(api, "op1"), "X-Tool-Key": TOOL_KEY}


def _anh_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (20, 20), (200, 180, 160)).save(buf, "JPEG")
    return buf.getvalue()


def test_toan_tuyen_thu_nap_vps(api):
    """THU-02 → NAP-01: gửi → ảnh → kéo → sửa → kéo lại → lock → da-nap → imported."""
    col = _login(api, "col1")
    u = str(uuid4())

    # 1) Collector gửi hồ sơ (kèm ngày cấp CCCD) → 201
    r = api.post("/api/ho-so", headers=col, json={
        "uuid": u, "ho_ten": "Nguyễn Thanh Tâm", "so_cccd": "070202008455",
        "ngay_sinh": "20021121", "gioi_tinh": "M",
        "noi_tt_raw": "Xã Phú Nghĩa, Tỉnh Đồng Nai", "ngay_cap_cccd": "2021-03-10",
    })
    assert r.status_code == 201

    # 2) Collector upload ảnh → co_anh
    r = api.post(f"/api/ho-so/{u}/anh", headers=col,
                 files={"file": ("a.jpg", _anh_bytes(), "image/jpeg")})
    assert r.status_code == 200 and r.json()["co_anh"] is True

    # 3) Operator kéo thấy đủ: ngày cấp (ISO) + có ảnh
    dong = next(x for x in api.get("/api/nap/keo", headers=_op(api)).json() if x["uuid"] == u)
    assert dong["ngay_cap_cccd"] == "2021-03-10"
    assert dong["co_anh"] is True
    assert dong["ho_ten"] == "Nguyễn Thanh Tâm"

    # 4) Operator tải ảnh thô về
    ra = api.get(f"/api/nap/{u}/anh", headers=_op(api))
    assert ra.status_code == 200 and ra.content[:3] == b"\xff\xd8\xff"

    # 5) Collector sửa tên khi còn chờ nạp → 200
    r = api.put(f"/api/ho-so/{u}", headers=col, json={"ho_ten": "Nguyễn Thanh Tâm Anh"})
    assert r.status_code == 200

    # 6) Operator kéo lại thấy BẢN MỚI (nền của "làm tươi" NAP-01)
    dong2 = next(x for x in api.get("/api/nap/keo", headers=_op(api)).json() if x["uuid"] == u)
    assert dong2["ho_ten"] == "Nguyễn Thanh Tâm Anh"

    # 7) Lock (pending → importing)
    assert api.post(f"/api/nap/{u}/lock", headers=_op(api)).json()["trang_thai"] == "importing"

    # 8) da-nap kèm MaDK → imported
    r = api.post(f"/api/nap/{u}/da-nap", headers=_op(api), json={"ma_dk": "70004K26B010001"})
    assert r.status_code == 200 and r.json()["trang_thai"] == "imported"

    # 9) imported KHÔNG kéo lại
    assert all(x["uuid"] != u for x in api.get("/api/nap/keo", headers=_op(api)).json())


def test_toan_tuyen_idempotent_gui_lai(api):
    """Gửi lại cùng uuid (mất mạng rồi thử lại) → 200, 1 bản ghi, không nhân đôi."""
    col = _login(api, "col1")
    u = str(uuid4())
    b = {"uuid": u, "ho_ten": "Trần Thị Hoà", "so_cccd": "012345678901"}
    assert api.post("/api/ho-so", headers=col, json=b).status_code == 201
    assert api.post("/api/ho-so", headers=col, json=b).status_code == 200  # gửi lại
    assert len(api.get("/api/ho-so/cua-toi", headers=col).json()) == 1


def test_toan_tuyen_collector_khong_keo_duoc(api):
    """Phân quyền: collector gọi hàng đợi nạp → 403 (chỉ operator/admin)."""
    r = api.get("/api/nap/keo", headers={**_login(api, "col1"), "X-Tool-Key": TOOL_KEY})
    assert r.status_code == 403
