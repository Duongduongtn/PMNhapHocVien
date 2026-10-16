import { expect, test, type Page } from "@playwright/test";

// KQD-04 đổi (task 141, CHANGES #77/#78) — giải trình chung + mẫu + Quản lý mẫu + chuyển hàng loạt + cảnh báo sau Lưu.
// Backend giả bằng page.route (POST /giai-trinh-lo, GET/PUT /mau-giai-trinh, POST /cap-nhat).
// Ảnh → <root>/anh-kiem/2026-10-16-KQD-task141/.

const KHOA = { ma_kh: "K40", ten_kh: "B01-K40", hang_gplx: "B", ngay_kg: "2026-07-30", ngay_bg: "2026-09-15", ngay_thi: "2026-09-20",
  dem: { dangky: 0, capnhat: 0, tuchoi: 4, giaitrinh: 0, ketxuat: 0 } };
const DAT = { ly_thuyet: 28, mo_phong: 7, hinh: 8, tien_lui: 7, duong: 8 };
const TRUOT = { ly_thuyet: 28, mo_phong: 7, hinh: 4.5, tien_lui: 7, duong: 8 };
const hv = (ma: string, ten: string, tt: string, kl: "dat" | "khong_dat" | null, diem: Record<string, number>, extra: Record<string, unknown> = {}) => ({
  ma_dk: ma, ho_ten: ten, ngay_sinh: "01/01/2000", so_cccd: "0792" + ma, so_ho_so: ma, hang: "B.01", ma_hang_moi: "B.01", ma_hang: "B11",
  tt_xuly: tt, ket_luan: kl, diem, gio_duong: 20, km_duong: 810, ...extra,
});
const DANH_SACH = [
  hv("A1", "NGUYỄN VĂN AN", "14", "dat", DAT, { ly_do_tu_choi: "Thiếu biên bản." }),
  hv("A2", "LÊ THỊ BÌNH", "14", "dat", DAT, { giai_trinh: "Giải trình riêng của Bình." }),
  hv("A3", "TRẦN VĂN CƯỜNG", "14", "khong_dat", TRUOT),
  hv("A4", "PHẠM THỊ DUNG", "14", "dat", DAT, { km_duong: null }),
];

interface Goi { ten: string; body: unknown }
async function giaBackend(page: Page, goi: Goi[], tuyChon: { loLoi?: "lo_loi" | "khong_ro"; capNhat?: Record<string, unknown> } = {}) {
  await page.addInitScript(() => localStorage.setItem("tool_session_token", "tok-test"));
  await page.route("**/local/**", (r) => r.fulfill({ json: [] }));
  await page.route("**/local/auth/me", (r) => r.fulfill({ json: { username: "thu1", ho_ten: "Nhân viên thử", vai_tro: "operator" } }));
  await page.route("**/local/config/moi-truong", (r) => r.fulfill({ json: { thu_muc_ghi_duoc: true, duong_dan: "x", da_cau_hinh: true } }));
  await page.route("**/version", (r) => r.fulfill({ json: { build: "dev", commit: "x" } }));
  await page.route("**/local/sync/targets", (r) => r.fulfill({ json: { selected: "t1", targets: [{ key: "t1", name: "DB đích", database: "GPLX_CDB_CSDT", host: "x" }] } }));
  await page.route("**/local/ketqua/khoa?**", (r) => r.fulfill({ json: [KHOA] }));
  await page.route("**/local/ketqua/hoc-vien?**", (r) => r.fulfill({ json: DANH_SACH }));
  await page.route("**/local/ketqua/chuong-trinh?**", (r) => r.fulfill({ json: { ma_kh: "K40", ct: "cu" } }));
  await page.route("**/local/ketqua/luat", (r) => r.fulfill({ json: { mon_bat_buoc: ["ly_thuyet", "mo_phong", "hinh", "tien_lui", "duong"] } }));
  await page.route("**/local/ketqua/mo-khoa**", (r) => r.fulfill({ json: { mo_duoc: false, goi_chua_gui: [], goi_da_gui: [] } }));
  await page.route("**/local/ketqua/sua-sau-gui**", (r) => r.fulfill({ json: [] }));
  let mau = { mau: ["Đã nộp lại ảnh chân dung đạt chuẩn."], phien_ban: 1 };
  await page.route("**/local/ketqua/mau-giai-trinh**", async (r) => {
    if (r.request().method() === "PUT") {
      const b = r.request().postDataJSON() as { mau: string[] };
      goi.push({ ten: "PUT mau", body: b });
      mau = { mau: b.mau, phien_ban: mau.phien_ban + 1 };
    }
    await r.fulfill({ json: mau });
  });
  await page.route("**/local/ketqua/giai-trinh-lo**", async (r) => {
    const b = r.request().postDataJSON() as { ma_dk: string[] };
    goi.push({ ten: "giai-trinh-lo", body: b });
    if (tuyChon.loLoi === "khong_ro") {
      return r.fulfill({ status: 502, json: { detail: { ketqua: "khong_ro", thong_bao: "Không rõ kết quả — kiểm tra lại danh sách trước khi gửi lại." } } });
    }
    return r.fulfill({ json: { ok: true, da_chuyen: b.ma_dk, bo_qua: [], giu_rieng: b.ma_dk.includes("A2") ? 1 : 0 } });
  });
  await page.route("**/local/ketqua/cap-nhat**", async (r) => {
    const b = r.request().postDataJSON() as { ma_dk: string };
    goi.push({ ten: "cap-nhat", body: b });
    await r.fulfill({ json: { ok: true, ma_dk: b.ma_dk, ket_luan: "dat", tt_moi: "14", so_giay: null, quy_doi: {}, ct: "cu", ...(tuyChon.capNhat ?? {}) } });
  });
}

