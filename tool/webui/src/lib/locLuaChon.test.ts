import { describe, expect, it } from "vitest";
import { DS_HANG_GPLX } from "../pages/tool/gplxDaCo";
import { chonKhiEnter, locLuaChon } from "./locLuaChon";

const NOI_CAP = [
  { ma: "01", ten: "01 — Hà Nội" },
  { ma: "42", ten: "42 — Hà Tĩnh" },
  { ma: "79", ten: "79 — Hồ Chí Minh" },
];

describe("BUG-19: Enter ở ô gõ để lọc", () => {
  const hang = (q: string) => chonKhiEnter(DS_HANG_GPLX, q)?.ma ?? null;
  it("chọn đúng hạng đã gõ", () => {
    expect(hang("B1")).toBe("cu:B1");
    expect(hang("b")).toBe("moi:B1");
    expect(hang("A")).toBe("moi:A2");
    expect(hang("A2")).toBe("cu:A2");
    expect(hang("B.01")).toBe("moi:B11");
    expect(hang("C1")).toBe("moi:C1");
  });
  it("hạng có ở cả hai luật hoặc chưa gõ thì không tự chọn", () => {
    for (const q of ["A1", "C", "D", ""]) expect(hang(q)).toBeNull();
  });
  it("ô Hạng không tìm trong chữ luật mới/cũ, dòng trùng khớp đứng đầu", () => {
    expect(locLuaChon(DS_HANG_GPLX, "a").every((o) => o.ten.startsWith("A"))).toBe(true);
    expect(locLuaChon(DS_HANG_GPLX, "B1")[0].ma).toBe("cu:B1");
  });
  it("tìm theo cả mã và tên, gõ dở nhiều khả năng thì không tự chọn", () => {
    expect(chonKhiEnter(NOI_CAP, "79")?.ma).toBe("79");
    expect(chonKhiEnter(NOI_CAP, "ha tinh")?.ma).toBe("42");
    expect(chonKhiEnter(NOI_CAP, "chi minh")?.ma).toBe("79");
    expect(chonKhiEnter(NOI_CAP, "Ha")).toBeNull();
  });
  it("gõ nối cả cụm trong tên vẫn tìm thấy", () => {
    const khoa = [{ ma: "1", ten: "K12 — B2 (KG 01/01/2026, 30 HV)" }, { ma: "2", ten: "K13 — B2 (KG 01/02/2026, 25 HV)" }];
    expect(locLuaChon(khoa, "K12 — B2").map((o) => o.ma)).toEqual(["1"]);
    expect(chonKhiEnter(khoa, "K12 — B2")?.ma).toBe("1");
    expect(chonKhiEnter(khoa, "B2")).toBeNull();
  });
  it("tên không có phần mã vẫn dùng được", () => {
    const xa = [{ ma: "1", ten: "Phường Tân Định" }, { ma: "2", ten: "Phường Tân Bình" }];
    expect(chonKhiEnter(xa, "tan dinh")?.ma).toBe("1");
    expect(chonKhiEnter(xa, "Phường Tân")).toBeNull();
  });
});
