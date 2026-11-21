import { describe, expect, it } from "vitest";
import type { HvBanIn } from "./tnbc2Api";
import { chuGiaiO, demTheoMuc, doiPhan, doiPhanLoat, locHocVien, trangThaiChung } from "./phanThi";

// TNB-08 — logic thuần màn chọn phần thi (tên mục do server tính, ở đây chỉ đổi tập phần + gom/đếm).
function hv(o: Partial<HvBanIn> & { ma_dk: string }): HvBanIn {
  return {
    stt: 1, ho_ten: "NGUYỄN VĂN AN", ngay_sinh: "01/01/2000", so_cmt: "0700", hang: "B2", nhom: "oto",
    phan: ["L", "H", "Đ"], phai_thi: ["L", "H", "Đ"], dat: [], da_thi: false, ma_nd: 1, ghi_chu: "SH lần đầu",
    da_sua: false, nguon: "chua_thi", ten_nguon: "Chưa thi", nguon_luc: "", ket_qua_sh: "",
    mac_dinh: { phai_thi: ["L", "H", "Đ"], dat: [], ma_nd: 1, ghi_chu: "SH lần đầu", da_thi: false },
    pm_cu: "", pm_cu_khac: false, ...o,
  };
}

describe("TNB-08 — bấm ô phần thi", () => {
  it("phải thi → đã đạt và ngược lại, giữ thứ tự phần của hạng", () => {
    const h = hv({ ma_dk: "A" });
    expect(doiPhan(h, "H")).toEqual(["L", "Đ"]);
    expect(doiPhan({ ...h, phai_thi: ["L", "Đ"] }, "H")).toEqual(["L", "H", "Đ"]);
  });

  it("tắt hết các ô cho tập rỗng (server trả dòng 'cần chọn')", () => {
    expect(doiPhan(hv({ ma_dk: "A", phai_thi: ["Đ"] }), "Đ")).toEqual([]);
  });

  it("mô tô dùng LT/TH", () => {
    const m = hv({ ma_dk: "M", nhom: "moto", phan: ["LT", "TH"], phai_thi: ["LT", "TH"] });
    expect(doiPhan(m, "LT")).toEqual(["TH"]);
  });
});

describe("TNB-08 — bộ ô chung cho nhiều học viên", () => {
  const a = hv({ ma_dk: "A", phai_thi: ["L", "H", "Đ"] });
  const b = hv({ ma_dk: "B", phai_thi: ["Đ"] });

  it("lẫn trạng thái → bấm = đánh dấu đã đạt cho tất cả", () => {
    expect(trangThaiChung([a, b], "L")).toBe("lan");
    expect(doiPhanLoat([a, b], "L")).toEqual([{ ma_dk: "A", phai_thi: ["H", "Đ"] }, { ma_dk: "B", phai_thi: ["Đ"] }]);
  });

  it("tất cả đã đạt → bấm = bắt thi lại cho tất cả", () => {
    expect(trangThaiChung([a, b], "H")).toBe("lan");
    const hai = [{ ...a, phai_thi: ["Đ"] }, b];
    expect(trangThaiChung(hai, "L")).toBe("dat");
    expect(doiPhanLoat(hai, "L")).toEqual([{ ma_dk: "A", phai_thi: ["L", "Đ"] }, { ma_dk: "B", phai_thi: ["L", "Đ"] }]);
  });

  it("bỏ qua học viên không có phần đó (A3/A4 trộn với mô tô)", () => {
    const m = hv({ ma_dk: "M", nhom: "moto", phan: ["LT", "TH"], phai_thi: ["LT", "TH"] });
    expect(doiPhanLoat([a, m], "Đ").map((x) => x.ma_dk)).toEqual(["A"]);
  });
});

describe("TNB-08 — dải đếm và lọc", () => {
  const ds = [
    hv({ ma_dk: "1" }),
    hv({ ma_dk: "2" }),
    hv({ ma_dk: "3", phai_thi: ["Đ"], ma_nd: 6, ghi_chu: "SH lại Đ", da_sua: true, ho_ten: "TRẦN THỊ BÌNH", so_cmt: "0791" }),
    hv({ ma_dk: "4", phai_thi: [], ma_nd: null, ghi_chu: "" }),
  ];

  it("đếm theo mục, tách 'chưa có phần thi' và 'đã sửa'", () => {
    const d = demTheoMuc(ds);
    expect(d.nhom.map((x) => [x.ten, x.n])).toEqual([["SH lần đầu", 2], ["SH lại Đ", 1]]);
    expect(d.can).toBe(1);
    expect(d.sua).toBe(1);
  });

  it("mục trùng mã nhưng khác nhóm hạng được đếm riêng", () => {
    const ba = hv({ ma_dk: "5", nhom: "a3a4", phan: ["LT", "TH", "Đ"], phai_thi: ["LT", "TH", "Đ"] });
    expect(demTheoMuc([ds[0], ba]).nhom).toHaveLength(2);
  });

  it("lọc theo mục, cần chọn, đã sửa và ô tìm tên/CMT", () => {
    expect(locHocVien(ds, "tat", "")).toHaveLength(4);
    expect(locHocVien(ds, "can", "").map((h) => h.ma_dk)).toEqual(["4"]);
    expect(locHocVien(ds, "sua", "").map((h) => h.ma_dk)).toEqual(["3"]);
    expect(locHocVien(ds, "oto|6", "").map((h) => h.ma_dk)).toEqual(["3"]);
    expect(locHocVien(ds, "tat", "bình").map((h) => h.ma_dk)).toEqual(["3"]);
    expect(locHocVien(ds, "tat", "0791").map((h) => h.ma_dk)).toEqual(["3"]);
  });
});

describe("TNB-08 — chữ giải thích khi rê chuột", () => {
  const tenPhan = { L: "Lý thuyết", H: "Sa hình", "Đ": "Đường" };
  it("ô phải thi", () => {
    expect(chuGiaiO(hv({ ma_dk: "A" }), "H", tenPhan)).toBe("Sa hình — phải thi. Bấm nếu học viên đã đạt phần này.");
  });
  it("ô đã đạt kèm nguồn và ngày", () => {
    const h = hv({ ma_dk: "A", phai_thi: ["Đ"], nguon: "so", ten_nguon: "Kết quả Sở", nguon_luc: "2026-10-12T08:00:00" });
    expect(chuGiaiO(h, "L", tenPhan)).toBe("Lý thuyết — đã đạt (Kết quả Sở · 12/10/2026). Bấm để bắt thi lại.");
  });
});
