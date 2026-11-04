// Chữ cái đầu của hai từ cuối trong tên, dùng cho ảnh đại diện khi chưa có ảnh ("Thu nhận 1" → "N1",
// "NGUYỄN VĂN AN" → "VA"). Không có tên thì trả dấu gạch.
export function chuCaiDau(ten: string | null | undefined): string {
  const tu = (ten ?? "").trim().split(/\s+/).filter(Boolean);
  if (!tu.length || ten === "—") return "—";
  const dau = (t: string) => Array.from(t)[0]?.toLocaleUpperCase("vi-VN") ?? "";
  return tu.length === 1 ? dau(tu[0]) : dau(tu[tu.length - 2]) + dau(tu[tu.length - 1]);
}

// Chọn một trong 3 tông nhạt theo tên, để mỗi người luôn cùng một màu và danh sách không đơn điệu.
export function tongTheoTen(ten: string | null | undefined): string {
  let h = 0;
  for (const c of ten ?? "") h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return ["bg-primary/10 text-primary", "bg-success/10 text-success", "bg-warning/10 text-warning"][h % 3];
}
