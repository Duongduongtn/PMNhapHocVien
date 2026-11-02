import { describe, expect, it } from "vitest";
import {
  DS_HANG_GPLX, bangMoi, docBang, duocMienLyThuyet, gomBang, khoaHang, loiBang, soGplxLa, tachKhoaHang, tenHang, trungHangDangKy,
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
