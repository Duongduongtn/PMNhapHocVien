"""QLY-09 — Đối soát & đồng bộ trạng thái VPS↔CSDT (CHANGES #28, TDD §11.8).

2 chế độ phát hiện (chỉ ĐỌC, không ghi):
- Theo khóa (operator/admin) → ca ②: CSDT có HV nhưng VPS chưa `imported`.
- Quét lạc toàn hệ (admin)    → ca ① (phantom: VPS imported & CSDT không có MaDK) + ca ③ (importing treo).

3 action sửa 1 chạm — TÁI DÙNG đường có sẵn, KHÔNG endpoint/SP nạp mới:
- ca ① → tra_ve_cho_nap + keo_ve_ve_cho (KHÔNG đụng CSDT: phantom vốn không có).
- ca ② → da_nap(uuid, ma_dk).
- ca ③ → unlock(uuid).
"""
from __future__ import annotations
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app import nap, vps
from app.db import sqlserver_cursor, ConfigChuaDay
from app.session import Phien, require_session
from app.vps import VpsLoi

router = APIRouter(prefix="/local/doi-soat", tags=["doi-soat"])

# Ngưỡng ca ③: importing "treo" khi quá ngưỡng job tự mở khóa (§7.2, ~15') — tránh đụng dòng
# đang nạp thật ở máy khác.
_NGUONG_TREO_GIAY = 15 * 60


def _loi_vps(e: VpsLoi) -> HTTPException:
    return HTTPException(status_code=502, detail=str(e))


def _chi_admin(phien: Phien) -> None:
    if phien.vai_tro != "admin":
        raise HTTPException(status_code=403, detail="Chỉ quản trị viên được quét bản ghi lạc toàn hệ.")


def _token(phien: Phien) -> str:
    if not phien.vps_token:
        raise HTTPException(status_code=409, detail="Phiên chưa có quyền máy chủ — đăng nhập lại.")
    return phien.vps_token


def _qua_nguong(locked_at: str | None) -> bool:
    """locked_at (ISO từ VPS, có tz) cũ hơn ngưỡng treo? None/parse lỗi → coi KHÔNG treo (an toàn)."""
    if not locked_at:
        return False
    try:
        t = datetime.fromisoformat(locked_at)
    except ValueError:
        return False
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - t).total_seconds() > _NGUONG_TREO_GIAY


@router.get("/khoa")
def doi_soat_khoa(ma_kh: str = Query(..., min_length=1), phien: Phien = Depends(require_session)):
    """Ca ② — theo khóa (operator/admin): HV còn ở CSDT nhưng VPS chưa `imported`.

    Neo ở CSDT (khóa có cột), tra uuid qua staging `nap_xong` → hỏi trạng thái VPS 1 lượt.
    `nap_xong` thiếu entry (máy khác / đã dọn) → ghi 'không tra được uuid', KHÔNG báo động giả."""
    token = _token(phien)
    try:
        with sqlserver_cursor() as cur:
            cur.execute(
                "SELECT hs.MaDK AS ma_dk, nl.HoVaTen AS ho_ten "
                "FROM NguoiLX_HoSo hs JOIN NguoiLX nl ON nl.MaDK = hs.MaDK "
                "WHERE hs.MaKhoaHoc = %s AND hs.TrangThai = 1",
                (ma_kh,),
            )
            hv_csdt = cur.fetchall()
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không truy vấn được SQL Server — kiểm kết nối.")

    # ma_dk → uuid (staging local). Thiếu uuid → không tra được (không khẳng định lệch).
    ten_theo_madk: dict[str, str | None] = {r["ma_dk"]: r["ho_ten"] for r in hv_csdt}
    uuid_theo_madk: dict[str, str] = {}
    khong_tra_duoc: list[dict] = []
    for ma_dk in ten_theo_madk:
        u = nap.lay_uuid_theo_ma_dk(ma_dk)
        if u:
            uuid_theo_madk[ma_dk] = u
        else:
            khong_tra_duoc.append({"ma_dk": ma_dk, "ho_ten": ten_theo_madk[ma_dk]})

    try:
        tt = vps.trang_thai_nhieu(token, list(uuid_theo_madk.values()))
    except VpsLoi as e:
        raise _loi_vps(e)

    ca2: list[dict] = []
    for ma_dk, uuid in uuid_theo_madk.items():
        row = tt.get(uuid)
        if row is None:
            # VPS không còn bản ghi (đã dọn PII) → không da_nap được, báo rõ (edge PRD).
            khong_tra_duoc.append({"ma_dk": ma_dk, "ho_ten": ten_theo_madk[ma_dk],
                                   "ly_do": "VPS không còn bản ghi gốc (đã dọn dữ liệu)"})
            continue
        if row.get("trang_thai") != "imported":
            ca2.append({"loai": "②", "ma_dk": ma_dk, "uuid": uuid,
                        "ho_ten": ten_theo_madk[ma_dk], "trang_thai_vps": row.get("trang_thai"),
                        "hanh_dong": "da_nap"})
    return {"ca2": ca2, "khong_tra_duoc": khong_tra_duoc}


