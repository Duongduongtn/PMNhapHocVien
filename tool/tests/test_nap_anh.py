"""QLY-05 — nạp/thay ảnh cho HV đã có (mức 2, không cần DB thật).

Unit: hàm ghi ảnh hướng A `ghi_anh_update` (ghi file + dựng câu UPDATE 5 cột) với cursor giả +
thư mục tạm; kiểm cả ghi mới lẫn ghi đè. Gate/validate tầng API. Ghi prod thật kiểm bằng tay/live.
"""
from datetime import datetime

from fastapi.testclient import TestClient

from app.main import app
from app.nap import ghi_anh_update

client = TestClient(app)


class FakeCursor:
    """Cursor giả: ghi lại (sql, params) để kiểm câu UPDATE mà không cần SQL Server.

    fetchone() trả TT_XuLy hiện tại cho SELECT mà ghi_anh_update chạy trước UPDATE (CHANGES #22).
    """

    def __init__(self, tt_xuly="01"):
        self.calls = []
        self._tt = tt_xuly

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return {"TT_XuLy": self._tt}


# ---- Unit: ghi ảnh hướng A ----
def test_ghi_anh_update_ghi_file_moi(tmp_path):
    cur = FakeCursor()
    now = datetime(2026, 10, 2, 9, 30)
    jp2 = b"\x00\x00\x00\x0cjP  fake-jp2"
    duong_dan = ghi_anh_update(cur, "MADK-1", "70004K26B010", jp2, str(tmp_path), now, "NV Nạp")

    f = tmp_path / "70004K26B010" / "MADK-1.jp2"
    assert f.read_bytes() == jp2                       # file ghi đúng chỗ (tên = MaDK)
    assert duong_dan == str(f)
    upd = [c for c in cur.calls if "UPDATE NguoiLX_HoSo" in c[0]]
    assert len(upd) == 1
    sql, params = upd[0]
    assert "TT_XuLy=%s" in sql                          # TT_XuLy parameterized (CHANGES #22)
    assert params == (str(f), "03", now, "NV Nạp", "MADK-1")  # HV '01' → nâng '03', WHERE MaDK


def test_ghi_anh_update_ghi_de_anh_cu(tmp_path):
    folder = tmp_path / "70004K26B010"
    folder.mkdir(parents=True)
    (folder / "MADK-1.jp2").write_bytes(b"anh-cu")
    cur = FakeCursor()
    ghi_anh_update(cur, "MADK-1", "70004K26B010", b"anh-moi", str(tmp_path), datetime.now(), "NV")
    assert (folder / "MADK-1.jp2").read_bytes() == b"anh-moi"  # ghi đè (thay ảnh)


# ---- Gate + validate tầng API (không chạm DB) ----
def test_nap_anh_chua_dang_nhap_401():
    assert client.post("/local/ho-so/nap-anh?ma_dk=X", json={"jp2_b64": "YWJj"}).status_code == 401


def test_nap_anh_thieu_ma_dk_422(auth_headers):
    r = client.post("/local/ho-so/nap-anh", headers=auth_headers, json={"jp2_b64": "YWJj"})
    assert r.status_code == 422


def test_nap_anh_jp2_rong_422(auth_headers):
    r = client.post("/local/ho-so/nap-anh?ma_dk=X", headers=auth_headers, json={"jp2_b64": "   "})
    assert r.status_code == 422


def test_nap_anh_base64_sai_400(auth_headers):
    # base64 không hợp lệ → 400 trước khi chạm DB.
    r = client.post("/local/ho-so/nap-anh?ma_dk=X", headers=auth_headers, json={"jp2_b64": "@@@khong-phai-base64@@@"})
    assert r.status_code == 400


# ---- Edge case: retry UPDATE theo MaDK (mock DB, không cần SQL Server) ----
class _FakeCur:
    def __init__(self, rows):
        self._rows = list(rows)

    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return self._rows.pop(0)


class _FakeConn:
    """Context manager giả thay sqlserver_conn: trả sẵn MaKhoaHoc + IMG_PATH cho 2 SELECT đầu."""

    def __init__(self, rows):
        self._cur = _FakeCur(rows)

    def cursor(self, as_dict=False):
        return self._cur

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_nap_anh_retry_khi_update_loi(auth_headers, monkeypatch):
    rows = [{"MaKhoaHoc": "70004K26B010"}, {"GiaTriTS": "D:/ANH"}]
    monkeypatch.setattr("app.routers.hoso.sqlserver_conn", lambda **k: _FakeConn(rows))
    calls = {"n": 0}

    def fake_ghi(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("UPDATE lỗi tạm thời")  # lần 1 lỗi
        return "D:/ANH/70004K26B010/MADK-1.jp2"         # lần 2 (retry) OK

    monkeypatch.setattr("app.routers.hoso.ghi_anh_update", fake_ghi)
    r = client.post("/local/ho-so/nap-anh?ma_dk=MADK-1", headers=auth_headers, json={"jp2_b64": "YWJj"})
    assert r.status_code == 200 and r.json()["co_anh"] is True
    assert calls["n"] == 2  # đã thử lại UPDATE theo MaDK (EC §11.5)


def test_nap_anh_file_khoa_khong_retry_409(auth_headers, monkeypatch):
    rows = [{"MaKhoaHoc": "70004K26B010"}, {"GiaTriTS": "D:/ANH"}]
    monkeypatch.setattr("app.routers.hoso.sqlserver_conn", lambda **k: _FakeConn(rows))
    calls = {"n": 0}

    def fake_ghi(*a, **k):
        calls["n"] += 1
        raise PermissionError("file đang bị khóa")

    monkeypatch.setattr("app.routers.hoso.ghi_anh_update", fake_ghi)
    r = client.post("/local/ho-so/nap-anh?ma_dk=MADK-1", headers=auth_headers, json={"jp2_b64": "YWJj"})
    assert r.status_code == 409          # báo đóng app cũ
    assert calls["n"] == 1               # KHÔNG thử lại khi file bị khóa
