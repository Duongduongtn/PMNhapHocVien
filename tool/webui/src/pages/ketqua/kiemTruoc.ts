// KQD-07 (task 120) — chuẩn hóa kết quả GET /local/ketqua/kiem-truoc để hiển thị.
// Quyết định UX 12/10/2026 (mock ui-mock/ketqua.html): học viên "Chưa có điểm" thì KHÔNG hiện thêm chip
// "Thiếu giờ/km" (chưa có điểm thì chắc chắn chưa có giờ/km). Backend vẫn trả đủ; UI lọc + đếm lại.
import type { KiemTruocKQD } from "../../lib/api";

export const LY_DO_NHAN: Record<string, string> = {
  chua_co_diem: "Chưa có điểm",
  thieu_mon: "Thiếu môn",
  thieu_gio_km: "Thiếu giờ/km thực hành",
  thieu_ket_luan: "Thiếu kết luận",
  // KQD-04 đổi (#77, task 139): Sở từ chối / đang giải trình
  thieu_giai_trinh: "Thiếu giải trình — chưa kết xuất được",
  khong_dat_o_90: "Đang giải trình nhưng không đạt — sẽ không kết xuất",
  giai_trinh_trong: "Đang giải trình nhưng giải trình trống",
};
export const LY_DO_THU_TU = [
  "chua_co_diem", "thieu_mon", "thieu_gio_km", "thieu_ket_luan",
  "thieu_giai_trinh", "khong_dat_o_90", "giai_trinh_trong",
] as const;

export const MON_NHAN: Record<string, string> = {
  ly_thuyet: "Lý thuyết",
  mo_phong: "Mô phỏng",
  hinh: "Sa hình",
  tien_lui: "Chữ chi",
  duong: "Đường trường",
};

export function hienThiKiemTruoc(r: KiemTruocKQD): KiemTruocKQD {
  const thieu = r.thieu.map((t) =>
    t.ly_do.includes("chua_co_diem") ? { ...t, ly_do: t.ly_do.filter((k) => k !== "thieu_gio_km") } : t,
  );
  const dem: Record<string, number> = {};
  for (const t of thieu) for (const k of t.ly_do) dem[k] = (dem[k] ?? 0) + 1;
  return { ...r, thieu, dem: dem as KiemTruocKQD["dem"] };
}

// Cảnh báo vàng "Giờ đường 18 < 20" (chỉ nhắc, không tính là thiếu).
export function nhanCanhBao(w: { loai: string; gia_tri: number; goi_y: number }): string {
  const ten = w.loai === "gio_duong" ? "Giờ đường" : "Km đường";
  return `${ten} ${w.gia_tri} < ${w.goi_y}`;
}
