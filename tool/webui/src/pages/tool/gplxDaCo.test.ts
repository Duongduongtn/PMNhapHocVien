import { describe, expect, it } from "vitest";
import {
  DS_HANG_GPLX, bangMoi, bangTrong, nhanHangGon, tomTatGplx, type BangGplx, dienNoiCapTheoSo, docBang, noiCapKhiDoiSo, suyNoiCapGplx, duocMienLyThuyet, gomBang, khoaHang, loiBang, soGplxLa, tachKhoaHang, tenHang, trungHangDangKy,
} from "./gplxDaCo";

const b = (over = {}) => ({ ...bangMoi(), hang: "B2", so: "790000000123", ngay_tt: "15/08/2012", ngay_cap: "27/04/2018", ...over });

describe("bảng hạng GPLX", () => {
  it("nhãn luật mới lưu đúng mã DM_HangGPLX", () => {
    const ten = (ma: string) => DS_HANG_GPLX.find((x) => x.ma === ma)?.ten;
    expect(ten("moi:A1m")).toBe("A1 — luật mới");
    expect(ten("moi:A2")).toBe("A — luật mới");
    expect(ten("moi:B1")).toBe("B — luật mới");
    expect(ten("moi:B11")).toBe("B.01 — luật mới");
    expect(ten("cu:B2")).toBe("B2 — luật cũ");
  });
  it("khóa chọn không trùng dù mã trùng giữa hai nhóm", () => {
    const ma = DS_HANG_GPLX.map((x) => x.ma);
    expect(new Set(ma).size).toBe(ma.length);
    expect(ma).toContain("moi:B1");
    expect(ma).toContain("cu:B1");
  });
  it("tách và ghép khóa, nhãn theo nhóm", () => {
    expect(tachKhoaHang("moi:A1m")).toEqual({ nhom: "moi", hang: "A1m" });
    expect(khoaHang({ ...bangMoi(), nhom: "moi", hang: "B1" })).toBe("moi:B1");
    expect(khoaHang(bangMoi())).toBe("");
    expect(tenHang({ nhom: "moi", hang: "A1m" })).toBe("A1");
    expect(tenHang({ nhom: "cu", hang: "A1" })).toBe("A1");
    expect(tenHang({ nhom: "moi", hang: "B1" })).toBe("B");
  });
});

describe("đổi ngày và dữ liệu nháp", () => {
  it("đọc JSON yyyymmdd thành dd/mm/yyyy, gom lại đúng", () => {
    const ds = docBang('[{"nhom":"cu","hang":"B2","so":"1","ngay_cap":"20180427"}]');
    expect(ds[0].ngay_cap).toBe("27/04/2018");
    expect(gomBang(ds)[0].ngay_cap).toBe("20180427");
  });
  it("JSON rỗng hoặc hỏng ra danh sách rỗng", () => {
    expect(docBang(null)).toEqual([]);
    expect(docBang("[]")).toEqual([]);
    expect(docBang("{hỏng")).toEqual([]);
  });
  it("ngày gõ dở giữ nguyên để nháp không mất", () => {
    expect(gomBang([b({ ngay_cap: "27/04" })])[0].ngay_cap).toBe("27/04");
  });
  it("bằng mô tô không gửi ngày hết hạn", () => {
    expect(gomBang([b({ hang: "A1", ngay_hh: "01/01/2030" })])[0].ngay_hh).toBe("");
    expect(gomBang([b({ ngay_hh: "01/01/2030" })])[0].ngay_hh).toBe("20300101");
  });
});

