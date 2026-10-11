import { describe, expect, it } from "vitest";
import { congSoGiay, danhLienTiep, khoaSoGiay, khoaTrungTrongLo, tachCotDan, tachSoGiay } from "./tnbcSoGiay";

// TNB-01 — số giấy CNTN: đánh liên tiếp, dán cột Excel, trùng trong lô.
describe("TNB-01 — số giấy CNTN", () => {
  it("tách tiền tố và số, giữ độ rộng", () => {
    expect(tachSoGiay("N1|7282")).toEqual({ tienTo: "N1|", so: 7282, rong: 4 });
    expect(tachSoGiay("  N1|0099 ")).toEqual({ tienTo: "N1|", so: 99, rong: 4 });
    expect(tachSoGiay("N1|")).toBeNull();
    expect(tachSoGiay("")).toBeNull();
  });

  it("cộng số giấy giữ số 0 đầu", () => {
    expect(congSoGiay("N1|0099", 1)).toBe("N1|0100");
    expect(congSoGiay("N1|7329", 0)).toBe("N1|7329");
    expect(congSoGiay("abc", 1)).toBeNull();
  });

  it("đánh liên tiếp theo thứ tự truyền vào", () => {
    expect(danhLienTiep("N1|7329", ["A", "B", "C"])).toEqual({ A: "N1|7329", B: "N1|7330", C: "N1|7331" });
    expect(danhLienTiep("khong-co-so", ["A"])).toBeNull();
  });

  it("dán cột Excel: bỏ dòng trống và lấy ô cuối của dòng nhiều cột", () => {
    expect(tachCotDan("N1|7329\r\nN1|7330\n\n  N1|7331  \n")).toEqual(["N1|7329", "N1|7330", "N1|7331"]);
    expect(tachCotDan("Nguyễn Thị Hoà\tN1|7329\nTrần Văn Bình\tN1|7330")).toEqual(["N1|7329", "N1|7330"]);
  });

  it("khóa so sánh bỏ | và khoảng trắng, không phân biệt hoa thường", () => {
    expect(khoaSoGiay("N1|7282")).toBe(khoaSoGiay("n1 7282"));
    expect(khoaSoGiay(null)).toBe("");
  });

  it("phát hiện trùng trong lô, bỏ ô trống", () => {
    const t = khoaTrungTrongLo(["N1|7329", "n1|7329", "N1|7330", "", ""]);
    expect([...t]).toEqual(["n17329"]);
  });
});
