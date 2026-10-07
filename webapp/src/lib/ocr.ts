// THU-06: đọc chữ in MẶT TRƯỚC CCCD bằng OCR làm lối nhập dự phòng khi QR không quét được.
// Quyết định kỹ thuật chốt ở TDD §6.7 (v5.8) + TDD-decisions §20:
//   - Engine: Tesseract.js (WASM, chạy CLIENT + dữ liệu 'vie') — RÀO CỨNG PII: ảnh CCCD
//     KHÔNG rời máy, không gửi server/dịch vụ ngoài.
//   - Tách trường: OCR TOÀN ảnh rồi regex theo NHÃN in trên thẻ (bền với ảnh chụp tay
//     nghiêng/cắt lệch hơn cắt-vùng-theo-tọa-độ).
//   - Mốc fail = đọc được Số CCCD hợp lệ 12 số hay không (CCCD là trường định danh; thiếu
//     nó thì hồ sơ vô nghĩa → báo fail, KHÔNG điền bừa). Có CCCD → điền phần đọc được,
//     trường thiếu/không chắc để trống + đánh dấu cho nhân viên soát.
//   - Downscale cạnh dài ≤ 1600px TRƯỚC khi OCR (tránh Tesseract.js treo/sập tab điện thoại).
//   - NGÀY CẤP không in ở mặt trước (ở mặt sau) → THU-06 KHÔNG đọc; để trống + đánh dấu,
//     nhân viên nhập tay (user chốt A, 07/10/2026 — Done-khi THU-06 sửa qua /capnhat).
//
// Phần TÁCH TRƯỜNG (tachTruongTuText) là hàm THUẦN, không DOM → test đơn vị (mức 2) bám đây.
// Phần chụp/downscale/chạy Tesseract cần DOM + worker → kiểm TAY mức 1 trên thẻ + điện thoại thật.

import { createWorker, type Worker } from "tesseract.js";
import type { GioiTinh } from "./qr";
import { boDau } from "./text";

// 5 trường OCR đọc được từ MẶT TRƯỚC (ngayCap ở mặt sau → luôn rỗng, nhập tay).
export const TRUONG_OCR = ["soCccd", "hoTen", "ngaySinh", "gioiTinh", "noiThuongTru"] as const;

// Kết quả OCR nạp vào màn xác nhận dùng chung (THU-01/02). Trường không đọc được → "".
export interface OcrFields {
  soCccd: string; // 12 số, hoặc ""
  hoTen: string;
  ngaySinh: string; // "dd/mm/yyyy" hoặc ""
  gioiTinh: GioiTinh | "";
  noiThuongTru: string;
  ngayCap: ""; // luôn rỗng — mặt trước không in ngày cấp; nhân viên nhập tay
}

export interface OcrKetQua {
  data: OcrFields;
  danhDau: string[]; // key các trường trống/không chắc → UI đánh dấu để nhân viên soát
}

export type OcrResult =
  | { ok: false; message: string }
  | { ok: true; ket: OcrKetQua };

const CANH_TOI_DA = 1600;

// ---- Tách trường từ text OCR (THUẦN — test đơn vị) ----

function dongSach(raw: string): string[] {
  return raw.split(/\r?\n/).map((d) => d.trim()).filter(Boolean);
}

// Phần sau dấu ":" đầu tiên trên dòng (nhãn thẻ in "Nhãn / Label: giá trị").
function sauDauHai(dong: string): string {
  const i = dong.indexOf(":");
  return i >= 0 ? dong.slice(i + 1).trim() : "";
}

// Chỉ số dòng chứa 1 trong các nhãn (khớp theo bản BỎ DẤU — OCR hay rụng dấu). -1 nếu không có.
function timDongNhan(dong: string[], nhanBoDau: string[]): number {
  return dong.findIndex((d) => {
    const bd = boDau(d);
    return nhanBoDau.some((n) => bd.includes(n));
  });
}

// Giá trị 1 dòng theo nhãn: lấy sau ":"; rỗng (nhãn đứng riêng) → lấy dòng kế nếu dòng kế
// KHÔNG phải một nhãn khác.
function giaTriTheoNhan(dong: string[], nhanBoDau: string[], nhanKhac: string[]): string {
  const i = timDongNhan(dong, nhanBoDau);
  if (i < 0) return "";
  const v = sauDauHai(dong[i]);
  if (v) return v;
  const ke = dong[i + 1];
  if (ke && !nhanKhac.some((n) => boDau(ke).includes(n))) return ke.trim();
  return "";
}

// Số CCCD: cụm 12 chữ số (có thể xen 1 khoảng trắng/chấm giữa các số). "" nếu không có.
function timSoCccd(raw: string): string {
  const cum = raw.match(/\d(?:[ .]?\d){11,}/g);
  if (!cum) return "";
  for (const c of cum) {
    const so = c.replace(/\D/g, "");
    if (so.length === 12) return so;
  }
  return "";
}

// "d/m/yyyy" (hoặc - . làm phân cách) → "dd/mm/yyyy" hợp lệ, zero-pad. Sai → "".
function chuanNgay(s: string): string {
  const m = s.match(/(\d{1,2})\s*[\/\-.]\s*(\d{1,2})\s*[\/\-.]\s*(\d{4})/);
  if (!m) return "";
  const d = Number(m[1]);
  const mo = Number(m[2]);
  const y = Number(m[3]);
  if (mo < 1 || mo > 12 || d < 1 || d > 31 || y < 1900 || y > 2100) return "";
  const dt = new Date(y, mo - 1, d);
  if (dt.getFullYear() !== y || dt.getMonth() !== mo - 1 || dt.getDate() !== d) return "";
  return `${String(d).padStart(2, "0")}/${String(mo).padStart(2, "0")}/${y}`;
}

