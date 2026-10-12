import { describe, expect, it } from "vitest";
import { nhanHan, sapXepTheoHan, tongHop } from "./hanGiayToHelper";
import type { HanGiayToPC } from "../../lib/api";

const r = (p: Partial<HanGiayToPC>): HanGiayToPC => ({
  hom_nay: "2026-10-12", nguong: 30,
  xe: { het_han: [], sap_het: [], chua_khai: [] },
  gv: { het_han: [], sap_het: [], chua_khai: [] },
  ngung: { xe: [], gv: [] },
  dem: { xe_het_han: 0, xe_sap_het: 0, gv_het_han: 0, gv_sap_het: 0, xe_chua_khai: 0, gv_chua_khai: 0, ngung_xe: 0, ngung_gv: 0 },
  ...p,
});

describe("nhanHan", () => {
  it("quá hạn / hôm nay / còn N ngày", () => {
    expect(nhanHan(-14)).toBe("Quá hạn 14 ngày");
    expect(nhanHan(0)).toBe("Hết hạn hôm nay");
    expect(nhanHan(30)).toBe("Còn 30 ngày");
  });
});

describe("tongHop", () => {
  it("rỗng → tong 0 (không có gì sắp hết hạn)", () => {
    expect(tongHop(r({})).tong).toBe(0);
  });
  it("đếm theo nhóm; 'chưa khai' không tính vào tong", () => {
    const x = { bien_so: "51A", hang: "B", muc: "het_han", giay: [], khoa: [] };
    const t = tongHop(r({
      xe: { het_han: [x], sap_het: [x, x], chua_khai: [x] },
      gv: { het_han: [], sap_het: [], chua_khai: [] },
      ngung: { xe: [{ bien_so: "51F", hang: "B", khoa: [] }], gv: [] },
    }));
    expect(t).toEqual({ xe: { het: 1, sap: 2 }, gv: { het: 0, sap: 0 }, ngung: 1, chuaKhai: 1, tong: 4 });
  });
});

describe("sapXepTheoHan", () => {
  it("ngày sớm nhất của dòng lên trước, không đổi mảng gốc", () => {
    const a = { id: "a", giay: [{ ngay: "2026-11-05" }, { ngay: "2026-10-20" }] };
    const b = { id: "b", giay: [{ ngay: "2026-09-28" }] };
    const goc = [a, b];
    expect(sapXepTheoHan(goc).map((d) => d.id)).toEqual(["b", "a"]);
    expect(goc.map((d) => d.id)).toEqual(["a", "b"]);
  });
});
