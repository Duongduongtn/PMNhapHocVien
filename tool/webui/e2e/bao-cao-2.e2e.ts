import { expect, test, type Page } from "@playwright/test";

// TNB-04 — Lập BC2 bước ①: chọn khóa. Backend giả bằng page.route; không đụng DB thật.

interface Mo { cacLanGoi: string[] }

const KHOA = [
  { ma_kh: "K001", ten_kh: "Khóa B2-01/2026", ngay_bg: "2026-09-20", khoa_cu: false, co_bc1: true, so_bc1: "112/BCI/2026",
    bc2_cua_khoa: [], san_sang: 150, can_xem: 3, thi_lai: 74, thi_lai_cua_khoa: 4 },
  { ma_kh: "K002", ten_kh: "Khóa C-02/2026", ngay_bg: "2026-08-10", khoa_cu: false, co_bc1: false, so_bc1: "",
    bc2_cua_khoa: [], san_sang: 20, can_xem: 0, thi_lai: 74, thi_lai_cua_khoa: 0 },
];
const KHOA_MOTO = [
  { ma_kh: "M001", ten_kh: "Khóa A1-05/2026", ngay_bg: "2026-09-01", khoa_cu: false, co_bc1: true, so_bc1: "90/BCI/2026",
    bc2_cua_khoa: [{ ma: "861/26-TTTĐ", trang_thai: 0, tong_ghi: 74 }], san_sang: 12, can_xem: 0, thi_lai: 5, thi_lai_cua_khoa: 1 },
];

async function giaBackend(page: Page, mo: Mo) {
  await page.addInitScript(() => localStorage.setItem("tool_session_token", "tok-test"));
  await page.route("**/local/auth/me", (r) => r.fulfill({ json: { username: "thu1", ho_ten: "Nhân viên thử", vai_tro: "operator" } }));
  await page.route("**/local/config/moi-truong", (r) => r.fulfill({ json: { thu_muc_ghi_duoc: true, duong_dan: "x", da_cau_hinh: true } }));
  await page.route("**/version", (r) => r.fulfill({ json: { build: "dev", commit: "x" } }));
  await page.route("**/local/tnbc2/bc2/khoa-san-sang?**", async (r) => {
    const u = new URL(r.request().url());
    mo.cacLanGoi.push(u.search);
    const loai = u.searchParams.get("loai");
    await r.fulfill({ json: { loai, hom_nay: "2026-10-11", thi_lai_thang: 12, thi_lai_tat_ca: 74,
      khoa: loai === "moto" ? KHOA_MOTO : KHOA } });
  });
}

test.describe("TNB-04 — Lập BC2 bước ①: chọn khóa", () => {
  test("hiện khóa kèm đếm Sẵn sàng / Thi lại / Cần xem; khóa chưa có BC1 mờ và khóa nút", async ({ page }) => {
    await giaBackend(page, { cacLanGoi: [] });
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    await page.getByRole("button", { name: "Lập BC2 mới" }).click();

    const k1 = page.getByTestId("khoa-K001");
    await expect(k1.getByText("Khóa B2-01/2026")).toBeVisible();
    await expect(k1.getByText("150")).toBeVisible();
    await expect(k1.getByText("Thi lại (≤ 12 tháng)")).toBeVisible();
    await expect(k1.getByText("112/BCI/2026")).toBeVisible();

    const k2 = page.getByTestId("khoa-K002");
    await expect(k2.getByText(/chưa có BC1/)).toBeVisible();
    await expect(k2.getByRole("button", { name: "Chọn khóa này →" })).toBeDisabled();
    await k2.click();                                            // bấm cả thẻ cũng không đi tiếp
    await expect(page.getByText("Chọn khóa cần lập BC2")).toBeVisible();
    if (process.env.CHUP_ANH) {
      for (const w of [800, 1280, 1440]) {
        await page.setViewportSize({ width: w, height: 800 });
        await page.screenshot({ path: `${process.env.CHUP_ANH}/${w}-buoc-1.png` });
      }
    }
  });

  test("chọn khóa → sang bước ②, đầu wizard ghi đúng khóa; quay về danh sách được", async ({ page }) => {
    await giaBackend(page, { cacLanGoi: [] });
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    await page.getByRole("button", { name: "Lập BC2 mới" }).click();
    await page.getByTestId("khoa-K001").getByRole("button", { name: "Chọn khóa này →" }).click();
    await expect(page.getByText("Bước 2 đang được dựng.")).toBeVisible();
    await expect(page.getByText(/Ô tô · Lập BC2 mới · Khóa B2-01\/2026/)).toBeVisible();
    await page.getByRole("button", { name: "← Danh sách BC2" }).click();
    await expect(page.getByRole("button", { name: "Lập BC2 mới" })).toBeVisible();
  });

  test("mô tô: khóa đã có BC2 đang mở → sang thêm học viên vào BC2 đó", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [] };
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    await page.getByRole("button", { name: "Mô tô" }).click();
    await page.getByRole("button", { name: "Lập BC2 mới" }).click();
    const k = page.getByTestId("khoa-M001");
    await expect(k.getByText("Đã có BC2 861/26-TTTĐ")).toBeVisible();
    await k.getByRole("button", { name: "Chọn khóa này →" }).click();
    await expect(page.getByText(/Khóa này đã có BC2 861\/26-TTTĐ/)).toBeVisible();
    await expect(page.getByText(/Thêm vào BC2 số 861\/26-TTTĐ/)).toBeVisible();
    expect(mo.cacLanGoi[0]).toContain("loai=moto");
  });

  test("công tắc Hiện khóa cũ gửi cu=true; Làm tươi gửi lam_tuoi=true", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [] };
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    await page.getByRole("button", { name: "Lập BC2 mới" }).click();
    await expect(page.getByTestId("khoa-K001")).toBeVisible();
    await page.getByLabel("Hiện khóa cũ").check();
    await expect.poll(() => mo.cacLanGoi.some((q) => q.includes("cu=true"))).toBe(true);
    await page.getByRole("button", { name: "Làm tươi" }).click();
    await expect.poll(() => mo.cacLanGoi.some((q) => q.includes("lam_tuoi=true"))).toBe(true);
  });
});
