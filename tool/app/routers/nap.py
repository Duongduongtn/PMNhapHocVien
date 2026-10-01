"""NAP-05 (2/2) — nạp 1 HV vào GPLX_CSDT + danh sách giấy tờ mặc định theo khóa.

- GET  /local/giay-to  : danh sách giấy tờ bắt buộc theo (MaLoaiHS, HangDT) cho checklist UI.
- POST /local/nap      : nạp 1 HV (SoHoSo + 1 SP gộp app cũ + ghi ảnh hướng A + giấy tờ). GHI PRODUCTION.

Mọi ghi DB qua SP (TDD §10). Đọc danh mục (khóa, tham số, giấy tờ) bằng SELECT parameterized
— login tool được SELECT danh mục, chỉ cấm INSERT/UPDATE trực tiếp bảng nghiệp vụ (TDD §12).
"""
from __future__ import annotations
import base64

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel

from app import nap, vps
from app.db import sqlserver_conn, sqlserver_cursor, ConfigChuaDay
from app.session import Phien, require_session
from app.vps import VpsLoi

router = APIRouter(prefix="/local", tags=["nap"])

# Tên tham số đường dẫn ảnh trong QTHT_ThamSoHT (đọc động, không hard-code — memory §6).
_TEN_TS_IMG = "IMG_PATH_CSDT"

# Giấy tờ mặc định theo loại HS + hạng đào tạo. Lọc MaHangGPLX = HangDT ('B', không phải 'B1');
# TenGT lấy tên ĐẦY ĐỦ từ DM_GiayTo, không lấy tên ngắn ở DM_LoaiHSo_GiayTo (memory §3).
_SQL_GIAY_TO = """
    SELECT g.MaGT AS MaGT, dg.TenGT AS TenGT
    FROM DM_LoaiHSo_GiayTo g
    JOIN DM_GiayTo dg ON dg.MaGT = g.MaGT
    WHERE g.MaLoaiHS = %s AND g.MaHangGPLX = %s AND g.TrangThai = 1
    ORDER BY g.MaGT
"""


class GiayTo(BaseModel):
    ma_gt: int
    ten_gt: str


@router.get("/giay-to", response_model=list[GiayTo])
def list_giay_to(ma_loai_hs: int = Query(...), hang_dt: str = Query(...)):
    """Giấy tờ bắt buộc mặc định cho (loại HS, hạng ĐT) — UI tick sẵn, cho bỏ tick."""
    try:
        with sqlserver_cursor() as cur:
            cur.execute(_SQL_GIAY_TO, (ma_loai_hs, hang_dt))
            rows = cur.fetchall()
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không đọc được danh mục giấy tờ — kiểm kết nối.")
    return [{"ma_gt": r["MaGT"], "ten_gt": r["TenGT"]} for r in rows]


@router.get("/kiem-trung-cccd")
def kiem_trung_cccd(ma_kh: str = Query(...), so_cmt: str = Query(...)):
    """NAP-06: kiểm SoCMT đã có trong CÙNG khóa chưa (cảnh báo sớm trước khi nạp).
    Chỉ trong khóa (BR-005) — khác khóa cho phép; không chặn toàn hệ thống. SP gộp vẫn
    là chốt chặn cuối (@p_out=-2) khi nạp."""
    if not so_cmt.strip():
        return {"trung": False, "so_ho_so": None}
    try:
        with sqlserver_cursor() as cur:
            cur.execute(
                "SELECT TOP 1 hs.SoHoSo AS SoHoSo FROM NguoiLX lx "
                "JOIN NguoiLX_HoSo hs ON hs.MaDK = lx.MaDK "
                "WHERE lx.SoCMT = %s AND hs.MaKhoaHoc = %s",
                (so_cmt.strip(), ma_kh),
            )
            row = cur.fetchone()
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không kiểm được trùng CCCD — kiểm kết nối.")
    return {"trung": bool(row), "so_ho_so": row["SoHoSo"] if row else None}


class NapIn(BaseModel):
    uuid: str                       # idempotent + truy vết + chống mồ côi
    ma_khoa_hoc: str
    ho_ten: str
    ngay_sinh: str                  # varchar(8) yyyymmdd
    gioi_tinh: str                  # 'M' / 'F'
    so_cmt: str
    ngay_cap_cmt: str | None = None
    noi_cap_cmt: str | None = None
    chi_tiet_tt: str = ""           # NoiTT (số nhà/thôn) — mặc định TRỐNG; KHÔNG nhét tên xã (AS-003)
    noi_tt_ma_dvhc: str
    noi_tt_ma_dvql: str
    chi_tiet_ct: str | None = None  # NoiCT; None → dùng chi_tiet_tt
    noi_ct_ma_dvhc: str | None = None
    noi_ct_ma_dvql: str | None = None
    giay_to_tick: list[int] = []    # danh sách MaGT đã tick
    anh_jp2_b64: str | None = None  # ảnh .jp2 đã xử lý (NAP-04); None → nạp thiếu ảnh (BR-011)


