// Nháp hồ sơ thu thập giữ ở máy (localStorage) sau khi quét/sửa xong (THU-01).
// THU-02 đọc lại nháp để chụp ảnh chân dung + gửi VPS. Trường khớp HoSoIn của server
// (server/app/routers/ho_so.py) nên THU-02 chỉ cần thêm ảnh rồi POST, không phải map lại.
import { gioiTinhToMF, ngaySinhToDb, ngayToIso, type CccdFields } from "./qr";

export interface HoSoNhap {
  uuid: string; // client sinh — idempotency key khi gửi (TDD §6.3)
  so_cccd: string;
  so_cmnd_cu: string; // "" nếu không có
  ho_ten: string;
  ngay_sinh: string; // yyyymmdd | yyyy0000
  gioi_tinh: "M" | "F";
  noi_tt_raw: string;
  ngay_cap_cccd: string; // yyyy-mm-dd | ""
  luc: string; // ISO — lúc giữ nháp
}

const KEY = "pmcs_ho_so_nhap";

export function taoUuid(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") return crypto.randomUUID();
  // Fallback RFC4122 v4 khi trình duyệt cũ không có crypto.randomUUID.
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

// Dựng bản nháp từ các trường đã xác nhận trên màn preview (đổi sang định dạng DB).
export function tuCccd(uuid: string, f: CccdFields): HoSoNhap {
  return {
    uuid,
    so_cccd: f.soCccd,
    so_cmnd_cu: f.soCmndCu.trim(),
    ho_ten: f.hoTen.trim().replace(/\s+/g, " "),
    ngay_sinh: ngaySinhToDb(f.ngaySinh),
    gioi_tinh: gioiTinhToMF(f.gioiTinh),
    noi_tt_raw: f.noiThuongTru.trim(),
    ngay_cap_cccd: ngayToIso(f.ngayCap),
    luc: new Date().toISOString(),
  };
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
  try {
    const ds = dsNhap().filter((x) => x.uuid !== hs.uuid);
    ds.unshift(hs);
    localStorage.setItem(KEY, JSON.stringify(ds));
  } catch {
    // localStorage không dùng được (chế độ riêng tư) — bỏ qua, không chặn luồng.
  }
}
