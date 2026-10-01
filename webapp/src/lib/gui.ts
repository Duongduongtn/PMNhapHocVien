// Gửi hồ sơ lên VPS + hàng đợi gửi lại khi mất mạng (TDD §6.3).
// Idempotent theo uuid: gửi lại bản đã nhận không nhân đôi (server trả 200).
import { guiAnh, guiHoSo } from "./api";
import { dsNhap, sangHoSoGui, xoaNhap, type HoSoNhap } from "./draft";

function dataUrlToBlob(durl: string): Blob {
  const [head, b64] = durl.split(",");
  const mime = head.match(/:(.*?);/)?.[1] ?? "image/jpeg";
  const bin = atob(b64);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  return new Blob([arr], { type: mime });
}

// Gửi một nháp. Thành công (kể cả đã gửi trước đó) → xóa nháp. Lỗi mạng/HTTP → ném ra.
export async function guiMot(hs: HoSoNhap): Promise<void> {
  const kq = await guiHoSo(sangHoSoGui(hs));
  // Chỉ gửi ảnh khi bản ghi còn pending và chưa có ảnh (tránh 409 lúc gửi lại sau khi đã nạp).
  if (kq.trang_thai === "pending" && !kq.co_anh && hs.anh_data_url) {
    await guiAnh(hs.uuid, dataUrlToBlob(hs.anh_data_url));
  }
  xoaNhap(hs.uuid);
}

// Gửi lại mọi nháp còn tồn (gọi khi có mạng trở lại). Trả số bản gửi được.
export async function guiLaiTatCa(): Promise<number> {
  let ok = 0;
  for (const hs of dsNhap()) {
    try {
      await guiMot(hs);
      ok += 1;
    } catch {
      // vẫn mất mạng hoặc lỗi — để lần sau
    }
  }
  return ok;
}

// Đăng ký 1 lần: có mạng trở lại → tự gửi lại nháp còn tồn.
let daDangKy = false;
export function dangKyGuiLai(): void {
  if (daDangKy || typeof window === "undefined") return;
  daDangKy = true;
  window.addEventListener("online", () => void guiLaiTatCa());
}
