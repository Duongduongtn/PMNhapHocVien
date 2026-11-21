"""TNB-08 task 166 — dựng PDF bằng mẫu Crystal của phần mềm cũ (subprocess giả; 1 test thật tự bỏ qua nếu máy không có)."""
import base64
import subprocess
from pathlib import Path

import pytest

from app import crystal_bc2 as cb
from app import paths
from app import tn_bc2_service as svc


@pytest.fixture
def pm_cu(tmp_path):
    """Thư mục phần mềm cũ giả: có mẫu + 3 dll."""
    d = tmp_path / "GPLX-test"
    (d / "PM1" / "Reports").mkdir(parents=True)
    (d / "PM1" / "Reports" / "rptBaoCao2.rpt").write_bytes(b"rpt")
    for x in cb.DLL_BAT_BUOC:
        (d / x).write_bytes(b"dll")
    return d


@pytest.fixture(autouse=True)
def co_lap(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "DATA_DIR", tmp_path / "data")
    (tmp_path / "data").mkdir()
    monkeypatch.setattr(cb, "_ps32", lambda: Path(__file__))          # "có" PowerShell 32-bit
    monkeypatch.setattr(cb, "_script", lambda: Path(__file__))        # "có" script
    saved = {}
    monkeypatch.setattr(cb.config_store, "load_config", lambda: dict(saved))
    monkeypatch.setattr(cb.config_store, "sua_config", lambda f: f(saved))
    return saved


DL = {"ma_kh": "K1", "ma_bc2": "81/2026", "tieu_de": {"maKH": "K1"}, "dong": [{"HoVaTen": "AN", "GhiChu": "SH lần đầu"}]}


def tep_tam(tmp_path):
    return list((tmp_path / "data").glob("bc2_*"))


def test_kiem_thu_muc(pm_cu, tmp_path):
    assert cb.kiem_thu_muc(pm_cu) == ""
    assert "rptBaoCao2.rpt" in cb.kiem_thu_muc(tmp_path)
    (pm_cu / cb.DLL_BAT_BUOC[0]).unlink()
    assert cb.DLL_BAT_BUOC[0] in cb.kiem_thu_muc(pm_cu)


def test_luu_thu_muc_hop_le_va_sai(pm_cu, tmp_path, co_lap):
    kq = cb.luu_thu_muc(str(pm_cu))
    assert co_lap["gplx_cu_dir"] == str(pm_cu) and kq["thu_muc"] == str(pm_cu) and kq["nguon"] == "da_luu"
    for sai in ("", str(tmp_path / "khong-co"), str(tmp_path)):
        with pytest.raises(svc.LoiNghiepVu) as e:
            cb.luu_thu_muc(sai)
        assert e.value.ma == "thu_muc_khong_hop_le" and e.value.http == 400


def test_dung_pdf_thanh_cong_va_xoa_tep_tam(pm_cu, tmp_path, monkeypatch):
    def chay(cmd, **kw):
        assert "-File" in cmd and cmd[cmd.index("-CrystalDir") + 1] == str(pm_cu)
        Path(cmd[cmd.index("-Pdf") + 1]).write_bytes(b"%PDF-1.4 abc")
        assert Path(cmd[cmd.index("-Json") + 1]).read_text(encoding="utf-8").count("SH lần đầu") == 1
        return subprocess.CompletedProcess(cmd, 0, "OK 12", "")
    monkeypatch.setattr(cb.subprocess, "run", chay)
    assert cb.dung_pdf(DL, thu_muc_pm_cu=str(pm_cu)).startswith(b"%PDF")
    assert tep_tam(tmp_path) == []


def test_thieu_phan_mem_cu_409(tmp_path, monkeypatch):
    monkeypatch.setattr(cb, "tu_do", lambda: [])
    with pytest.raises(svc.LoiNghiepVu) as e:
        cb.dung_pdf(DL)
    assert (e.value.ma, e.value.http) == ("chua_co_phan_mem_cu", 409) and tep_tam(tmp_path) == []