async function chonKhoa(page: Page) {
  await page.goto("/ket-qua/cap-nhat");
  await page.getByPlaceholder("Gõ tên khóa hoặc MaKH…").click();
  await page.getByText("B01-K40").first().click();
  await expect(page.getByText("NGUYỄN VĂN AN")).toBeVisible();
}
const tab = (page: Page, ten: string) => page.locator("button", { hasText: new RegExp("^" + ten + "\\s+\\d") });

test.describe("KQD-04 #77 — giải trình chung + mẫu", () => {
  test("nút Giải trình chung mở khung; chọn mẫu điền sẵn; Lưu thành mẫu gửi PUT đủ danh sách", async ({ page }) => {
    const goi: Goi[] = [];
    await giaBackend(page, goi);
    await chonKhoa(page);
    await expect(page.getByLabel("Giải trình chung của khóa")).toHaveCount(0);   // thu gọn mặc định
    await page.getByRole("button", { name: /Giải trình chung/ }).click();
    await page.getByLabel("Chọn mẫu giải trình").selectOption({ index: 1 });
    await expect(page.getByLabel("Giải trình chung của khóa")).toHaveValue("Đã nộp lại ảnh chân dung đạt chuẩn.");
    await page.getByLabel("Giải trình chung của khóa").fill("Đã bổ sung biên bản sát hạch.");
    await page.getByRole("button", { name: "Lưu thành mẫu" }).click();
    await expect.poll(() => goi.find((g) => g.ten === "PUT mau")).toBeTruthy();
    expect((goi.find((g) => g.ten === "PUT mau")!.body as { mau: string[] }).mau).toEqual(
      ["Đã nộp lại ảnh chân dung đạt chuẩn.", "Đã bổ sung biên bản sát hạch."]);
  });

  test("Quản lý mẫu: sửa + xóa + thêm rồi Lưu thay đổi → một PUT thay toàn bộ danh sách", async ({ page }) => {
    const goi: Goi[] = [];
    await giaBackend(page, goi);
    await chonKhoa(page);
    await page.getByRole("button", { name: /Giải trình chung/ }).click();
    await page.getByRole("button", { name: "Quản lý mẫu" }).click();
    const hop = page.getByRole("dialog", { name: "Quản lý mẫu giải trình" });
    await hop.getByLabel("Mẫu 1").fill("Mẫu đã sửa lại.");
    await hop.getByRole("button", { name: "+ Thêm mẫu" }).click();
    await hop.getByLabel("Mẫu 2").fill("Mẫu thêm mới.");
    await hop.getByRole("button", { name: "+ Thêm mẫu" }).click();       // mẫu 3 để trống → bị loại
    await hop.getByRole("button", { name: "Lưu thay đổi" }).click();
    await expect.poll(() => goi.find((g) => g.ten === "PUT mau")).toBeTruthy();
    const b = goi.find((g) => g.ten === "PUT mau")!.body as { mau: string[]; phien_ban: number };
    expect(b.phien_ban).toBe(1);
    expect(b.mau.filter((m) => m.trim())).toEqual(["Mẫu đã sửa lại.", "Mẫu thêm mới."]);
  });
});