// Giới tính: cắt phần sau "Quốc tịch"/"Nationality" (cùng dòng) rồi dò token Nam/Nữ.
// Tránh khớp nhầm "Nam" trong "Việt Nam".
function docGioiTinh(v: string): GioiTinh | "" {
  const bd = boDau(v);
  const cat = ["quoc tich", "nationality"]
    .map((k) => bd.indexOf(k))
    .filter((i) => i >= 0)
    .sort((a, b) => a - b)[0];
  const phan = cat !== undefined ? v.slice(0, cat) : v;
  const t = boDau(phan);
  if (/\bnu\b|nữ|nử/.test(phan) || /\bnu\b/.test(t)) return "Nữ";
  if (/\bnam\b/.test(t)) return "Nam";
  return "";
}

/** Tách 5 trường mặt trước từ text OCR. Không có CCCD 12 số → fail (không điền gì). */
export function tachTruongTuText(raw: string): OcrResult {
  const soCccd = timSoCccd(raw ?? "");
  if (!soCccd) {
    return {
      ok: false,
      message: "Không đọc được Số CCCD (12 số) từ ảnh — chụp lại rõ/gần hơn hoặc chuyển Nhập tay.",
    };
  }

  const dong = dongSach(raw);
  const NHAN = {
    hoTen: ["ho va ten", "full name"],
    ngaySinh: ["ngay sinh", "date of birth"],
    gioiTinh: ["gioi tinh", "sex"],
    noiTT: ["noi thuong tru", "place of residence"],
  };
  const MOI_NHAN = [...NHAN.hoTen, ...NHAN.ngaySinh, ...NHAN.gioiTinh, ...NHAN.noiTT];

  const hoTen = giaTriTheoNhan(dong, NHAN.hoTen, MOI_NHAN)
    .replace(/[^\p{L}\p{M} ]+/gu, "")
    .replace(/\s+/g, " ")
    .trim();
  const ngaySinh = chuanNgay(giaTriTheoNhan(dong, NHAN.ngaySinh, MOI_NHAN));
  const gioiTinh = docGioiTinh(giaTriTheoNhan(dong, NHAN.gioiTinh, MOI_NHAN));

  // Nơi thường trú: nối các dòng sau nhãn tới khi gặp nhãn khác / "có giá trị đến" / "quê quán".
  let noiThuongTru = "";
  const iTT = timDongNhan(dong, NHAN.noiTT);
  if (iTT >= 0) {
    const DUNG = ["co gia tri den", "date of expiry", "que quan", "place of origin", "dac diem", ...MOI_NHAN];
    const phan: string[] = [];
    const dau = sauDauHai(dong[iTT]);
    if (dau) phan.push(dau);
    for (let k = iTT + 1; k < dong.length; k++) {
      if (DUNG.some((n) => boDau(dong[k]).includes(n))) break;
      phan.push(dong[k]);
    }
    noiThuongTru = phan.join(", ").replace(/\s*,\s*/g, ", ").replace(/\s+/g, " ").trim();
  }

  const data: OcrFields = { soCccd, hoTen, ngaySinh, gioiTinh, noiThuongTru, ngayCap: "" };
  const danhDau = [
    ...TRUONG_OCR.filter((k) => !data[k]),
    "ngayCap", // luôn đánh dấu — nhân viên nhập tay
  ];
  return { ok: true, ket: { data, danhDau } };
}

// ---- Chụp/đọc ảnh (DOM + Tesseract worker — kiểm tay mức 1) ----

function taiAnh(url: string): Promise<HTMLImageElement> {
  return new Promise((res, rej) => {
    const img = new Image();
    img.onload = () => res(img);
    img.onerror = () => rej(new Error("Không đọc được ảnh"));
    img.src = url;
  });
}

// Vẽ ảnh vào canvas thu nhỏ (cạnh dài ≤ 1600px) để Tesseract chạy nhẹ, không treo máy.
async function veCanvasThuNho(anh: Blob): Promise<HTMLCanvasElement> {
  const url = URL.createObjectURL(anh);
  try {
    const img = await taiAnh(url);
    const canhGoc = Math.max(img.naturalWidth, img.naturalHeight) || 1;
    const tyLe = Math.min(1, CANH_TOI_DA / canhGoc);
    const w = Math.max(1, Math.round(img.naturalWidth * tyLe));
    const h = Math.max(1, Math.round(img.naturalHeight * tyLe));
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("Không tạo được canvas");
    ctx.drawImage(img, 0, 0, w, h);
    return canvas;
  } finally {
    URL.revokeObjectURL(url);
  }
}

/**
 * Đọc CCCD từ ảnh mặt trước. OCR chạy CLIENT (ảnh không rời máy). Đọc xong HỦY ảnh khỏi
 * bộ nhớ (xóa canvas, thu hồi URL) — caller (task 80) cũng không được giữ lại Blob.
 */
export async function docTheCccd(anh: Blob): Promise<OcrResult> {
  let canvas: HTMLCanvasElement | null = null;
  let worker: Worker | null = null;
  try {
    canvas = await veCanvasThuNho(anh);
    worker = await createWorker("vie");
    const { data } = await worker.recognize(canvas);
    return tachTruongTuText(data.text);
  } catch {
    return { ok: false, message: "Không chạy được OCR trên thiết bị này — thử lại hoặc chuyển Nhập tay." };
  } finally {
    if (worker) await worker.terminate();
    if (canvas) {
      canvas.width = 0;
      canvas.height = 0; // bỏ pixel ảnh thẻ khỏi bộ nhớ (PII)
    }
  }
}
