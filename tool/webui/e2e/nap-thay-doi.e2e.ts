import { expect, test, type Page } from "@playwright/test";

// NAP-08 — báo hồ sơ chưa nạp vừa được app web cập nhật: dải cảnh báo, danh sách, chip, lọc, Đã xem,
// cảnh báo đậm khi nháp giữ ảnh cũ ("Dùng ảnh mới" / "Giữ ảnh cũ"). Backend giả bằng page.route; không đụng DB thật.

interface TD { uuid: string; ho_ten: string; truong: string[]; luc: string; nhap_giu_anh_cu: boolean }
interface Mo { ds: TD[]; daXem: Record<string, unknown>[]; boAnh: string[] }

const hv = (uuid: string, ten: string) => ({
  uuid, so_cccd: `0792000000${uuid.slice(-2)}`, so_cmnd_cu: null, ho_ten: ten, ngay_sinh: "19900501", gioi_tinh: "F",
  noi_tt_raw: "Số 5, Hà Nội", ngay_cap: "20200101", noi_cap_cccd: "", co_anh: 1, created_at: null,
  trang_thai: "cho", loi: null, ma_dk: null, so_ho_so: null, gplx_da_co_json: null,
});
const DIA_CHI = JSON.stringify({ ma_dvhc: "01001", ma_dvql: "01", ten_xa: "Phường Ba Đình", ten_tinh: "Hà Nội" });

const moi = (): Mo => ({
  daXem: [], boAnh: [],
  ds: [
    { uuid: "u01", ho_ten: "Nguyễn Thị Hoà", truong: ["tt:ho_ten", "tt:noi_tt_raw", "dc_reset"], luc: "2026-11-04T09:12:00", nhap_giu_anh_cu: false },
    { uuid: "u02", ho_ten: "Trần Văn Bình", truong: ["anh"], luc: "2026-11-04T09:12:00", nhap_giu_anh_cu: true },
  ],
});

async function vao(page: Page, mo: Mo, w = 1280) {
  await page.addInitScript(() => localStorage.setItem("tool_session_token", "tok-test"));
  await page.route("**/local/auth/me", (r) => r.fulfill({ json: { username: "thu1", ho_ten: "Nhân viên thử", vai_tro: "operator" } }));
  await page.route("**/local/config/moi-truong", (r) => r.fulfill({ json: { thu_muc_ghi_duoc: true, duong_dan: "x", da_cau_hinh: true } }));
  await page.route("**/version", (r) => r.fulfill({ json: { build: "dev", commit: "x" } }));
  await page.route("**/local/khoa-hoc?**", (r) => r.fulfill({ json: [{ ma_kh: "K001", ten_kh: "Khóa thử", hang_gplx: "B", hang_dt: "B", ma_so_gtvt: "01", ma_loai_hs: 2 }] }));
  await page.route("**/local/dvhc/so-gtvt", (r) => r.fulfill({ json: [] }));
  await page.route("**/local/dvhc/noi-cap-gplx", (r) => r.fulfill({ json: [] }));
  await page.route("**/local/giay-to?**", (r) => r.fulfill({ json: [{ ma_gt: 1, ten_gt: "CCCD" }] }));
  await page.route("**/local/nap/danh-sach", (r) => r.fulfill({ json: [hv("u01", "Nguyễn Thị Hoà"), hv("u02", "Trần Văn Bình"), hv("u03", "Lê Văn Cường")] }));
  await page.route(/\/local\/nap\/nhap(\?.*)?$/, (r) => r.fulfill({ json: [] }));
  await page.route(/\/local\/nap\/nhap\/[^/?]+$/, async (r) => {
    const uuid = decodeURIComponent(new URL(r.request().url()).pathname.split("/").pop() ?? "");
    if (r.request().method() !== "GET") return r.fulfill({ json: { ok: true } });
    await r.fulfill({ json: { uuid, dia_chi_json: DIA_CHI, chi_tiet: null, noi_cap: null, ngay_cap: null, tick_json: null,
      jp2_b64: uuid === "u02" ? "QUJD" : null, anh_preview: null, updated_at: null, chon_in_gplx: null, gplx_da_co_json: null, gplx_goc_json: null } });
  });
  await page.route("**/local/nap/keo/*/anh", (r) => r.fulfill({ status: 404, body: "" }));
  await page.route("**/local/nap/thay-doi", (r) => r.fulfill({ json: mo.ds }));
  await page.route("**/local/nap/thay-doi/da-xem", async (r) => {
    const b = r.request().postDataJSON() as { uuids?: string[]; tat_ca?: boolean; loai?: string };
    mo.daXem.push(b);
    if (b.tat_ca) mo.ds = [];
    else for (const u of b.uuids ?? []) {
      const d = mo.ds.find((x) => x.uuid === u);
      if (!d) continue;
      d.truong = b.loai ? d.truong.filter((t) => t !== b.loai) : [];
      if (b.loai === "anh") d.nhap_giu_anh_cu = false;
    }
    mo.ds = mo.ds.filter((d) => d.truong.length > 0);
    await r.fulfill({ json: { ok: true } });
  });
  await page.route("**/local/nap/nhap/*/bo-anh", async (r) => {
    const uuid = decodeURIComponent(new URL(r.request().url()).pathname.split("/").slice(-2)[0]);
    mo.boAnh.push(uuid);
    mo.ds = mo.ds.map((d) => (d.uuid === uuid ? { ...d, truong: d.truong.filter((t) => t !== "anh"), nhap_giu_anh_cu: false } : d)).filter((d) => d.truong.length > 0);
    await r.fulfill({ json: { ok: true, uuid, da_bo: true } });
  });
  await page.setViewportSize({ width: w, height: 900 });
  await page.goto("/tool/nap");
  await expect(page.getByTestId("hv-u03")).toBeVisible();
}

