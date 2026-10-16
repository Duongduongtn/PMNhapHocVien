// KQD-04 #77 (task 141) — logic thuần của giải trình hàng loạt: xem trước phía máy + nhãn lý do bỏ qua.
// Server (POST /giai-trinh-lo) vẫn là nơi quyết định cuối; đây chỉ để hộp xác nhận nói trước "đủ điều kiện X · bỏ qua Y".
import type { GiaiTrinhLoBoQua, HocVienKQD } from "../../lib/api";

export const LY_DO_LO_NHAN: Record<string, string> = {
  khong_tim_thay: "không tìm thấy hồ sơ",
  khong_thuoc_co_so: "không thuộc cơ sở của máy",
  da_gui_hoac_hoan_thanh: "đã gửi Sở / hoàn thành",
  da_o_dang_giai_trinh: "đã ở Đang giải trình",
  khong_con_o_so_tu_choi: "không còn ở Sở từ chối",
  khong_dat: "Không đạt — không được kết xuất",
  chua_du_diem: "chưa đủ điểm / giờ-km / số giấy",
};

const MON = ["ly_thuyet", "mo_phong", "hinh", "tien_lui", "duong"] as const;

export interface XemTruocLo {
  du: HocVienKQD[];
  boQua: { hv: HocVienKQD; lyDo: string }[];
  giuRieng: number;
}

/** Xem trước một lô: chỉ HV đang 14 + Đạt + đủ 5 điểm + đủ giờ/km đường mới "đủ điều kiện" (server kiểm thêm số giấy). */
export function xemTruocLo(chon: HocVienKQD[], giaiTrinhRieng: (h: HocVienKQD) => string): XemTruocLo {
  const du: HocVienKQD[] = [];
  const boQua: { hv: HocVienKQD; lyDo: string }[] = [];
  for (const h of chon) {
    if (h.tt_xuly === "90") boQua.push({ hv: h, lyDo: LY_DO_LO_NHAN.da_o_dang_giai_trinh });
    else if (h.tt_xuly !== "14") boQua.push({ hv: h, lyDo: LY_DO_LO_NHAN.khong_con_o_so_tu_choi });
    else if (h.ket_luan !== "dat") boQua.push({ hv: h, lyDo: LY_DO_LO_NHAN.khong_dat });
    else if (MON.some((m) => h.diem[m] == null) || h.gio_duong == null || h.km_duong == null)
      boQua.push({ hv: h, lyDo: LY_DO_LO_NHAN.chua_du_diem });
    else du.push(h);
  }
  const giuRieng = du.filter((h) => giaiTrinhRieng(h).trim() !== "").length;
  return { du, boQua, giuRieng };
}

/** Tóm tắt kết quả server → một câu cho thông báo. */
export function tomTatKetQuaLo(r: { da_chuyen: string[]; bo_qua: GiaiTrinhLoBoQua[]; giu_rieng: number }, ten: (ma: string) => string): string {
  const parts = [`Đã chuyển ${r.da_chuyen.length} học viên sang "Đã giải trình" (chờ kết xuất lại ở phần mềm CDB)`];
  if (r.giu_rieng > 0) parts.push(`giữ giải trình riêng ${r.giu_rieng}`);
  if (r.bo_qua.length > 0) {
    const chiTiet = r.bo_qua.slice(0, 3).map((b) => `${ten(b.ma_dk)} (${LY_DO_LO_NHAN[b.ly_do] ?? b.ly_do})`).join("; ");
    parts.push(`bỏ qua ${r.bo_qua.length}: ${chiTiet}${r.bo_qua.length > 3 ? "…" : ""}`);
  }
  return parts.join(" · ") + ".";
}

const NHAN_MON: Record<string, string> = {
  ly_thuyet: "Lý thuyết", mo_phong: "Mô phỏng", hinh: "Sa hình", tien_lui: "Chữ chi", duong: "Đường trường",
};
const NHAN_THIEU: Record<string, string> = {
  chua_co_diem: "chưa có điểm", thieu_mon: "thiếu môn", thieu_gio_km: "thiếu giờ/km thực hành",
  thieu_ket_luan: "thiếu kết luận", thieu_so_giay: "thiếu số giấy HTKH",
};

/** MỌI người bị bỏ qua, mỗi người một dòng kèm lý do (và môn/mục thiếu) — PRD KQD-04 "lý do từng người". */
export function chiTietBoQua(bo: GiaiTrinhLoBoQua[], ten: (ma: string) => string): string[] {
  return bo.map((b) => {
    let ld = LY_DO_LO_NHAN[b.ly_do] ?? b.ly_do;
    const ct = b.chi_tiet;
    if (ct && ct.ly_do.length > 0) {
      const mon = ct.mon_thieu.map((m) => NHAN_MON[m] ?? m);
      const muc = ct.ly_do.map((k) => (k === "thieu_mon" && mon.length ? `thiếu môn ${mon.join(", ")}` : NHAN_THIEU[k] ?? k));
      ld = `${ld}: ${muc.join("; ")}`;
    }
    return `${ten(b.ma_dk)} — ${ld}`;
  });
}

/** Thông báo sau khi LƯU 1 HV (TDD §11D.13 "Cảnh báo bắt buộc"). `vang` = thông báo vàng đứng lâu. */
export function thongBaoSauLuu(p: {
  ten: string; ttTruoc: string | null; ketLuan: "dat" | "khong_dat"; ttMoi: string;
  thieuGiaiTrinh?: boolean; canhBao?: string | null; soGiay?: string | null;
}): { vang: boolean; text: string } {
  if (p.canhBao === "chua_chuyen_90")
    return { vang: true, text: `Đã lưu điểm ${p.ten} nhưng CHƯA chuyển sang "Đã giải trình" (lỗi tạm). Bấm Lưu lại để chuyển.` };
  if (p.thieuGiaiTrinh)
    return { vang: true, text: `Đã lưu điểm ${p.ten} — CHƯA có giải trình nên chưa chuyển sang "Đã giải trình" và chưa kết xuất lại được. Nhập giải trình (riêng hoặc chung của khóa) rồi Lưu lại.` };
  if (p.ttTruoc === "14" && p.ttMoi === "90")
    return { vang: false, text: `Đã lưu ${p.ten} — ĐẠT · chuyển sang "Đã giải trình" (chờ kết xuất lại ở phần mềm CDB).` };
  if (p.ttTruoc === "14" && p.ketLuan === "khong_dat")
    return { vang: true, text: `Đã lưu điểm ${p.ten} — Không đạt, còn ở "Cần xử lý" (phần mềm CDB không kết xuất học viên Không đạt).` };
  return { vang: false, text: `Đã lưu ${p.ten} — ${p.ketLuan === "dat" ? "ĐẠT" : "Không đạt"}${p.soGiay ? ` · ${p.soGiay}` : ""}` };
}
