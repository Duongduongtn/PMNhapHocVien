// THU-01 — parse chuỗi QR CCCD + chuyển định dạng DB (mức 2). Hàm thuần, không DOM.
import { describe, it, expect } from "vitest";
import {
  parseCccdQr,
  ngaySinhToDb,
  ngayToIso,
  gioiTinhToMF,
  kiemDoDaiTen,
} from "./qr";

// 7 trường: CCCD | CMND cũ | Họ tên | NgaySinh(ddMMyyyy) | Giới tính | Nơi TT | NgayCap(ddMMyyyy)
const QR7 = "070202008455|221334455|Nguyễn Thanh Tâm|21112002|Nam|Xã Phú Nghĩa, Tỉnh Đồng Nai|10032021";
// 6 trường (không có CMND cũ)
const QR6 = "070202008455|Trần Thị Hoà|05051995|Nữ|Phường Tân Mai, Tỉnh Đồng Nai|03042019";

describe("THU-01 — parseCccdQr (6/7 trường)", () => {
  it("7 trường hợp lệ → đủ trường, có CMND cũ", () => {
    const r = parseCccdQr(QR7);
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.data).toEqual({
      soCccd: "070202008455",
      soCmndCu: "221334455",
      hoTen: "Nguyễn Thanh Tâm",
      ngaySinh: "21/11/2002",
      gioiTinh: "Nam",
      noiThuongTru: "Xã Phú Nghĩa, Tỉnh Đồng Nai",
      ngayCap: "10/03/2021",
    });
  });

  it("6 trường hợp lệ → soCmndCu rỗng", () => {
    const r = parseCccdQr(QR6);
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.data.soCmndCu).toBe("");
    expect(r.data.hoTen).toBe("Trần Thị Hoà");
    expect(r.data.gioiTinh).toBe("Nữ");
    expect(r.data.ngayCap).toBe("03/04/2019");
  });

  it("ngày sinh chỉ có năm (dd=00, MM=00) → trả 'yyyy'", () => {
    const r = parseCccdQr("070202008455|Lê Văn Cường|00001990|Nam|Xã K, Tỉnh L|10032021");
    expect(r.ok).toBe(true);
    if (!r.ok) return;
    expect(r.data.ngaySinh).toBe("1990");
  });

  it("số trường ≠ 6 và ≠ 7 → lỗi", () => {
    expect(parseCccdQr("a|b|c|d|e").ok).toBe(false); // 5 trường
  });

  it("CCCD không đủ 12 số → lỗi", () => {
    const r = parseCccdQr("07020200845|Tên A|21112002|Nam|Xã K|10032021"); // 11 số
    expect(r.ok).toBe(false);
    if (r.ok) return;
    expect(r.message).toContain("CCCD");
  });

  it("CMND cũ có nhưng ≠ 9 số → lỗi", () => {
    const r = parseCccdQr("070202008455|22133445|Tên A|21112002|Nam|Xã K|10032021"); // 8 số
    expect(r.ok).toBe(false);
  });

  it("giới tính lạ → lỗi; 'Nu'/'Nử' → Nữ", () => {
    expect(parseCccdQr("070202008455|Tên A|21112002|X|Xã K|10032021").ok).toBe(false);
    const r1 = parseCccdQr("070202008455|Tên A|21112002|Nu|Xã K|10032021");
    const r2 = parseCccdQr("070202008455|Tên A|21112002|Nử|Xã K|10032021");
    expect(r1.ok && r1.data.gioiTinh).toBe("Nữ");
    expect(r2.ok && r2.data.gioiTinh).toBe("Nữ");
  });

  it("ngày sinh sai định dạng → lỗi", () => {
    expect(parseCccdQr("070202008455|Tên A|2111200|Nam|Xã K|10032021").ok).toBe(false); // 7 số
  });

  it("ngày không tồn tại (30/02) → lỗi (new Date rollover)", () => {
    expect(parseCccdQr("070202008455|Tên A|30022000|Nam|Xã K|10032021").ok).toBe(false);
  });

  it("ngày cấp chỉ có năm → lỗi (ngày cấp phải đủ ngày)", () => {
    expect(parseCccdQr("070202008455|Tên A|21112002|Nam|Xã K|00002021").ok).toBe(false);
  });

  it("chuỗi rỗng → lỗi", () => {
    expect(parseCccdQr("").ok).toBe(false);
    expect(parseCccdQr("   ").ok).toBe(false);
  });

  it("họ tên rỗng (6 trường) → lỗi", () => {
    const r = parseCccdQr("070202008455||21112002|Nam|Xã K|10032021");
    expect(r.ok).toBe(false);
    if (r.ok) return;
    expect(r.message).toContain("Họ tên");
  });

  it("nơi thường trú rỗng → lỗi", () => {
    const r = parseCccdQr("070202008455|Tên A|21112002|Nam||10032021");
    expect(r.ok).toBe(false);
    if (r.ok) return;
    expect(r.message).toContain("thường trú");
  });
});

describe("THU-01 — chuyển định dạng DB", () => {
  it("ngaySinhToDb: dd/mm/yyyy → yyyymmdd; chỉ năm → yyyy0000", () => {
    expect(ngaySinhToDb("21/11/2002")).toBe("20021121");
    expect(ngaySinhToDb("1990")).toBe("19900000");
    expect(ngaySinhToDb("linh tinh")).toBe("");
  });

  it("ngayToIso: dd/mm/yyyy → yyyy-mm-dd", () => {
    expect(ngayToIso("10/03/2021")).toBe("2021-03-10");
    expect(ngayToIso("")).toBe("");
  });

  it("gioiTinhToMF: Nam → M, Nữ → F", () => {
    expect(gioiTinhToMF("Nam")).toBe("M");
    expect(gioiTinhToMF("Nữ")).toBe("F");
  });
});

describe("THU-01 — kiemDoDaiTen (EC-030 cảnh báo độ dài)", () => {
  it("tên bình thường → không cảnh báo", () => {
    expect(kiemDoDaiTen("Nguyễn Thanh Tâm")).toEqual([]);
  });

  it("họ tên 1 từ ngắn → không cảnh báo (họ đệm = 0)", () => {
    expect(kiemDoDaiTen("Nguyễn")).toEqual([]);
  });

  it("họ tên 26–50 ký tự → chỉ 'Họ tên in' (≤25) vượt, HoVaTen (≤50) chưa", () => {
    const ten = "A".repeat(10) + " " + "B".repeat(19); // dài 30; tên=19 (≤20), họ đệm=10
    const kt = kiemDoDaiTen(ten);
    const nhan = kt.map((x) => x.ten);
    expect(nhan).toContain("Họ tên in");
    expect(nhan).not.toContain("Họ và tên");
  });

  it("họ tên > 50 ký tự → cảnh báo Họ và tên (dai 51)", () => {
    const ten = "A".repeat(30) + " " + "B".repeat(20); // dài 51; họ đệm=30, tên=20
    const kt = kiemDoDaiTen(ten);
    const hvt = kt.find((x) => x.ten === "Họ và tên");
    expect(hvt?.dai).toBe(51);
    expect(hvt?.max).toBe(50);
  });
});
