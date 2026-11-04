import { describe, expect, it } from "vitest";
import { canMapLai, gioThayDoi, nhanThayDoi, tomTatThayDoi } from "./napThayDoi";

describe("nhanThayDoi", () => {
  it("dịch mã sang nhãn tiếng Việt, ảnh và GPLX lên đầu", () => {
    expect(nhanThayDoi(["tt:ho_ten", "gplx", "anh"])).toEqual(["Ảnh", "GPLX", "Họ tên"]);
  });
  it("bỏ mã lạ và mã ghi chú dc_reset", () => {
    expect(nhanThayDoi(["dc_reset", "xyz", "tt:noi_tt_raw"])).toEqual(["Nơi thường trú"]);
  });
  it("rỗng thì rỗng", () => {
    expect(nhanThayDoi([])).toEqual([]);
  });
});

describe("tomTatThayDoi / canMapLai", () => {
  it("nơi thường trú kèm ghi chú cần map lại khi địa chỉ nháp đã reset", () => {
    expect(canMapLai(["tt:noi_tt_raw", "dc_reset"])).toBe(true);
    expect(tomTatThayDoi(["tt:noi_tt_raw", "dc_reset", "anh"])).toBe("Ảnh · Nơi thường trú (cần map lại)");
  });
  it("không reset thì không ghi chú", () => {
    expect(tomTatThayDoi(["tt:noi_tt_raw"])).toBe("Nơi thường trú");
  });
});

describe("gioThayDoi", () => {
  it("đổi ISO sang dd/mm/yyyy HH:mm", () => {
    expect(gioThayDoi("2026-11-04T09:12:00")).toBe("04/11/2026 09:12");
  });
  it("không đọc được thì giữ nguyên", () => {
    expect(gioThayDoi("không rõ")).toBe("không rõ");
  });
});