test.describe("KQD-04 #77 — chuyển hàng loạt", () => {
  test("tab Cần xử lý: tích → hộp xác nhận nêu đủ điều kiện/bỏ qua/giữ riêng → chuyển gửi đúng danh sách", async ({ page }) => {
    const goi: Goi[] = [];
    await giaBackend(page, goi);
    await chonKhoa(page);
    await tab(page, "Cần xử lý").click();
    await page.getByLabel("Chọn tất cả học viên Sở từ chối ở trang này").check();
    await page.getByRole("button", { name: /Giải trình & chuyển chờ kết xuất lại \(4\)/ }).click();
    const hop = page.getByRole("dialog", { name: "Giải trình và chuyển chờ kết xuất lại" });
    await expect(hop).toContainText("Đã chọn 4");
    await expect(hop).toContainText("đủ điều kiện 2");        // A1, A2 (A3 không đạt, A4 thiếu km)
    await expect(hop).toContainText("bỏ qua 2");
    await expect(hop).toContainText("Không đạt — không được kết xuất");
    await expect(hop).toContainText("chưa đủ điểm / giờ-km / số giấy");
    await expect(hop).toContainText("1 người đã có giải trình riêng");
    // nội dung rỗng → khóa nút + dòng đỏ
    const nut = hop.getByRole("button", { name: /^Chuyển 2 học viên/ });
    await expect(nut).toBeDisabled();
    await expect(hop).toContainText("Phải có nội dung giải trình mới chuyển được");
    await hop.getByLabel("Nội dung giải trình hàng loạt").fill("Đã bổ sung biên bản sát hạch.");
    await expect(nut).toBeEnabled();
    await nut.click();
    await expect.poll(() => goi.find((g) => g.ten === "giai-trinh-lo")).toBeTruthy();
    const b = goi.find((g) => g.ten === "giai-trinh-lo")!.body as { ma_dk: string[]; noi_dung: string; ghi_de_rieng: boolean };
    expect(b.noi_dung).toBe("Đã bổ sung biên bản sát hạch.");
    expect(b.ghi_de_rieng).toBe(false);
    expect([...b.ma_dk].sort()).toEqual(["A1", "A2", "A3", "A4"]);   // server mới là nơi quyết cuối
    await expect(page.getByText(/Đã chuyển 4 học viên/)).toBeVisible();
  });

  test("mất kết nối khi lưu → thông báo vàng 'Không rõ kết quả', danh sách được tải lại", async ({ page }) => {
    const goi: Goi[] = [];
    await giaBackend(page, goi, { loLoi: "khong_ro" });
    await chonKhoa(page);
    await tab(page, "Cần xử lý").click();
    await page.getByLabel("Chọn NGUYỄN VĂN AN").check();
    await page.getByRole("button", { name: /Giải trình & chuyển chờ kết xuất lại \(1\)/ }).click();
    const hop = page.getByRole("dialog", { name: "Giải trình và chuyển chờ kết xuất lại" });
    await hop.getByLabel("Nội dung giải trình hàng loạt").fill("Đã bổ sung.");
    await hop.getByRole("button", { name: /^Chuyển 1 học viên/ }).click();
    await expect(page.getByRole("alert")).toContainText("Không rõ kết quả");
  });
});

