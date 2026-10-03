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
    pw = {"admin1": "admin-pass", "op1": "op-pass", "col1": "col-pass", "col2": "col-pass"}[username]
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


# ═══════════ Checkpoint 8 — cụm xóa/gỡ hồ sơ (THU-05 + QLY-08 + NAP-01 task 44) ═══════════
# Mức 3 phía VPS. Phần tool gọi SQL Server (usp_NguoiLX_Delete, ảnh _DELETED, BC1 guard, staging)
# nằm ngoài tuyến này — verify live sau deploy (TDD §14.3); đã có unit test mock ở task 43/44.

def _gui(api, col, **kw):
    """Collector gửi 1 hồ sơ pending, trả uuid."""
    u = str(uuid4())
    body = {"uuid": u, "ho_ten": "Nguyễn Thị Hoà", "so_cccd": "012345678901"}
    body.update(kw)
    assert api.post("/api/ho-so", headers=col, json=body).status_code == 201
    return u


# ── Luồng A — THU-05 + NAP-01 đồng bộ xóa: gửi → xóa ở app web → kéo biến mất ──
def test_a1_gui_xoa_keo_bien_mat(api):
    """A1 (THU-05→NAP-01): collector xóa hồ sơ pending → /keo không còn + /da-xoa trả uuid."""
    col = _login(api, "col1")
    u = _gui(api, col, ho_ten="Trần Văn Bảy")
    assert api.request("DELETE", f"/api/ho-so/{u}", headers=col).status_code == 204
    # Kéo không còn thấy (đã deleted)
    assert all(x["uuid"] != u for x in api.get("/api/nap/keo", headers=_op(api)).json())
    # da-xoa báo uuid này đã xóa → tool dùng để bỏ dòng staging tương ứng
    assert u in api.get("/api/nap/da-xoa", headers=_op(api)).json()["uuids"]


def test_a2_idor_xoa_ho_so_nguoi_khac_404(api):
    """A2 (THU-05): collector KHÁC xóa hồ sơ không phải của mình → 404 (không lộ tồn tại)."""
    u = _gui(api, _login(api, "col1"), ho_ten="Lê Thị Hồng")
    r = api.request("DELETE", f"/api/ho-so/{u}", headers=_login(api, "col2"))
    assert r.status_code == 404
    # Hồ sơ KHÔNG bị xóa → operator vẫn kéo thấy
    assert any(x["uuid"] == u for x in api.get("/api/nap/keo", headers=_op(api)).json())


def test_a4_admin_xoa_ho_so_collector(api):
    """A4 (THU-05): admin xóa được hồ sơ của bất kỳ collector nào → 2xx + da-xoa trả uuid."""
    u = _gui(api, _login(api, "col1"), ho_ten="Phạm Văn Tám")
    assert api.request("DELETE", f"/api/ho-so/{u}", headers=_login(api, "admin1")).status_code == 204
    assert u in api.get("/api/nap/da-xoa", headers=_op(api)).json()["uuids"]


def test_a5_da_xoa_rong_khi_khong_co_gi_moi(api):
    """A5 (NAP-01 phòng thủ): không xóa hồ sơ nào → da-xoa trả rỗng. Chống bỏ nhầm dòng staging
    (TDD §11.7: KHÔNG suy 'đã xóa' từ vắng mặt trong /keo)."""
    _gui(api, _login(api, "col1"), ho_ten="Võ Thị Chín")  # có pending nhưng KHÔNG xóa
    assert api.get("/api/nap/da-xoa", headers=_op(api)).json()["uuids"] == []


# ── Luồng B — QLY-08 gỡ về chờ nạp (phía VPS): nạp → gỡ → về hàng chờ ──
def _nap_imported(api, ma_dk):
    """gửi → lock → da-nap → trả uuid đã imported (kèm ma_dk)."""
    u = _gui(api, _login(api, "col1"), ho_ten="Đặng Thị Mười")
    assert api.post(f"/api/nap/{u}/lock", headers=_op(api)).json()["trang_thai"] == "importing"
    assert api.post(f"/api/nap/{u}/da-nap", headers=_op(api), json={"ma_dk": ma_dk}).status_code == 200
    return u


def test_b1_go_ve_cho_nap_ve_hang_cho(api):
    """B1 (QLY-08 VPS): nạp → tra-uuid theo ma_dk → tra-ve-cho-nap (imported→pending, gỡ ma_dk)
    → /keo thấy lại; tra-uuid theo ma_dk cũ nay 404 (xác nhận ma_dk đã gỡ, không nạp lại trùng)."""
    ma_dk = "70004K26B010042"
    u = _nap_imported(api, ma_dk)
    # imported → chưa kéo lại được
    assert all(x["uuid"] != u for x in api.get("/api/nap/keo", headers=_op(api)).json())
    # Tool tra uuid gốc theo ma_dk (fallback khi staging local mất)
    assert api.get("/api/nap/tra-uuid", headers=_op(api), params={"ma_dk": ma_dk}).json()["uuid"] == u
    # Trả về chờ nạp → pending
    r = api.post(f"/api/nap/{u}/tra-ve-cho-nap", headers=_op(api))
    assert r.status_code == 200 and r.json()["trang_thai"] == "pending"
    # Về hàng chờ → kéo lại thấy
    assert any(x["uuid"] == u for x in api.get("/api/nap/keo", headers=_op(api)).json())
    # ma_dk đã gỡ → tra-uuid theo ma_dk cũ không còn trả về
    assert api.get("/api/nap/tra-uuid", headers=_op(api), params={"ma_dk": ma_dk}).status_code == 404


def test_b3_go_ve_khi_da_xoa_409(api):
    """B3 (QLY-08 nhánh lỗi): hồ sơ đã bị xóa (deleted) → tra-ve-cho-nap 409 (không còn bản gốc)."""
    col = _login(api, "col1")
    u = _gui(api, col, ho_ten="Bùi Văn Một")
    assert api.request("DELETE", f"/api/ho-so/{u}", headers=col).status_code == 204
    assert api.post(f"/api/nap/{u}/tra-ve-cho-nap", headers=_op(api)).status_code == 409


def test_b4_ve_pending_collector_sua_lai_duoc(api):
    """B4 (QLY-08 Done#8, CHANGES #26): sau khi gỡ về pending, collector lại sửa hồ sơ được
    (app web làm chủ khi trước nạp — TDD §7.5)."""
    u = _nap_imported(api, "70004K26B010043")
    assert api.post(f"/api/nap/{u}/tra-ve-cho-nap", headers=_op(api)).status_code == 200
    r = api.put(f"/api/ho-so/{u}", headers=_login(api, "col1"), json={"ho_ten": "Đặng Thị Mười Một"})
    assert r.status_code == 200
    dong = next(x for x in api.get("/api/nap/keo", headers=_op(api)).json() if x["uuid"] == u)
    assert dong["ho_ten"] == "Đặng Thị Mười Một"
