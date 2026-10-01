import { describe, it, expect } from "vitest";
import { maskNgay } from "./ODate";

describe("ODate — maskNgay (tự chèn / khi gõ số, giữ năm-only)", () => {
  it("gõ đủ 8 số → dd/mm/yyyy", () => {
    expect(maskNgay("01012000")).toBe("01/01/2000");
    expect(maskNgay("31122026")).toBe("31/12/2026");
  });

  it("≤4 số giữ nguyên (năm-only hoặc đang gõ)", () => {
    expect(maskNgay("2000")).toBe("2000");
    expect(maskNgay("19")).toBe("19");
  });

  it("chèn dấu từ số thứ 5", () => {
    expect(maskNgay("01012")).toBe("01/01/2");
    expect(maskNgay("010120")).toBe("01/01/20");
  });

  it("bỏ ký tự không phải số + cắt quá 8 số", () => {
    expect(maskNgay("01/01/2000")).toBe("01/01/2000");
    expect(maskNgay("01-01-2000")).toBe("01/01/2000");
    expect(maskNgay("010120009")).toBe("01/01/2000");
    expect(maskNgay("abc")).toBe("");
  });
});