def _nap_mot(body: NapIn) -> dict:
    """Lõi nạp 1 HV vào khóa (GHI PRODUCTION) — dùng chung cho nạp đơn và nạp lô.

    Raise: HTTPException (khóa không có / chưa cấu hình ảnh), ValueError (vượt độ dài /
    trùng CCCD / SP từ chối), ConfigChuaDay, Exception (lỗi DB). Trả dict kết quả đầy đủ.
    SP gộp atomic → lỗi tự rollback, bản ghi KHÔNG nửa vời.
    """
    try:
        jp2 = base64.b64decode(body.anh_jp2_b64) if body.anh_jp2_b64 else None
    except Exception:
        raise HTTPException(status_code=400, detail="Ảnh .jp2 gửi lên không hợp lệ.")

    with sqlserver_conn() as conn:
        cur = conn.cursor(as_dict=True)

        # Khóa đích (nguồn chuẩn cho hạng/loại — không tin client)
        cur.execute(
            "SELECT MaKH, HangGPLX, HangDT, MaSoGTVT FROM KhoaHoc WHERE MaKH=%s AND TrangThai=1",
            (body.ma_khoa_hoc,),
        )
        k = cur.fetchone()
        if not k:
            raise HTTPException(status_code=404, detail="Không tìm thấy khóa học (hoặc khóa đã khóa).")
        khoa = {
            "ma_kh": k["MaKH"], "hang_gplx": k["HangGPLX"],
            "hang_dt": k["HangDT"], "ma_so_gtvt": k["MaSoGTVT"],
        }
        ma_loai_hs = nap.suy_ma_loai_hs(k["HangGPLX"])
        hang_dt = k["HangDT"] or k["HangGPLX"]

        # Đường dẫn ảnh gốc (đọc động từ tham số hệ thống)
        cur.execute("SELECT GiaTriTS FROM QTHT_ThamSoHT WHERE TenTS=%s", (_TEN_TS_IMG,))
        row = cur.fetchone()
        if jp2 and not (row and row["GiaTriTS"]):
            raise HTTPException(status_code=502, detail="Chưa cấu hình IMG_PATH_CSDT trên DB đích.")
        img_path = row["GiaTriTS"] if row else ""

        # Giấy tờ: lấy danh sách mặc định theo khóa rồi lọc đúng dòng đã tick (tên từ DB)
        cur.execute(_SQL_GIAY_TO, (ma_loai_hs, hang_dt))
        ten_theo_ma = {r["MaGT"]: r["TenGT"] for r in cur.fetchall()}
        giay_to = [{"ma_gt": g, "ten_gt": ten_theo_ma[g]}
                   for g in body.giay_to_tick if g in ten_theo_ma]

        hv = {
            "ho_ten": body.ho_ten, "ngay_sinh": body.ngay_sinh, "gioi_tinh": body.gioi_tinh,
            "so_cmt": body.so_cmt, "ngay_cap_cmt": body.ngay_cap_cmt,
            "noi_cap_cmt": body.noi_cap_cmt or "",
            "chi_tiet_tt": body.chi_tiet_tt,                 # NoiTT (mặc định trống)
            "noi_tt_ma_dvhc": body.noi_tt_ma_dvhc,
            "noi_tt_ma_dvql": body.noi_tt_ma_dvql,
            "chi_tiet_ct": body.chi_tiet_ct or body.chi_tiet_tt,
            "noi_ct_ma_dvhc": body.noi_ct_ma_dvhc or body.noi_tt_ma_dvhc,
            "noi_ct_ma_dvql": body.noi_ct_ma_dvql or body.noi_tt_ma_dvql,
        }
        # nguoi="" → NguoiNhanHSo/NguoiThuNhanAnh trống, khớp app cũ (55/55 HV thật để trống)
        return nap.nap_mot_hv(conn, hv, khoa, jp2, img_path, "", body.uuid, giay_to)


@router.post("/nap")
def nap_ho_so(body: NapIn):
    """Nạp 1 HV vào khóa (GHI PRODUCTION). SP gộp atomic → lỗi tự rollback, bản ghi giữ pending."""
    try:
        r = _nap_mot(body)
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:                       # validate độ dài cột → báo cho UI sửa
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Nạp hồ sơ thất bại — bản ghi giữ pending, thử lại.")
    return {"ma_dk": r["ma_dk"], "so_ho_so": r["so_ho_so"], "so_giay_to": r["so_giay_to"]}


# ===== NAP-01 — kéo hàng đợi VPS → staging + nạp lô =====================

