import { describe, expect, it } from "vitest";
import type { HvUngVien } from "./tnbc2Api";
import { demDaChon, gomTheoKhoaGoc, khopTim, trichMaTuVanBan } from "./tnbcUngVien";

// TNB-04 — bước ②: tìm không dấu, gom thi lại theo khóa gốc.
const hv = (ma_dk: string, ten: string, cmt: string, ma_kh: string, bg: string): HvUngVien => ({
  ma_dk, so_ho_so: "", ten, ngay_sinh: "01/05/1990", cmt, so_giay: "", hang: "B2", ma_kh, ten_kh: `Khóa ${ma_kh}`,
  tt: "14", ten_trang_thai: "Chưa đạt BC2 — cần lập lại", ma_bc2: "", bg, nhom: "thi_lai", ma_ly_do: "", ly_do: "",
  goi_y_xu_ly: null, tich_san: false, tuoi_thang: 3, trong_nguong: true,
});

describe("TNB-04 — bước ② chọn học viên", () => {
  const ds = [
    hv("C-1", "Nguyễn Thị Hoà", "079203011111", "K1", "2026-05-01"),
    hv("C-2", "Trần Văn Bình", "079203022222", "K2", "2026-08-01"),
    hv("C-3", "Lê Đức Anh", "079203033333", "K1", "2026-05-01"),
  ];

  it("tìm không dấu theo tên, theo CMT và theo mã đăng ký", () => {
    expect(khopTim(ds[0], "nguyen thi hoa")).toBe(true);
    expect(khopTim(ds[2], "le duc anh")).toBe(true);
    expect(khopTim(ds[1], "0792030222")).toBe(true);
    expect(khopTim(ds[0], "c-1")).toBe(true);
    expect(khopTim(ds[0], "tran")).toBe(false);
    expect(khopTim(ds[0], "   ")).toBe(true);
  });

  it("gom theo khóa gốc, khóa bế giảng gần nhất lên đầu", () => {
    const g = gomTheoKhoaGoc(ds);
    expect(g.map((k) => k.ma_kh)).toEqual(["K2", "K1"]);
    expect(g[1].hocVien.map((h) => h.ma_dk)).toEqual(["C-1", "C-3"]);
  });

  it("đếm số đã chọn trong một nhóm", () => {
    expect(demDaChon(ds, new Set(["C-1", "C-3", "C-9"]))).toBe(2);
    expect(demDaChon([], new Set(["C-1"]))).toBe(0);
  });

  it("trích mã từ văn bản dán: bỏ dòng trống và dòng trùng, giữ thứ tự", () => {
    expect(trichMaTuVanBan("079203011111\r\n\n079203022222\n079203011111\n  C-0003  \n")).toEqual([
      "079203011111",
      "079203022222",
      "C-0003",
    ]);
  });

  it("dòng nhiều cột (dán cả tên + CMT): lấy ô trông như CMT, không có thì lấy ô đầu", () => {
    expect(trichMaTuVanBan("Nguyễn Thị Hoà\t079203011111\t01/05/1990\nTrần Văn Bình\tC-0002\n")).toEqual([
      "079203011111",
      "Trần Văn Bình",
    ]);
  });

  it("không phân biệt hoa thường khi loại trùng; văn bản rỗng → mảng rỗng", () => {
    expect(trichMaTuVanBan("c-0001\nC-0001\n")).toEqual(["c-0001"]);
    expect(trichMaTuVanBan("  \n\n")).toEqual([]);
  });
});
