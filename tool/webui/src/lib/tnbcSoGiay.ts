// Logic thuần cho số giấy chứng nhận tốt nghiệp (CNTN) — dạng `N1|7282` (TNB-01, TDD §11F.2).
// Không gọi mạng. Khóa so sánh khớp `tn_bc2_rules.khoa_so_giay` của backend.

/** Khóa so sánh số giấy: bỏ `|` và khoảng trắng, không phân biệt hoa/thường. */
export const khoaSoGiay = (s: string | null | undefined): string => (s ?? "").replace(/[|\s]/g, "").toLowerCase();

/** `N1|7282` → { tienTo: "N1|", so: 7282, rong: 4 }; không kết thúc bằng số → null. */
export function tachSoGiay(s: string | null | undefined): { tienTo: string; so: number; rong: number } | null {
  const m = /^(.*?)(\d+)$/.exec((s ?? "").trim());
  return m ? { tienTo: m[1], so: Number(m[2]), rong: m[2].length } : null;
}

/** Số giấy thứ `n` kể từ `batDau` (giữ tiền tố và độ rộng chữ số: `N1|0099` + 1 → `N1|0100`). */
export function congSoGiay(batDau: string, n: number): string | null {
  const t = tachSoGiay(batDau);
  return t ? t.tienTo + String(t.so + n).padStart(t.rong, "0") : null;
}

/**
 * Đánh số liên tiếp từ `batDau` cho danh sách mã đăng ký theo đúng thứ tự truyền vào.
 * Trả null nếu số bắt đầu không kết thúc bằng chữ số.
 */
export function danhLienTiep(batDau: string, dsMaDk: string[]): Record<string, string> | null {
  if (!tachSoGiay(batDau)) return null;
  const kq: Record<string, string> = {};
  dsMaDk.forEach((ma, i) => {
    kq[ma] = congSoGiay(batDau, i) as string;
  });
  return kq;
}

/** Tách văn bản dán từ Excel (một cột) thành các số giấy; bỏ dòng trống, lấy ô cuối nếu dán nhiều cột. */
export function tachCotDan(text: string): string[] {
  return text
    .split(/\r?\n/)
    .map((dong) => dong.split("\t").pop()!.trim())
    .filter((v) => v !== "");
}

/** Các khóa số giấy xuất hiện từ hai lần trở lên trong `cacSo` (bỏ ô trống). */
export function khoaTrungTrongLo(cacSo: Iterable<string>): Set<string> {
  const dem = new Map<string, number>();
  for (const so of cacSo) {
    const k = khoaSoGiay(so);
    if (k) dem.set(k, (dem.get(k) ?? 0) + 1);
  }
  return new Set([...dem].filter(([, n]) => n > 1).map(([k]) => k));
}