def _quet_trang_thai(token: str, trang_thai: str) -> list[dict]:
    """Lấy TRỌN các bản ghi 1 trạng thái trên VPS (phân trang 500/lượt)."""
    items: list[dict] = []
    offset = 0
    for _ in range(50):  # chặn vòng lặp (tối đa ~25.000 bản/lượt quét)
        kq = vps.admin_ho_so(token, trang_thai=trang_thai, limit=500, offset=offset)
        phan = kq.get("items", [])
        items.extend(phan)
        if len(items) >= kq.get("total", 0) or not phan:
            break
        offset += len(phan)
    return items


@router.get("/lac")
def quet_lac(phien: Phien = Depends(require_session)):
    """Ca ① + ③ — quét lạc toàn hệ (admin). Neo ở trạng thái VPS, check một chiều sang CSDT."""
    _chi_admin(phien)
    token = _token(phien)
    try:
        imported = _quet_trang_thai(token, "imported")
        importing = _quet_trang_thai(token, "importing")
    except VpsLoi as e:
        raise _loi_vps(e)

    # Ca ① phantom: VPS imported có ma_dk nhưng CSDT KHÔNG có MaDK đó.
    phantom: list[dict] = []
    ma_dks = [it["ma_dk"] for it in imported if it.get("ma_dk")]
    co_trong_csdt = _madk_ton_tai(ma_dks) if ma_dks else set()
    for it in imported:
        ma_dk = it.get("ma_dk")
        if ma_dk and ma_dk not in co_trong_csdt:
            phantom.append({"loai": "①", "uuid": it["uuid"], "ma_dk": ma_dk,
                            "ho_ten": it.get("ho_ten"), "hanh_dong": "tra_ve_cho_nap"})

    # Ca ③ treo: VPS importing quá ngưỡng (không ai đang nạp thật).
    treo = [{"loai": "③", "uuid": it["uuid"], "ho_ten": it.get("ho_ten"),
             "locked_at": it.get("locked_at"), "hanh_dong": "unlock"}
            for it in importing if _qua_nguong(it.get("locked_at"))]
    return {"phantom": phantom, "treo": treo}


def _madk_ton_tai(ma_dks: list[str]) -> set[str]:
    """Tập MaDK có thật trong CSDT (NguoiLX_HoSo) trong danh sách đưa vào."""
    if not ma_dks:
        return set()
    try:
        with sqlserver_cursor() as cur:
            cho = ",".join(["%s"] * len(ma_dks))
            cur.execute(f"SELECT MaDK FROM NguoiLX_HoSo WHERE MaDK IN ({cho})", tuple(ma_dks))
            return {r["MaDK"] for r in cur.fetchall()}
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không truy vấn được SQL Server — kiểm kết nối.")


@router.post("/da-nap")
def sua_ca2(uuid: str = Query(..., min_length=1), ma_dk: str = Query(..., min_length=1),
            phien: Phien = Depends(require_session)):
    """Ca ② — "Đánh dấu đã nạp" (tái dùng vps.da_nap). Operator/admin."""
    try:
        vps.da_nap(_token(phien), uuid, ma_dk)
    except VpsLoi as e:
        raise _loi_vps(e)
    return {"ok": True, "uuid": uuid, "ma_dk": ma_dk}


@router.post("/tra-ve")
def sua_ca1(uuid: str = Query(..., min_length=1), phien: Phien = Depends(require_session)):
    """Ca ① phantom — "Trả về chờ nạp" (VPS imported→pending + staging về 'cho'). KHÔNG đụng CSDT
    (phantom vốn không có MaDK). Admin."""
    _chi_admin(phien)
    try:
        vps.tra_ve_cho_nap(_token(phien), uuid)
    except VpsLoi as e:
        raise _loi_vps(e)
    nap.keo_ve_ve_cho(uuid)  # đưa dòng staging về 'cho' (nếu còn) + gỡ vé nap_xong (BUG-01)
    return {"ok": True, "uuid": uuid}


@router.post("/mo-khoa")
def sua_ca3(uuid: str = Query(..., min_length=1), phien: Phien = Depends(require_session)):
    """Ca ③ importing treo — "Mở khóa" (tái dùng vps.unlock, importing→pending). Admin."""
    _chi_admin(phien)
    try:
        vps.unlock(_token(phien), uuid)
    except VpsLoi as e:
        raise _loi_vps(e)
    return {"ok": True, "uuid": uuid}
