import { describe, it, expect } from "vitest";
import { hintDiem } from "./diemHint";

// Hồi quy BUG 07/10/2026 (KQD-01): lưới không hiện điểm đã lưu cho HV đã cập nhật (09/10/14/90).
// Code cũ: gợi ý chỉ "→ quy đổi" hoặc "—" (bỏ qua điểm đã lưu) → với (over=false, qd=null) trả "—".
describe("hintDiem — gợi ý điểm dưới ô nhập (BUG KQD-01)", () => {
  it("chưa gõ mà HV đã có điểm lưu → 'đã lưu X,X' (FAIL trên code cũ: ra '—')", () => {
    expect(hintDiem(false, null, 8.3)).toBe("đã lưu 8,3");
    expect(hintDiem(false, null, 5.0)).toBe("đã lưu 5,0");
  });
  it("đang gõ hợp lệ → preview quy đổi, KHÔNG đè điểm lưu", () => {
    expect(hintDiem(false, 6.0, 8.3)).toBe("→ 6,0");
  });
  it("vượt khung → 'sai' (ưu tiên cao nhất)", () => {
    expect(hintDiem(true, null, 8.3)).toBe("sai");
  });
  it("HV chưa có điểm + chưa gõ → '—'", () => {
    expect(hintDiem(false, null, null)).toBe("—");
    expect(hintDiem(false, null, undefined)).toBe("—");
  });
});