test.describe("KQD-04 #77 — chống sai sót khi chuyển lô", () => {
  test("lỗi mạng phía trình duyệt (tool sập) → 'Không rõ kết quả', KHÔNG báo 'chưa chuyển ai'", async ({ page }) => {
    await giaBackend(page, []);
    await page.route("**/local/ketqua/giai-trinh-lo**", (r) => r.abort("failed"));
    await chonKhoa(page);
    await tab(page, "Cần xử lý").click();
    await page.getByLabel("Chọn NGUYỄN VĂN AN").check();
    await page.getByRole("button", { name: /Giải trình & chuyển chờ kết xuất lại \(1\)/ }).click();
    const hop = page.getByRole("dialog", { name: "Giải trình và chuyển chờ kết xuất lại" });
    await hop.getByLabel("Nội dung giải trình hàng loạt").fill("Đã bổ sung.");
    await hop.getByRole("button", { name: /^Chuyển 1 học viên/ }).click();
    await expect(page.getByRole("alert")).toContainText("Không rõ kết quả");
    await expect(page.getByRole("alert")).not.toContainText("chưa chuyển học viên nào");
  });

  test("nội dung > 1000 ký tự: KHÔNG cắt âm thầm — đếm đỏ và khóa nút chuyển", async ({ page }) => {
    await giaBackend(page, []);
    await chonKhoa(page);
    await tab(page, "Cần xử lý").click();
    await page.getByLabel("Chọn NGUYỄN VĂN AN").check();
    await page.getByRole("button", { name: /Giải trình & chuyển chờ kết xuất lại \(1\)/ }).click();
    const hop = page.getByRole("dialog", { name: "Giải trình và chuyển chờ kết xuất lại" });
    await hop.getByLabel("Nội dung giải trình hàng loạt").fill("x".repeat(1001));
    await expect(hop).toContainText("1001/1000");
    await expect(hop.getByRole("button", { name: /^Chuyển 1 học viên/ })).toBeDisabled();
  });

  test("kết quả lô liệt kê MỌI người bị bỏ qua kèm lý do (không chỉ 3 người đầu)", async ({ page }) => {
    await giaBackend(page, []);
    await page.route("**/local/ketqua/giai-trinh-lo**", (r) => r.fulfill({ json: {
      ok: true, da_chuyen: [], giu_rieng: 0,
      bo_qua: [
        { ma_dk: "A1", ly_do: "khong_dat" },
        { ma_dk: "A2", ly_do: "chua_du_diem", chi_tiet: { ly_do: ["thieu_mon"], mon_thieu: ["mo_phong"] } },
        { ma_dk: "A3", ly_do: "khong_thuoc_co_so" },
        { ma_dk: "A4", ly_do: "chua_du_diem", chi_tiet: { ly_do: ["thieu_so_giay"], mon_thieu: [] } },
      ] } }));
    await chonKhoa(page);
    await tab(page, "Cần xử lý").click();
    await page.getByLabel("Chọn tất cả học viên Sở từ chối ở trang này").check();
    await page.getByRole("button", { name: /Giải trình & chuyển chờ kết xuất lại/ }).click();
    const hop = page.getByRole("dialog", { name: "Giải trình và chuyển chờ kết xuất lại" });
    await hop.getByLabel("Nội dung giải trình hàng loạt").fill("Đã bổ sung.");
    await hop.getByRole("button", { name: /^Chuyển \d+ học viên/ }).click();
    const canh = page.getByRole("alert");
    await expect(canh).toContainText("Không chuyển 4 học viên");
    await expect(canh).toContainText("thiếu môn Mô phỏng");
    await expect(canh).toContainText("thiếu số giấy HTKH");
    await expect(canh).toContainText("PHẠM THỊ DUNG");   // đủ 4 người, người thứ 4 vẫn có mặt
  });
});

