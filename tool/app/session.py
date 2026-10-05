"""Phiên đăng nhập cục bộ của tool (HTG-01③, option A + A1).

Vì sao có lớp này: token JWT do VPS phát (ký bằng jwt_secret trên VPS, user ở
PostgreSQL) — tool localhost chỉ nối SQL Server, không tự xác thực JWT đó được.
Nên tool đăng nhập THAY MẶT: gọi VPS /api/auth/login để xác thực tài khoản +
vai trò, rồi tự phát một session token cục bộ cho các endpoint /local/*.
Tool vẫn nạp được khi VPS chập chờn (chỉ cần VPS online lúc đăng nhập).

Session giữ trong bộ nhớ (tool chạy 1 tiến trình, 1 máy) — tool khởi động lại thì
đăng nhập lại. Chỉ 'operator'/'admin' dùng được tool (collector không nạp DB — §5.3).
"""
from __future__ import annotations

import json
import secrets
from dataclasses import dataclass

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import config_store, dpapi

VAI_TRO_DUNG_TOOL = ("operator", "admin")

_bearer = HTTPBearer(auto_error=True)

# DGT-04 — phiên lưu ra đĩa (mã hóa DPAPI, ràng máy+user) để mở lại tool vào thẳng.
# Cùng thư mục cấu hình; heartbeat đổi refresh token mỗi HEARTBEAT_SECONDS (< 8h để
# vps_token không kịp hết hạn giữa hai lần làm mới).
SESSION_FILE = config_store.CONFIG_DIR / "session.bin"
HEARTBEAT_SECONDS = 3 * 60 * 60   # 3 giờ


@dataclass
class Phien:
    username: str
    ho_ten: str | None
    vai_tro: str
    vps_token: str | None = None       # JWT do VPS phát (gọi /api/nap/* thay mặt operator)
    refresh_token: str | None = None   # DGT-04 — đổi lấy vps_token mới qua heartbeat


# token cục bộ → phiên. In-memory, reset khi tool khởi động lại; nạp lại từ đĩa (DGT-04).
_phien_theo_token: dict[str, Phien] = {}


# ── DGT-04: lưu/nạp phiên ra đĩa (mã hóa DPAPI) ──
def _luu_phien_dia(token: str, phien: Phien) -> None:
    """Ghi phiên xuống đĩa (DPAPI). Best-effort — lỗi ghi KHÔNG chặn đăng nhập."""
    try:
        blob = dpapi.bao_ve(json.dumps({
            "token": token,
            "username": phien.username,
            "ho_ten": phien.ho_ten,
            "vai_tro": phien.vai_tro,
            "vps_token": phien.vps_token,
            "refresh_token": phien.refresh_token,
        }, ensure_ascii=False).encode("utf-8"))
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        SESSION_FILE.write_bytes(blob)
    except Exception:
        pass


def _xoa_phien_dia() -> None:
    try:
        SESSION_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def nap_phien_tu_dia() -> None:
    """Khởi động tool: khôi phục phiên từ đĩa → mở lại vào thẳng (DGT-04).

    File thiếu/ghi-dở/giải-mã-lỗi (copy sang máy khác, mất key, hỏng đĩa) → BỎ QUA,
    về màn đăng nhập; KHÔNG để exception nổi lên (console đã ẩn ở bản đóng gói)."""
    try:
        if not SESSION_FILE.exists():
            return
        data = json.loads(dpapi.giai_ma(SESSION_FILE.read_bytes()).decode("utf-8"))
        token = data["token"]
        _phien_theo_token[token] = Phien(
            username=data["username"], ho_ten=data.get("ho_ten"), vai_tro=data["vai_tro"],
            vps_token=data.get("vps_token"), refresh_token=data.get("refresh_token"),
        )
    except Exception:
        _xoa_phien_dia()


