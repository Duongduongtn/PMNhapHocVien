// Parse chuỗi QR mặt trước CCCD gắn chip (chuẩn Bộ Công an 2021, TT 06/2021).
// Tham khảo cách parse từ dự án webThanhdat (cùng ngành) — xem memory ref-quet-qr-cccd.
// Chuỗi tách bằng "|", 6 hoặc 7 trường (CMND cũ tùy có):
//   CCCD(12) | [CMND cũ(9)] | Họ tên | Ngày sinh(ddMMyyyy) | Giới tính(Nam/Nữ) | Nơi TT | Ngày cấp(ddMMyyyy)
// Hàm thuần, không phụ thuộc DOM → test đơn vị (mức 2) bám trực tiếp vào đây.

export type GioiTinh = "Nam" | "Nữ";

// Các trường hiển thị trên màn preview để user kiểm/sửa (định dạng Việt Nam).
export interface CccdFields {
  soCccd: string; // 12 số
  soCmndCu: string; // "" hoặc 9 số
  hoTen: string;
  ngaySinh: string; // "dd/mm/yyyy" hoặc "yyyy" (CCCD chỉ ghi năm)
  gioiTinh: GioiTinh;
  noiThuongTru: string;
  ngayCap: string; // "dd/mm/yyyy"
}

export type ParseResult = { ok: true; data: CccdFields } | { ok: false; message: string };

const RE_8 = /^\d{8}$/;

function laSoHet(s: string): boolean {
  return s.length > 0 && /^\d+$/.test(s);
}

// ddMMyyyy → "dd/mm/yyyy". Chỉ có năm (dd=00, MM=00) + choChiNam → "yyyy". Sai → null.
function docNgay(s: string, choChiNam: boolean): string | null {
  if (!RE_8.test(s)) return null;
  const dd = s.slice(0, 2);
  const mm = s.slice(2, 4);
  const yyyy = s.slice(4, 8);
  const y = Number(yyyy);
  if (y < 1900 || y > 2100) return null;
  if (choChiNam && dd === "00" && mm === "00") return yyyy;
  const d = Number(dd);
  const m = Number(mm);
  if (m < 1 || m > 12 || d < 1 || d > 31) return null;
  const dt = new Date(y, m - 1, d);
  if (dt.getFullYear() !== y || dt.getMonth() !== m - 1 || dt.getDate() !== d) return null;
  return `${dd}/${mm}/${yyyy}`;
}

function docGioiTinh(s: string): GioiTinh | null {
  const t = s.trim();
  if (t === "Nam") return "Nam";
  if (t === "Nữ" || t === "Nu" || t === "Nử") return "Nữ";
  return null;
}

export function parseCccdQr(raw: string): ParseResult {
  const input = (raw ?? "").trim();
  if (!input) return { ok: false, message: "Chuỗi QR rỗng" };

  const parts = input.split("|").map((p) => p.trim());
  if (parts.length !== 6 && parts.length !== 7)
    return { ok: false, message: `Chuỗi QR không đúng chuẩn — cần 6 hoặc 7 trường, đọc được ${parts.length}` };

  const has7 = parts.length === 7;
  const soCccd = parts[0];
  const soCmndCu = has7 ? parts[1] : "";
  const hoTen = has7 ? parts[2] : parts[1];
  const ngaySinhRaw = has7 ? parts[3] : parts[2];
  const gioiTinhRaw = has7 ? parts[4] : parts[3];
  const noiTT = has7 ? parts[5] : parts[4];
  const ngayCapRaw = has7 ? parts[6] : parts[5];

  if (soCccd.length !== 12 || !laSoHet(soCccd)) return { ok: false, message: "Số CCCD phải có đúng 12 chữ số" };
  if (soCmndCu && (soCmndCu.length !== 9 || !laSoHet(soCmndCu)))
    return { ok: false, message: "Số CMND cũ phải có đúng 9 chữ số (nếu có)" };
  if (!hoTen) return { ok: false, message: "Họ tên rỗng" };

  const ngaySinh = docNgay(ngaySinhRaw, true);
  if (!ngaySinh) return { ok: false, message: "Ngày sinh không đúng định dạng ddMMyyyy" };

  const gt = docGioiTinh(gioiTinhRaw);
  if (!gt) return { ok: false, message: 'Giới tính phải là "Nam" hoặc "Nữ"' };

  if (!noiTT) return { ok: false, message: "Nơi thường trú rỗng" };

  const ngayCap = docNgay(ngayCapRaw, false);
  if (!ngayCap) return { ok: false, message: "Ngày cấp không đúng định dạng ddMMyyyy" };

  return { ok: true, data: { soCccd, soCmndCu, hoTen, ngaySinh, gioiTinh: gt, noiThuongTru: noiTT, ngayCap } };
}

