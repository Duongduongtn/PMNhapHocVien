// Nháp hồ sơ thu thập giữ ở máy (localStorage): quét/nhập xong (THU-01) → chụp ảnh + gửi (THU-02).
// Giữ nháp để gửi lại khi mất mạng (TDD §6.3, idempotent theo uuid). Trường khớp HoSoIn server.
import { gioiTinhToMF, ngaySinhToDb, ngayToIso, type CccdFields } from "./qr";
import type { HoSoGui } from "./api";

export interface HoSoNhap {
  uuid: string; // client sinh — idempotency key khi gửi
  so_cccd: string;
  so_cmnd_cu: string;
  ho_ten: string;
  ngay_sinh: string; // yyyymmdd | yyyy0000
  gioi_tinh: "M" | "F";
  noi_tt_raw: string;
  ngay_cap_cccd: string; // yyyy-mm-dd | ""
  noi_cap_cccd: string; // "" — QR không có, để tool/sau điền
  anh_data_url?: string; // ảnh chân dung JPEG (data URL) — giữ để gửi lại khi offline
  luc: string; // ISO — lúc giữ nháp
}

const KEY = "pmcs_ho_so_nhap";

export function taoUuid(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") return crypto.randomUUID();
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

// Dựng bản nháp từ các trường đã xác nhận trên màn preview (đổi sang định dạng DB).
export function tuCccd(uuid: string, f: CccdFields): HoSoNhap {
  return {
    uuid,
    so_cccd: f.soCccd.trim(),
    so_cmnd_cu: f.soCmndCu.trim(),
    ho_ten: f.hoTen.trim().replace(/\s+/g, " "),
    ngay_sinh: ngaySinhToDb(f.ngaySinh),
    gioi_tinh: gioiTinhToMF(f.gioiTinh),
    noi_tt_raw: f.noiThuongTru.trim(),
    ngay_cap_cccd: ngayToIso(f.ngayCap),
    noi_cap_cccd: "",
    luc: new Date().toISOString(),
  };
}

function ghi(ds: HoSoNhap[]): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(ds));
  } catch {
    // localStorage không dùng được (chế độ riêng tư / đầy) — bỏ qua, không chặn luồng.
  }
}

export function dsNhap(): HoSoNhap[] {
  try {
    const s = localStorage.getItem(KEY);
    return s ? (JSON.parse(s) as HoSoNhap[]) : [];
  } catch {
    return [];
  }
}

export function luuNhap(hs: HoSoNhap): void {
  ghi([hs, ...dsNhap().filter((x) => x.uuid !== hs.uuid)]);
}

export function capNhatNhap(uuid: string, patch: Partial<HoSoNhap>): void {
  const ds = dsNhap();
  const i = ds.findIndex((x) => x.uuid === uuid);
  if (i >= 0) {
    ds[i] = { ...ds[i], ...patch };
    ghi(ds);
  }
}

export function xoaNhap(uuid: string): void {
  ghi(dsNhap().filter((x) => x.uuid !== uuid));
}

// Map nháp → payload gửi server (chuỗi rỗng → null để Pydantic nhận date/optional đúng).
export function sangHoSoGui(hs: HoSoNhap): HoSoGui {
  return {
    uuid: hs.uuid,
    so_cccd: hs.so_cccd || null,
    so_cmnd_cu: hs.so_cmnd_cu || null,
    ho_ten: hs.ho_ten || null,
    ngay_sinh: hs.ngay_sinh || null,
    gioi_tinh: hs.gioi_tinh,
    noi_tt_raw: hs.noi_tt_raw || null,
    ngay_cap_cccd: hs.ngay_cap_cccd || null,
    noi_cap_cccd: hs.noi_cap_cccd || null,
  };
}
