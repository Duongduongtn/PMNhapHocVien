"""Khách gọi VPS cho luồng nạp (NAP-01) — kéo hàng đợi + khóa vòng đời bản ghi.

Tool nối SQL Server để nạp, nhưng hàng đợi hồ sơ nằm trên VPS (PostgreSQL). Module
này gọi các endpoint `/api/nap/*` của VPS, đính kèm hai lớp xác thực mà server bắt
(TDD §4.4, §7.2):
- `Authorization: Bearer <JWT operator>` — JWT do VPS phát lúc đăng nhập (giữ trong phiên).
- `X-Tool-Key: <vps_api_key>` — khóa máy, lấy từ cấu hình tool đã mã hóa.

Mọi lỗi mạng/HTTP gói vào `VpsLoi` (kèm `status` khi là lỗi HTTP) để router đổi thành
thông báo rõ cho nhân viên. KHÔNG log token/CCCD.
"""
from __future__ import annotations

import httpx

from app import config_store

_TIMEOUT = 15.0        # kéo danh sách / tải ảnh
_TIMEOUT_NGAN = 10.0   # lock / da-nap / unlock


class VpsLoi(Exception):
    """Lỗi khi gọi VPS. `status` = mã HTTP VPS trả (None nếu lỗi mạng)."""

    def __init__(self, thong_bao: str, status: int | None = None):
        super().__init__(thong_bao)
        self.status = status


def _base_va_headers(vps_token: str | None) -> tuple[str, dict[str, str]]:
    """Lấy URL VPS + headers xác thực từ cấu hình + phiên. Thiếu thứ gì → VpsLoi."""
    cfg = config_store.load_config()
    vps_url = (cfg.get("vps_url") or "").rstrip("/")
    tool_key = cfg.get("vps_api_key") or ""
    if not vps_url:
        raise VpsLoi("Chưa cấu hình URL VPS — vào Cấu hình trước.")
    if not tool_key:
        raise VpsLoi("Chưa cấu hình API key VPS — vào Cấu hình trước.")
    if not vps_token:
        raise VpsLoi("Phiên chưa có quyền VPS — đăng nhập lại.")
    headers = {"Authorization": f"Bearer {vps_token}", "X-Tool-Key": tool_key}
    return vps_url, headers


def _goi(method: str, path: str, vps_token: str | None, *, timeout=_TIMEOUT_NGAN, **kwargs) -> httpx.Response:
    base, headers = _base_va_headers(vps_token)
    try:
        r = httpx.request(method, f"{base}{path}", headers=headers, timeout=timeout, **kwargs)
    except httpx.HTTPError as e:
        raise VpsLoi("Không tới được VPS — kiểm kết nối rồi thử lại.") from e
    return r


def keo(vps_token: str | None, limit: int = 200, cursor: str | None = None) -> list[dict]:
    """Kéo danh sách bản ghi `pending` chưa bị khóa (FIFO). cursor = created_at bản cuối lượt trước."""
    params: dict[str, object] = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    r = _goi("GET", "/api/nap/keo", vps_token, timeout=_TIMEOUT, params=params)
    if r.status_code != 200:
        raise VpsLoi("VPS trả lỗi khi kéo hàng đợi.", r.status_code)
    return r.json()


def tai_anh(vps_token: str | None, uuid: str) -> bytes | None:
    """Tải ảnh thô của 1 hồ sơ. Chưa có ảnh (404) → None; lỗi khác → VpsLoi."""
    r = _goi("GET", f"/api/nap/{uuid}/anh", vps_token, timeout=_TIMEOUT)
    if r.status_code == 404:
        return None
    if r.status_code != 200:
        raise VpsLoi("VPS trả lỗi khi tải ảnh.", r.status_code)
    return r.content


def lock(vps_token: str | None, uuid: str) -> None:
    """Khóa bản ghi trước khi nạp (pending→importing). Đã bị khóa/đã nạp → VpsLoi(status=409)."""
    r = _goi("POST", f"/api/nap/{uuid}/lock", vps_token)
    if r.status_code == 409:
        raise VpsLoi("Hồ sơ đang được nạp ở máy khác hoặc đã nạp.", 409)
    if r.status_code != 200:
        raise VpsLoi("VPS trả lỗi khi khóa hồ sơ.", r.status_code)


def da_nap(vps_token: str | None, uuid: str, ma_dk: str) -> None:
    """Đánh dấu đã nạp vào DB đích (kèm ma_dk) + mở khóa."""
    r = _goi("POST", f"/api/nap/{uuid}/da-nap", vps_token, json={"ma_dk": ma_dk})
    if r.status_code != 200:
        raise VpsLoi("VPS trả lỗi khi xác nhận đã nạp.", r.status_code)


def unlock(vps_token: str | None, uuid: str) -> None:
    """Mở khóa khi nạp lỗi → bản ghi quay lại pending để nạp lại."""
    r = _goi("POST", f"/api/nap/{uuid}/unlock", vps_token)
    if r.status_code != 200:
        raise VpsLoi("VPS trả lỗi khi mở khóa hồ sơ.", r.status_code)


def tra_uuid(vps_token: str | None, ma_dk: str) -> str | None:
    """Tra uuid gốc theo ma_dk (QLY-08 bước 2 — fallback khi staging nap_xong local không còn).
    Không thấy bản đã nạp (404) → None; lỗi khác → VpsLoi."""
    r = _goi("GET", "/api/nap/tra-uuid", vps_token, params={"ma_dk": ma_dk})
    if r.status_code == 404:
        return None
    if r.status_code != 200:
        raise VpsLoi("VPS trả lỗi khi tra mã hồ sơ gốc.", r.status_code)
    return r.json().get("uuid")


def tra_ve_cho_nap(vps_token: str | None, uuid: str) -> None:
    """Trả bản ghi gốc về chờ nạp (imported→pending, gỡ ma_dk) — QLY-08 bước 4. VPS idempotent
    khi đã pending (trả 200 → retry an toàn). Bản ghi `deleted`/`importing`/không còn (404/409) →
    VpsLoi(status) để router báo 'không còn bản gốc trên VPS, chỉ có thể Xóa hẳn'."""
    r = _goi("POST", f"/api/nap/{uuid}/tra-ve-cho-nap", vps_token)
    if r.status_code == 404:
        raise VpsLoi("VPS không còn bản gốc hồ sơ để trả về chờ nạp.", 404)
    if r.status_code == 409:
        raise VpsLoi("VPS không còn bản gốc đã nạp để trả về (đã xóa hoặc đã dọn dữ liệu).", 409)
    if r.status_code != 200:
        raise VpsLoi("VPS trả lỗi khi trả hồ sơ về chờ nạp.", r.status_code)
