import { expect, test, type Page } from "@playwright/test";

// Lưới Cập nhật KQĐT — chip kết luận KHÔNG được ngắt dòng ở cột "Kết luận" (16/10/2026):
// "Không đạt · đã lưu" từng rớt xuống 2 dòng vì chip thiếu whitespace-nowrap + cột 132px.
// Backend giả bằng page.route. Ảnh 4 viewport → <root>/anh-kiem/2026-10-16-KQD-luoi-chip/.

const KHOA = { ma_kh: "K40", ten_kh: "B01-K40", hang_gplx: "B", ngay_kg: "2026-07-30", ngay_bg: "2026-09-15", ngay_thi: "2026-09-20",
  dem: { dangky: 1, capnhat: 2, tuchoi: 1, giaitrinh: 1, ketxuat: 1 } };
const RONG = { ly_thuyet: null, mo_phong: null, hinh: null, tien_lui: null, duong: null };
const DAT = { ly_thuyet: 8, mo_phong: 7, hinh: 8, tien_lui: 7, duong: 8 };
const TRUOT = { ly_thuyet: 8, mo_phong: 7, hinh: 4.5, tien_lui: 7, duong: 8 };
const hv = (ma: string, ten: string, tt: string, kl: "dat" | "khong_dat" | null, diem: Record<string, number | null>) => ({
  ma_dk: ma, ho_ten: ten, ngay_sinh: "01/01/2000", so_cccd: "0792" + ma, so_ho_so: ma, hang: "B.01", ma_hang_moi: "B.01", ma_hang: "B11",
  tt_xuly: tt, ket_luan: kl, diem: { ...RONG, ...diem }, gio_duong: 18.4, km_duong: 719.4,
});
const DANH_SACH = [
  hv("A1", "NGUYỄN VĂN AN", "03", null, {}),
  hv("A2", "LÊ THỊ BÌNH", "09", "dat", DAT),
  hv("A3", "TRẦN VĂN CƯỜNG", "10", "khong_dat", TRUOT),
  hv("A4", "PHẠM THỊ DUNG", "14", "khong_dat", TRUOT),
  hv("A5", "VÕ THỊ EM", "90", "dat", DAT),
  hv("A6", "HOÀNG NGUYỄN THANH TRƯỜNG GIANG", "12", "dat", DAT),
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
}

for (const w of [375, 800, 1280, 1440]) {
  test(`chip kết luận một dòng + ảnh ${w}`, async ({ page }) => {
    await page.setViewportSize({ width: w, height: 900 });
    await giaBackend(page);
    await page.goto("/ket-qua/cap-nhat");
    await page.getByPlaceholder("Gõ tên khóa hoặc MaKH…").click();
    await page.getByText("B01-K40").first().click();
    await expect(page.getByText("NGUYỄN VĂN AN")).toBeVisible();

    const chip = page.getByText("Không đạt · đã lưu", { exact: true }).first();
    const h = await chip.evaluate((el) => el.getBoundingClientRect().height);
    const hDat = await page.getByText("Đạt · đã lưu", { exact: true }).first().evaluate((el) => el.getBoundingClientRect().height);
    // 1 dòng 11px + py-0.5 + viền ≈ 20-22px; 2 dòng ≥ 32px
    expect(h).toBeLessThan(26);
    expect(Math.abs(h - hDat)).toBeLessThan(2);

    await page.screenshot({ path: `../../anh-kiem/2026-10-16-KQD-luoi-chip/${w}.png`, fullPage: false });
  });
}

test("chẩn đoán: bỏ nowrap thì chip có rớt dòng không (xác nhận nguyên nhân)", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await giaBackend(page);
  await page.goto("/ket-qua/cap-nhat");
  await page.getByPlaceholder("Gõ tên khóa hoặc MaKH…").click();
  await page.getByText("B01-K40").first().click();
  const chip = page.getByText("Không đạt · đã lưu", { exact: true }).first();
  await expect(chip).toBeVisible();
  const r = await chip.evaluate((el) => {
    const cell = el.closest("td")!;
    el.classList.remove("whitespace-nowrap");
    const sau = el.getBoundingClientRect().height;
    return { cellW: cell.getBoundingClientRect().width, sau };
  });
  console.log("cột Kết luận rộng", r.cellW, "px; bỏ nowrap → chip cao", r.sau, "px");
});

test("tiêu đề cột môn không rớt dòng ở 1280", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await giaBackend(page);
  await page.goto("/ket-qua/cap-nhat");
  await page.getByPlaceholder("Gõ tên khóa hoặc MaKH…").click();
  await page.getByText("B01-K40").first().click();
  await expect(page.getByText("NGUYỄN VĂN AN")).toBeVisible();
  const hs = await page.locator("thead th").evaluateAll((els) => els.map((e) => ({ t: (e.textContent || "").trim(), h: Math.round(e.getBoundingClientRect().height), w: Math.round(e.getBoundingClientRect().width), sw: (e as HTMLElement).scrollWidth })));
  console.log(JSON.stringify(hs));
});
