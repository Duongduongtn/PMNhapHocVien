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


def doi_refresh(refresh_token: str) -> dict:
    """DGT-04 — đổi refresh token lấy cặp (access_token, refresh_token) MỚI.

    KHÔNG cần Bearer (tự xác thực bằng chính refresh token). VPS 401/403 =
    refresh bị thu hồi / tài khoản bị khóa → VpsLoi(status) để heartbeat đá phiên."""
    cfg = config_store.load_config()
    vps_url = (cfg.get("vps_url") or "").rstrip("/")
    if not vps_url:
        raise VpsLoi("Chưa cấu hình URL VPS.")
    try:
        r = httpx.post(f"{vps_url}/api/auth/refresh",
                       json={"refresh_token": refresh_token}, timeout=_TIMEOUT_NGAN)
    except httpx.HTTPError as e:
        raise VpsLoi("Không tới được VPS để làm mới phiên.") from e
    if r.status_code != 200:
        raise VpsLoi("Làm mới phiên thất bại.", status=r.status_code)
    return r.json()


def logout_refresh(vps_token: str | None, refresh_token: str | None) -> None:
    """DGT-04 — thu hồi phiên ở VPS khi Đăng xuất (xóa refresh token). Best-effort."""
    try:
        base, headers = _base_va_headers(vps_token)
    except VpsLoi:
        return
    try:
        httpx.post(f"{base}/api/auth/logout", headers=headers,
                   json={"refresh_token": refresh_token}, timeout=_TIMEOUT_NGAN)
    except httpx.HTTPError:
        pass


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


def da_xoa(vps_token: str | None, since: str | None = None) -> dict:
    """DS uuid hồ sơ collector đã XÓA ở app web (THU-05) từ mốc `since` — NAP-01 task 44 đồng bộ
    khi "Kéo về". Trả {"uuids": [...], "moc": <iso>}. since=None → từ đầu. Lỗi → VpsLoi."""
    params = {"since": since} if since else {}
    r = _goi("GET", "/api/nap/da-xoa", vps_token, timeout=_TIMEOUT, params=params)
    if r.status_code != 200:
        raise VpsLoi("VPS trả lỗi khi lấy danh sách đã xóa.", r.status_code)
    return r.json()


def gplx_bo_sung(vps_token: str | None, cursor: str | None = None, limit: int = 200) -> dict:
    """Hồ sơ đã nạp được bổ sung GPLX ở app web (QLY-10). Trả {"items", "co_tiep", "cursor"}. Lỗi → VpsLoi."""
    params: dict = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    r = _goi("GET", "/api/nap/gplx-bo-sung", vps_token, timeout=_TIMEOUT, params=params)
    if r.status_code != 200:
        raise VpsLoi("VPS trả lỗi khi lấy GPLX bổ sung.", r.status_code)
    return r.json()


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


def trang_thai_nhieu(vps_token: str | None, uuids: list[str]) -> dict[str, dict]:
    """QLY-09 ca ② — tra trạng thái VPS của nhiều uuid một lượt (đối soát theo khóa). Trả dict
    {uuid: {trang_thai, ma_dk, locked_at}}; uuid không có trên VPS → KHÔNG xuất hiện trong dict."""
    uuids = [u for u in uuids if u]
    if not uuids:
        return {}
    r = _goi("GET", "/api/nap/trang-thai", vps_token, timeout=_TIMEOUT, params={"uuids": ",".join(uuids)})
    if r.status_code != 200:
        raise VpsLoi("VPS trả lỗi khi tra trạng thái hồ sơ.", r.status_code)
    return {row["uuid"]: row for row in r.json()}


def admin_ho_so(vps_token: str | None, trang_thai: str | None = None,
                limit: int = 500, offset: int = 0) -> dict:
    """QLY-09 ca ①③ — quét bản ghi theo trạng thái VPS (admin, tái dùng HTG-03). Trả
    {"items": [{uuid, ma_dk, locked_at, trang_thai, ...}], "total": n}. Lỗi → VpsLoi."""
    params: dict[str, object] = {"limit": limit, "offset": offset}
    if trang_thai:
        params["trang_thai"] = trang_thai
    r = _goi("GET", "/api/admin/ho-so", vps_token, timeout=_TIMEOUT, params=params)
    if r.status_code != 200:
        raise VpsLoi("VPS trả lỗi khi quét bản ghi đối soát.", r.status_code)
    return r.json()