describe("thông báo nghiệp vụ", () => {
  it.each(["A1", "Am", "A1m"])("khóa %s có bằng ô tô: miễn lý thuyết", (k) => {
    expect(duocMienLyThuyet(k, [b({ hang: "B2" })])).toBe(true);
    expect(duocMienLyThuyet(k, [b({ hang: "A1m" }), b({ hang: "C1" })])).toBe(true);
  });
  it("không miễn: khóa A2, khóa ô tô, hoặc chỉ có bằng mô tô", () => {
    expect(duocMienLyThuyet("A2", [b({ hang: "B2" })])).toBe(false);
    expect(duocMienLyThuyet("B1", [b({ hang: "B2" })])).toBe(false);
    expect(duocMienLyThuyet("A1m", [b({ hang: "A1" })])).toBe(false);
  });
  it("trùng hạng so theo mã", () => {
    expect(trungHangDangKy("B1", [b({ hang: "B1" })])).toBe(true);
    expect(trungHangDangKy("A1m", [b({ hang: "A1" })])).toBe(false);
  });
  it("nhắc số GPLX khác 12 chữ số, ô trống không nhắc", () => {
    expect(soGplxLa("790000000123")).toBe(false);
    expect(soGplxLa("7900")).toBe(true);
    expect(soGplxLa("")).toBe(false);
  });
  it("lỗi chặn: thiếu hạng, số, ngày sai; bằng mô tô bỏ qua hết hạn", () => {
    expect(loiBang(bangMoi())).toEqual(["Chưa chọn hạng", "Chưa nhập số GPLX", "Chưa nhập ngày trúng tuyển", "Chưa nhập ngày cấp"]);
    expect(loiBang(b({ ngay_cap: "01/01/2010" }))).toEqual(["Ngày cấp phải sau ngày trúng tuyển"]);
    expect(loiBang(b({ ngay_hh: "27/04/2018" }))).toEqual(["Ngày hết hạn phải sau ngày cấp"]);
    expect(loiBang(b({ ngay_cap: "27/04" }))).toEqual(["Ngày cấp chưa đúng dd/mm/yyyy"]);
    expect(loiBang(b({ hang: "A1", ngay_hh: "27" }))).toEqual([]);
    expect(loiBang(b())).toEqual([]);
  });
});

describe("Nơi cấp suy từ số GPLX (user chốt 10/11/2026)", () => {
  const NC = [{ ma: "70" }, { ma: "79" }];
  it("12 chữ số, 2 số đầu có trong danh mục → mã đó; còn lại không đoán", () => {
    expect(suyNoiCapGplx("700239000070", NC)).toBe("70");
    expect(suyNoiCapGplx(" 790000000123 ", NC)).toBe("79");
    expect(suyNoiCapGplx("7002390000", NC)).toBe("");      // chưa đủ 12 số
    expect(suyNoiCapGplx("510171010240", NC)).toBe("");    // mã không có trong danh mục
    expect(suyNoiCapGplx("70023900007a", NC)).toBe("");
  });
  it("chỉ điền ô đang trống, không ghi đè nơi cấp đã có; không đổi gì thì giữ nguyên mảng", () => {
    const ds = [{ so: "700239000070", don_vi: "" }, { so: "790000000123", don_vi: "75" }];
    expect(dienNoiCapTheoSo(ds, NC)).toEqual([{ so: "700239000070", don_vi: "70" }, { so: "790000000123", don_vi: "75" }]);
    const daDu = [{ so: "700239000070", don_vi: "75" }];
    expect(dienNoiCapTheoSo(daDu, NC)).toBe(daDu);
  });
  it("sửa số: nơi cấp tự điền đi theo số mới, nơi cấp người nhập chọn khác thì giữ", () => {
    expect(noiCapKhiDoiSo("70023900007", "700239000070", "", NC)).toBe("70");
    expect(noiCapKhiDoiSo("700239000070", "790239000070", "70", NC)).toBe("79");
    expect(noiCapKhiDoiSo("700239000070", "79023900007", "70", NC)).toBe("");
    expect(noiCapKhiDoiSo("700239000070", "790239000070", "75", NC)).toBe("75");
  });
});

describe("Tóm tắt + badge GPLX (popup, CHANGES #99)", () => {
  const b = (x: Partial<BangGplx>): BangGplx => ({ ...bangMoi(), ...x });
  const NC = [{ ma: "79", ten: "79 — Hồ Chí Minh" }];
  it("tóm tắt mỗi bằng một dòng, bỏ bằng trống", () => {
    expect(tomTatGplx([b({ hang: "B2", so: "790000000123", don_vi: "79" }), b({})], NC)).toEqual(["B2 · 790000000123 · Hồ Chí Minh"]);
    expect(tomTatGplx([b({ so: "1" })], NC)).toEqual(["Chưa chọn hạng · 1"]);
  });
  it("badge tối đa 2 hạng rồi +n", () => {
    expect(nhanHangGon([b({ hang: "B2" })])).toBe("B2");
    expect(nhanHangGon([b({ hang: "B2" }), b({ nhom: "moi", hang: "A1m" }), b({ hang: "C" }), b({ hang: "D" })])).toBe("B2·A1 +2");
    expect(bangTrong(bangMoi())).toBe(true);
  });
});