def _loi_vps(e: VpsLoi) -> HTTPException:
    """VpsLoi → HTTPException: giữ mã VPS cho các mã client cần biết, còn lại gộp 502."""
    st = e.status if e.status in (401, 403, 404, 409) else 502
    return HTTPException(status_code=st, detail=str(e))


@router.post("/nap/keo")
def keo_hang_doi(phien: Phien = Depends(require_session), limit: int = Query(200, ge=1, le=500)):
    """Kéo bản ghi `pending` từ VPS về staging (dedup theo uuid). Kéo trọn bằng cursor.

    VPS lỗi ngay từ đầu → báo lỗi; lỗi giữa chừng → giữ phần đã kéo, dừng. Trả số bản ghi
    MỚI thêm + tổng trong staging."""
    tong_moi = 0
    cursor: str | None = None
    for _ in range(50):  # chặn vòng lặp vô hạn (tối đa ~25.000 bản ghi/lượt kéo)
        try:
            rows = vps.keo(phien.vps_token, limit=limit, cursor=cursor)
        except VpsLoi as e:
            if tong_moi == 0:
                raise _loi_vps(e)
            break  # đã kéo được một phần → giữ, để nhân viên xử lý phần đã có
        if not rows:
            break
        tong_moi += nap.keo_ve_upsert(rows)
        if len(rows) < limit:
            break
        cursor = rows[-1].get("created_at")
    return {"keo_ve": tong_moi, "tong": len(nap.keo_ve_danh_sach())}


@router.get("/nap/danh-sach")
def danh_sach_keo_ve():
    """Toàn bộ hàng đã kéo về (metadata). UI lọc Cần xử lý/Đã nạp + tìm + IN HOA (CHANGES #6/#10)."""
    return nap.keo_ve_danh_sach()


@router.get("/nap/keo/{uuid}/anh")
def tai_anh_keo_ve(uuid: str, phien: Phien = Depends(require_session)):
    """Tải ảnh thô 1 hồ sơ từ VPS về (hiển thị + để xử lý .jp2). Chưa có ảnh → 404."""
    try:
        data = vps.tai_anh(phien.vps_token, uuid)
    except VpsLoi as e:
        raise _loi_vps(e)
    if data is None:
        raise HTTPException(status_code=404, detail="Hồ sơ chưa có ảnh.")
    media = "image/png" if data[:8] == b"\x89PNG\r\n\x1a\n" else "image/jpeg"
    return Response(content=data, media_type=media)


class NapLoIn(BaseModel):
    items: list[NapIn]  # mỗi HV đã được UI chuẩn bị đủ (khóa, địa chỉ DVHC, giấy tờ, ảnh .jp2)


@router.post("/nap/nap-lo")
def nap_lo_endpoint(body: NapLoIn, phien: Phien = Depends(require_session)):
    """Nạp lô nhiều HV đã kéo về (EC-071): mỗi HV KHÓA trên VPS (pending→importing) →
    nạp SQL Server → xác nhận `da_nap` (kèm MaDK). 1 HV lỗi KHÔNG hỏng cả lô — ghi dòng
    lỗi + mở khóa lại (về pending để nạp sau). Cập nhật trạng thái staging cho từng dòng.
    """
    token = phien.vps_token
    items = [it.model_dump() for it in body.items]

    def nap_fn(item: dict) -> dict:
        uuid = str(item["uuid"])
        vps.lock(token, uuid)  # VpsLoi(409) → lô ghi dòng lỗi "đang nạp máy khác", KHÔNG mở khóa
        try:
            r = _nap_mot(NapIn(**item))
        except HTTPException as e:
            _mo_khoa_im_lang(token, uuid)
            raise RuntimeError(str(e.detail))  # đưa lý do rõ (khóa không có, chưa cấu hình ảnh…)
        except Exception:
            _mo_khoa_im_lang(token, uuid)
            raise
        vps.da_nap(token, uuid, r["ma_dk"])  # lỗi ở đây → VpsLoi; HV đã nạp, retry hội tụ nhờ idempotent UUID
        return {"ma_dk": r["ma_dk"], "so_ho_so": r["so_ho_so"], "so_giay_to": r["so_giay_to"]}

    kq = nap.nap_lo(items, nap_fn)
    for dong in kq["ket_qua"]:
        if dong["ok"]:
            nap.keo_ve_cap_nhat(dong["uuid"], trang_thai="xong",
                                ma_dk=dong.get("ma_dk"), so_ho_so=dong.get("so_ho_so"))
        else:
            nap.keo_ve_cap_nhat(dong["uuid"], trang_thai="loi", loi=dong.get("loi"))
    return kq


def _mo_khoa_im_lang(token: str | None, uuid: str) -> None:
    """Mở khóa sau khi nạp lỗi; nuốt lỗi VPS (nếu VPS cũng down, job 15' tự mở khóa — TDD §7.2)."""
    try:
        vps.unlock(token, uuid)
    except VpsLoi:
        pass
