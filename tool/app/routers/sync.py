"""Phân hệ Đồng bộ CDB — API localhost (SYNC-02 trước; SYNC-01/03 thêm sau).

Ghi vào CSDL ĐÍCH (GPLX_CDB_CSDT) — tách khỏi router Nạp. Gác session như các
router /local/* nghiệp vụ khác (mount kèm require_session ở main.py).
"""
from __future__ import annotations

import json
import logging
import queue
import re
import threading
import uuid
from datetime import date, datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from app import config_store, sync_helpers, sync_service, sync_history
from app.db import sqlserver_conn, sqlserver_cursor_dich, sqlserver_conn_dich, ConfigChuaDay

logger = logging.getLogger(__name__)

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


# ========== SYNC-01 (phần chạy: run + SSE) — task 58 ==========
# App 1 người dùng localhost → job lưu dict theo job_id, hàng đợi thread-safe.
_jobs: dict[str, dict] = {}


class RunIn(BaseModel):
    ma_kh_nguon: str
    ma_kh_dich: str
    ngay_nhap_hs: date
    target_key: str | None = None
    so_cmt_chon: list[str] = Field(default_factory=list)  # CCCD các HV được tick


def _khoa_hang_nguon(conn, ma_kh: str) -> str | None:
    cur = conn.cursor()
    cur.execute("SELECT HangGPLX FROM dbo.KhoaHoc WHERE MaKH=%s", (ma_kh,))
    r = cur.fetchone()
    return (r[0] or "").strip() if r else None


def _khoa_ngaykg(conn, ma_kh: str):
    cur = conn.cursor()
    cur.execute("SELECT NgayKG FROM dbo.KhoaHoc WHERE MaKH=%s", (ma_kh,))
    r = cur.fetchone()
    return r[0] if r else None


@router.post("/run")
def run(body: RunIn) -> dict:
    """Mở job đồng bộ (chạy nền) -> trả job_id. UI mở SSE /stream xem tiến trình.

    Validate TRƯỚC khi mở job: hạng khóa nguồn = hạng khóa đích; ngày nhập HS <=
    NgàyKG khóa đích (backdate >90 ngày do UI tự xác nhận trước)."""
    db = _db_dich(body.target_key)
    tt = config_store.get_sync_config()["options"]
    try:
        with sqlserver_conn() as cn, sqlserver_conn_dich(db) as cd:
            hang_nguon = _khoa_hang_nguon(cn, body.ma_kh_nguon)
            khoa_info = sync_helpers.get_khoa_info(cd, body.ma_kh_dich)
            ngay_kg = _khoa_ngaykg(cd, body.ma_kh_dich)
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)

    if not khoa_info:
        raise HTTPException(status_code=400, detail="Không tìm thấy khóa đích.")
    if body.ngay_nhap_hs > datetime.now().date():
        raise HTTPException(status_code=400, detail="Ngày nhập HS không được sau hôm nay.")
    if hang_nguon and khoa_info["hang_gplx"] and hang_nguon != khoa_info["hang_gplx"]:
        raise HTTPException(
            status_code=400,
            detail=f"Hạng xe không khớp: khóa nguồn {hang_nguon} khác khóa đích {khoa_info['hang_gplx']}.",
        )
    if ngay_kg is not None:
        kg = ngay_kg.date() if hasattr(ngay_kg, "date") else ngay_kg
        if body.ngay_nhap_hs > kg:
            raise HTTPException(
                status_code=400,
                detail=f"Ngày nhập HS ({body.ngay_nhap_hs:%d/%m/%Y}) sau NgàyKG khóa đích ({kg:%d/%m/%Y}).",
            )

    job_id = uuid.uuid4().hex
    q: queue.Queue = queue.Queue()
    _jobs[job_id] = {"q": q, "done": False, "summary": None}
    threading.Thread(target=_chay_job, args=(job_id, db, body, khoa_info, tt), daemon=True).start()
    return {"job_id": job_id}


def _ensure_madk_unique(cd, ma_dk, ma_csdt, ngay_hs, max_retry=3):
    """Guard chống trùng MaDK (race hiếm). Trùng -> sinh lại, tối đa 3 lần."""
    cur = ma_dk
    for _ in range(max_retry):
        if not sync_helpers.kiem_tra_madk_ton_tai(cd, cur):
            return cur
        cur = sync_helpers.sinh_madk_batch(cd, ma_csdt, ngay_hs, 1)[0]
    if sync_helpers.kiem_tra_madk_ton_tai(cd, cur):
        raise RuntimeError(f"MaDK trùng sau {max_retry} lần: {cur}")
    return cur


