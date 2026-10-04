"""Phân hệ Đồng bộ CDB — API localhost (SYNC-02 trước; SYNC-01/03 thêm sau).

Ghi vào CSDL ĐÍCH (GPLX_CDB_CSDT) — tách khỏi router Nạp. Gác session như các
router /local/* nghiệp vụ khác (mount kèm require_session ở main.py).
"""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app import config_store, sync_helpers, sync_service
from app.db import sqlserver_conn, sqlserver_cursor_dich, sqlserver_conn_dich, ConfigChuaDay

router = APIRouter(prefix="/local/sync", tags=["sync"])

# 7 mã TT_XuLy phổ biến gán cho hồ sơ sau sync (port sync_tool v2.0). Hằng cố định.
TT_XULY_OPTIONS = [
    {"ma": "01", "ten": "Nhận hồ sơ", "ghi_chu": "Vừa nhập, chưa thu ảnh"},
    {"ma": "02", "ten": "Đã gửi yêu cầu thu ảnh", "ghi_chu": "Chờ VPĐK thu ảnh"},
    {"ma": "03", "ten": "Đã nhận ảnh chân dung", "ghi_chu": "Sẵn sàng Kết xuất DKKH (mặc định)"},
    {"ma": "05", "ten": "Đã gửi BC1", "ghi_chu": "Đã báo cáo 1 lên TW"},
    {"ma": "07", "ten": "Đạt BC1", "ghi_chu": "BC1 duyệt OK"},
    {"ma": "11", "ten": "Đã lập BC2", "ghi_chu": "Đã có kết quả BC2"},
    {"ma": "13", "ten": "Đạt BC2", "ghi_chu": "BC2 duyệt OK"},
]
_VALID_TT = {o["ma"] for o in TT_XULY_OPTIONS}


class TargetIn(BaseModel):
    key: str = ""
    name: str
    database: str

    @field_validator("name", "database")
    @classmethod
    def _khong_rong(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Không được để trống")
        return v.strip()


class OptionsIn(BaseModel):
    tt_xuly_force: str = config_store.SYNC_TT_XULY_MAC_DINH
    update_tong_so_hv: bool = True


class SaveTargetsIn(BaseModel):
    targets: list[TargetIn] = Field(default_factory=list)
    selected: str = ""
    options: OptionsIn = Field(default_factory=OptionsIn)


class TestIn(BaseModel):
    database: str

    @field_validator("database")
    @classmethod
    def _khong_rong(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Chưa nhập tên database")
        return v.strip()


def _sinh_key(name: str, da_dung: set[str]) -> str:
    """Sinh key từ tên hiển thị (chữ thường, ký tự lạ → '_') + bảo đảm duy nhất."""
    base = re.sub(r"[^a-z0-9_]+", "_", name.lower()).strip("_") or "target"
    key, n = base, 1
    while key in da_dung:
        n += 1
        key = f"{base}_{n}"
    return key


@router.get("/targets")
def get_targets() -> dict:
    """Danh sách CSDL đích + CSDL đang chọn + tùy chọn + danh mục TT_XuLy."""
    cfg = config_store.get_sync_config()
    return {**cfg, "tt_xuly_options": TT_XULY_OPTIONS}


@router.put("/targets")
def save_targets(body: SaveTargetsIn) -> dict:
    """Lưu danh sách CSDL đích + CSDL mặc định + tùy chọn (mã hóa cục bộ).

    Tự sinh key cho target chưa có key (UI chỉ nhập tên + database). Xóa khỏi
    danh sách KHÔNG xóa database thật — chỉ gỡ khỏi cấu hình tool."""
    tt = body.options.tt_xuly_force if body.options.tt_xuly_force in _VALID_TT else config_store.SYNC_TT_XULY_MAC_DINH
    da_dung: set[str] = set()
    targets: list[dict] = []
    for t in body.targets:
        key = t.key.strip() if t.key.strip() else _sinh_key(t.name, da_dung)
        if key in da_dung:
            key = _sinh_key(t.name, da_dung)
        da_dung.add(key)
        targets.append({"key": key, "name": t.name, "database": t.database})
    cfg = config_store.save_sync_config(
        targets=targets,
        selected=body.selected.strip(),
        options={"tt_xuly_force": tt, "update_tong_so_hv": body.options.update_tong_so_hv},
    )
    return {**cfg, "tt_xuly_options": TT_XULY_OPTIONS}


@router.post("/targets/test")
def test_target(body: TestIn) -> dict:
    """Thử nối CSDL đích (dùng chung host/user/pass của Nạp) + đếm NguoiLX."""
    try:
        with sqlserver_cursor_dich(body.database) as cur:
            cur.execute("SELECT COUNT(*) AS n FROM dbo.NguoiLX")
            row = cur.fetchone()
            n = row["n"] if isinstance(row, dict) else row[0]
        return {"ok": True, "count": int(n), "message": f"Kết nối OK — {int(n):,} người lái".replace(",", ".")}
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001 — gói lỗi nối thành thông báo cho UI
        return {"ok": False, "count": 0, "message": f"Lỗi kết nối: {e.__class__.__name__}"}


# ========== SYNC-01 (phần đọc: năm/khóa/HV) — task 57 ==========
# Nguồn = CSDL Nạp (GPLX_CSDT, sqlserver_conn). Đích = target đang chọn/được chỉ định.


def _db_dich(target_key: str | None) -> str:
    t = config_store.get_sync_target(target_key)
    if not t or not t.get("database"):
        raise HTTPException(status_code=400, detail="Chưa chọn CSDL đích — vào Quản lý CSDL đích.")
    return t["database"]


def _loi_db(e: Exception) -> HTTPException:
    if isinstance(e, ConfigChuaDay):
        return HTTPException(status_code=400, detail=str(e))
    return HTTPException(status_code=502, detail="Không truy vấn được SQL Server — kiểm kết nối.")


@router.get("/nguon/nam")
def nguon_nam() -> list[int]:
    """Các năm có khóa ở CSDL nguồn (GPLX_CSDT)."""
    try:
        with sqlserver_conn() as conn:
            return sync_helpers.load_years_from_khoa(conn)
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)


@router.get("/nguon/khoa")
def nguon_khoa(nam: int) -> list[dict]:
    """Khóa nguồn theo năm (TrangThai=1)."""
    try:
        with sqlserver_conn() as conn:
            return sync_helpers.load_khoa_hoc_by_year(conn, nam)
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)