def lam_moi_phien(token: str) -> bool:
    """Heartbeat — đổi refresh token lấy vps_token mới cho 1 phiên (DGT-04).

    True = phiên còn hiệu lực (đã làm mới, hoặc lỗi mạng tạm nên giữ nguyên).
    False = refresh bị thu hồi / tài khoản bị khóa → xóa phiên, buộc đăng nhập lại.
    Không có refresh token (VPS chưa cấp — chưa deploy) → giữ nguyên, trả True."""
    phien = _phien_theo_token.get(token)
    if phien is None:
        return False
    if not phien.refresh_token:
        return True
    from app import vps  # import trễ tránh phụ thuộc vòng khi nạp module
    try:
        kq = vps.doi_refresh(phien.refresh_token)
    except vps.VpsLoi as e:
        if e.status in (401, 403):   # refresh bị thu hồi / TK khóa → ra
            _phien_theo_token.pop(token, None)
            _xoa_phien_dia()
            return False
        return True                  # lỗi mạng tạm → giữ phiên, thử lần sau
    phien.vps_token = kq.get("access_token") or phien.vps_token
    phien.refresh_token = kq.get("refresh_token") or phien.refresh_token
    _luu_phien_dia(token, phien)
    return True


def dang_nhap_qua_vps(username: str, password: str) -> tuple[str, Phien]:
    """Xác thực tài khoản qua VPS → phát session token cục bộ. Trả (token, phiên).

    Lỗi: 400 chưa cấu hình VPS · 401 sai tài khoản / không đủ quyền · 502 không tới VPS.
    """
    vps_url = (config_store.load_config().get("vps_url") or "").rstrip("/")
    if not vps_url:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Chưa cấu hình URL VPS — vào Cấu hình trước.")

    try:
        r = httpx.post(
            f"{vps_url}/api/auth/login",
            # DGT-04: cap_refresh=True → VPS cấp refresh token (phiên vĩnh viễn, chỉ qua tool).
            # VPS chưa deploy task 69 → field dư bị bỏ qua, refresh_token=None (vẫn đăng nhập được).
            json={"username": username, "password": password, "cap_refresh": True},
            timeout=10.0,
        )
    except httpx.HTTPError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Không tới được VPS để đăng nhập.")

    if r.status_code == 401:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sai tài khoản hoặc mật khẩu.")
    if r.status_code != 200:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "VPS trả lỗi khi đăng nhập.")

    data = r.json()
    vai_tro = data.get("vai_tro", "")
    if vai_tro not in VAI_TRO_DUNG_TOOL:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Tài khoản không có quyền nạp DB (cần nhân viên nạp hoặc quản trị).")

    phien = Phien(
        username=data.get("username", username),
        ho_ten=data.get("ho_ten"),
        vai_tro=vai_tro,
        vps_token=data.get("access_token"),   # giữ để gọi /api/nap/* (kéo/lock/da-nap)
        refresh_token=data.get("refresh_token"),   # DGT-04 — None nếu VPS chưa cấp
    )
    token = secrets.token_urlsafe(32)
    _phien_theo_token[token] = phien
    _luu_phien_dia(token, phien)   # DGT-04 — vào thẳng ở lần mở sau
    return token, phien


def dang_xuat(token: str) -> None:
    """Lối ra duy nhất của phiên vĩnh viễn: xóa phiên RAM + đĩa + thu hồi refresh ở VPS."""
    phien = _phien_theo_token.pop(token, None)
    _xoa_phien_dia()
    if phien and phien.refresh_token:
        from app import vps  # import trễ
        try:
            vps.logout_refresh(phien.vps_token, phien.refresh_token)
        except Exception:
            pass


def require_session(cred: HTTPAuthorizationCredentials = Depends(_bearer)) -> Phien:
    """Gác endpoint /local/* (trừ config + auth): buộc session token cục bộ hợp lệ."""
    phien = _phien_theo_token.get(cred.credentials)
    if phien is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Chưa đăng nhập hoặc phiên đã hết.")
    return phien
