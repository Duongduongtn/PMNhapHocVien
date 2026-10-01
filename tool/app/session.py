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

import secrets
from dataclasses import dataclass

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import config_store

VAI_TRO_DUNG_TOOL = ("operator", "admin")

_bearer = HTTPBearer(auto_error=True)


@dataclass
class Phien:
    username: str
    ho_ten: str | None
    vai_tro: str
    vps_token: str | None = None   # JWT do VPS phát (gọi /api/nap/* thay mặt operator)


# token cục bộ → phiên. In-memory, reset khi tool khởi động lại.
_phien_theo_token: dict[str, Phien] = {}


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
            json={"username": username, "password": password},
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
    )
    token = secrets.token_urlsafe(32)
    _phien_theo_token[token] = phien
    return token, phien


def dang_xuat(token: str) -> None:
    _phien_theo_token.pop(token, None)


def require_session(cred: HTTPAuthorizationCredentials = Depends(_bearer)) -> Phien:
    """Gác endpoint /local/* (trừ config + auth): buộc session token cục bộ hợp lệ."""
    phien = _phien_theo_token.get(cred.credentials)
    if phien is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Chưa đăng nhập hoặc phiên đã hết.")
    return phien
