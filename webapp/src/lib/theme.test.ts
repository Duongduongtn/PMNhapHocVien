import { describe, expect, it } from "vitest";
import { chonChe } from "./theme";

describe("chonChe", () => {
  it("chưa lưu thì theo máy", () => {
    expect(chonChe(null, true)).toBe("toi");
    expect(chonChe(null, false)).toBe("sang");
    expect(chonChe(undefined, true)).toBe("toi");
  });
  it("đã lưu thì thắng cài đặt máy", () => {
    expect(chonChe("sang", true)).toBe("sang");
    expect(chonChe("toi", false)).toBe("toi");
  });
  it("giá trị lạ trong bộ nhớ bị bỏ qua, theo máy", () => {
    expect(chonChe("xanh", true)).toBe("toi");
    expect(chonChe("", false)).toBe("sang");
  });
});