def test_thieu_powershell_32_bit_409(pm_cu, monkeypatch):
    monkeypatch.setattr(cb, "_ps32", lambda: Path("Z:/khong/co.exe"))
    with pytest.raises(svc.LoiNghiepVu) as e:
        cb.dung_pdf(DL, thu_muc_pm_cu=str(pm_cu))
    assert e.value.ma == "chua_co_phan_mem_cu"


def test_qua_gio_504_va_xoa_tep_tam(pm_cu, tmp_path, monkeypatch):
    def chay(cmd, **kw):
        Path(cmd[cmd.index("-Json") + 1]).exists()
        raise subprocess.TimeoutExpired(cmd, 60)
    monkeypatch.setattr(cb.subprocess, "run", chay)
    with pytest.raises(svc.LoiNghiepVu) as e:
        cb.dung_pdf(DL, thu_muc_pm_cu=str(pm_cu))
    assert (e.value.ma, e.value.http) == ("dung_ban_in_qua_lau", 504) and tep_tam(tmp_path) == []


def test_loi_crystal_502_gon_va_xoa_tep_tam(pm_cu, tmp_path, monkeypatch):
    monkeypatch.setattr(cb.subprocess, "run", lambda cmd, **kw: subprocess.CompletedProcess(
        cmd, 1, "", "Error in formula  Khoa:\n" + "x" * 900))
    with pytest.raises(svc.LoiNghiepVu) as e:
        cb.dung_pdf(DL, thu_muc_pm_cu=str(pm_cu))
    assert (e.value.ma, e.value.http) == ("dung_ban_in_loi", 502) and len(e.value.noi_dung) < 400
    assert tep_tam(tmp_path) == []


def test_pdf_rong_la_loi(pm_cu, tmp_path, monkeypatch):
    monkeypatch.setattr(cb.subprocess, "run", lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "OK", ""))
    with pytest.raises(svc.LoiNghiepVu) as e:
        cb.dung_pdf(DL, thu_muc_pm_cu=str(pm_cu))
    assert e.value.ma == "dung_ban_in_loi" and tep_tam(tmp_path) == []


# ── Router: xem-truoc ──
class _Cur:
    pass


@pytest.fixture
def client(monkeypatch, auth_headers):
    from contextlib import contextmanager
    from fastapi.testclient import TestClient
    from app.main import app
    from app.routers import tn_bc2 as router
    from app import tn_bc2_in as ib

    hs = [{"ma_dk": "D1", "ma_nd": 1}, {"ma_dk": "D2", "ma_nd": 6}]
    st = {"hs": hs}

    @contextmanager
    def _cur(as_dict=True):
        yield _Cur()

    monkeypatch.setattr(router, "sqlserver_cursor", _cur)
    monkeypatch.setattr(ib, "du_lieu_ban_in", lambda cur, ma, **kw: {"ma_bc2": ma, "hoc_vien": st["hs"], "ma_kh": "K1",
                                                                       "tieu_de": {}, "so_chon_lai": 0})
    monkeypatch.setattr(ib, "du_lieu_crystal", lambda dl: {"dong": []})
    c = TestClient(app)

    class _C:
        state = st
        def post(self, u, **kw): return c.post(u, headers=auth_headers, **kw)
        def get(self, u, **kw): return c.get(u, headers=auth_headers, **kw)
        def put(self, u, **kw): return c.put(u, headers=auth_headers, **kw)
    return _C()


def test_router_xem_truoc_tra_pdf(client, monkeypatch):
    from app.routers import tn_bc2 as router
    monkeypatch.setattr(router.crystal_bc2, "dung_pdf", lambda dl: b"%PDF-1.4 x")
    r = client.post("/local/tnbc2/bc2/81/2026/xem-truoc")
    # JSON base64, không application/pdf (phần mềm tải file của trình duyệt sẽ bắt phản hồi PDF)
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/json")
    assert base64.b64decode(r.json()["pdf_base64"]).startswith(b"%PDF")
    assert r.headers["cache-control"] == "no-store"


