"""Đăng nhập cục bộ của tool (HTG-01③): /local/auth/login|logout|me.

login xác thực qua VPS rồi phát session token cục bộ (xem app/session.py).
Nhóm endpoint này KHÔNG bị gác token (login là cửa vào); me/logout tự gác.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app import session

router = APIRouter(prefix="/local/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=True)


class LoginIn(BaseModel):
    username: str
    password: str


class LoginOut(BaseModel):
    session_token: str
    username: str
    ho_ten: str | None
    vai_tro: str


class MeOut(BaseModel):
    username: str
    ho_ten: str | None
    vai_tro: str


@router.post("/login", response_model=LoginOut)
def login(body: LoginIn) -> LoginOut:
    token, phien = session.dang_nhap_qua_vps(body.username.strip(), body.password)
    return LoginOut(session_token=token, username=phien.username, ho_ten=phien.ho_ten, vai_tro=phien.vai_tro)


@router.get("/me", response_model=MeOut)
def me(phien: session.Phien = Depends(session.require_session)) -> MeOut:
    return MeOut(username=phien.username, ho_ten=phien.ho_ten, vai_tro=phien.vai_tro)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(cred: HTTPAuthorizationCredentials = Depends(_bearer)) -> None:
    session.dang_xuat(cred.credentials)
