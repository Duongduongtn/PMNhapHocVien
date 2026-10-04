"""HTG-03 — bộ lọc & xóa PII thủ công (mức 2). SQLite in-memory, không cần PostgreSQL.

Phủ: lọc theo trạng thái · lọc theo khoảng ngày (quy đổi biên ngày VN→UTC) · phân trang ·
xóa tay hard-delete + unlink ảnh + ghi audit 'xoa_pii_tay' · 404 · phân quyền 403 · 422.
"""
from datetime import datetime, timezone

from sqlalchemy import select

from app.models.ho_so import AuditLog, HoSoThuThap


def _login(api, username, password):
    return api.post("/api/auth/login", json={"username": username, "password": password})


def _token(api, username, password):
    return _login(api, username, password).json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def _utc(y, mo, d, h=12, mi=0):
    return datetime(y, mo, d, h, mi, tzinfo=timezone.utc)


def _seed(db, **kw):
    hs = HoSoThuThap(**kw)
    db.add(hs)
    db.commit()
    db.refresh(hs)
    return hs


# ── Lọc ──
def test_loc_tat_ca_phan_trang(api, db_setup):
    db, _ = db_setup
    for i in range(5):
        _seed(db, ho_ten=f"HV {i}", so_cccd=f"07020000000{i}", trang_thai="pending")
    tok = _token(api, "admin1", "admin-pass")
    r = api.get("/api/admin/ho-so?limit=2&offset=0", headers=_h(tok))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert set(body["items"][0]) >= {"uuid", "ho_ten", "so_cccd", "noi_tt_raw", "trang_thai", "co_anh", "created_at"}


def test_loc_theo_trang_thai(api, db_setup):
    db, _ = db_setup
    _seed(db, ho_ten="A", trang_thai="pending")
    _seed(db, ho_ten="B", trang_thai="imported")
    _seed(db, ho_ten="C", trang_thai="imported")
    tok = _token(api, "admin1", "admin-pass")
    r = api.get("/api/admin/ho-so?trang_thai=imported", headers=_h(tok))
    assert r.status_code == 200
    assert r.json()["total"] == 2
    assert all(it["trang_thai"] == "imported" for it in r.json()["items"])


def test_loc_tra_ma_dk_va_locked_at(api, db_setup):
    """QLY-09: list admin trả thêm ma_dk (ca ① phantom) + locked_at (ca ③ treo)."""
    db, _ = db_setup
    _seed(db, ho_ten="Imp", trang_thai="imported", ma_dk="MDK-1")
    tok = _token(api, "admin1", "admin-pass")
    it = api.get("/api/admin/ho-so?trang_thai=imported", headers=_h(tok)).json()["items"][0]
    assert "ma_dk" in it and it["ma_dk"] == "MDK-1"
    assert "locked_at" in it  # có field (giá trị None khi không khóa)


def test_loc_trang_thai_sai_422(api):
    tok = _token(api, "admin1", "admin-pass")
    assert api.get("/api/admin/ho-so?trang_thai=linh_tinh", headers=_h(tok)).status_code == 422


def test_loc_theo_ngay_bien_mui_gio_vn(api, db_setup):
    """Lọc ngày gửi 15/09/2026 (giờ VN) phải gộp bản rìa ngày và loại bản thuộc 16/09 VN."""
    db, _ = db_setup
    # 14/09 18:00 UTC = 15/09 01:00 VN → thuộc 15/09
    a = _seed(db, ho_ten="Rìa đầu", created_at=_utc(2026, 9, 14, 18, 0), trang_thai="pending")
    # 15/09 10:00 UTC = 15/09 17:00 VN → thuộc 15/09
    b = _seed(db, ho_ten="Giữa ngày", created_at=_utc(2026, 9, 15, 10, 0), trang_thai="pending")
    # 15/09 17:30 UTC = 16/09 00:30 VN → KHÔNG thuộc 15/09
    c = _seed(db, ho_ten="Qua ngày", created_at=_utc(2026, 9, 15, 17, 30), trang_thai="pending")
    tok = _token(api, "admin1", "admin-pass")
    r = api.get("/api/admin/ho-so?tu_ngay=2026-09-15&den_ngay=2026-09-15", headers=_h(tok))
    assert r.status_code == 200
    ten = {it["ho_ten"] for it in r.json()["items"]}
    assert ten == {"Rìa đầu", "Giữa ngày"}
    assert "Qua ngày" not in ten
    assert str(c.uuid)  # giữ tham chiếu cho rõ ý, c cố ý nằm ngoài


def test_loc_ngay_sai_dinh_dang_422(api):
    tok = _token(api, "admin1", "admin-pass")
    assert api.get("/api/admin/ho-so?tu_ngay=15/09/2026", headers=_h(tok)).status_code == 422


def test_loc_collector_403(api):
    tok = _token(api, "col1", "col-pass")
    assert api.get("/api/admin/ho-so", headers=_h(tok)).status_code == 403


def test_loc_operator_403(api):
    tok = _token(api, "op1", "op-pass")
    assert api.get("/api/admin/ho-so", headers=_h(tok)).status_code == 403


# ── Xóa tay ──
def test_xoa_tay_kem_anh_va_audit(api, db_setup, tmp_path):
    db, _ = db_setup
    anh = tmp_path / "anh_tho.jpg"
    anh.write_bytes(b"fake-jpeg")
    hs = _seed(db, ho_ten="Xóa tôi", so_cccd="070200000099", anh_tho_path=str(anh), trang_thai="imported")
    tok = _token(api, "admin1", "admin-pass")

    r = api.delete(f"/api/admin/ho-so/{hs.uuid}", headers=_h(tok))
    assert r.status_code == 200 and r.json()["da_xoa"] is True

    db.expunge_all()
    assert db.get(HoSoThuThap, hs.uuid) is None          # bản ghi mất
    assert not anh.exists()                                # ảnh thô bị unlink
    log = db.scalars(select(AuditLog).where(AuditLog.uuid_hs == hs.uuid)).all()
    assert len(log) == 1 and log[0].hanh_dong == "xoa_pii_tay"  # có dấu vết, không ghi CCCD
    assert log[0].chi_tiet is None


def test_xoa_tay_khong_co_anh_khong_loi(api, db_setup):
    db, _ = db_setup
    hs = _seed(db, ho_ten="Không ảnh", trang_thai="pending")
    tok = _token(api, "admin1", "admin-pass")
    assert api.delete(f"/api/admin/ho-so/{hs.uuid}", headers=_h(tok)).status_code == 200
    db.expunge_all()
    assert db.get(HoSoThuThap, hs.uuid) is None


def test_xoa_tay_khong_ton_tai_404(api):
    tok = _token(api, "admin1", "admin-pass")
    r = api.delete("/api/admin/ho-so/00000000-0000-0000-0000-000000000000", headers=_h(tok))
    assert r.status_code == 404


def test_xoa_tay_collector_403(api, db_setup):
    db, _ = db_setup
    hs = _seed(db, ho_ten="Ai đó", trang_thai="pending")
    tok = _token(api, "col1", "col-pass")
    assert api.delete(f"/api/admin/ho-so/{hs.uuid}", headers=_h(tok)).status_code == 403
    db.expunge_all()
    assert db.get(HoSoThuThap, hs.uuid) is not None  # không bị xóa
