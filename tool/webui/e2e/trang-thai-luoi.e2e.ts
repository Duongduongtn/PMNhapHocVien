import { expect, test, type Page } from "@playwright/test";

// KQD-01 đổi (task 140, CHANGES #77/#78) — lưới Cập nhật KQĐT: cột Trạng thái nghiệp vụ + dải tab nhóm việc có đếm
// + lý do Sở từ chối trên dòng + 2 chip cảnh báo + header gọn. Backend giả bằng page.route.
// Ảnh 4 viewport → <root>/anh-kiem/2026-10-16-KQD-task140/.

const KHOA = { ma_kh: "K40", ten_kh: "B01-K40", hang_gplx: "B", ngay_kg: "2026-07-30", ngay_bg: "2026-09-15", ngay_thi: "2026-09-20",
  dem: { dangky: 1, capnhat: 4, tuchoi: 3, giaitrinh: 2, ketxuat: 1 } };
const RONG = { ly_thuyet: null, mo_phong: null, hinh: null, tien_lui: null, duong: null };
const DAT = { ly_thuyet: 28, mo_phong: 7, hinh: 8, tien_lui: 7, duong: 8 };
const TRUOT = { ly_thuyet: 28, mo_phong: 7, hinh: 4.5, tien_lui: 7, duong: 8 };
type Kl = "dat" | "khong_dat" | null;
const hv = (ma: string, ten: string, tt: string, kl: Kl, diem: Record<string, number | null>, extra: Record<string, unknown> = {}) => ({
  ma_dk: ma, ho_ten: ten, ngay_sinh: "01/01/2000", so_cccd: "0792" + ma, so_ho_so: ma, hang: "B.01", ma_hang_moi: "B.01", ma_hang: "B11",
  tt_xuly: tt, ket_luan: kl, diem: { ...RONG, ...diem }, gio_duong: 20, km_duong: 810, ...extra,
});
const DANH_SACH = [
  hv("A1", "NGUYỄN VĂN AN", "03", null, {}),
  hv("A2", "LÊ THỊ BÌNH", "09", "dat", DAT),
  hv("A3", "TRẦN VĂN CƯỜNG", "10", "khong_dat", TRUOT),
  hv("A4", "PHẠM THỊ DUNG", "14", "dat", DAT, { ly_do_tu_choi: "Ảnh chân dung không đạt chuẩn, đề nghị cập nhật lại." }),
  hv("A5", "VÕ THỊ EM", "14", "dat", DAT, { ly_do_tu_choi: "Thiếu biên bản.", giai_trinh: "Đã bổ sung biên bản." }),
  hv("A6", "ĐẶNG VĂN PHÚC", "90", "dat", DAT, { giai_trinh: "Đã giải trình." }),
  hv("A7", "BÙI THỊ GIANG", "90", "khong_dat", TRUOT, { giai_trinh: "Đã giải trình." }),
  hv("A8", "HOÀNG VĂN HẠNH", "12", "dat", DAT),
  hv("A9", "TRƯƠNG VĂN KHÁNH", "14", "khong_dat", TRUOT),
];

async function giaBackend(page: Page) {
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
}

async function chonKhoa(page: Page) {
  await page.goto("/ket-qua/cap-nhat");
  await page.getByPlaceholder("Gõ tên khóa hoặc MaKH…").click();
  await page.getByText("B01-K40").first().click();
  await expect(page.getByText("NGUYỄN VĂN AN")).toBeVisible();
}
const tab = (page: Page, ten: string) => page.locator("button", { hasText: new RegExp("^" + ten + "\\s+\\d") });

