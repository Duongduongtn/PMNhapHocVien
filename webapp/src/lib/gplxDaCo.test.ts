import { describe, expect, it } from "vitest";
import { DS_HANG_GPLX, DS_NOI_CAP_GPLX, bangMoi, bangTrong, tomTatGplx, type BangGplx, chonKhiEnter, locLuaChon, loiBang, loiDanhSach, loiTungO, noiCapKhiDoiSo, oSaiDau, sangServer, soGplxLa, suyNoiCapGplx, tuServer } from "./gplxDaCo";
import { boDau } from "./text";

const b = (over = {}) => ({ ...bangMoi(), hang: "B2", so: "790000000123", ngay_tt: "15/08/2012", ngay_cap: "27/04/2018", ...over });

describe("GPLX đã có ở app web", () => {
  it("đổi ngày hai chiều", () => {
    const form = tuServer([{ nhom: "cu", hang: "B2", so: "1", ngay_cap: "20180427" }]);
    expect(form[0].ngay_cap).toBe("27/04/2018");
    expect(sangServer(form)[0].ngay_cap).toBe("20180427");
    expect(tuServer(null)).toEqual([]);
  });
  it("bằng mô tô không gửi ngày hết hạn", () => {
    expect(sangServer([b({ hang: "A1", ngay_hh: "01/01/2030" })])[0].ngay_hh).toBe("");
  });
  it("chặn gửi khi thiếu hạng, số hoặc ngày sai", () => {
    expect(loiBang(bangMoi())).toEqual(["Chưa chọn hạng", "Chưa nhập số GPLX", "Chưa nhập ngày trúng tuyển", "Chưa nhập ngày cấp"]);
    expect(loiBang(b({ ngay_cap: "01/01/2010" }))).toEqual(["Ngày cấp phải sau ngày trúng tuyển"]);
    expect(loiBang(b({ ngay_hh: "27/04/2018" }))).toEqual(["Ngày hết hạn phải sau ngày cấp"]);
    expect(loiDanhSach([b(), b({ ngay_cap: "27/04" })])).toContain("bằng 2");
    expect(loiDanhSach([b()])).toBeNull();
    expect(loiDanhSach([])).toBeNull();
  });
  it("BUG-17: Enter chọn đúng hạng, trùng ở hai luật thì không tự chọn", () => {
    const enter = (q: string) => chonKhiEnter(DS_HANG_GPLX, q);
    expect(enter("B1")).toBe("cu:B1");
    expect(enter("b")).toBe("moi:B1");
    expect(enter("A")).toBe("moi:A2");
    expect(enter("A2")).toBe("cu:A2");
    expect(enter("B.01")).toBe("moi:B11");
    expect(enter("C1")).toBe("moi:C1");
    for (const q of ["A1", "C", "D", ""]) expect(enter(q)).toBeNull();
    expect(locLuaChon(DS_HANG_GPLX, "B1")[0].ma).toBe("cu:B1");
    expect(locLuaChon(DS_HANG_GPLX, "a").every((o) => o.ten.startsWith("A"))).toBe(true);
  });
  it("BUG-17: Nơi cấp nhận đúng mã hoặc tên, gõ dở không tự chọn", () => {
    const enter = (q: string) => chonKhiEnter(DS_NOI_CAP_GPLX, q);
    expect(enter("01")).toBe("01");
    expect(enter("ha tinh")).toBe("42");
    expect(enter("Ha")).toBeNull();
  });
  it("BUG-18: ngày không có thật bị chặn", () => {
    expect(loiBang(b({ ngay_cap: "31/02/2018" }))).toContain("Ngày cấp chưa đúng dd/mm/yyyy");
  });
  it("mỗi lỗi gắn đúng ô, tìm được ô sai đầu tiên (CHANGES #86)", () => {
    expect(loiTungO(bangMoi()).map((x) => x.o)).toEqual(["hang", "so", "ngay_tt", "ngay_cap"]);
    expect(loiTungO(b({ ngay_cap: "01/01/2010" }))[0].o).toBe("ngay_cap");
    expect(loiTungO(b({ ngay_hh: "27/04/2018" }))[0].o).toBe("ngay_hh");
    expect(oSaiDau([b(), b({ so: "" })])).toBe("gplx-1-so");
    expect(oSaiDau([b()])).toBeNull();
    expect(oSaiDau([])).toBeNull();
  });
  it("số khác 12 chữ số chỉ nhắc", () => {
    expect(soGplxLa("7900")).toBe(true);
    expect(soGplxLa("790000000123")).toBe(false);
  });
  it("danh sách Nơi cấp theo DM_DonViGTVT, tìm được theo mã và tên không dấu", () => {
    const tim = (q: string) => DS_NOI_CAP_GPLX.filter((o) => boDau(o.ten).includes(boDau(q))).map((o) => o.ma);
    expect(tim("qlhc")).toEqual(["00"]);
    expect(tim("binh phuoc")).toEqual(["70"]);
    expect(tim("70")).toEqual(["70"]);
    expect(tim("tay ninh")).toEqual(["72"]);
    expect(tim("long an")).toEqual(["80"]);
    expect(DS_NOI_CAP_GPLX).toHaveLength(65);
    expect(new Set(DS_NOI_CAP_GPLX.map((o) => o.ma)).size).toBe(DS_NOI_CAP_GPLX.length);
  });
});

