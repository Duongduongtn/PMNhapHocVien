import os

# Khi chạy test: không warm-up rembg (tránh tải model u2net ~170MB) + không chạy
# heartbeat nền (DGT-04) để test không gọi VPS thật.
os.environ.setdefault("TOOL_SKIP_WARMUP", "1")
os.environ.setdefault("TOOL_SKIP_HEARTBEAT", "1")

import pytest

from app import session as _session


@pytest.fixture(autouse=True)
def _co_lap_session_file(tmp_path, monkeypatch):
    """DGT-04 — trỏ phiên-đĩa vào thư mục tạm để test KHÔNG ghi `config/session.bin` thật."""
    monkeypatch.setattr(_session, "SESSION_FILE", tmp_path / "session.bin")
    yield


@pytest.fixture
def auth_headers():
    """Session token operator giả cho test endpoint /local/* nghiệp vụ (gác HTG-01③).

    Bơm thẳng vào store, không gọi VPS — chỉ để qua cổng tới tầng validate/handler."""
    token = "test-session-token"
    _session._phien_theo_token[token] = _session.Phien(
        username="op-test", ho_ten="NV Nạp (test)", vai_tro="operator"
    )
    yield {"Authorization": f"Bearer {token}"}
    _session._phien_theo_token.pop(token, None)
