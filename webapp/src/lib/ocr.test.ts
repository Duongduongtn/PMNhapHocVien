// THU-06 — tách trường từ text OCR mặt trước CCCD (mức 2). Hàm thuần, không DOM.
// Bám TDD §6.7: mốc fail = CCCD 12 số; ngày cấp luôn rỗng (mặt sau); điền phần đọc được
// + đánh dấu trường thiếu.
import { describe, it, expect } from "vitest";
import { tachTruongTuText } from "./ocr";

// Text OCR mô phỏng Tesseract đọc mặt trước CCCD gắn chip (nhãn song ngữ, có nhiễu đầu thẻ).
const TEXT_DU = [
  "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
  "Độc lập - Tự do - Hạnh phúc",
  "CĂN CƯỚC CÔNG DÂN",
  "Số / No.: 070202008455",
  "Họ và tên / Full name: NGUYỄN THANH TÂM",
  "Ngày sinh / Date of birth: 21/11/2002",
  "Giới tính / Sex: Nam    Quốc tịch / Nationality: Việt Nam",
  "Nơi thường trú / Place of residence:",
  "Thôn 2, Trấn Biên",
  "Đồng Nai",
  "Có giá trị đến / Date of expiry: 21/11/2027",
].join("\n");

describe("THU-06 — tachTruongTuText", () => {
  it("ảnh đủ nhãn → 5 trường mặt trước đúng, ngày cấp rỗng + đánh dấu", () => {
    const r = tachTruongTuText(TEXT_DU);
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.ket.data.soCccd).toBe("070202008455");
    expect(r.ket.data.hoTen).toBe("NGUYỄN THANH TÂM");
    expect(r.ket.data.ngaySinh).toBe("21/11/2002");
    expect(r.ket.data.gioiTinh).toBe("Nam");
    expect(r.ket.data.noiThuongTru).toBe("Thôn 2, Trấn Biên, Đồng Nai");
    expect(r.ket.data.ngayCap).toBe(""); // mặt trước không in ngày cấp
    expect(r.ket.danhDau).toContain("ngayCap"); // luôn đánh dấu để nhân viên nhập tay
  });

  it("không có CCCD 12 số → fail, không điền gì", () => {
    const r = tachTruongTuText("Họ và tên / Full name: NGUYỄN VĂN A\nGiới tính / Sex: Nam");
    expect(r.ok).toBe(false);
    if (r.ok) return;
    expect(r.message).toMatch(/12 số/);
  });

  it("CCCD in cách nhóm (có khoảng trắng) vẫn gộp đủ 12 số", () => {
    const r = tachTruongTuText("Số / No.: 0702 0200 8455\nGiới tính / Sex: Nữ");
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.ket.data.soCccd).toBe("070202008455");
    expect(r.ket.data.gioiTinh).toBe("Nữ");
  });

  it("đọc được một phần → điền phần có, trường thiếu để trống + đánh dấu", () => {
    // Có CCCD nhưng thiếu nhãn giới tính & nơi thường trú
    const r = tachTruongTuText("Số / No.: 070202008455\nHọ và tên / Full name: TRẦN THỊ HOÀ");
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.ket.data.hoTen).toBe("TRẦN THỊ HOÀ");
    expect(r.ket.data.gioiTinh).toBe("");
    expect(r.ket.data.noiThuongTru).toBe("");
    expect(r.ket.danhDau).toEqual(expect.arrayContaining(["gioiTinh", "noiThuongTru", "ngayCap"]));
    expect(r.ket.danhDau).not.toContain("hoTen"); // hoTen đọc được → không đánh dấu
  });

  it('không khớp nhầm "Nam" trong "Việt Nam" khi nhãn giới tính thiếu', () => {
    const r = tachTruongTuText("Số / No.: 070202008455\nQuốc tịch / Nationality: Việt Nam");
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.ket.data.gioiTinh).toBe(""); // không có nhãn "Giới tính" → không suy ra Nam
  });

  it("ngày sinh 1 chữ số ngày/tháng → zero-pad dd/mm/yyyy; ngày sai → rỗng", () => {
    const ok = tachTruongTuText("Số / No.: 070202008455\nNgày sinh / Date of birth: 5/3/1990");
    expect(ok.ok).toBe(true);
    if (ok.ok) expect(ok.ket.data.ngaySinh).toBe("05/03/1990");
    const sai = tachTruongTuText("Số / No.: 070202008455\nNgày sinh / Date of birth: 32/13/1990");
    expect(sai.ok).toBe(true);
    if (sai.ok) expect(sai.ket.data.ngaySinh).toBe("");
  });
});