describe("Nơi cấp suy từ số GPLX (user chốt 10/11/2026)", () => {
  it("điền theo 2 số đầu khi số đủ 12 chữ số và mã có trong danh mục Nơi cấp", () => {
    expect(suyNoiCapGplx("700239000070", DS_NOI_CAP_GPLX)).toBe("70");
    expect(suyNoiCapGplx("751260009163", DS_NOI_CAP_GPLX)).toBe("75");
    expect(suyNoiCapGplx("75126000916", DS_NOI_CAP_GPLX)).toBe("");
    expect(suyNoiCapGplx("030000000000", DS_NOI_CAP_GPLX)).toBe("");   // 03 không có trong danh mục
  });
  it("sửa số: chỉ đổi nơi cấp đang trống hoặc đang do máy tự điền", () => {
    expect(noiCapKhiDoiSo("", "700239000070", "", DS_NOI_CAP_GPLX)).toBe("70");
    expect(noiCapKhiDoiSo("700239000070", "790239000070", "70", DS_NOI_CAP_GPLX)).toBe("79");
    expect(noiCapKhiDoiSo("700239000070", "790239000070", "75", DS_NOI_CAP_GPLX)).toBe("75");
  });
});

describe("Tóm tắt GPLX ở form (popup, CHANGES #99)", () => {
  const b = (x: Partial<BangGplx>): BangGplx => ({ ...bangMoi(), ...x });
  it("mỗi bằng một dòng: hạng · số · tỉnh; bỏ bằng trống", () => {
    expect(tomTatGplx([b({ hang: "B2", so: "790000000123", don_vi: "79" }), b({})], DS_NOI_CAP_GPLX)).toEqual(["B2 · 790000000123 · Hồ Chí Minh"]);
    expect(tomTatGplx([b({ nhom: "moi", hang: "A1m", so: "700239000070" })], DS_NOI_CAP_GPLX)).toEqual(["A1 · 700239000070"]);
    expect(tomTatGplx([b({ so: "1" })], DS_NOI_CAP_GPLX)).toEqual(["Chưa chọn hạng · 1"]);
    expect(tomTatGplx([], DS_NOI_CAP_GPLX)).toEqual([]);
  });
  it("bằng chưa nhập ô nào coi như không có", () => {
    expect(bangTrong(bangMoi())).toBe(true);
    expect(bangTrong(b({ don_vi: "70" }))).toBe(false);
  });
});
