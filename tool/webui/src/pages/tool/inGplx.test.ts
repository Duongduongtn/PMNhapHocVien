import { describe, expect, it } from "vitest";
import { IN_GPLX_NHAN, IN_GPLX_THU_TU, ghiChuMacDinh, inGplxMacDinh, laInGplx, laMoTo } from "./inGplx";

// Phản chiếu backend `nap.chon_in_gplx_mac_dinh` (tests/test_in_gplx.py): mô tô A* → 3, ô tô → 2.
describe("Chọn in GPLX — mặc định theo hạng khóa", () => {
  it.each(["A1", "A1m", "A2", "A3", "A01", "a1", " A1 "])("mô tô %s → không thời hạn (3)", (h) => {
    expect(laMoTo(h)).toBe(true);
    expect(inGplxMacDinh(h)).toBe(3);
  });
  it.each(["B1", "B11", "B2", "C", "C1", "D", "E", "FC"])("ô tô %s → có thời hạn (2)", (h) => {
    expect(laMoTo(h)).toBe(false);
    expect(inGplxMacDinh(h)).toBe(2);
  });
  it.each([null, undefined, "", "  "])("hạng trống %s → có thời hạn như trước (2)", (h) => {
    expect(inGplxMacDinh(h)).toBe(2);
  });
});

describe("tên loại in GPLX để người nạp đọc", () => {
  it("đủ nhãn tiếng Việt có dấu cho 3 giá trị", () => {
    expect(IN_GPLX_NHAN[2]).toBe("In 01 GPLX có thời hạn");
    expect(IN_GPLX_NHAN[3]).toBe("In 01 GPLX không thời hạn");
    expect(IN_GPLX_NHAN[1]).toContain("ghép");
  });
  it("thứ tự hiện: có thời hạn · không thời hạn · ghép", () => {
    expect(IN_GPLX_THU_TU).toEqual([2, 3, 1]);
  });
  it("ghi chú nói rõ khóa mô tô/ô tô và giá trị điền sẵn", () => {
    expect(ghiChuMacDinh("A1")).toContain("Khóa mô tô (hạng A1)");
    expect(ghiChuMacDinh("A1")).toContain("In 01 GPLX không thời hạn");
    expect(ghiChuMacDinh("B2")).toContain("Khóa ô tô (hạng B2)");
    expect(ghiChuMacDinh("B2")).toContain("In 01 GPLX có thời hạn");
    expect(ghiChuMacDinh(null)).toContain("Khóa ô tô");
  });
  it("laInGplx chỉ nhận 1/2/3", () => {
    expect([1, 2, 3].every(laInGplx)).toBe(true);
    expect([0, 4, "2", null, undefined].some(laInGplx)).toBe(false);
  });
});
