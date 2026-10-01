import os

# Khi chạy test: không warm-up rembg (tránh tải model u2net ~170MB).
os.environ.setdefault("TOOL_SKIP_WARMUP", "1")

import pytest

from app import session as _session


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
