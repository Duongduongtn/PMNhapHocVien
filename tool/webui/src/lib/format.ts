// Helper định dạng chuẩn Việt Nam (vi-VN)
export const soVN = (n: number) => new Intl.NumberFormat("vi-VN").format(n);
export const tienVN = (n: number) => soVN(n) + " đồng";
export const phanTram = (n: number) =>
  new Intl.NumberFormat("vi-VN", { minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(n) + "%";
// Ngày dd/mm/yyyy
export const ngayVN = (d: Date) =>
  `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`;

// yyyymmdd → dd/mm/yyyy (hiển thị); chỉ có năm (yyyy0000) → yyyy; rỗng → "".
export const ymdToVN = (s: string | null | undefined): string => {
  const d = (s || "").replace(/\D/g, "");
  if (d.length !== 8) return "";
  const [y, mo, dd] = [d.slice(0, 4), d.slice(4, 6), d.slice(6, 8)];
  return mo === "00" || dd === "00" ? y : `${dd}/${mo}/${y}`;
};

// NAP-01: bỏ dấu tiếng Việt (NFD + xóa dấu kết hợp + đ→d) để tìm/so khớp không dấu.
export const boDau = (s: string): string =>
  (s || "")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase();

// NAP-01: cảnh báo chính tả tên mức A — KHÔNG từ điển tên (tránh báo nhầm), chỉ bắt dấu hiệu máy đọc được:
//   thiếu dấu tiếng Việt / có số hoặc ký tự lạ / khoảng trắng thừa. Trả lý do (chuỗi) hoặc "" nếu ổn.
export const nghiSaiChinhTa = (hoTen: string): string => {
  const ten = hoTen || "";
  if (!ten.trim()) return "";
  const lyDo: string[] = [];
  if (/\d/.test(ten)) lyDo.push("có chữ số");
  // Chỉ cho phép chữ cái (kể cả có dấu) + khoảng trắng + gạch nối/nháy (tên dân tộc:
  // H'Hen Niê, Y-Bih); ký tự khác là lạ.
  if (/[^\p{L}\s'’-]/u.test(ten)) lyDo.push("có ký tự lạ");
  if (/\s{2,}/.test(ten) || ten !== ten.trim()) lyDo.push("khoảng trắng thừa");
  // Thiếu dấu: tên có chữ cái nhưng hoàn toàn không có dấu tiếng Việt (bỏ dấu ra bằng chính nó).
  const coChu = /\p{L}/u.test(ten);
  if (coChu && boDau(ten) === ten.toLowerCase()) lyDo.push("nghi thiếu dấu tiếng Việt");
  return lyDo.join(", ");
};
