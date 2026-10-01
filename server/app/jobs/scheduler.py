"""Lịch chạy job nền (TDD §7.3).

Quét xóa PII mỗi giờ. Dùng BackgroundScheduler (chạy trong tiến trình API);
đủ cho 1 tiến trình gunicorn worker nạp job. Mỗi lần chạy tự mở/đóng session riêng.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.db import SessionLocal
from app.jobs.pii import xoa_pii_qua_han

logger = logging.getLogger("thunhan.jobs")


def _chay_xoa_pii() -> None:
    db = SessionLocal()
    try:
        so_xoa = xoa_pii_qua_han(db)
        if so_xoa:
            logger.info("Job xóa PII: đã xóa %d bản ghi quá hạn", so_xoa)
    except Exception:  # noqa: BLE001 — job nền: nuốt lỗi để không chết scheduler, có log
        logger.exception("Job xóa PII lỗi")
    finally:
        db.close()


def tao_scheduler() -> BackgroundScheduler:
    """Tạo scheduler đã cấu hình job xóa PII mỗi giờ (chưa start)."""
    scheduler = BackgroundScheduler(timezone="Asia/Ho_Chi_Minh")
    scheduler.add_job(_chay_xoa_pii, "interval", hours=1, id="xoa_pii", replace_existing=True)
    return scheduler
