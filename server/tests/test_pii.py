"""Test HTG-02 (2/2) — job xóa PII 30 ngày (mức 2, SQLite in-memory, TDD §7.3).

Phủ: xóa pending/imported quá hạn + ghi audit, giữ bản còn mới,
BỎ QUA bản importing (EC-040), xóa kèm file ảnh thô, mốc 30 ngày.
"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import func, select

from app.jobs.pii import xoa_pii_qua_han
from app.models.ho_so import AuditLog, HoSoThuThap

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)


def _them(db, trang_thai: str, ngay_tuoi: int, anh_tho_path: str | None = None):
    # CHANGES #44: job tính tuổi theo updated_at → backdate cả hai mốc cho rõ ý "N ngày không ai chạm".
    moc = NOW - timedelta(days=ngay_tuoi)
    hs = HoSoThuThap(
        uuid=uuid4(),
        trang_thai=trang_thai,
        ho_ten="A",
        anh_tho_path=anh_tho_path,
        created_at=moc,
        updated_at=moc,
    )
    db.add(hs)
    db.commit()
    return hs


def test_xoa_pending_qua_han(db_setup):
    db, _ = db_setup
    hs = _them(db, "pending", 40)
    so = xoa_pii_qua_han(db, now=NOW, retention_days=30)
    assert so == 1
    assert db.get(HoSoThuThap, hs.uuid) is None
    # có ghi audit xoa_pii
    assert db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.hanh_dong == "xoa_pii")) == 1


def test_xoa_imported_qua_han(db_setup):
    db, _ = db_setup
    _them(db, "imported", 45)
    assert xoa_pii_qua_han(db, now=NOW, retention_days=30) == 1


def test_imported_chup_bu_gia_han_khong_xoa(db_setup):
    """CHANGES #44: HV imported gửi 45 ngày trước nhưng collector vừa chụp bù ảnh
    (updated_at mới 5 ngày) → job tính theo updated_at → GIỮ, chờ operator kéo."""
    db, _ = db_setup
    hs = _them(db, "imported", 45)
    hs.updated_at = NOW - timedelta(days=5)  # chụp bù gần đây
    db.commit()
    assert xoa_pii_qua_han(db, now=NOW, retention_days=30) == 0
    assert db.get(HoSoThuThap, hs.uuid) is not None


def test_giu_ban_con_moi(db_setup):
    db, _ = db_setup
    hs = _them(db, "pending", 10)  # mới 10 ngày
    assert xoa_pii_qua_han(db, now=NOW, retention_days=30) == 0
    assert db.get(HoSoThuThap, hs.uuid) is not None


def test_bo_qua_importing(db_setup):
    db, _ = db_setup
    hs = _them(db, "importing", 40)  # đang nạp dở — EC-040
    assert xoa_pii_qua_han(db, now=NOW, retention_days=30) == 0
    assert db.get(HoSoThuThap, hs.uuid) is not None


def test_xoa_kem_file_anh(db_setup, tmp_path):
    db, _ = db_setup
    f = tmp_path / "anh.jpg"
    f.write_bytes(b"\xff\xd8\xff dummy")
    _them(db, "pending", 40, anh_tho_path=str(f))
    assert xoa_pii_qua_han(db, now=NOW, retention_days=30) == 1
    assert not f.exists()  # file ảnh thô đã bị xóa


def test_thieu_file_anh_khong_loi(db_setup, tmp_path):
    db, _ = db_setup
    _them(db, "pending", 40, anh_tho_path=str(tmp_path / "khong-ton-tai.jpg"))
    # file đã bị xóa tay trước đó → job vẫn xóa bản ghi, không ném lỗi
    assert xoa_pii_qua_han(db, now=NOW, retention_days=30) == 1


def test_moc_30_ngay(db_setup):
    db, _ = db_setup
    _them(db, "pending", 29)  # chưa quá hạn
    _them(db, "pending", 31)  # quá hạn
    assert xoa_pii_qua_han(db, now=NOW, retention_days=30) == 1
