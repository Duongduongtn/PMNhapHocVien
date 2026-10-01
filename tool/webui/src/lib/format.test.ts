// NAP-01 — helper bỏ dấu / cảnh báo chính tả mức A / hiển thị ngày (mức 2). Hàm thuần.
import { describe, it, expect } from "vitest";
import { boDau, nghiSaiChinhTa, ymdToVN } from "./format";

describe("NAP-01 — boDau (tìm không dấu)", () => {
  it("bỏ dấu tiếng Việt + đ→d, về chữ thường", () => {
    expect(boDau("Nguyễn")).toBe("nguyen");
    expect(boDau("Đà Nẵng")).toBe("da nang");
    expect(boDau("TRẦN THỊ HOÀ")).toBe("tran thi hoa");
  });

  it("đầu vào đã là ASCII → về chữ thường, không đổi khác", () => {
    expect(boDau("NGUYEN VAN A")).toBe("nguyen van a");
  });

  it("null/undefined → chuỗi rỗng", () => {
    expect(boDau(null as unknown as string)).toBe("");
    expect(boDau(undefined as unknown as string)).toBe("");
  });
});

describe("NAP-01 — nghiSaiChinhTa (chính tả mức A)", () => {
  it("tên có dấu đầy đủ → không cảnh báo", () => {
    expect(nghiSaiChinhTa("Nguyễn Văn An")).toBe("");
  });

  it("tên IN HOA có dấu → KHÔNG báo thiếu dấu (mọi tên trên màn nạp đều IN HOA)", () => {
    expect(nghiSaiChinhTa("NGUYỄN VĂN AN")).toBe("");
  });

  it("tên không dấu → nghi thiếu dấu", () => {
    expect(nghiSaiChinhTa("NGUYEN VAN A")).toContain("thiếu dấu");
  });

  it("có chữ số → cảnh báo", () => {
    expect(nghiSaiChinhTa("Nguyễn Văn 2")).toContain("có chữ số");
  });

  it("khoảng trắng thừa — giữa dòng", () => {
    expect(nghiSaiChinhTa("Nguyễn  Văn An")).toContain("khoảng trắng thừa");
  });

  it("khoảng trắng thừa — đầu dòng", () => {
    expect(nghiSaiChinhTa(" Nguyễn Văn An")).toContain("khoảng trắng thừa");
  });

  it("ký tự lạ → cảnh báo", () => {
    expect(nghiSaiChinhTa("Nguyễn@An")).toContain("ký tự lạ");
  });

  it("tên dân tộc có gạch nối / nháy (có dấu) → KHÔNG báo ký tự lạ (❔1)", () => {
    expect(nghiSaiChinhTa("H'Hen Niê")).toBe("");
    expect(nghiSaiChinhTa("Lê-Na")).toBe("");
  });

  it("rỗng / toàn khoảng trắng → không cảnh báo", () => {
    expect(nghiSaiChinhTa("")).toBe("");
    expect(nghiSaiChinhTa("   ")).toBe("");
  });
});

describe("NAP-01 — ymdToVN (yyyymmdd → hiển thị)", () => {
  it("yyyymmdd → dd/mm/yyyy", () => {
    expect(ymdToVN("20021121")).toBe("21/11/2002");
  });

  it("chỉ năm (yyyy0000) → yyyy", () => {
    expect(ymdToVN("19900000")).toBe("1990");
  });

  it("rỗng / null / undefined → rỗng", () => {
    expect(ymdToVN("")).toBe("");
    expect(ymdToVN(null)).toBe("");
    expect(ymdToVN(undefined)).toBe("");
  });
});
