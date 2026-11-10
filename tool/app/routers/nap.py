"""NAP-05 (2/2) — nạp 1 HV vào GPLX_CSDT + danh sách giấy tờ mặc định theo khóa.

- GET  /local/giay-to  : danh sách giấy tờ bắt buộc theo (MaLoaiHS, HangDT) cho checklist UI.
- POST /local/nap      : nạp 1 HV (SoHoSo + 1 SP gộp app cũ + ghi ảnh hướng A + giấy tờ). GHI PRODUCTION.

Mọi ghi DB qua SP (TDD §10). Đọc danh mục (khóa, tham số, giấy tờ) bằng SELECT parameterized
— login tool được SELECT danh mục, chỉ cấm INSERT/UPDATE trực tiếp bảng nghiệp vụ (TDD §12).
"""
from __future__ import annotations
import base64

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field, field_validator

from app import nap, vps
from app.db import sqlserver_conn, sqlserver_cursor, ConfigChuaDay
from app.session import Phien, require_session
from app.vps import VpsLoi

router = APIRouter(prefix="/local", tags=["nap"])

# Tên tham số đường dẫn ảnh trong QTHT_ThamSoHT (đọc động, không hard-code — memory §6).
_TEN_TS_IMG = "IMG_PATH_CSDT"

# Giấy tờ mặc định theo loại HS + mã hạng trong danh mục. TenGT lấy tên ĐẦY ĐỦ từ DM_GiayTo, không lấy tên
# ngắn ở DM_LoaiHSo_GiayTo (memory §3). Mã hạng dò lần lượt qua `ma_hang_giay_to` (BUG giấy tờ trống 10/11/2026).
_SQL_GIAY_TO = """
    SELECT g.MaGT AS MaGT, dg.TenGT AS TenGT
    FROM DM_LoaiHSo_GiayTo g
    JOIN DM_GiayTo dg ON dg.MaGT = g.MaGT
    WHERE g.MaLoaiHS = %s AND g.MaHangGPLX = %s AND g.TrangThai = 1
    ORDER BY g.MaGT
"""


def ma_hang_giay_to(hang_dt: str | None, hang_gplx: str | None) -> list[str]:
    """Các mã hạng để tra DM_LoaiHSo_GiayTo, theo thứ tự ưu tiên, không trùng.

    Danh mục ghi mã không dấu chấm và không có mọi mã hạng mới: khóa B11 có HangDT 'B.01' nhưng danh mục ghi
    'B01'; khóa A2 có HangDT 'Am' mà danh mục chỉ có 'A2'. Tra đúng HangDT thì ra rỗng và hồ sơ nạp vào không có
    giấy tờ nào. Dò HangDT → HangDT bỏ dấu chấm → HangGPLX (đã kiểm mọi hạng A*/B*/C/C1 trên DB Nạp 10/11/2026)."""
    kq: list[str] = []
    for m in ((hang_dt or "").strip(), (hang_dt or "").strip().replace(".", ""), (hang_gplx or "").strip()):
        if m and m not in kq:
            kq.append(m)
    return kq


def doc_giay_to(cur, ma_loai_hs: int, hang_dt: str | None, hang_gplx: str | None) -> list[dict]:
    """Danh sách giấy tờ mặc định đầu tiên không rỗng theo `ma_hang_giay_to`. Rỗng = danh mục thiếu hẳn."""
    for ma in ma_hang_giay_to(hang_dt, hang_gplx):
        cur.execute(_SQL_GIAY_TO, (ma_loai_hs, ma))
        rows = cur.fetchall()
        if rows:
            return [{"ma_gt": r["MaGT"], "ten_gt": r["TenGT"]} for r in rows]
    return []


THIEU_ANH = "Thiếu ảnh — đã nạp nhưng ghi file ảnh lỗi. Bổ sung ảnh ở Tra cứu DB."

KHOA_DA_BC1 = "Khóa đã lập Báo cáo 1 — không nạp thêm học viên được. Chọn khóa khác rồi nạp lại."

