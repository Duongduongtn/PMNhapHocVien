import { describe, expect, it } from "vitest";
import { gioiTinhNap, thieuThongTin } from "./napSanSang";

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
