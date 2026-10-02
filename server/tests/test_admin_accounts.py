"""HTG-04/05/06 — quản lý tài khoản (mức 2). SQLite in-memory, không cần PostgreSQL.

Phủ: tự đổi mật khẩu (HTG-06) · list/reset/khóa tài khoản + chặn tự khóa (HTG-05) ·
xem tool-key chỉ admin (HTG-04) · phân quyền 403.
"""
from app.config import get_settings


def _login(api, username, password):
    return api.post("/api/auth/login", json={"username": username, "password": password})


def _token(api, username, password):
    return _login(api, username, password).json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


# ── HTG-06: tự đổi mật khẩu ──
def test_doi_mat_khau_thanh_cong(api):
    tok = _token(api, "col1", "col-pass")
    r = api.post("/api/auth/doi-mat-khau", headers=_h(tok),
                 json={"mat_khau_hien_tai": "col-pass", "mat_khau_moi": "col-moi-1"})
    assert r.status_code == 204
    # mật khẩu cũ hết tác dụng, mật khẩu mới đăng nhập được
    assert _login(api, "col1", "col-pass").status_code == 401
    assert _login(api, "col1", "col-moi-1").status_code == 200


def test_doi_mat_khau_sai_hien_tai(api):
    tok = _token(api, "col1", "col-pass")
    r = api.post("/api/auth/doi-mat-khau", headers=_h(tok),
                 json={"mat_khau_hien_tai": "sai", "mat_khau_moi": "x1234"})
    assert r.status_code == 400
    assert _login(api, "col1", "col-pass").status_code == 200  # không đổi


def test_doi_mat_khau_moi_qua_ngan_422(api):
    tok = _token(api, "col1", "col-pass")
    r = api.post("/api/auth/doi-mat-khau", headers=_h(tok),
                 json={"mat_khau_hien_tai": "col-pass", "mat_khau_moi": "a"})
    assert r.status_code == 422


def test_doi_mat_khau_can_dang_nhap(api):
    assert api.post("/api/auth/doi-mat-khau",
                    json={"mat_khau_hien_tai": "x", "mat_khau_moi": "yyyy"}).status_code in (401, 403)


# ── HTG-05: list + reset + khóa ──
def test_list_users_admin_phan_trang(api):
    tok = _token(api, "admin1", "admin-pass")
    r = api.get("/api/admin/users?limit=2&offset=0", headers=_h(tok))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 4          # admin1, op1, col1, col2 (conftest)
    assert len(body["items"]) == 2     # phân trang limit=2


def test_list_users_collector_403(api):
    tok = _token(api, "col1", "col-pass")
    assert api.get("/api/admin/users", headers=_h(tok)).status_code == 403


def test_reset_mat_khau_admin(api):
    tok = _token(api, "admin1", "admin-pass")
    uid = api.post("/api/admin/users", headers=_h(tok),
                   json={"username": "nv9", "password": "pw-cu", "vai_tro": "collector"}).json()["id"]
    r = api.post(f"/api/admin/users/{uid}/reset-mat-khau", headers=_h(tok), json={"password": "pw-moi-1"})
    assert r.status_code == 200
    assert _login(api, "nv9", "pw-cu").status_code == 401
    assert _login(api, "nv9", "pw-moi-1").status_code == 200


def test_reset_mat_khau_collector_403(api):
    tok_admin = _token(api, "admin1", "admin-pass")
    uid = api.post("/api/admin/users", headers=_h(tok_admin),
                   json={"username": "nv10", "password": "pw", "vai_tro": "collector"}).json()["id"]
    tok_col = _token(api, "col1", "col-pass")
    assert api.post(f"/api/admin/users/{uid}/reset-mat-khau", headers=_h(tok_col),
                    json={"password": "pw-moi"}).status_code == 403


def test_admin_khoa_tai_khoan_khac(api):
    tok = _token(api, "admin1", "admin-pass")
    uid = api.post("/api/admin/users", headers=_h(tok),
                   json={"username": "nv11", "password": "pw", "vai_tro": "operator"}).json()["id"]
    r = api.put(f"/api/admin/users/{uid}", headers=_h(tok), json={"is_active": False})
    assert r.status_code == 200 and r.json()["is_active"] is False
    assert _login(api, "nv11", "pw").status_code == 403  # bị khóa


def test_admin_khong_tu_khoa_minh(api):
    tok = _token(api, "admin1", "admin-pass")
    me = api.get("/api/auth/me", headers=_h(tok)).json()
    r = api.put(f"/api/admin/users/{me['id']}", headers=_h(tok), json={"is_active": False})
    assert r.status_code == 400  # chặn tự khóa


# ── HTG-04: tool-key chỉ admin ──
def test_tool_key_admin(api):
    tok = _token(api, "admin1", "admin-pass")
    r = api.get("/api/admin/tool-key", headers=_h(tok))
    assert r.status_code == 200
    assert r.json()["tool_key"] == get_settings().tool_api_key


def test_tool_key_operator_403(api):
    tok = _token(api, "op1", "op-pass")
    assert api.get("/api/admin/tool-key", headers=_h(tok)).status_code == 403


def test_tool_key_collector_403(api):
    tok = _token(api, "col1", "col-pass")
    assert api.get("/api/admin/tool-key", headers=_h(tok)).status_code == 403


def test_tool_key_can_dang_nhap(api):
    assert api.get("/api/admin/tool-key").status_code in (401, 403)
