// Bỏ dấu tiếng Việt + thường hóa, để tìm kiếm không phân biệt dấu (TDD §6.4).
// NFD tách dấu kết hợp rồi xóa; đ/Đ không tách qua NFD nên xử riêng.
export function boDau(s: string): string {
  return s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase()
    .trim();
}

// Khớp 1 bản ghi theo chuỗi tìm: theo tên (bỏ dấu 2 vế) HOẶC số CCCD (chứa chuỗi số).
export function khopTim(q: string, hoTen: string | null, soCccd: string | null): boolean {
  const query = q.trim();
  if (!query) return true;
  const theoTen = boDau(hoTen ?? "").includes(boDau(query));
  const soQuery = query.replace(/\D/g, "");
  const theoCccd = soQuery.length > 0 && (soCccd ?? "").includes(soQuery);
  return theoTen || theoCccd;
}
