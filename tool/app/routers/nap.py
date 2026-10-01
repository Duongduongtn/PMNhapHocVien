"""NAP-05 (2/2) — nạp 1 HV vào GPLX_CSDT + danh sách giấy tờ mặc định theo khóa.

- GET  /local/giay-to  : danh sách giấy tờ bắt buộc theo (MaLoaiHS, HangDT) cho checklist UI.
- POST /local/nap      : nạp 1 HV (SoHoSo + 3 SP + .jp2 + giấy tờ đã tick). GHI PRODUCTION.

Mọi ghi DB qua SP (TDD §10). Đọc danh mục (khóa, tham số, giấy tờ) bằng SELECT parameterized
— login tool được SELECT danh mục, chỉ cấm INSERT/UPDATE trực tiếp bảng nghiệp vụ (TDD §12).
"""
from __future__ import annotations
import base64

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app import nap
from app.db import sqlserver_conn, sqlserver_cursor, ConfigChuaDay

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


class NapIn(BaseModel):
    uuid: str                       # idempotent + truy vết + chống mồ côi
    ma_khoa_hoc: str
    ho_ten: str
    ngay_sinh: str                  # varchar(8) yyyymmdd
    gioi_tinh: str                  # 'M' / 'F'
    so_cmt: str
    ngay_cap_cmt: str | None = None
    noi_cap_cmt: str | None = None
    noi_tt: str = ""
    noi_tt_ma_dvhc: str
    noi_tt_ma_dvql: str
    noi_ct: str | None = None
    noi_ct_ma_dvhc: str | None = None
    noi_ct_ma_dvql: str | None = None
    giay_to_tick: list[int] = []    # danh sách MaGT đã tick
    anh_jp2_b64: str | None = None  # ảnh .jp2 đã xử lý (NAP-04); None → nạp thiếu ảnh (BR-011)


@router.post("/nap")
def nap_ho_so(body: NapIn):
    """Nạp 1 HV vào khóa (GHI PRODUCTION). Lỗi giữa chừng → compensation, bản ghi giữ pending."""
    try:
        jp2 = base64.b64decode(body.anh_jp2_b64) if body.anh_jp2_b64 else None
    except Exception:
        raise HTTPException(status_code=400, detail="Ảnh .jp2 gửi lên không hợp lệ.")

    try:
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
                "noi_tt": body.noi_tt, "noi_tt_ma_dvhc": body.noi_tt_ma_dvhc,
                "noi_tt_ma_dvql": body.noi_tt_ma_dvql,
                "noi_ct": body.noi_ct or body.noi_tt,
                "noi_ct_ma_dvhc": body.noi_ct_ma_dvhc or body.noi_tt_ma_dvhc,
                "noi_ct_ma_dvql": body.noi_ct_ma_dvql or body.noi_tt_ma_dvql,
            }
            r = nap.nap_mot_hv(conn, hv, khoa, jp2, img_path, "operator", body.uuid, giay_to)
    except HTTPException:
        raise
    except ConfigChuaDay as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:                       # validate độ dài cột → báo cho UI sửa
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Nạp hồ sơ thất bại — bản ghi giữ pending, thử lại.")

    return {"ma_dk": r["ma_dk"], "so_ho_so": r["so_ho_so"], "so_giay_to": r["so_giay_to"]}
