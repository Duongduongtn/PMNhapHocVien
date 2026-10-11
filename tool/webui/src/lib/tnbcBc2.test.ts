import { describe, expect, it } from "vitest";
import { DO_DAI_MA_BCII, khoaSoBc2, kiemSoBc2 } from "./tnbcBc2";

// TNB-03 — số BC2 (= MaBCII varchar 13): thiếu, quá dài, trùng không phân biệt hoa thường và Ð/Đ.
describe("TNB-03 — số BC2", () => {
  it("khóa so sánh coi Ð (DB) = Đ (gõ tay), không phân biệt hoa thường", () => {
    expect(khoaSoBc2("861/26-TTÐ")).toBe(khoaSoBc2("861/26-ttđ"));
    expect(khoaSoBc2(null)).toBe("");
  });

  it("hợp lệ khi có số, đủ độ dài và chưa tồn tại", () => {
    expect(kiemSoBc2("81/2026", ["80/2026", "861/26-TTTĐ"])).toEqual([]);
  });

  it("chặn số rỗng", () => {
    expect(kiemSoBc2("   ", [])).toEqual(["Cần nhập số báo cáo"]);
  });

  it("chặn số dài hơn cột MaBCII", () => {
    const so = "9".repeat(DO_DAI_MA_BCII + 1);
    expect(kiemSoBc2(so, []).join(" ")).toContain("tối đa 13 ký tự");
    expect(kiemSoBc2("9".repeat(DO_DAI_MA_BCII), [])).toEqual([]);
  });

  it("chặn số trùng, kể cả khác hoa thường và Ð/Đ", () => {
    expect(kiemSoBc2("861/26-ttđ", ["861/26-TTÐ"]).join(" ")).toContain("đã tồn tại");
  });
});
