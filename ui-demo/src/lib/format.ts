// Helper định dạng chuẩn Việt Nam (vi-VN)
export const soVN = (n: number) => new Intl.NumberFormat("vi-VN").format(n);
export const tienVN = (n: number) => soVN(n) + " đồng";
export const phanTram = (n: number) =>
  new Intl.NumberFormat("vi-VN", { minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(n) + "%";
// Ngày dd/mm/yyyy
export const ngayVN = (d: Date) =>
  `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`;