// ---- Chuyển sang định dạng DB đích (TDD §6.2) ----

// "dd/mm/yyyy" | "yyyy" → "yyyymmdd" | "yyyy0000". Rỗng/sai → "".
export function ngaySinhToDb(s: string): string {
  const t = s.trim();
  if (/^\d{4}$/.test(t)) return `${t}0000`;
  const m = t.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!m) return "";
  return `${m[3]}${m[2]}${m[1]}`;
}

// "dd/mm/yyyy" → "yyyy-mm-dd" (ISO, cho cột date ngay_cap_cccd). Rỗng/sai → "".
export function ngayToIso(s: string): string {
  const m = s.trim().match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!m) return "";
  return `${m[3]}-${m[2]}-${m[1]}`;
}

export function gioiTinhToMF(g: GioiTinh): "M" | "F" {
  return g === "Nam" ? "M" : "F";
}

// ---- Suy Giới tính + Năm sinh từ số CCCD (gợi ý nhập nhanh) ----
// Số CCCD 12 số mã hóa sẵn ở chữ số thứ 4 (index 3): 0/1 = thế kỷ 20 (19xx),
// 2/3 = thế kỷ 21 (20xx), 4/5 = 21xx… — chẵn là Nam, lẻ là Nữ. Hai số kế (index 4-5)
// là năm sinh trong thế kỷ đó. Cần ≥ 6 chữ số đầu. Chỉ là GỢI Ý mặc định, user sửa được.
export function suyTuCccd(cccd: string): { gioiTinh: GioiTinh; namSinh: string } | null {
  const s = cccd.replace(/\D/g, "");
  if (s.length < 6) return null;
  const ma = Number(s[3]);
  const theKy = 1900 + Math.floor(ma / 2) * 100;
  const nam = theKy + Number(s.slice(4, 6));
  return { gioiTinh: ma % 2 === 0 ? "Nam" : "Nữ", namSinh: String(nam) };
}

// ---- Cảnh báo độ dài tên (EC-030) ----
// Giới hạn cột DB đích (nvarchar): HoVaTen ≤50, HoDemNLX ≤30, TenNLX ≤20, HoVaTenIn ≤25.
// Tách tên như tool nạp (NAP-05): từ cuối = Tên, phần còn lại = Họ đệm. Cảnh báo sớm
// để user sửa/cắt, giữ dấu tiếng Việt; không để tràn cột làm SP lỗi lúc nạp.
export interface CanhBaoTen {
  ten: string;
  max: number;
  dai: number;
}

export function kiemDoDaiTen(hoTen: string): CanhBaoTen[] {
  const full = hoTen.trim().replace(/\s+/g, " ");
  const tu = full ? full.split(" ") : [];
  const ten = tu.length ? tu[tu.length - 1] : "";
  const hoDem = tu.slice(0, -1).join(" ");
  const kt: CanhBaoTen[] = [
    { ten: "Họ và tên", max: 50, dai: full.length },
    { ten: "Họ đệm", max: 30, dai: hoDem.length },
    { ten: "Tên", max: 20, dai: ten.length },
    { ten: "Họ tên in", max: 25, dai: full.length },
  ];
  return kt.filter((x) => x.dai > x.max);
}

// ---- Vùng quét cho bộ quét thư viện qr-scanner (nhánh iPhone/iOS — BUG-14) ----
// iOS Safari không có BarcodeDetector → dùng QrScanner của thư viện. Mặc định thư viện chỉ
// quét vùng GIỮA khung (~2/3 cạnh ngắn) nên BỎ SÓT mã QR CCCD nằm lệch GÓC TRÊN PHẢI thẻ.
// Hàm này ép quét TOÀN khung hình + giữ độ phân giải (downscale tối đa 1024, không để tụt
// ~400 mặc định làm mất mã nhỏ). w/h ≤ 0 (video chưa sẵn) → mặc định 1280×720 an toàn.
export interface VungQuet {
  x: number;
  y: number;
  width: number;
  height: number;
  downScaledWidth: number;
  downScaledHeight: number;
}

export function tinhVungQuet(w: number, h: number): VungQuet {
  const vw = w > 0 ? w : 1280;
  const vh = h > 0 ? h : 720;
  return {
    x: 0,
    y: 0,
    width: vw,
    height: vh,
    downScaledWidth: Math.min(vw, 1024),
    downScaledHeight: Math.min(vh, 1024),
  };
}