test.describe("KQD-04 #77 — cảnh báo sau Lưu một học viên", () => {
  async function nhapVaLuu(page: Page, ten: string) {
    const dong = page.locator("tr", { hasText: ten });
    await dong.locator('input[data-kqd-c="2"]').fill("85");
    await dong.getByRole("button", { name: "Lưu", exact: true }).click();
  }

  test("Đạt thiếu giải trình → thông báo vàng ĐỨNG LÂU nói rõ chưa kết xuất được", async ({ page }) => {
    const goi: Goi[] = [];
    await giaBackend(page, goi, { capNhat: { thieu_giai_trinh: true, tt_moi: "14" } });
    await chonKhoa(page);
    await nhapVaLuu(page, "NGUYỄN VĂN AN");
    const canh = page.getByRole("alert");
    await expect(canh).toContainText("CHƯA có giải trình");
    await expect(canh).toContainText("chưa kết xuất lại được");
    await page.waitForTimeout(4500);                              // không tự tắt như thông báo thường
    await expect(canh).toBeVisible();
    await canh.getByRole("button", { name: "Đóng cảnh báo" }).click();
    await expect(page.getByRole("alert")).toHaveCount(0);
  });

  test("Đạt + có giải trình chung → gửi giai_trinh_chung và thông báo thường 'chuyển sang Đã giải trình'", async ({ page }) => {
    const goi: Goi[] = [];
    await giaBackend(page, goi, { capNhat: { tt_moi: "90" } });
    await chonKhoa(page);
    await page.getByRole("button", { name: /Giải trình chung/ }).click();
    await page.getByLabel("Giải trình chung của khóa").fill("Đã bổ sung biên bản.");
    await nhapVaLuu(page, "NGUYỄN VĂN AN");
    await expect(page.getByText(/chuyển sang "Đã giải trình"/)).toBeVisible();
    await expect(page.getByRole("alert")).toHaveCount(0);
    const b = goi.find((g) => g.ten === "cap-nhat")!.body as { giai_trinh_chung?: string | null; giai_trinh?: string | null };
    expect(b.giai_trinh_chung).toBe("Đã bổ sung biên bản.");
    expect(b.giai_trinh ?? null).toBeNull();                       // không gửi '' làm xóa giải trình đã lưu
  });

  test("bước chuyển lỗi → cảnh báo vàng 'CHƯA chuyển' kèm gợi ý Lưu lại", async ({ page }) => {
    await giaBackend(page, [], { capNhat: { canh_bao: "chua_chuyen_90", tt_moi: "14" } });
    await chonKhoa(page);
    await nhapVaLuu(page, "NGUYỄN VĂN AN");
    await expect(page.getByRole("alert")).toContainText("CHƯA chuyển");
    await expect(page.getByRole("alert")).toContainText("Bấm Lưu lại");
  });
});

test("header 1280: ô tìm nằm CÙNG hàng với dải tab (không rớt xuống hàng 3)", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await giaBackend(page, []);
  await chonKhoa(page);
  const yTab = (await tab(page, "Tất cả").boundingBox())!.y;
  const yTim = (await page.getByPlaceholder("Tìm tên / CCCD").boundingBox())!.y;
  expect(Math.abs(yTim - yTab)).toBeLessThan(14);
});

for (const w of [375, 800, 1280, 1440]) {
  test(`ảnh giải trình hàng loạt ${w}`, async ({ page }) => {
    await page.setViewportSize({ width: w, height: 900 });
    await giaBackend(page, []);
    await chonKhoa(page);
    await tab(page, "Cần xử lý").click();
    await page.getByRole("button", { name: /Giải trình chung/ }).click();
    await page.getByLabel("Giải trình chung của khóa").fill("Đã bổ sung biên bản sát hạch.");
    // Tool dùng trên máy tính (rộng ≥ ~1180, bảng cuộn ngang): 375 chỉ chụp bố cục, không thao tác.
    if (w < 800) {
      await page.screenshot({ path: `../../anh-kiem/2026-10-16-KQD-task141/${w}-da-chon.png` });
      return;
    }
    await page.getByLabel("Chọn tất cả học viên Sở từ chối ở trang này").check({ force: true });
    await page.screenshot({ path: `../../anh-kiem/2026-10-16-KQD-task141/${w}-da-chon.png` });
    await page.getByRole("button", { name: /Giải trình & chuyển chờ kết xuất lại/ }).click({ force: true });
    await page.screenshot({ path: `../../anh-kiem/2026-10-16-KQD-task141/${w}-hop-xac-nhan.png` });
  });
}