const ngan = (page: Page) => page.getByRole("complementary", { name: "Ngăn chuẩn bị hồ sơ" });

test.describe("NAP-08 — hồ sơ chưa nạp được app web cập nhật", () => {
  test("dải cảnh báo, danh sách chỉ nêu tên trường, chip và bộ lọc", async ({ page }) => {
    const mo = moi();
    await vao(page, mo);
    const dai = page.getByTestId("dai-thay-doi");
    await expect(dai).toContainText("2 hồ sơ được app web cập nhật sau lần kéo trước");
    await page.getByTestId("mo-ds-thay-doi").click();
    await expect(page.getByTestId("ds-thay-doi-u01")).toContainText("Họ tên · Nơi thường trú (cần map lại)");
    await expect(page.getByTestId("ds-thay-doi-u02")).toContainText("Ảnh");
    await expect(page.getByTestId("ds-thay-doi-u02")).toContainText("Nháp giữ ảnh cũ");
    await expect(page.getByTestId("chip-thay-doi-u01")).toHaveText("App web đã sửa");
    await expect(page.getByTestId("chip-thay-doi-u02")).toHaveText("Ảnh đã đổi");
    await expect(page.getByTestId("chip-thay-doi-u03")).toHaveCount(0);
    // lọc chỉ hồ sơ được app web sửa
    await page.getByTestId("loc-thay-doi").click();
    await expect(page.getByTestId("hv-u03")).toHaveCount(0);
    await expect(page.getByTestId("hv-u01")).toBeVisible();
    await page.getByTestId("loc-thay-doi").click();
    await expect(page.getByTestId("hv-u03")).toBeVisible();
  });

  test("Đã xem tất cả: dải cảnh báo biến mất, chip biến mất", async ({ page }) => {
    const mo = moi();
    await vao(page, mo);
    await page.getByTestId("da-xem-tat-ca").click();
    await expect(page.getByTestId("dai-thay-doi")).toHaveCount(0);
    await expect(page.getByTestId("chip-thay-doi-u01")).toHaveCount(0);
    expect(mo.daXem).toEqual([{ tat_ca: true }]);
  });

  test("mở hồ sơ nháp giữ ảnh cũ: cảnh báo đậm, Dùng ảnh mới gọi bỏ ảnh nháp", async ({ page }) => {
    const mo = moi();
    await vao(page, mo);
    await page.getByTestId("hv-u02").click();
    const b = ngan(page).getByTestId("banner-anh-cu");
    await expect(b).toContainText("Ảnh đã đổi ở app web, nháp đang giữ ảnh cũ");
    await expect(b).toContainText("hồ sơ sẽ được nạp với ảnh cũ trong nháp");
    await b.getByTestId("dung-anh-moi").click();
    await expect(ngan(page).getByTestId("banner-anh-cu")).toHaveCount(0);
    expect(mo.boAnh).toEqual(["u02"]);
    await expect(page.getByTestId("chip-thay-doi-u02")).toHaveCount(0);
  });

  test("Giữ ảnh cũ chỉ gỡ loại ảnh, không bỏ ảnh nháp", async ({ page }) => {
    const mo = moi();
    await vao(page, mo);
    await page.getByTestId("hv-u02").click();
    await ngan(page).getByTestId("giu-anh-cu").click();
    await expect(ngan(page).getByTestId("banner-anh-cu")).toHaveCount(0);
    expect(mo.daXem).toEqual([{ uuids: ["u02"], loai: "anh" }]);
    expect(mo.boAnh).toEqual([]);
  });

  test("hồ sơ chỉ đổi thông tin: banner nhẹ có nút Đã xem, không có cảnh báo đậm", async ({ page }) => {
    const mo = moi();
    await vao(page, mo);
    await page.getByTestId("hv-u01").click();
    await expect(ngan(page).getByTestId("banner-anh-cu")).toHaveCount(0);
    const nhe = ngan(page).getByTestId("banner-thay-doi");
    await expect(nhe).toContainText("Họ tên · Nơi thường trú (cần map lại)");
    await nhe.getByRole("button", { name: "Đã xem" }).click();
    await expect(ngan(page).getByTestId("banner-thay-doi")).toHaveCount(0);
  });

  test("không có hồ sơ nào đổi: không hiện dải cảnh báo, không có nút lọc", async ({ page }) => {
    const mo = moi();
    mo.ds = [];
    await vao(page, mo);
    await expect(page.getByTestId("dai-thay-doi")).toHaveCount(0);
    await expect(page.getByTestId("loc-thay-doi")).toHaveCount(0);
  });
});
