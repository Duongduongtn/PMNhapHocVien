import { describe, expect, it } from "vitest";
import { chuConThieu, gioiTinhNap, kiemTuoi, thieuThongTin } from "./napSanSang";

describe("A6 — thông tin bắt buộc trước khi nạp", () => {
  it("giới tính: dùng giá trị gửi về; trống thì suy từ chữ số thứ 4 CCCD; không suy được thì null", () => {
    expect(gioiTinhNap("F", "079200000001")).toBe("F");
    expect(gioiTinhNap(null, "079200000001")).toBe("M"); // số thứ 4 = 2 (chẵn) → Nam
    expect(gioiTinhNap("", "079301000001")).toBe("F");   // số thứ 4 = 3 (lẻ) → Nữ
    expect(gioiTinhNap("U", "")).toBeNull();
    expect(gioiTinhNap("U", "079301000001")).toBe("F");  // 'U' (VPS cho phép) coi như trống → suy từ CCCD
    expect(gioiTinhNap(null, "123456789")).toBeNull();    // CMND cũ 9 số không suy được
  });
  it("liệt kê đúng mục thiếu, đủ thì rỗng", () => {
    expect(thieuThongTin({ ho_ten: "A", ngay_sinh: "19900101", gioi_tinh: "M", so_cccd: null })).toEqual([]);
    expect(thieuThongTin({ ho_ten: " ", ngay_sinh: null, gioi_tinh: null, so_cccd: "123" })).toEqual(["họ tên", "ngày sinh", "giới tính"]);
    expect(thieuThongTin({ ho_ten: "A", ngay_sinh: "19900101", gioi_tinh: null, so_cccd: "079200000001" })).toEqual([]);
  });
});

describe("NAP-09 — kiểm tuổi theo hạng, tính tại ngày nạp", () => {
  const hom = new Date(2026, 10, 10); // 10/11/2026
  it("chưa đủ 18: tuổi, ngày đủ tuổi, còn thiếu", () => {
    expect(kiemTuoi("20081225", 18, hom)).toEqual({ du: false, tuoi: 17, ngayDuTuoi: "20261225", conThieuNgay: 45 });
  });
  it("đúng sinh nhật hôm nay là đủ", () => {
    expect(kiemTuoi("20081110", 18, hom)).toMatchObject({ du: true, tuoi: 18, conThieuNgay: 0 });
    expect(kiemTuoi("20081111", 18, hom)).toMatchObject({ du: false, tuoi: 17, conThieuNgay: 1 });
  });
  it("sinh 29/02, năm đủ tuổi không nhuận → 01/03", () => {
    expect(kiemTuoi("20100228", 18, hom)?.ngayDuTuoi).toBe("20280228");
    expect(kiemTuoi("20080229", 18, hom)?.ngayDuTuoi).toBe("20260301");
    expect(kiemTuoi("20080229", 18, hom)?.du).toBe(true);
  });
  it("tuổi nâng hạng 24 / 27; ngày sinh hỏng → null", () => {
    expect(kiemTuoi("20030101", 24, hom)?.du).toBe(false);
    expect(kiemTuoi("19990101", 27, hom)?.du).toBe(true);
    expect(kiemTuoi("20080231", 18, hom)).toBeNull();
    expect(kiemTuoi("", 18, hom)).toBeNull();
  });
  it("chữ còn thiếu", () => {
    expect(chuConThieu(45)).toBe("45 ngày");
    expect(chuConThieu(90)).toBe("3 tháng");
    expect(chuConThieu(174)).toBe("5 tháng");
    expect(chuConThieu(477)).toBe("1 năm 3 tháng");
    expect(chuConThieu(366)).toBe("1 năm");
  });
});

