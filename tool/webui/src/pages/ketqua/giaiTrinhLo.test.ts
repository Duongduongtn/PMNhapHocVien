import { describe, it, expect } from "vitest";
import type { HocVienKQD } from "../../lib/api";
import { LY_DO_LO_NHAN, chiTietBoQua, thongBaoSauLuu, tomTatKetQuaLo, xemTruocLo } from "./giaiTrinhLo";

// KQD-04 đổi (task 141, TDD §11D.13) — xem trước lô, tóm tắt kết quả, thông báo sau Lưu (3 ca + lỗi bước chuyển).
const DAT = { ly_thuyet: 8, mo_phong: 7, hinh: 8, tien_lui: 7, duong: 8 };
const hv = (ma: string, tt: string, kl: "dat" | "khong_dat" | null, o: Partial<HocVienKQD> = {}): HocVienKQD => ({
  ma_dk: ma, ho_ten: `HV ${ma}`, ngay_sinh: "01/01/2000", so_cccd: "079" + ma, so_ho_so: ma, hang: "B.01",
  ma_hang_moi: "B.01", ma_hang: "B11", tt_xuly: tt, ket_luan: kl, diem: { ...DAT }, gio_duong: 20, km_duong: 810, ...o,
});
const rieng = (h: HocVienKQD) => h.giai_trinh ?? "";

describe("xem trước lô giải trình", () => {
  it("chỉ 14 + Đạt + đủ điểm + đủ giờ/km mới đủ điều kiện", () => {
    const r = xemTruocLo([
      hv("OK", "14", "dat"),
      hv("KD", "14", "khong_dat"),
      hv("D90", "90", "dat"),
      hv("T09", "09", "dat"),
      hv("THIEU", "14", "dat", { diem: { ...DAT, mo_phong: null } }),
      hv("NOKM", "14", "dat", { km_duong: null }),
    ], rieng);
    expect(r.du.map((h) => h.ma_dk)).toEqual(["OK"]);
    const ly = Object.fromEntries(r.boQua.map((b) => [b.hv.ma_dk, b.lyDo]));
    expect(ly.KD).toBe(LY_DO_LO_NHAN.khong_dat);
    expect(ly.D90).toBe(LY_DO_LO_NHAN.da_o_dang_giai_trinh);
    expect(ly.T09).toBe(LY_DO_LO_NHAN.khong_con_o_so_tu_choi);
    expect(ly.THIEU).toBe(LY_DO_LO_NHAN.chua_du_diem);
    expect(ly.NOKM).toBe(LY_DO_LO_NHAN.chua_du_diem);
  });

  it("đếm người đã có giải trình riêng (sẽ được giữ)", () => {
    const r = xemTruocLo([hv("A", "14", "dat", { giai_trinh: "Riêng A" }), hv("B", "14", "dat", { giai_trinh: "  " }), hv("C", "14", "dat")], rieng);
    expect(r.du).toHaveLength(3);
    expect(r.giuRieng).toBe(1);
  });
});

describe("tóm tắt kết quả server", () => {
  it("nêu số đã chuyển, giữ riêng, bỏ qua kèm lý do", () => {
    const t = tomTatKetQuaLo(
      { da_chuyen: ["A", "B"], giu_rieng: 1, bo_qua: [{ ma_dk: "C", ly_do: "khong_dat" }, { ma_dk: "D", ly_do: "chua_du_diem" }] },
      (m) => `HV ${m}`,
    );
    expect(t).toContain("Đã chuyển 2 học viên");
    expect(t).toContain("giữ giải trình riêng 1");
    expect(t).toContain("bỏ qua 2");
    expect(t).toContain("HV C (Không đạt — không được kết xuất)");
  });
});

describe("thông báo sau Lưu một học viên", () => {
  const goc = { ten: "Nguyễn A", ttTruoc: "14", ketLuan: "dat" as const, ttMoi: "14" };
  it("Đạt + có giải trình → sang Đang giải trình (thông báo thường)", () => {
    const r = thongBaoSauLuu({ ...goc, ttMoi: "90" });
    expect(r.vang).toBe(false);
    expect(r.text).toContain("chuyển sang \"Đã giải trình\"");
  });
  it("Đạt thiếu giải trình → thông báo VÀNG nói rõ chưa kết xuất được", () => {
    const r = thongBaoSauLuu({ ...goc, thieuGiaiTrinh: true });
    expect(r.vang).toBe(true);
    expect(r.text).toContain("CHƯA có giải trình");
    expect(r.text).toContain("chưa kết xuất lại được");
  });
  it("Không đạt → giữ Cần xử lý, thông báo vàng", () => {
    const r = thongBaoSauLuu({ ...goc, ketLuan: "khong_dat" });
    expect(r.vang).toBe(true);
    expect(r.text).toContain("không kết xuất học viên Không đạt");
  });
  it("điểm đã lưu nhưng bước chuyển lỗi → vàng + nút Lưu lại", () => {
    const r = thongBaoSauLuu({ ...goc, canhBao: "chua_chuyen_90" });
    expect(r.vang).toBe(true);
    expect(r.text).toContain("Bấm Lưu lại");
  });
  it("HV bình thường (03 → 09) → thông báo thường như cũ", () => {
    const r = thongBaoSauLuu({ ten: "B", ttTruoc: "03", ketLuan: "dat", ttMoi: "09", soGiay: "SG-1" });
    expect(r).toEqual({ vang: false, text: "Đã lưu B — ĐẠT · SG-1" });
  });
});

describe("chi tiết từng người bị bỏ qua (PRD KQD-04: lý do từng người)", () => {
  it("liệt kê MỌI người (không cắt ở 3) kèm môn/mục thiếu", () => {
    const bo = [
      { ma_dk: "A", ly_do: "khong_dat" },
      { ma_dk: "B", ly_do: "chua_du_diem", chi_tiet: { ly_do: ["thieu_mon", "thieu_gio_km"], mon_thieu: ["mo_phong", "duong"] } },
      { ma_dk: "C", ly_do: "chua_du_diem", chi_tiet: { ly_do: ["thieu_so_giay"], mon_thieu: [] } },
      { ma_dk: "D", ly_do: "khong_thuoc_co_so" },
      { ma_dk: "E", ly_do: "da_o_dang_giai_trinh" },
    ];
    const r = chiTietBoQua(bo, (m) => `HV ${m}`);
    expect(r).toHaveLength(5);
    expect(r[0]).toBe("HV A — Không đạt — không được kết xuất");
    expect(r[1]).toContain("thiếu môn Mô phỏng, Đường trường");
    expect(r[1]).toContain("thiếu giờ/km thực hành");
    expect(r[2]).toContain("thiếu số giấy HTKH");
    expect(r[3]).toContain("không thuộc cơ sở của máy");
  });
});