def test_router_xem_truoc_chan_khi_con_hv_chua_co_phan_thi(client):
    client.state["hs"] = [{"ma_dk": "D1", "ma_nd": 1}, {"ma_dk": "D2", "ma_nd": None}]
    r = client.post("/local/tnbc2/bc2/81/2026/xem-truoc")
    assert r.status_code == 409 and r.json()["detail"]["ma"] == "con_hv_can_chon" and r.json()["detail"]["ds_ma_dk"] == ["D2"]
    client.state["hs"] = []
    assert client.post("/local/tnbc2/bc2/81/2026/xem-truoc").json()["detail"]["ma"] == "bc2_khong_co_hoc_vien"


def test_router_xem_truoc_thieu_phan_mem_cu_409(client, monkeypatch):
    from app.routers import tn_bc2 as router
    def loi(dl):
        raise svc.LoiNghiepVu("chua_co_phan_mem_cu", "Máy này chưa dựng được bản in", 409)
    monkeypatch.setattr(router.crystal_bc2, "dung_pdf", loi)
    r = client.post("/local/tnbc2/bc2/81/2026/xem-truoc")
    assert r.status_code == 409 and r.json()["detail"]["ma"] == "chua_co_phan_mem_cu"


def test_router_gplx_cu_dir(client, pm_cu):
    assert client.get("/local/tnbc2/gplx-cu-dir").status_code == 200
    r = client.put("/local/tnbc2/gplx-cu-dir", json={"thu_muc": str(pm_cu)})
    assert r.status_code == 200 and r.json()["thu_muc"] == str(pm_cu)
    r = client.put("/local/tnbc2/gplx-cu-dir", json={"thu_muc": "Z:/khong-co"})
    assert r.status_code == 400 and r.json()["detail"]["ma"] == "thu_muc_khong_hop_le"


# ── Thật: chỉ chạy khi máy có phần mềm cũ + PowerShell 32-bit (máy dev/CSĐT) ──
def test_dung_pdf_that_neu_co_phan_mem_cu(monkeypatch, tmp_path):
    monkeypatch.undo()
    monkeypatch.setattr(paths, "DATA_DIR", tmp_path)
    tm = next(iter(cb.tu_do()), "")
    if not tm or not cb._ps32().is_file():
        pytest.skip("Máy không có phần mềm cũ / PowerShell 32-bit")
    dl = {"ma_kh": "70004K26B0107", "ma_bc2": "99/2026",
          "tieu_de": {"maKH": "70004K26B0107", "TenCSDT": "Trung Tâm", "CoQuanQL": "Sở", "LanhDao": "", "HangGPLX": "B",
                      "MucTieuDT": "", "NgayKG": "2026-07-30T00:00:00", "NgayBG": "2026-09-15T00:00:00",
                      "ThoiGianDT": 48, "TongSoHV": 1, "SoHocVienHienCo": 1},
          "dong": [{"HoVaTen": "NGUYỄN VĂN AN", "NgaySinh": "01/01/2000", "SoCMT": "070200000001", "NoiCT": " Xã A",
                    "GiayCNSK": True, "HangGPLXDaCo": "", "SoNamLX": 0, "SoKmLXAnToan": 0, "CCTN": None,
                    "GhiChu": "SH lại H + Đ"}]}
    pdf = cb.dung_pdf(dl, thu_muc_pm_cu=tm)
    assert pdf.startswith(b"%PDF") and len(pdf) > 5000
    import pdfplumber, io
    with pdfplumber.open(io.BytesIO(pdf)) as p:
        txt = p.pages[0].extract_text()
    assert "DANH SÁCH THÍ SINH DỰ SÁT HẠCH" in txt and "NGUYỄN VĂN AN" in txt and "SH lại H + Đ" in txt.replace("\n", " ")