KHONG_CO_GIAY_TO = ("Khóa này chưa có danh mục giấy tờ kèm theo trong DB Nạp — không nạp để tránh hồ sơ thiếu "
                    "giấy tờ. Báo quản trị bổ sung danh mục (scripts/bo_sung_giay_to_hang_moi.sql).")


class GiayTo(BaseModel):
    ma_gt: int
    ten_gt: str


@router.get("/giay-to", response_model=list[GiayTo])
def list_giay_to(ma_loai_hs: int = Query(...), hang_dt: str = Query(...), hang_gplx: str | None = None):
    """Giấy tờ bắt buộc mặc định cho (loại HS, hạng ĐT) — UI tick sẵn, cho bỏ tick."""
    try:
        with sqlserver_cursor() as cur:
            ds = doc_giay_to(cur, ma_loai_hs, hang_dt, hang_gplx)
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Không đọc được danh mục giấy tờ — kiểm kết nối.")
    return ds


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
    # "Chọn in GPLX": 1 Ghép · 2 Có thời hạn · 3 Không thời hạn. None → MẶC ĐỊNH THEO HẠNG khóa (server quyết:
    # mô tô A* → 3, ô tô → 2). Ngoài {1,2,3} → 422.
    chon_in_gplx: int | None = None
    # GPLX đã có (NAP-07): chỉ kiểm hình dạng ở đây; kiểm nghiệp vụ trong nap.dung_chuoi_gplx_da_co để nạp lô
    # báo lỗi đúng dòng thay vì 422 cả lô. None → không ghi gì.
    gplx_da_co: list[dict] | None = None

    @field_validator("chon_in_gplx")
    @classmethod
    def _chon_in_gplx_hop_le(cls, v):
        if v is not None and v not in nap.IN_GPLX_HOP_LE:
            raise ValueError("chon_in_gplx phải là 1 (ghép), 2 (có thời hạn) hoặc 3 (không thời hạn)")
        return v


