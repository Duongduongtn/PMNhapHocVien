// Ô "Chọn in GPLX" của phần mềm cũ (cboInGplx) — cột NguoiLX_HoSo.CHON_IN_GPLX.
// 1 = ghép (có TH + không TH) · 2 = có thời hạn · 3 = không thời hạn. Dữ liệu thật ở DB Nạp: ô tô → 2, mô tô → 3.
// PHẢN CHIẾU `nap.chon_in_gplx_mac_dinh` ở backend (A* → 3, còn lại → 2); backend vẫn quyết cuối khi không gửi giá trị.

export type InGplx = 1 | 2 | 3;

export const IN_GPLX_NHAN: Record<InGplx, string> = {
  2: "In 01 GPLX có thời hạn",
  3: "In 01 GPLX không thời hạn",
  1: "In 01 GPLX (ghép: có thời hạn + không thời hạn)",
};

/** Thứ tự hiện trong danh sách chọn: hai lựa chọn thường dùng trước, "ghép" cuối. */
export const IN_GPLX_THU_TU: InGplx[] = [2, 3, 1];

export const laMoTo = (hang: string | null | undefined): boolean => /^A/i.test((hang ?? "").trim());

/** Mặc định theo HẠNG của khóa: mô tô (A*) → không thời hạn; ô tô và hạng trống → có thời hạn. */
export const inGplxMacDinh = (hang: string | null | undefined): InGplx => (laMoTo(hang) ? 3 : 2);

export function laInGplx(v: unknown): v is InGplx {
  return v === 1 || v === 2 || v === 3;
}

/** Câu gợi ý dưới ô chọn: nói rõ khóa này là mô tô hay ô tô và vì sao đã điền sẵn. */
export function ghiChuMacDinh(hang: string | null | undefined): string {
  const loai = laMoTo(hang) ? "mô tô" : "ô tô";
  const h = (hang ?? "").trim();
  return `Khóa ${loai}${h ? ` (hạng ${h})` : ""} → điền sẵn "${IN_GPLX_NHAN[inGplxMacDinh(hang)]}" — sửa nếu hồ sơ này in khác.`;
}