@router.get("/dich/nam")
def dich_nam(target_key: str | None = None) -> list[int]:
    """Các năm có khóa ở CSDL đích."""
    db = _db_dich(target_key)
    try:
        with sqlserver_conn_dich(db) as conn:
            return sync_helpers.load_years_from_khoa(conn)
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)


@router.get("/dich/khoa")
def dich_khoa(nam: int, target_key: str | None = None) -> list[dict]:
    """Khóa đích theo năm, kèm cờ `bc1` (đã lập Báo cáo 1 → cảnh báo, phương án B)."""
    db = _db_dich(target_key)
    try:
        with sqlserver_conn_dich(db) as conn:
            return sync_helpers.load_khoa_hoc_by_year(conn, nam, with_bc1=True)
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)


class HocVienIn(BaseModel):
    ma_kh_nguon: str
    target_key: str | None = None


def _fmt(v):
    return v.isoformat() if hasattr(v, "isoformat") else v


@router.post("/hoc-vien")
def hoc_vien(body: HocVienIn) -> dict:
    """HV khóa nguồn + đối chiếu CSDL đích (skip HV đã có) + cờ E1/E2.

    E1: thiếu CCCD (SoCMT rỗng) — sẽ chặn khi sync. E2: trùng CCCD trong chính
    danh sách nguồn — cảnh báo. Trả danh sách cho lưới + số liệu tổng hợp."""
    from collections import Counter

    db = _db_dich(body.target_key)
    try:
        with sqlserver_conn() as cn, sqlserver_conn_dich(db) as cd:
            hv_list = sync_service.load_hoc_vien_nguon(cn, body.ma_kh_nguon)
            so_cmt = [(h.get("SoCMT") or "").strip() for h in hv_list]
            enrich = sync_helpers.enrich_from_db_dich(cd, so_cmt)
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)

    dem = Counter(c for c in so_cmt if c)
    rows, da_co, thieu, trung = [], 0, 0, 0
    for h in hv_list:
        cc = (h.get("SoCMT") or "").strip()
        info = enrich.get(cc)
        e1 = not cc
        e2 = bool(cc) and dem[cc] > 1
        if info:
            da_co += 1
        if e1:
            thieu += 1
        if e2:
            trung += 1
        rows.append({
            "ho_ten": h.get("HoVaTen"),
            "so_cmt": cc,
            "hang_gplx": h.get("HangGPLX"),
            "ma_dk_nguon": h.get("MaDK"),
            "ngay_hs_nguon": _fmt(h.get("NgayNhanHSo")),
            "da_co_dich": bool(info),
            "ma_dk_dich": info["ma_dk"] if info else None,
            "ngay_hs_dich": _fmt(info["ngay_hs_latest"]) if info else None,
            "so_hs_dich": info["so_hs"] if info else None,
            "thieu_cccd": e1,
            "trung_cccd_nguon": e2,
        })
    return {
        "hoc_vien": rows,
        "tong": len(rows),
        "da_co_dich": da_co,
        "se_tao_moi": len(rows) - da_co,
        "thieu_cccd": thieu,
        "trung_cccd_nguon": trung,
    }