def _nap_mot(body: NapIn) -> dict:
    """Lõi nạp 1 HV vào khóa (GHI PRODUCTION) — dùng chung cho nạp đơn và nạp lô.

    Raise: HTTPException (khóa không có / chưa cấu hình ảnh), ValueError (vượt độ dài /
    trùng CCCD / SP từ chối), ConfigChuaDay, Exception (lỗi DB). Trả dict kết quả đầy đủ.
    SP gộp atomic → lỗi tự rollback, bản ghi KHÔNG nửa vời.
    """
    so_cu = nap.so_gplx_keo_ve(body.uuid)  # CHANGES #101: số app web gửi từ trước giữ nguyên thì không chặn dạng
    nap.dung_chuoi_gplx_da_co(body.gplx_da_co, ngay_sinh=body.ngay_sinh, so_cu=so_cu)  # sai → báo ngay, trước khi đụng DB
    try:
        jp2 = base64.b64decode(body.anh_jp2_b64) if body.anh_jp2_b64 else None
    except Exception:
        raise HTTPException(status_code=400, detail="Ảnh .jp2 gửi lên không hợp lệ.")

    with sqlserver_conn() as conn:
        cur = conn.cursor(as_dict=True)

        # Khóa đích (nguồn chuẩn cho hạng/loại — không tin client)
        cur.execute(
            "SELECT MaKH, HangGPLX, HangDT, MaSoGTVT, "
            "CASE WHEN EXISTS (SELECT 1 FROM BaoCaoI b WHERE b.MaKH = KhoaHoc.MaKH) THEN 1 ELSE 0 END AS bc1 "
            "FROM KhoaHoc WHERE MaKH=%s AND TrangThai=1",
            (body.ma_khoa_hoc,),
        )
        k = cur.fetchone()
        if not k:
            raise HTTPException(status_code=404, detail="Không tìm thấy khóa học (hoặc khóa đã khóa).")
        # BR-012: khóa đã lập BC1 không thêm HV. Danh sách khóa đã ẩn khóa BC1, nhưng khóa có thể vừa lập BC1
        # sau lúc màn Nạp mở → kiểm lại ngay lúc ghi (cùng chốt chặn với sửa/xóa/đổi khóa).
        # Hồ sơ đã có vé nạp xong (đã vào DB, nạp lại chỉ để báo bù VPS — BUG-21) thì không ghi gì thêm,
        # nên không chặn; nếu không, khóa lập BC1 sau lần nạp đầu sẽ chặn báo bù mãi mãi.
        if k.get("bc1") and not nap._done_get(body.uuid):
            raise HTTPException(status_code=409, detail=KHOA_DA_BC1)
        khoa = {
            "ma_kh": k["MaKH"], "hang_gplx": k["HangGPLX"],
            "hang_dt": k["HangDT"], "ma_so_gtvt": k["MaSoGTVT"],
        }
        ma_loai_hs = nap.suy_ma_loai_hs(k["HangGPLX"], k["HangDT"])

        # Đường dẫn ảnh gốc (đọc động từ tham số hệ thống)
        cur.execute("SELECT GiaTriTS FROM QTHT_ThamSoHT WHERE TenTS=%s", (_TEN_TS_IMG,))
        row = cur.fetchone()
        if jp2 and not (row and row["GiaTriTS"]):
            raise HTTPException(status_code=502, detail="Chưa cấu hình IMG_PATH_CSDT trên DB đích.")
        img_path = row["GiaTriTS"] if row else ""

        # Giấy tờ: lấy danh sách mặc định theo khóa rồi lọc đúng dòng đã tick (tên từ DB)
        ten_theo_ma = {g["ma_gt"]: g["ten_gt"] for g in doc_giay_to(cur, ma_loai_hs, k["HangDT"], k["HangGPLX"])}
        if not ten_theo_ma:
            raise ValueError(KHONG_CO_GIAY_TO)
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
            "chon_in_gplx": body.chon_in_gplx,               # None → build_params_sp_gop chọn theo hạng khóa
            "gplx_da_co": body.gplx_da_co,
            "gplx_so_cu": so_cu,
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

    VPS lỗi ngay từ đầu → báo lỗi; lỗi giữa chừng → giữ phần đã kéo, dừng. Kéo lại **làm tươi**
    bản còn 'chờ nạp' (CHANGES #11). Trả số thêm mới + số làm tươi + tổng trong staging."""
    tong_moi = tong_tuoi = tong_reset = 0
    cursor: str | None = None
    for _ in range(50):  # chặn vòng lặp vô hạn (tối đa ~25.000 bản ghi/lượt kéo)
        try:
            rows = vps.keo(phien.vps_token, limit=limit, cursor=cursor)
        except VpsLoi as e:
            if tong_moi == 0 and tong_tuoi == 0:
                raise _loi_vps(e)
            break  # đã kéo được một phần → giữ, để nhân viên xử lý phần đã có
        if not rows:
            break
        moi, tuoi, reset = nap.keo_ve_upsert(rows)
        tong_moi += moi
        tong_tuoi += tuoi
        tong_reset += reset
        if len(rows) < limit:
            break
        cursor = rows[-1].get("created_at")

    # NAP-01 task 44 — đồng bộ xóa: bỏ dòng staging 'cho' mà collector đã XÓA ở app web (THU-05).
    # Dùng danh sách da-xoa (KHÔNG suy từ vắng mặt trong /keo — keo còn lọc lock + limit → bỏ nhầm).
    # Chỉ bỏ dòng CHƯA nạp ('cho'); dòng đã nạp/lỗi giữ nguyên. Lỗi bước này KHÔNG hỏng kéo (đã
    # kéo xong ở trên); mốc chỉ tiến khi lấy được danh sách — lần sau lấy lại từ mốc cũ.
    so_bo = 0
    try:
        kq_xoa = vps.da_xoa(phien.vps_token, since=nap.lay_moc_da_xoa())
        for u in kq_xoa.get("uuids", []):
            if nap.keo_ve_xoa_neu_cho(u):
                so_bo += 1
        if kq_xoa.get("moc"):
            nap.luu_moc_da_xoa(kq_xoa["moc"])
    except VpsLoi:
        pass  # kéo chính đã xong; đồng bộ xóa để lượt kéo sau, không chặn luồng

    return {"keo_ve": tong_moi, "lam_tuoi": tong_tuoi, "bo_da_xoa": so_bo,
            "dia_chi_reset": tong_reset, "thay_doi": len(nap.thay_doi_ds()), "tong": len(nap.keo_ve_danh_sach())}


# ---- NAP-08 — hồ sơ chưa nạp được app web cập nhật (TDD §10.8) --------------
@router.get("/nap/thay-doi")
def thay_doi_ds(phien: Phien = Depends(require_session)):
    """Danh sách hồ sơ CHƯA NẠP mà app web đổi sau lần kéo trước: học viên, mã trường đổi, lúc phát hiện,
    cờ nháp-giữ-ảnh-cũ. Chỉ nêu tên trường, không trả giá trị cá nhân."""
    return nap.thay_doi_ds()


class DaXemIn(BaseModel):
    uuids: list[str] | None = None
    tat_ca: bool = False
    loai: str | None = Field(None, max_length=20)  # chỉ gỡ loại này (ví dụ "anh" = Giữ ảnh cũ), không gỡ cả dòng


@router.post("/nap/thay-doi/da-xem")
def thay_doi_da_xem(body: DaXemIn, phien: Phien = Depends(require_session)):
    """"Đã xem": từng hồ sơ (`uuids`) hoặc tất cả (`tat_ca`). Không đụng VPS/DB."""
    if not body.tat_ca and not body.uuids:
        raise HTTPException(status_code=422, detail="Cần uuids hoặc tat_ca.")
    if body.uuids and len(body.uuids) > 1000:
        raise HTTPException(status_code=422, detail="Tối đa 1000 hồ sơ một lượt.")
    nap.thay_doi_da_xem(None if body.tat_ca else body.uuids, loai=body.loai)
    return {"ok": True}


@router.get("/nap/danh-sach")
def danh_sach_keo_ve():
    """Toàn bộ hàng đã kéo về (metadata). UI lọc Cần xử lý/Đã nạp + tìm + IN HOA (CHANGES #6/#10)."""
    return nap.keo_ve_danh_sach()


class BoQuaIn(BaseModel):
    uuids: list[str]  # uuid dòng cần bỏ khỏi hàng đợi (1 hay nhiều, mọi trạng thái)


@router.post("/nap/bo-qua")
def bo_khoi_hang_doi(body: BoQuaIn, phien: Phien = Depends(require_session)):
    """NAP-01 #51 — "Bỏ khỏi hàng đợi" 1 hay nhiều dòng, MỌI trạng thái. TOOL-LOCAL, KHÔNG đụng
    DB prod/VPS (tách bạch 'Xóa khỏi DB' của Tra cứu DB — tránh xóa nhầm prod). Dòng 'cho'/'loi'
    → tool nhớ "bỏ qua" (tombstone) nên "Kéo về từ VPS" sau KHÔNG mang về lại; 'xong' bỏ như cũ,
    không tombstone (xem nap.bo_qua_nhieu + lý do QLY-08). Thay endpoint DELETE /keo-ve/{uuid} cũ
    (task 38) — gộp 1 đường, tombstone xử theo trạng thái từng uuid. Dọn kèm nháp (ảnh PII)."""
    if len(body.uuids) > 1000:
        raise HTTPException(status_code=422, detail="Bỏ tối đa 1000 hồ sơ một lượt.")
    return nap.bo_qua_nhieu(body.uuids)


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


# ---- Nháp chuẩn bị BỀN (NAP-01, CHANGES #32, TDD §9.3a) ---------------------
class NhapChuanBiIn(BaseModel):
    dia_chi_json: str | None = None   # địa chỉ 2 cấp đã map (JSON); None = chưa map
    chi_tiet: str | None = None       # số nhà/thôn (NoiTT)
    noi_cap: str | None = None        # nơi cấp CCCD
    ngay_cap: str | None = None       # ngày cấp CCCD 'yyyymmdd' (CHANGES #43); None/'' = chưa đặt
    tick_json: str | None = None      # danh sách MaGT đã tick (JSON)
    jp2_b64: str | None = None        # ảnh đã đổi nền (.jp2 base64) — PII
    anh_preview: str | None = None    # PNG xem trước (base64)
    chon_in_gplx: int | None = None   # "Chọn in GPLX" (1/2/3) đã chọn; None = theo mặc định của hạng
    gplx_da_co_json: str | None = Field(None, max_length=8000)  # NULL chưa sửa · '[]' đã xóa hết · JSON bản đã sửa
    gplx_goc_json: str | None = Field(None, max_length=8000)    # bản keo_ve lúc nhân viên sửa

    @field_validator("chon_in_gplx")
    @classmethod
    def _chon_in_gplx_hop_le(cls, v):
        if v is not None and v not in nap.IN_GPLX_HOP_LE:
            raise ValueError("chon_in_gplx phải là 1, 2 hoặc 3")
        return v


@router.get("/nap/nhap")
def nhap_co_list(uuids: str = Query(..., description="danh sách uuid, ngăn bằng dấu phẩy"),
                 phien: Phien = Depends(require_session)):
    """Cờ NHẸ (co_dia_chi/co_anh/co_tick) cho 2 chip cả lưới — KHÔNG trả ảnh (§10.5).
    Dùng `?uuids=a,b,c`; uuid không có nháp → cả 3 cờ False."""
    ds = [u.strip() for u in uuids.split(",") if u.strip()]
    return nap.nhap_co(ds)


@router.get("/nap/nhap/{uuid}")
def nhap_doc_mot(uuid: str, phien: Phien = Depends(require_session)):
    """Đọc ĐẦY ĐỦ 1 nháp (kèm jp2_b64 + anh_preview) — gọi khi MỞ drawer Chuẩn bị.
    Chưa có nháp → trả rỗng (các trường None), KHÔNG 404 (dòng mới chưa chuẩn bị là bình thường)."""
    return nap.nhap_doc(uuid) or {
        "uuid": uuid, "dia_chi_json": None, "chi_tiet": None, "noi_cap": None, "ngay_cap": None,
        "tick_json": None, "jp2_b64": None, "anh_preview": None, "updated_at": None, "chon_in_gplx": None,
        "gplx_da_co_json": None, "gplx_goc_json": None,
    }


@router.put("/nap/nhap/{uuid}")
def nhap_luu_mot(uuid: str, body: NhapChuanBiIn, phien: Phien = Depends(require_session)):
    """Lưu (upsert) nháp chuẩn bị — gọi khi đóng drawer / debounce (không mỗi phím)."""
    nap.nhap_luu(uuid, **body.model_dump())
    return {"ok": True, "uuid": uuid}


@router.post("/nap/nhap/{uuid}/bo-anh")
def nhap_bo_anh_mot(uuid: str, phien: Phien = Depends(require_session)):
    """NAP-08 "Dùng ảnh mới": bỏ RIÊNG ảnh trong nháp, giữ địa chỉ/giấy tờ; ảnh mới tải lại từ VPS khi mở xử lý ảnh.
    Idempotent — không có nháp thì `da_bo=False`."""
    return {"ok": True, "uuid": uuid, "da_bo": nap.nhap_bo_anh(uuid)}


@router.delete("/nap/nhap/{uuid}")
def nhap_xoa_mot(uuid: str, phien: Phien = Depends(require_session)):
    """Nút "Xóa nháp" — operator chủ động dọn 1 nháp (gồm ảnh PII). Idempotent (TDD-decisions §11)."""
    nap.nhap_xoa(uuid)
    return {"ok": True, "uuid": uuid}


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
    gplx_theo_uuid = {str(it["uuid"]): it["gplx_da_co"] for it in items}

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
        # Phòng tuyến 2 (QLY-09, chặn phantom BUG-01) + báo bù (A1, 10/11/2026): vé cũ (`trung_uuid`, không
        # INSERT) nghĩa là lần trước đã vào DB nhưng VPS chưa biết (lock vừa thành công ⇒ VPS chưa imported,
        # thường do mất mạng lúc báo da_nap). Chỉ báo bù khi học viên CÒN trong DB Nạp; không còn (đã bị xóa)
        # thì không báo — giữ đúng chốt chặn: không gắn imported cho bản ghi không có trong CSDT.
        if r.get("trung_uuid"):
            try:
                con = _con_trong_db_nap(r["ma_dk"])
            except Exception:
                _mo_khoa_im_lang(token, uuid)
                raise RuntimeError("Không kiểm được DB Nạp để báo bù cho VPS — kiểm kết nối rồi Nạp lại.")
            if not con:
                _mo_khoa_im_lang(token, uuid)
                raise RuntimeError(f"Đã từng nạp (MaDK {r['ma_dk']}) nhưng không còn trong DB Nạp — "
                                   "không báo VPS; xem panel Đối soát.")
        try:
            vps.da_nap(token, uuid, r["ma_dk"])
        except VpsLoi:
            _mo_khoa_im_lang(token, uuid)
            raise RuntimeError(f"Đã nạp vào DB Nạp (MaDK {r['ma_dk']}) nhưng chưa báo được VPS — "
                               "bấm Nạp lại để báo bù (không tạo trùng).")
        kq = {"ma_dk": r["ma_dk"], "so_ho_so": r["so_ho_so"], "so_giay_to": r["so_giay_to"]}
        # A5 (10/11/2026): HV đã vào DB nhưng ghi file ảnh lỗi → vẫn tính đã nạp (không nạp lại kẻo trùng)
        # nhưng kèm cảnh báo để người nạp bổ sung ảnh, không báo xanh im lặng.
        if r.get("anh_loi"):
            kq["canh_bao"] = THIEU_ANH
        return kq

    kq = nap.nap_lo(items, nap_fn)
    for dong in kq["ket_qua"]:
        if dong["ok"]:
            nap.keo_ve_cap_nhat(dong["uuid"], trang_thai="xong", loi=dong.get("canh_bao"),
                                ma_dk=dong.get("ma_dk"), so_ho_so=dong.get("so_ho_so"),
                                gplx_da_co=gplx_theo_uuid.get(str(dong["uuid"])))  # ghi TRƯỚC khi xóa nháp
            nap.nhap_xoa(dong["uuid"])  # nạp xong → dọn nháp bền kèm ảnh PII (CHANGES #32)
        else:
            nap.keo_ve_cap_nhat(dong["uuid"], trang_thai="loi", loi=dong.get("loi"))
    return kq


def _con_trong_db_nap(ma_dk: str) -> bool:
    """Học viên MaDK còn trong DB Nạp không (dùng trước khi báo bù da_nap cho vé cũ). Lỗi kết nối → ném ra."""
    with sqlserver_cursor() as cur:
        cur.execute("SELECT 1 AS co FROM NguoiLX_HoSo WHERE MaDK=%s", (ma_dk,))
        return cur.fetchone() is not None


def _mo_khoa_im_lang(token: str | None, uuid: str) -> None:
    """Mở khóa sau khi nạp lỗi; nuốt lỗi VPS (nếu VPS cũng down, job 15' tự mở khóa — TDD §7.2)."""
    try:
        vps.unlock(token, uuid)
    except VpsLoi:
        pass
