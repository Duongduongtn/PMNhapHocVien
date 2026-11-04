import { describe, expect, it } from "vitest";
import { chuCaiDau, tongTheoTen } from "./chuCai";

describe("chuCaiDau", () => {
  it("lấy chữ đầu của hai từ cuối, giữ dấu và viết hoa", () => {
    expect(chuCaiDau("NGUYỄN VĂN AN")).toBe("VA");
    expect(chuCaiDau("Thu nhận 1")).toBe("N1");
    expect(chuCaiDau("đặng thị ánh")).toBe("TÁ");
  });
  it("một từ thì lấy một chữ; rỗng hoặc dấu gạch thì trả dấu gạch", () => {
    expect(chuCaiDau("An")).toBe("A");
    expect(chuCaiDau("")).toBe("—");
    expect(chuCaiDau(null)).toBe("—");
    expect(chuCaiDau("—")).toBe("—");
  });
});

describe("tongTheoTen", () => {
  it("cùng tên luôn ra cùng màu", () => {
    expect(tongTheoTen("LÊ MINH CƯỜNG")).toBe(tongTheoTen("LÊ MINH CƯỜNG"));
  });
});