def _chay_job(job_id: str, db: str, body: RunIn, khoa_info: dict, tt: dict) -> None:
    """Vòng chạy đồng bộ trong thread nền. Đẩy sự kiện vào queue cho SSE.

    KHÔNG xóa NguoiLX 'mồ côi' toàn DB (bước này ở sync_tool quét cả CSDL đích ->
    rủi ro xóa nhầm dữ liệu phần mềm khác; không cần cho sinh MaDK)."""
    q: queue.Queue = _jobs[job_id]["q"]

    def emit(ev):
        q.put(ev)

    ok_c = skip_c = loi_c = 0
    tong_so_hv_after = None
    try:
        with sqlserver_conn() as cn, sqlserver_conn_dich(db, autocommit=True) as cd:
            hv_list = sync_service.load_hoc_vien_nguon(cn, body.ma_kh_nguon)
            chon = {c.strip() for c in body.so_cmt_chon if c and c.strip()}
            if chon:
                hv_list = [h for h in hv_list if (h.get("SoCMT") or "").strip() in chon]
            so_cmt = [(h.get("SoCMT") or "").strip() for h in hv_list]
            enrich = sync_helpers.enrich_from_db_dich(cd, so_cmt)

            moi = [h for h in hv_list if (h.get("SoCMT") or "").strip()
                   and (h.get("SoCMT") or "").strip() not in enrich]
            is_today = body.ngay_nhap_hs == datetime.now().date()
            madk_iter = None
            ma_csdt = khoa_info["ma_csdt"]
            if moi and not is_today and len(ma_csdt) == 5:
                madk_list = sync_helpers.sinh_madk_batch(cd, ma_csdt, body.ngay_nhap_hs, len(moi))
                madk_iter = iter(madk_list)

            next_so = sync_service.next_so_ho_so(cd, body.ma_kh_dich) + 1
            batch = sync_history.SyncBatch(
                khoa_moi=body.ma_kh_dich, khoa_cu=body.ma_kh_nguon,
                ngay_nhap_hs_chon=body.ngay_nhap_hs, can_bo=sync_service.NGUOI_TAO_MAC_DINH,
                sync_at_start=datetime.now(),
            )
            store = sync_history.HistoryStore()

            for idx, h in enumerate(hv_list, 1):
                cc = (h.get("SoCMT") or "").strip()
                ten = h.get("HoVaTen") or ""
                if not cc:  # E1
                    loi_c += 1
                    emit({"loai": "hv", "stt": idx, "so_cmt": cc, "ho_ten": ten,
                          "trang_thai": "Lỗi: thiếu CCCD", "mau": "loi"})
                    continue
                if cc in enrich:  # skip
                    skip_c += 1
                    emit({"loai": "hv", "stt": idx, "so_cmt": cc, "ho_ten": ten, "mau": "skip",
                          "trang_thai": f"Bỏ qua — đã có ({enrich[cc]['ma_dk']})"})
                    continue
                ma_dk_pre = next(madk_iter) if madk_iter is not None else None
                try:
                    if ma_dk_pre:
                        ma_dk_pre = _ensure_madk_unique(cd, ma_dk_pre, ma_csdt, body.ngay_nhap_hs)
                    kq = sync_service.sync_one_hv(
                        cd, cn, h, khoa_info, body.ma_kh_dich, next_so, tt["tt_xuly_force"],
                        ma_dk_pre=ma_dk_pre, ngay_nhap_hs=body.ngay_nhap_hs,
                    )
                except Exception as ex:  # noqa: BLE001
                    kq = sync_service.KetQuaHV(ok=False, loi=str(ex))
                if kq.ok:
                    ok_c += 1
                    next_so += 1
                    batch.ma_dk_moi.append(kq.ma_dk)
                    try:
                        store.save_batch(batch)
                    except OSError:
                        pass
                    tt_txt = f"Đã tạo {kq.ma_dk}" + (" (giấy tờ lỗi)" if kq.giay_to_loi else "")
                    emit({"loai": "hv", "stt": idx, "so_cmt": cc, "ho_ten": ten,
                          "trang_thai": tt_txt, "mau": "ok", "ma_dk": kq.ma_dk})
                else:
                    loi_c += 1
                    emit({"loai": "hv", "stt": idx, "so_cmt": cc, "ho_ten": ten, "mau": "loi",
                          "trang_thai": f"Lỗi: {kq.loi}"})

            if tt.get("update_tong_so_hv"):
                try:
                    cur = cd.cursor()
                    cur.execute(
                        "SET NOCOUNT ON; UPDATE dbo.KhoaHoc SET TongSoHV="
                        "(SELECT COUNT(*) FROM dbo.NguoiLX_HoSo WHERE MaKhoaHoc=%s) WHERE MaKH=%s; "
                        "SELECT TongSoHV FROM dbo.KhoaHoc WHERE MaKH=%s",
                        (body.ma_kh_dich, body.ma_kh_dich, body.ma_kh_dich),
                    )
                    r = cur.fetchone()
                    tong_so_hv_after = r[0] if r else None
                except Exception:  # noqa: BLE001
                    pass
    except Exception as e:  # noqa: BLE001
        emit({"loai": "loi_he_thong", "message": str(e)})
        logger.error("Job sync %s lỗi: %s", job_id, e)

    summary = {"loai": "xong", "ok": ok_c, "skip": skip_c, "loi": loi_c, "tong_so_hv": tong_so_hv_after}
    _jobs[job_id]["summary"] = summary
    _jobs[job_id]["done"] = True
    emit(summary)
    q.put(None)


