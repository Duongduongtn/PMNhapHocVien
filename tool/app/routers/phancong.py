"""Phân công GV – xe (PCG) — router tool máy CSDT. TDD §11E.

Task 86: CHỈ ĐỌC + kiểm (`POST /kiem-tra` không ghi). Ghi (`/ghi`) thêm ở task 87.
Mount kèm `require_session` ở main.py (collector không có session cục bộ → 403).
Mọi truy vấn qua `sqlserver_conn_dich(target_key)` — KHÔNG đụng DB Nạp.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from fastapi import Depends

from app import phancong_nhat_ky as nhat_ky
from app import phancong_service as svc
from app.db import ConfigChuaDay, sqlserver_conn_dich
from app.routers.sync import _db_dich, _loi_db
from app.session import Phien, require_session

router = APIRouter(prefix="/local/phancong", tags=["phancong"])


class PcIn(BaseModel):
    id: int | str | None = None
    ma: str
    mon: list[int] = Field(default_factory=list)
    tu: str = ""
    den: str = ""


class GhepIn(BaseModel):
    id: int | str | None = None   # MaLichSD nếu dòng đã có ở CDB; id tạm ("n1") nếu mới
    ma: str
    xe: str = ""
    tu: str = ""
    den: str = ""
    dia_diem: str = ""


class BanNhapIn(BaseModel):
    ma_kh: str
    gv_khoa: list[str] = Field(default_factory=list, max_length=300)
    pc: list[PcIn] = Field(default_factory=list, max_length=1000)
    xe_khoa: list[str] = Field(default_factory=list, max_length=300)
    ghep: list[GhepIn] = Field(default_factory=list, max_length=300)


def _csdt(conn) -> str:
    ma = svc.ma_csdt(conn)
    if not ma:
        raise HTTPException(status_code=400, detail="CSDL đích thiếu MA_CSDT trong QTHT_ThamSoHT.")
    return ma


@router.get("/khoa")
def ds_khoa(q: str = "", target_key: str | None = None) -> list[dict]:
    """Combobox khóa của CSĐT hiện tại (kèm hạng, ngày KG→BG, cờ đã gửi DKKH)."""
    db = _db_dich(target_key)
    try:
        with sqlserver_conn_dich(db) as conn:
            return svc.ds_khoa(conn, _csdt(conn), q)
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)


@router.get("/mon")
def ds_mon(target_key: str | None = None) -> list[dict]:
    db = _db_dich(target_key)
    try:
        with sqlserver_conn_dich(db) as conn:
            return svc.ds_mon(conn)
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)


@router.get("/khoa/{ma_kh}")
def hien_trang(ma_kh: str, target_key: str | None = None) -> dict:
    """Hiện trạng 1 khóa: thông tin khóa + GV/phân công/xe/ghép xe (kèm id dòng CDB)."""
    db = _db_dich(target_key)
    try:
        with sqlserver_conn_dich(db) as conn:
            ma = _csdt(conn)
            kh = svc.doc_khoa(conn, ma, ma_kh)
            if kh is None:
                raise HTTPException(status_code=404, detail="Không tìm thấy khóa học ở CSDL đích.")
            return {"khoa": kh, **svc.hien_trang(conn, ma_kh, svc.ds_mon(conn))}
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)


@router.get("/giao-vien")
def ds_giao_vien(ma_kh: str = Query(..., min_length=1), target_key: str | None = None) -> dict:
    """Danh mục GV của CSĐT + "bận" ở các khóa khác (để hiện huy hiệu "đang dạy khóa Y")."""
    db = _db_dich(target_key)
    try:
        with sqlserver_conn_dich(db) as conn:
            ma = _csdt(conn)
            ds = svc.ds_giao_vien(conn, ma)
            ban_gv, _ = svc.ban_khac(conn, ma_kh, [g["ma"] for g in ds], [])
            for g in ds:
                g["ban"] = ban_gv.get(g["ma"], [])
            return {"giao_vien": ds}
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)


@router.get("/xe")
def ds_xe(ma_kh: str = Query(..., min_length=1), target_key: str | None = None) -> dict:
    db = _db_dich(target_key)
    try:
        with sqlserver_conn_dich(db) as conn:
            ma = _csdt(conn)
            ds = svc.ds_xe(conn, ma)
            _, ban_xe = svc.ban_khac(conn, ma_kh, [], [x["bs"] for x in ds])
            for x in ds:
                x["ban"] = ban_xe.get(x["bs"], [])
            return {"xe": ds}
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)


@router.post("/kiem-tra")
def kiem_tra(body: BanNhapIn, target_key: str | None = None) -> dict:
    """Kiểm bản nháp theo luật CDB — KHÔNG ghi. UI gọi (debounce) để hiện lỗi sống;
    `/ghi` (task 87) kiểm lại lần cuối trước khi ghi."""
    db = _db_dich(target_key)
    try:
        with sqlserver_conn_dich(db) as conn:
            return svc.kiem_tra(conn, _csdt(conn), body.ma_kh, body.model_dump())
    except KeyError:
        raise HTTPException(status_code=404, detail="Không tìm thấy khóa học ở CSDL đích.")
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)


@router.post("/goi-y-ghep-xe")
def goi_y_ghep_xe(body: BanNhapIn, target_key: str | None = None) -> dict:
    """Gợi ý xe cho GV thực hành chưa có xe (xem trước — KHÔNG ghi gì)."""
    db = _db_dich(target_key)
    try:
        with sqlserver_conn_dich(db) as conn:
            return svc.goi_y_ghep_xe(conn, _csdt(conn), body.ma_kh, body.model_dump())
    except KeyError:
        raise HTTPException(status_code=404, detail="Không tìm thấy khóa học ở CSDL đích.")
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)


class GhiIn(BanNhapIn):
    da_xem_canh_bao: bool = False
    xac_nhan_csdl_that: bool = False


def _chua_co_csdt():
    raise HTTPException(status_code=400, detail="CSDL đích thiếu MA_CSDT trong QTHT_ThamSoHT.")


@router.post("/ghi")
def ghi(body: GhiIn, target_key: str | None = None, phien: Phien = Depends(require_session)) -> dict:
    """Ghi bản nháp vào CDB đích. Server tự suy ra thay đổi, KIỂM LẠI toàn bộ luật (không tin
    client), 409 khi còn ⛔ hoặc ⚠ chưa xác nhận, rồi ghi từng dòng bằng SP (không SP xóa lan).
    Lỗi giữa chừng → 200 `ok=false` kèm `da_ghi`/`chua_ghi` để làm tiếp."""
    db = _db_dich(target_key)
    try:
        with sqlserver_conn_dich(db, autocommit=True) as conn:
            return svc.ghi(conn, svc.ma_csdt(conn) or _chua_co_csdt(), body.ma_kh,
                           body.model_dump(exclude={"da_xem_canh_bao", "xac_nhan_csdl_that"}), phien.username,
                           body.da_xem_canh_bao, body.xac_nhan_csdl_that, nhat_ky)
    except svc.LoiNghiepVu as e:
        raise HTTPException(status_code=e.http, detail={"loi": e.ma, "thong_bao": e.thong_bao, **e.du_lieu})
    except KeyError:
        raise HTTPException(status_code=404, detail="Không tìm thấy khóa học ở CSDL đích.")
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)


@router.get("/nhat-ky")
def nhat_ky_gan_day(ma_kh: str | None = None) -> list[dict]:
    """Nhật ký ghi gần đây (sqlite phía tool): ai · lúc nào · khóa · thay đổi · kết quả."""
    return nhat_ky.gan_day(ma_kh)