test.describe("KQD-01 #77 — cột Trạng thái + dải tab", () => {
  test("tab có đếm đúng nhóm việc; Cần xử lý = 14 + 90 không đạt", async ({ page }) => {
    await giaBackend(page);
    await chonKhoa(page);
    await expect(tab(page, "Tất cả")).toContainText("9");
    await expect(tab(page, "Chưa nhập")).toContainText("1");
    await expect(tab(page, "Chờ kết xuất")).toContainText("2");       // 09 + 90 Đạt
    await expect(tab(page, "Không đạt")).toContainText("1");
    await expect(tab(page, "Cần xử lý")).toContainText("4");          // 14 ×3 + 90 Không đạt
    await expect(tab(page, "Đã gửi / Hoàn thành")).toContainText("1");
  });

  test("bấm tab Cần xử lý chỉ còn 14 và 90 không đạt", async ({ page }) => {
    await giaBackend(page);
    await chonKhoa(page);
    await tab(page, "Cần xử lý").click();
    await expect(page.getByText("PHẠM THỊ DUNG")).toBeVisible();
    await expect(page.getByText("VÕ THỊ EM")).toBeVisible();
    await expect(page.getByText("BÙI THỊ GIANG")).toBeVisible();
    await expect(page.getByText("LÊ THỊ BÌNH")).toHaveCount(0);
    await expect(page.getByText("ĐẶNG VĂN PHÚC")).toHaveCount(0);      // 90 Đạt ở Chờ kết xuất
  });

  test("cột Trạng thái: nhãn nghiệp vụ, không lộ mã số", async ({ page }) => {
    await giaBackend(page);
    await chonKhoa(page);
    const dong = (ten: string) => page.locator("tr", { hasText: ten });
    await expect(dong("LÊ THỊ BÌNH")).toContainText("Đã nhập · chờ kết xuất");
    await expect(dong("PHẠM THỊ DUNG")).toContainText("Sở từ chối");
    await expect(dong("ĐẶNG VĂN PHÚC")).toContainText("Đã giải trình");
    await expect(dong("HOÀNG VĂN HẠNH")).toContainText("Đã gửi Sở · chờ duyệt");
    await expect(dong("NGUYỄN VĂN AN")).toContainText("Chưa nhập điểm");
  });

  test("lý do Sở từ chối hiện ngay trên dòng HV 14", async ({ page }) => {
    await giaBackend(page);
    await chonKhoa(page);
    await expect(page.locator("tr", { hasText: "PHẠM THỊ DUNG" })).toContainText("Sở: Ảnh chân dung không đạt chuẩn");
  });

  test("chip cảnh báo: 14 Đạt thiếu giải trình (cam) · 90 không đạt (đỏ); 14 đã giải trình thì không", async ({ page }) => {
    await giaBackend(page);
    await chonKhoa(page);
    await expect(page.locator("tr", { hasText: "PHẠM THỊ DUNG" })).toContainText("Thiếu giải trình — chưa kết xuất được");
    await expect(page.locator("tr", { hasText: "VÕ THỊ EM" })).not.toContainText("Thiếu giải trình");
    await expect(page.locator("tr", { hasText: "BÙI THỊ GIANG" })).toContainText("Đang giải trình nhưng không đạt");
    await expect(page.locator("tr", { hasText: "ĐẶNG VĂN PHÚC" })).not.toContainText("Đang giải trình nhưng không đạt");
  });

  test("sửa lẻ: gõ 1 môn làm đủ Đạt thì chip 'thiếu giải trình' hiện NGAY (môn khác lấy điểm đã lưu)", async ({ page }) => {
    await giaBackend(page);
    await chonKhoa(page);
    const dong = page.locator("tr", { hasText: "TRƯƠNG VĂN KHÁNH" });
    await expect(dong).not.toContainText("Thiếu giải trình");           // đã lưu Không đạt (sa hình 4,5)
    await dong.locator('input[data-kqd-c="2"]').fill("85");             // sa hình 85 → quy đổi ≥ 5 → ĐẠT
    await expect(dong).toContainText("Thiếu giải trình — chưa kết xuất được");
  });

  test("Chú giải mở/đóng và liệt kê trạng thái", async ({ page }) => {
    await giaBackend(page);
    await chonKhoa(page);
    await page.getByRole("button", { name: "Chú giải" }).click();
    await expect(page.getByText("Kết xuất ở phần mềm CDB").first()).toBeVisible();
  });
});

for (const w of [375, 800, 1280, 1440]) {
  test(`ảnh lưới ${w}`, async ({ page }) => {
    await page.setViewportSize({ width: w, height: 900 });
    await giaBackend(page);
    await chonKhoa(page);
    await page.screenshot({ path: `../../anh-kiem/2026-10-16-KQD-task140/${w}.png` });
    if (w === 1280) {
      await tab(page, "Cần xử lý").click();
      await page.screenshot({ path: `../../anh-kiem/2026-10-16-KQD-task140/${w}-can-xu-ly.png` });
    }
  });
}
