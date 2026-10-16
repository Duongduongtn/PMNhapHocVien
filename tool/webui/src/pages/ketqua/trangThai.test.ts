import { describe, it, expect } from "vitest";
import { CANH_BAO_NHAN, TABS, TT_NHAN, canhBaoDong, demTab, khopTab, type HvTrangThai } from "./trangThai";

// Cùng 10 học viên mẫu với backend `tests/test_ketqua_nhom.py` — điều kiện tab phải PHẢN CHIẾU `_NHOM_DK`.
const HV = (tt: string, kl: "dat" | "khong_dat" | null): HvTrangThai => ({ tt_xuly: tt, ket_luan: kl });
const MAU: Record<string, HvTrangThai> = {
  a03: HV("03", null), a04: HV("04", null), a09: HV("09", "dat"), a10: HV("10", "khong_dat"),
  a90d: HV("90", "dat"), a90k: HV("90", "khong_dat"), a90n: HV("90", null),
  a14: HV("14", "dat"), a12: HV("12", "dat"), a13: HV("13", "dat"),
};
const ds = Object.values(MAU);
const ma = (tab: Parameters<typeof khopTab>[0]) => Object.keys(MAU).filter((k) => khopTab(tab, MAU[k])).sort();

describe("dải tab nhóm việc (KQD-01 #77)", () => {
  it("Chờ kết xuất = 09 + 90 Đạt", () => expect(ma("chokx")).toEqual(["a09", "a90d"]));
  it("Không đạt = 10", () => expect(ma("khongdat")).toEqual(["a10"]));
  it("Cần xử lý = 14 + 90 không đạt/trống kết luận", () => expect(ma("canxuly")).toEqual(["a14", "a90k", "a90n"]));
  it("Đã gửi/Hoàn thành = 12/13", () => expect(ma("dagui")).toEqual(["a12", "a13"]));
  it("Chưa nhập = 03/04", () => expect(ma("chuanhap")).toEqual(["a03", "a04"]));
  it("5 tab (trừ Tất cả) phủ hết, không HV nào ở hai tab", () => {
    const cac = TABS.filter((t) => t.key !== "all");
    expect(cac.reduce((n, t) => n + ds.filter(t.khop).length, 0)).toBe(ds.length);
  });
  it("đếm tab", () => {
    const d = demTab(ds);
    expect(d).toMatchObject({ all: 10, chuanhap: 2, chokx: 2, khongdat: 1, canxuly: 3, dagui: 2 });
    expect(demTab(null).all).toBe(0);
  });
  it("tab Cần xử lý được đánh dấu cảnh báo", () => {
    expect(TABS.find((t) => t.key === "canxuly")?.canhBao).toBe(true);
  });
});

describe("nhãn trạng thái nghiệp vụ", () => {
  it("đủ 8 mã, không lộ mã số trong nhãn", () => {
    for (const k of ["03", "04", "09", "10", "12", "13", "14", "90"]) {
      expect(TT_NHAN[k].nhan).toBeTruthy();
      expect(TT_NHAN[k].nhan).not.toMatch(/\b(03|04|09|10|12|13|14|90)\b/);
    }
  });
});

describe("cảnh báo trên dòng", () => {
  it("90 mà không đạt hoặc chưa có kết luận → khong_dat_o_90", () => {
    expect(canhBaoDong({ tt: "90", dat: false, coGiaiTrinh: true })).toBe("khong_dat_o_90");
    expect(canhBaoDong({ tt: "90", dat: null, coGiaiTrinh: true })).toBe("khong_dat_o_90");
    expect(canhBaoDong({ tt: "90", dat: true, coGiaiTrinh: true })).toBeNull();
  });
  it("14 Đạt mà chưa giải trình → thieu_giai_trinh; có giải trình hoặc không đạt thì không", () => {
    expect(canhBaoDong({ tt: "14", dat: true, coGiaiTrinh: false })).toBe("thieu_giai_trinh");
    expect(canhBaoDong({ tt: "14", dat: true, coGiaiTrinh: true })).toBeNull();
    expect(canhBaoDong({ tt: "14", dat: false, coGiaiTrinh: false })).toBeNull();
  });
  it("trạng thái khác không cảnh báo; chip có nhãn tiếng Việt", () => {
    expect(canhBaoDong({ tt: "09", dat: true, coGiaiTrinh: false })).toBeNull();
    expect(CANH_BAO_NHAN.thieu_giai_trinh.nhan).toContain("chưa kết xuất được");
  });
});
