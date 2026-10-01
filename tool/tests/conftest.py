import os

# Khi chạy test: không warm-up rembg (tránh tải model u2net ~170MB).
os.environ.setdefault("TOOL_SKIP_WARMUP", "1")
