import { describe, expect, it } from "vitest";
import { bangNhau, chuanHoaGio, fmtVn, parseGio, parseKm, soHien } from "./gioThucHanh";

describe("parseGio", () => {
  it("hh:mm → thập phân làm tròn 2 chữ số", () => {
    expect(parseGio("20:30")).toBe(20.5);
    expect(parseGio("20:20")).toBe(20.33);
    expect(parseGio("16:19")).toBe(16.32);
    expect(parseGio("0:59")).toBe(0.98);
    expect(parseGio("28:26")).toBe(28.43);   // giờ ≥ 24 vẫn đúng
  });
  it("số thập phân giữ nguyên (phẩy hoặc chấm)", () => {
    expect(parseGio("20,5")).toBe(20.5);
    expect(parseGio("20.5")).toBe(20.5);
    expect(parseGio("12")).toBe(12);
  });
  it("trống → null; sai dạng → 'sai'", () => {
    expect(parseGio("")).toBeNull();
    expect(parseGio("  ")).toBeNull();
    expect(parseGio("20:75")).toBe("sai");
    expect(parseGio("abc")).toBe("sai");
    expect(parseGio("20:")).toBe("sai");
  });
});

describe("chuanHoaGio", () => {
  it("hh:mm đổi sang thập phân khi rời ô", () => {
    expect(chuanHoaGio("20:30")).toBe("20,5");
    expect(chuanHoaGio("20:20")).toBe("20,33");
    expect(chuanHoaGio("24:00")).toBe("24");
  });
  it("số thập phân và rác giữ nguyên như đã gõ", () => {
    expect(chuanHoaGio("20.5")).toBe("20.5");
    expect(chuanHoaGio("20,5")).toBe("20,5");
    expect(chuanHoaGio("20:75")).toBe("20:75");   // sai → để nguyên, viền đỏ báo người dùng
    expect(chuanHoaGio("")).toBe("");
  });
});

describe("soHien / fmtVn / bangNhau", () => {
  it("real của CDB không lộ đuôi 18.399999…", () => {
    expect(soHien(18.399999618530273)).toBe("18,4");
    expect(soHien(719.4000244140625)).toBe("719,4");
    expect(soHien(null)).toBe("");
  });
  it("dấu nghìn chỉ ở bảng, ô nhập không có", () => {
    expect(fmtVn(1008.19)).toBe("1.008,19");
    expect(soHien(1008.19)).toBe("1008,19");
    expect(fmtVn(null)).toBe("—");
  });
  it("so bằng nhau sau làm tròn", () => {
    expect(bangNhau(18.399999618530273, 18.4)).toBe(true);
    expect(bangNhau(18.4, 18.5)).toBe(false);
    expect(bangNhau(null, null)).toBe(true);
    expect(bangNhau(null, 0)).toBe(false);
  });
});

describe("parseKm", () => {
  it("số kiểu VN và số thường", () => {
    expect(parseKm("725,63")).toBe(725.63);
    expect(parseKm("725.63")).toBe(725.63);
    expect(parseKm("1.008,19")).toBe(1008.19);
    expect(parseKm("810")).toBe(810);
  });
  it("trống → null; rác → 'sai'", () => {
    expect(parseKm("")).toBeNull();
    expect(parseKm("12a")).toBe("sai");
    expect(parseKm("1,008.19")).toBe("sai");
  });
});
