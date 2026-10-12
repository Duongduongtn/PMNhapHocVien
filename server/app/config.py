"""Cấu hình dịch vụ VPS — đọc từ biến môi trường (TDD §15).

Dùng pydantic-settings: thiếu biến bắt buộc → app báo lỗi ngay lúc khởi động,
không để chạy nửa vời rồi hỏng khi có request đầu tiên.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Backend VPS (TDD §15) ──
    app_domain: str = "http://localhost:8000"
    database_url: str = "postgresql+psycopg://thunhan:thunhan@localhost:5432/thunhan_db"
    jwt_secret: str = "doi-bien-nay-o-moi-truong-that"  # khóa ký JWT (auth)
    anh_tho_dir: str = "/data/anh-tho"
    pii_retention_days: int = 30
    tool_api_key: str = "doi-key-nay-o-moi-truong-that"  # tool gửi qua X-Tool-Key (task 15)

    # ── Hàng đợi thu thập (task 15 — HTG-02, TDD §7) ──
    import_lock_timeout_min: int = 15          # khóa importing quá hạn → job mở (EC-002) — CHƯA có job dùng giá trị này
    max_anh_bytes: int = 8 * 1024 * 1024       # ảnh thô ≤ 8 MB (TDD §7.4)
    max_anh_pixels: int = 25_000_000           # chặn ảnh "bung nén" ~25 MP (TDD §7.4)

    # ── Job nền (task 16 — HTG-02 2/2, TDD §7.3) ──
    enable_scheduler: bool = True              # tắt khi test / worker phụ (chỉ 1 worker nên bật)


@lru_cache
def get_settings() -> Settings:
    return Settings()