# ── Soát xuất file (21/11/2026): an toàn đường dẫn/dll, lỗi không lộ dữ liệu, chờ lượt, tệp tạm ──
@pytest.mark.parametrize("t", ["\\may-la\chia-se\GPLX", "//may-la/chia-se", "GPLX-test", "..\GPLX", ""])
def test_duong_dan_unc_tuong_doi_bi_tu_choi(t, pm_cu):
    assert cb.duong_dan_an_toan(t) is False
    if t:
        with pytest.raises(svc.LoiNghiepVu) as e:
            cb.luu_thu_muc(t)
        assert e.value.ma == "thu_muc_khong_hop_le"


def test_o_usb_hoac_o_mang_khong_duoc_dung(pm_cu, monkeypatch):
    monkeypatch.setattr(cb, "_o_co_dinh", lambda o: False)           # ổ cắm ngoài
    assert cb.duong_dan_an_toan(str(pm_cu)) is False
    with pytest.raises(svc.LoiNghiepVu):
        cb.luu_thu_muc(str(pm_cu))
    with pytest.raises(svc.LoiNghiepVu) as e:                        # cả khi truyền thẳng vào dung_pdf
        cb.dung_pdf(DL, thu_muc_pm_cu=str(pm_cu))
    assert e.value.ma == "chua_co_phan_mem_cu"
    assert cb.tu_do() == []


def test_thong_bao_loi_khong_lo_du_lieu_crystal(pm_cu, monkeypatch):
    monkeypatch.setattr(cb.subprocess, "run", lambda cmd, **kw: subprocess.CompletedProcess(
        cmd, 1, "", r"Couldn't store <NGUYỄN VĂN AN> in SoNamLX Column at D:\GPLX\in_bc2.ps1 070200000001"))
    with pytest.raises(svc.LoiNghiepVu) as e:
        cb.dung_pdf(DL, thu_muc_pm_cu=str(pm_cu))
    nd = e.value.noi_dung
    assert "NGUYỄN" not in nd and "070200000001" not in nd and "\\" not in nd and e.value.du_lieu == {"ma_thoat": 1}


def test_goi_powershell_ma_hoa_utf8_va_khong_doi_stdin(pm_cu, monkeypatch):
    thay = {}
    def chay(cmd, **kw):
        thay.update(kw)
        Path(cmd[cmd.index("-Pdf") + 1]).write_bytes(b"%PDF-1")
        return subprocess.CompletedProcess(cmd, 0, "OK", "")
    monkeypatch.setattr(cb.subprocess, "run", chay)
    cb.dung_pdf(DL, thu_muc_pm_cu=str(pm_cu))
    assert thay["encoding"] == "utf-8" and thay["errors"] == "replace" and thay["stdin"] == subprocess.DEVNULL


def test_cho_luot_qua_han_409_va_khong_tao_tep_tam(pm_cu, tmp_path, monkeypatch):
    assert cb._KHOA.acquire(timeout=1)
    try:
        with pytest.raises(svc.LoiNghiepVu) as e:
            cb.dung_pdf(DL, thu_muc_pm_cu=str(pm_cu), cho_luot=0.05)
        assert (e.value.ma, e.value.http) == ("ban_in_dang_ban", 409)
        assert tep_tam(tmp_path) == []                                # tệp (họ tên) không nằm chờ trên đĩa
    finally:
        cb._KHOA.release()


def test_quet_thu_muc_tam_cu_va_giu_thu_muc_moi(tmp_path):
    import os, time
    cu, moi = tmp_path / "data" / "bc2_cu", tmp_path / "data" / "bc2_moi"
    for d in (cu, moi):
        d.mkdir(parents=True)
        (d / "du_lieu.json").write_text("{}", encoding="utf-8")
    quá_cu = time.time() - cb.TUOI_TEP_TAM_TOI_DA - 60
    os.utime(cu, (quá_cu, quá_cu))
    cb.quet_tep_tam_cu()
    assert not cu.exists() and moi.exists()


def test_json_decimal_thanh_so_khong_phai_chuoi():
    import json
    from decimal import Decimal
    j = json.loads(json.dumps({"a": Decimal("0"), "b": Decimal("1.5")}, default=cb._mac_dinh_json))
    assert j == {"a": 0, "b": 1.5}
