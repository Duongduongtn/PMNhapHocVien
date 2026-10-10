import type { SuaSauGuiDiem } from "../../lib/api";

// Định dạng điểm VN (thập phân dấu phẩy, 1 chữ số) + so "trước → sau" cho KQD-05 sửa sau gửi.
export const d1 = (x: number | null | undefined): string => (x == null ? "—" : x.toFixed(1).replace(".", ","));

export const MON_SSG: { key: Exclude<keyof SuaSauGuiDiem, "ket_luan">; nhan: string }[] = [
  { key: "ly_thuyet", nhan: "LT" },
  { key: "mo_phong", nhan: "MP" },
  { key: "hinh", nhan: "Sa hình" },
  { key: "tien_lui", nhan: "Chữ chi" },
  { key: "duong", nhan: "Đường" },
];

export const nhanKetLuan = (k: "dat" | "khong_dat" | null | undefined): string =>
  k === "dat" ? "Đạt" : k === "khong_dat" ? "Không đạt" : "—";

/** Các môn đã đổi điểm so với lúc mở (so tới 1 chữ số thập phân, đúng cái người dùng nhìn thấy). */
export function monDaDoi(truoc: Partial<SuaSauGuiDiem>, hien: SuaSauGuiDiem) {
  return MON_SSG.filter((m) => d1(truoc[m.key]) !== d1(hien[m.key])).map((m) => ({
    nhan: m.nhan,
    truoc: d1(truoc[m.key]),
    sau: d1(hien[m.key]),
  }));
}
