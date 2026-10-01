"""Tạo tài khoản admin đầu tiên trên VPS (TDD §5.4) — không mở self-register.

Chạy:  python -m scripts.seed_admin --username admin --ho-ten "Quản trị"
Mật khẩu: nhập qua biến môi trường SEED_ADMIN_PASSWORD (không truyền trên dòng lệnh để khỏi lưu vào history).
"""
import argparse
import os
import sys

from sqlalchemy import select

from app.auth.security import hash_password
from app.db import SessionLocal
from app.models.user import User


def main() -> int:
    ap = argparse.ArgumentParser(description="Tạo tài khoản admin đầu tiên")
    ap.add_argument("--username", required=True)
    ap.add_argument("--ho-ten", default=None)
    args = ap.parse_args()

    password = os.environ.get("SEED_ADMIN_PASSWORD")
    if not password:
        print("Thiếu mật khẩu: đặt biến môi trường SEED_ADMIN_PASSWORD trước khi chạy.", file=sys.stderr)
        return 2

    db = SessionLocal()
    try:
        if db.scalar(select(User).where(User.username == args.username)) is not None:
            print(f"Tài khoản '{args.username}' đã tồn tại — không tạo lại.", file=sys.stderr)
            return 1
        db.add(User(username=args.username, password_hash=hash_password(password), ho_ten=args.ho_ten, vai_tro="admin"))
        db.commit()
        print(f"Đã tạo admin '{args.username}'.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
