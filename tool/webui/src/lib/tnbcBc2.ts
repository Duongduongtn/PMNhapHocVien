// Logic thuần cho số BC2 (= MaBCII, TNB-03). Khớp `tn_bc2_rules.khoa_so_bc2` / `kiem_so_bc2` của backend.

/** MaBCII là varchar(13) trong DB. */
export const DO_DAI_MA_BCII = 13;

/** Khóa so sánh: không phân biệt hoa/thường, `Ð` (U+00D0, dạng DB trả ra) = `Đ` (U+0110, dạng nhân viên gõ). */
export const khoaSoBc2 = (s: string | null | undefined): string =>
  (s ?? "").trim().replace(/Ð/g, "Đ").replace(/ð/g, "đ").toLowerCase();

/** Lý do chặn số BC2 (rỗng = hợp lệ): thiếu · quá dài · trùng với số đã có. */
export function kiemSoBc2(so: string, daCo: Iterable<string>): string[] {
  const t = so.trim();
  if (!t) return ["Cần nhập số báo cáo"];
  const loi: string[] = [];
  if (t.length > DO_DAI_MA_BCII) loi.push(`Số báo cáo tối đa ${DO_DAI_MA_BCII} ký tự`);
  const k = khoaSoBc2(t);
  for (const x of daCo) {
    if (khoaSoBc2(x) === k) {
      loi.push(`Số BC2 ${t} đã tồn tại — đổi số khác`);
      break;
    }
  }
  return loi;
}
