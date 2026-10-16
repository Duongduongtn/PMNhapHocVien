// KQD-01 đổi (task 140, TDD §11D.13) — nhãn trạng thái NGHIỆP VỤ + dải tab nhóm việc + cảnh báo trên dòng.
// Một nguồn cho lưới "Cập nhật KQĐT" (và Theo dõi kết xuất — task 142). Mã `TT_XuLy` chỉ để tooltip.
// Các điều kiện tab PHẢN CHIẾU `_NHOM_DK` ở backend (`routers/ketqua.py`): đổi một bên phải đổi bên kia.

export type TabKQD = "all" | "chuanhap" | "chokx" | "khongdat" | "canxuly" | "dagui";

export interface TrangThaiNhan {
  nhan: string;
  cls: string; // lớp màu chip
  viec: string; // dòng nhỏ "việc cần làm"
}

export const TT_NHAN: Record<string, TrangThaiNhan> = {
  "03": { nhan: "Chưa nhập điểm", cls: "text-muted-foreground bg-muted border-border", viec: "Nhập điểm rồi Lưu" },
  "04": { nhan: "Chưa nhập điểm", cls: "text-muted-foreground bg-muted border-border", viec: "Nhập điểm rồi Lưu" },
  "09": { nhan: "Đã nhập · chờ kết xuất", cls: "text-success bg-success/10 border-success/40", viec: "Kết xuất ở phần mềm CDB" },
  "10": { nhan: "Đã nhập · Không đạt", cls: "text-destructive bg-destructive/10 border-destructive/40", viec: "Không kết xuất" },
  "12": { nhan: "Đã gửi Sở · chờ duyệt", cls: "text-primary bg-primary/10 border-primary/40", viec: "🔒 chờ Sở phản hồi" },
  "13": { nhan: "Sở đã duyệt", cls: "text-primary bg-primary/10 border-primary/40", viec: "🔒 hoàn thành" },
  "14": { nhan: "Sở từ chối", cls: "text-white bg-destructive border-destructive", viec: "Sửa điểm + giải trình" },
  "90": { nhan: "Đã giải trình", cls: "text-warning bg-warning/10 border-warning/50", viec: "Chờ kết xuất lại ở phần mềm CDB" },
};

export interface HvTrangThai {
  tt_xuly: string | null;
  ket_luan: "dat" | "khong_dat" | null;
}

const dat90 = (h: HvTrangThai) => h.tt_xuly === "90" && h.ket_luan === "dat";

export interface TabDef {
  key: TabKQD;
  nhan: string;
  khop: (h: HvTrangThai) => boolean;
  tip?: string;
  canhBao?: boolean; // nổi đỏ khi > 0
}

export const TABS: TabDef[] = [
  { key: "all", nhan: "Tất cả", khop: () => true },
  { key: "chuanhap", nhan: "Chưa nhập", khop: (h) => h.tt_xuly === "03" || h.tt_xuly === "04" },
  { key: "chokx", nhan: "Chờ kết xuất", khop: (h) => h.tt_xuly === "09" || dat90(h),
    tip: "Đã nhập (Đạt) và đã giải trình — chờ kết xuất ở phần mềm CDB" },
  { key: "khongdat", nhan: "Không đạt", khop: (h) => h.tt_xuly === "10" },
  { key: "canxuly", nhan: "Cần xử lý", canhBao: true,
    khop: (h) => h.tt_xuly === "14" || (h.tt_xuly === "90" && h.ket_luan !== "dat"),
    tip: "Sở từ chối + Đang giải trình nhưng không đạt (không kết xuất được)" },
  { key: "dagui", nhan: "Đã gửi / Hoàn thành", khop: (h) => h.tt_xuly === "12" || h.tt_xuly === "13" },
];

export function demTab(ds: HvTrangThai[] | null): Record<TabKQD, number> {
  const out = {} as Record<TabKQD, number>;
  for (const t of TABS) out[t.key] = ds ? ds.filter(t.khop).length : 0;
  return out;
}

export function khopTab(tab: TabKQD, h: HvTrangThai): boolean {
  return (TABS.find((t) => t.key === tab) ?? TABS[0]).khop(h);
}

export type CanhBaoDong = "khong_dat_o_90" | "thieu_giai_trinh" | null;

/** Cảnh báo ngay trên dòng. `dat`: kết luận HIỆN TẠI (live từ ô nhập, hoặc đã lưu); null = chưa có kết luận. */
export function canhBaoDong(p: { tt: string | null; dat: boolean | null; coGiaiTrinh: boolean }): CanhBaoDong {
  if (p.tt === "90" && p.dat !== true) return "khong_dat_o_90";
  if (p.tt === "14" && p.dat === true && !p.coGiaiTrinh) return "thieu_giai_trinh";
  return null;
}

export const CANH_BAO_NHAN: Record<Exclude<CanhBaoDong, null>, { nhan: string; cls: string; tip: string }> = {
  khong_dat_o_90: {
    nhan: "Đang giải trình nhưng không đạt — sẽ không kết xuất",
    cls: "text-destructive bg-destructive/10 border-destructive/50",
    tip: "Học viên đang ở Đang giải trình mà Không đạt/chưa có kết luận — phần mềm CDB không kết xuất.",
  },
  thieu_giai_trinh: {
    nhan: "Thiếu giải trình — chưa kết xuất được",
    cls: "text-warning bg-warning/10 border-warning/50",
    tip: "Chưa có giải trình nên chưa chuyển sang Đang giải trình; ghi giải trình rồi Lưu.",
  },
};