@router.get("/stream")
def stream(job: str):
    """SSE tiến trình job. Ngắt kết nối giữa chừng -> job vẫn chạy tới hết."""
    j = _jobs.get(job)
    if not j:
        raise HTTPException(status_code=404, detail="Không tìm thấy job (hết hạn hoặc sai id).")

    def gen():
        q: queue.Queue = j["q"]
        while True:
            try:
                ev = q.get(timeout=25)
            except queue.Empty:
                yield ": keepalive\n\n"
                continue
            if ev is None:
                break
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
        _jobs.pop(job, None)

    return StreamingResponse(gen(), media_type="text/event-stream")


# ========== SYNC-03 (Lịch sử & Hủy sync khóa) — task 60 ==========
# Port rollback dual-mode sync_tool v2.0: xóa theo MaDK nhật ký JSON (nhóm chính)
# CỘNG nhóm công cụ cũ NguoiTao='SYNC' (tương thích ngược). Cascade NguoiLX→HoSo
# →GiayTo tự dọn. CSDL đích GPLX_CDB_CSDT không lập BC1 nên xóa an toàn; vẫn bắt
# lỗi FK BaoCaoI (NO_ACTION) phòng khi HV đã BC1 → báo rõ thay vì lỗi SQL thô.


class RollbackIn(BaseModel):
    ma_kh: str
    target_key: str | None = None

    @field_validator("ma_kh")
    @classmethod
    def _khong_rong(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Thiếu mã khóa cần hủy")
        return v.strip()


@router.get("/lich-su")
def lich_su() -> list[dict]:
    """Các lần sync đã ghi nhật ký trên máy tool (mọi khóa). Thuần đọc JSON cục bộ
    — không cần DB, file hỏng tự bỏ qua. Mới nhất lên đầu."""
    try:
        store = sync_history.HistoryStore()
    except OSError:
        return []
    out = []
    for b in store.list_all_batches():
        out.append({
            "khoa_moi": b.khoa_moi,
            "khoa_cu": b.khoa_cu,
            "sync_at": b.sync_at_start.isoformat(),
            "can_bo": b.can_bo,
            "so_tao": len(b.all_ma_dk_new()),
        })
    return out


@router.get("/rollback/preview")
def rollback_preview(ma_kh: str, target_key: str | None = None) -> dict:
    """Đếm chính xác số bản ghi SẼ xóa (cho hộp xác nhận): nhóm nhật ký (MaDK còn
    tồn tại ở khóa đích) + nhóm công cụ cũ NguoiTao='SYNC'."""
    db = _db_dich(target_key)
    store = sync_history.HistoryStore()
    log_madk = sorted(store.get_all_ma_dk_for_khoa(ma_kh))
    try:
        with sqlserver_conn_dich(db) as cd:
            cur = cd.cursor()
            log_con = 0
            if log_madk:
                marks = ",".join(["%s"] * len(log_madk))
                cur.execute(
                    f"SELECT COUNT(*) FROM dbo.NguoiLX_HoSo WHERE MaKhoaHoc=%s AND MaDK IN ({marks})",
                    (ma_kh, *log_madk),
                )
                log_con = cur.fetchone()[0]
            cur.execute(
                "SELECT COUNT(*) FROM dbo.NguoiLX_HoSo WHERE MaKhoaHoc=%s AND NguoiTao='SYNC'",
                (ma_kh,),
            )
            sync_con = cur.fetchone()[0]
    except Exception as e:  # noqa: BLE001
        raise _loi_db(e)
    return {
        "log_count": len(log_madk),
        "log_con_dich": int(log_con),
        "sync_group": int(sync_con),
        "tong": int(log_con) + int(sync_con),
    }


@router.post("/rollback")
def rollback(body: RollbackIn) -> dict:
    """Hủy sync 1 khóa: xóa HV do tool tạo khỏi CSDL đích. KHÔNG hoàn tác được.

    Một transaction (autocommit=False) — vướng bất cứ dòng nào (vd HV đã BC1 bị
    FK chặn) thì hủy TOÀN BỘ, không để khóa nửa vời. Nhật ký JSON giữ nguyên."""
    db = _db_dich(body.target_key)
    store = sync_history.HistoryStore()
    log_madk = sorted(store.get_all_ma_dk_for_khoa(body.ma_kh))
    tt = config_store.get_sync_config()["options"]
    hs_del = nlx_del = 0
    tong_so_hv = None
    try:
        with sqlserver_conn_dich(db, autocommit=False) as cd:
            cur = cd.cursor()
            # Nhóm nhật ký (MaDK): PK NguoiLX_HoSo = MaDK; xóa NguoiLX cascade HoSo+GiayTo.
            for madk in log_madk:
                cur.execute(
                    "DELETE FROM dbo.NguoiLX_HoSo WHERE MaDK=%s AND MaKhoaHoc=%s",
                    (madk, body.ma_kh),
                )
                hs_del += cur.rowcount
                cur.execute(
                    "DELETE FROM dbo.NguoiLX WHERE MaDK=%s "
                    "AND NOT EXISTS (SELECT 1 FROM dbo.NguoiLX_HoSo WHERE MaDK=%s)",
                    (madk, madk),
                )
                nlx_del += cur.rowcount
            # Nhóm công cụ cũ NguoiTao='SYNC' (tương thích ngược sync_tool v1.07).
            cur.execute(
                "DELETE GT FROM dbo.NguoiLXHS_GiayTo GT "
                "JOIN dbo.NguoiLX_HoSo HS ON GT.MaDK=HS.MaDK AND GT.SoHoSo=HS.SoHoSo "
                "WHERE HS.MaKhoaHoc=%s AND HS.NguoiTao='SYNC'",
                (body.ma_kh,),
            )
            cur.execute(
                "DELETE FROM dbo.NguoiLX_HoSo WHERE MaKhoaHoc=%s AND NguoiTao='SYNC'",
                (body.ma_kh,),
            )
            hs_del += cur.rowcount
            cur.execute(
                "DELETE FROM dbo.NguoiLX "
                "WHERE MaDK NOT IN (SELECT MaDK FROM dbo.NguoiLX_HoSo) AND NguoiTao='SYNC'"
            )
            nlx_del += cur.rowcount
            # Cập nhật lại TongSoHV (nếu bật tùy chọn).
            if tt.get("update_tong_so_hv"):
                cur.execute(
                    "SET NOCOUNT ON; UPDATE dbo.KhoaHoc SET TongSoHV="
                    "(SELECT COUNT(*) FROM dbo.NguoiLX_HoSo WHERE MaKhoaHoc=%s) WHERE MaKH=%s; "
                    "SELECT TongSoHV FROM dbo.KhoaHoc WHERE MaKH=%s",
                    (body.ma_kh, body.ma_kh, body.ma_kh),
                )
                r = cur.fetchone()
                tong_so_hv = r[0] if r else None
            cd.commit()
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001 — gói lỗi FK BC1 thành thông báo nghiệp vụ
        msg = str(e)
        if "BaoCaoI" in msg or "REFERENCE" in msg.upper():
            raise HTTPException(
                status_code=409,
                detail="Không hủy được: khóa này có học viên đã lập Báo cáo 1 "
                       "(CSDL chặn xóa). Gỡ Báo cáo 1 ở phần mềm CDB trước rồi hủy lại. "
                       "Chưa xóa học viên nào.",
            )
        raise _loi_db(e)
    return {"hs_del": int(hs_del), "nlx_del": int(nlx_del), "tong_so_hv": tong_so_hv}
