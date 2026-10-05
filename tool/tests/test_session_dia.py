"""DGT-04 (task 70) — phiên lưu đĩa DPAPI + heartbeat làm mới token (mức 2).

SESSION_FILE đã được conftest trỏ vào thư mục tạm (autouse) nên không đụng config thật.
Trên Windows dùng DPAPI thật; ngoài Windows fallback Fernet — cả hai đều round-trip được.
"""
from app import dpapi, session, vps


def _phien(**kw):
    base = dict(username="op1", ho_ten="NV Nạp", vai_tro="operator",
                vps_token="jwt-cu", refresh_token="rt-1")
    base.update(kw)
    return session.Phien(**base)


def test_dpapi_roundtrip():
    data = "phiên bí mật — café 2026".encode("utf-8")
    blob = dpapi.bao_ve(data)
    assert blob != data
    assert dpapi.giai_ma(blob) == data


def test_luu_nap_phien_roundtrip():
    session._phien_theo_token.clear()
    session._luu_phien_dia("tok-1", _phien())
    session._phien_theo_token.clear()          # giả lập tắt tool (mất RAM)
    session.nap_phien_tu_dia()                  # mở lại → vào thẳng
    p = session._phien_theo_token.get("tok-1")
    assert p is not None
    assert p.username == "op1" and p.vai_tro == "operator"
    assert p.vps_token == "jwt-cu" and p.refresh_token == "rt-1"
    session._phien_theo_token.clear()


def test_nap_phien_file_hong_bo_qua():
    session._phien_theo_token.clear()
    session.SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    session.SESSION_FILE.write_bytes(b"rac-khong-giai-ma-duoc")
    session.nap_phien_tu_dia()                  # không ném, không nạp
    assert session._phien_theo_token == {}
    assert not session.SESSION_FILE.exists()    # file hỏng bị dọn → về đăng nhập


def test_nap_phien_khong_co_file():
    session._phien_theo_token.clear()
    session.nap_phien_tu_dia()
    assert session._phien_theo_token == {}


def test_lam_moi_phien_doi_token(monkeypatch):
    session._phien_theo_token.clear()
    session._phien_theo_token["t"] = _phien(vps_token="cu", refresh_token="rt-cu")
    monkeypatch.setattr(vps, "doi_refresh",
                        lambda rt: {"access_token": "moi", "refresh_token": "rt-moi"})
    assert session.lam_moi_phien("t") is True
    p = session._phien_theo_token["t"]
    assert p.vps_token == "moi" and p.refresh_token == "rt-moi"
    session._phien_theo_token.clear()


def test_lam_moi_phien_bi_thu_hoi_401(monkeypatch):
    session._phien_theo_token.clear()
    session._phien_theo_token["t"] = _phien(refresh_token="rt-cu")

    def _raise(rt):
        raise vps.VpsLoi("thu hồi", status=401)

    monkeypatch.setattr(vps, "doi_refresh", _raise)
    assert session.lam_moi_phien("t") is False
    assert "t" not in session._phien_theo_token   # phiên bị đá
    session._phien_theo_token.clear()


def test_lam_moi_phien_loi_mang_giu_phien(monkeypatch):
    session._phien_theo_token.clear()
    session._phien_theo_token["t"] = _phien(vps_token="cu", refresh_token="rt-cu")

    def _raise(rt):
        raise vps.VpsLoi("mất mạng", status=None)

    monkeypatch.setattr(vps, "doi_refresh", _raise)
    assert session.lam_moi_phien("t") is True     # lỗi tạm → giữ phiên
    assert session._phien_theo_token["t"].vps_token == "cu"
    session._phien_theo_token.clear()


def test_lam_moi_phien_chua_co_refresh():
    session._phien_theo_token.clear()
    session._phien_theo_token["t"] = _phien(refresh_token=None)
    assert session.lam_moi_phien("t") is True      # VPS chưa cấp → giữ nguyên
    session._phien_theo_token.clear()


def test_dang_xuat_xoa_phien_dia(monkeypatch):
    session._phien_theo_token.clear()
    phien = _phien(refresh_token="rt")
    session._phien_theo_token["t"] = phien
    session._luu_phien_dia("t", phien)
    assert session.SESSION_FILE.exists()
    monkeypatch.setattr(vps, "logout_refresh", lambda a, b: None)
    session.dang_xuat("t")
    assert "t" not in session._phien_theo_token
    assert not session.SESSION_FILE.exists()
    session._phien_theo_token.clear()
