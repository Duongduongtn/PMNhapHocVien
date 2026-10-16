import { expect, test, type Page } from "@playwright/test";

// Ô "Chọn in GPLX" ở màn Nạp (NAP-01): điền sẵn theo hạng khóa kèm TÊN loại in, đổi được, lưu nháp, gửi đúng khi nạp.
// Mô tô (A*) → "In 01 GPLX không thời hạn" (3) · ô tô → "In 01 GPLX có thời hạn" (2). Backend giả bằng page.route.

interface Mo {
  luu: { uuid: string; body: Record<string, unknown> }[];
  napLo: { items: Record<string, unknown>[] }[];
  nhapSan?: number | null; // chon_in_gplx đã lưu sẵn trong nháp của u01
}

const khoaCua = (hang: string) => [{
  ma_kh: "K001", ten_kh: hang.startsWith("A") ? "Khóa mô tô A1-01/2026" : "Khóa ô tô B2-01/2026",
  hang_gplx: hang, hang_dt: hang, ma_so_gtvt: "01", ma_loai_hs: hang.startsWith("A") ? 1 : 2,
}];
const hv = (uuid: string, ten: string) => ({
  uuid, so_cccd: `0792000000${uuid.slice(-2)}`, so_cmnd_cu: null, ho_ten: ten, ngay_sinh: "19900501", gioi_tinh: "F",
  noi_tt_raw: "Số 5, Hà Nội", ngay_cap: "20200101", noi_cap_cccd: "", co_anh: 1, created_at: null,
  trang_thai: "cho", loi: null, ma_dk: null, so_ho_so: null,
});
const DIA_CHI = JSON.stringify({ ma_dvhc: "01001", ma_dvql: "01", ten_xa: "Phường Ba Đình", ten_tinh: "Hà Nội" });

async function giaBackend(page: Page, mo: Mo, hang: string) {
  await page.addInitScript(() => localStorage.setItem("tool_session_token", "tok-test"));
  await page.route("**/local/auth/me", (r) => r.fulfill({ json: { username: "thu1", ho_ten: "Nhân viên thử", vai_tro: "operator" } }));
  await page.route("**/local/config/moi-truong", (r) => r.fulfill({ json: { thu_muc_ghi_duoc: true, duong_dan: "x", da_cau_hinh: true } }));
  await page.route("**/version", (r) => r.fulfill({ json: { build: "dev", commit: "x" } }));
  await page.route("**/local/khoa-hoc?**", (r) => r.fulfill({ json: khoaCua(hang) }));
  await page.route("**/local/dvhc/so-gtvt", (r) => r.fulfill({ json: [] }));
  await page.route("**/local/giay-to?**", (r) => r.fulfill({ json: [{ ma_gt: 1, ten_gt: "CCCD" }, { ma_gt: 2, ten_gt: "Ảnh thẻ" }] }));
  const rows = [hv("u01", "Nguyễn Thị Hoà"), hv("u02", "Trần Văn Bình")];
  await page.route("**/local/nap/danh-sach", (r) => r.fulfill({ json: rows }));
  await page.route(/\/local\/nap\/nhap(\?.*)?$/, (r) => r.fulfill({ json: [] }));
  await page.route(/\/local\/nap\/nhap\/[^/?]+$/, async (r) => {
    const uuid = decodeURIComponent(new URL(r.request().url()).pathname.split("/").pop() ?? "");
    if (r.request().method() === "PUT") {
      mo.luu.push({ uuid, body: r.request().postDataJSON() });
      return r.fulfill({ json: { ok: true } });
    }
    if (r.request().method() === "DELETE") return r.fulfill({ json: { ok: true } });
    await r.fulfill({ json: { uuid, dia_chi_json: DIA_CHI, chi_tiet: null, noi_cap: null, ngay_cap: null, tick_json: null,
      jp2_b64: null, anh_preview: null, updated_at: null, chon_in_gplx: uuid === "u01" ? (mo.nhapSan ?? null) : null } });
  });
  await page.route("**/local/nap/keo/*/anh", (r) => r.fulfill({ status: 404, body: "" }));
  await page.route("**/local/nap/nap-lo", async (r) => {
    const b = r.request().postDataJSON() as { items: { uuid: string }[] };
    mo.napLo.push(b);
    const it = b.items[0];
    await r.fulfill({ json: { tong: 1, thanh_cong: 1, that_bai: 0, ket_qua: [{ uuid: it.uuid, ok: true, ma_dk: `MD-${it.uuid}`, so_ho_so: "0001" }] } });
  });
}

const ngan = (page: Page) => page.getByRole("complementary", { name: "Ngăn chuẩn bị hồ sơ" });
const o = (page: Page) => ngan(page).locator("#chon-in-gplx");

async function vao(page: Page, hang: string, mo: Mo = { luu: [], napLo: [] }, w = 1280) {
  await giaBackend(page, mo, hang);
  await page.setViewportSize({ width: w, height: 820 });
  await page.goto("/tool/nap");
  await expect(page.getByTestId("hv-u01")).toBeVisible();
  await page.getByTestId("hv-u01").click();
  await expect(ngan(page).getByText("NGUYỄN THỊ HOÀ")).toBeVisible();
  return mo;
}

async function napLoTatCa(page: Page) {
  await page.getByTestId("hv-u02").click(); // mở cả hai để cả hai đủ điều kiện (đã map địa chỉ)
  await expect(ngan(page).getByText("TRẦN VĂN BÌNH")).toBeVisible();
  await page.getByLabel("Chọn tất cả học viên trong danh sách").check();
  await page.getByRole("button", { name: /Nạp 2 học viên vào/ }).click();
  await ngan(page).getByRole("button", { name: "Bắt đầu nạp" }).click();
  await expect(ngan(page).getByTestId("tien-do-nap")).toContainText("2/2 · 100%");
}

const chonCuaUuid = (mo: Mo, uuid: string) => mo.napLo.flatMap((b) => b.items).find((i) => i.uuid === uuid)?.chon_in_gplx;

test.describe("Chọn in GPLX ở màn Nạp — điền sẵn theo hạng khóa", () => {
  test("khóa MÔ TÔ → điền sẵn 'In 01 GPLX không thời hạn' kèm ghi chú khóa mô tô", async ({ page }) => {
    await vao(page, "A1");
    await expect(o(page)).toHaveValue("3");
    await expect(o(page).locator("option:checked")).toHaveText("In 01 GPLX không thời hạn");
    await expect(ngan(page)).toContainText("Khóa mô tô (hạng A1)");
  });

  test("khóa Ô TÔ → điền sẵn 'In 01 GPLX có thời hạn' kèm ghi chú khóa ô tô", async ({ page }) => {
    await vao(page, "B2");
    await expect(o(page)).toHaveValue("2");
    await expect(o(page).locator("option:checked")).toHaveText("In 01 GPLX có thời hạn");
    await expect(ngan(page)).toContainText("Khóa ô tô (hạng B2)");
  });

  test("ô liệt kê đủ 3 lựa chọn có tên tiếng Việt", async ({ page }) => {
    await vao(page, "B2");
    await expect(o(page).locator("option")).toHaveText([
      "In 01 GPLX có thời hạn", "In 01 GPLX không thời hạn", "In 01 GPLX (ghép: có thời hạn + không thời hạn)"]);
  });

  test("nạp lô khóa mô tô khi KHÔNG đổi gì → gửi chon_in_gplx = 3 cho mọi học viên", async ({ page }) => {
    const mo = await vao(page, "A1");
    await napLoTatCa(page);
    expect(chonCuaUuid(mo, "u01")).toBe(3);
    expect(chonCuaUuid(mo, "u02")).toBe(3);
  });

  test("nạp lô khóa ô tô khi KHÔNG đổi gì → gửi chon_in_gplx = 2", async ({ page }) => {
    const mo = await vao(page, "B2");
    await napLoTatCa(page);
    expect(chonCuaUuid(mo, "u01")).toBe(2);
    expect(chonCuaUuid(mo, "u02")).toBe(2);
  });

  test("đổi u01 sang 'ghép' → nháp lưu 1, nạp gửi 1 cho u01, u02 vẫn theo hạng (2)", async ({ page }) => {
    const mo = await vao(page, "B2");
    await o(page).selectOption("1");
    await page.getByTestId("hv-u02").click();
    await expect(ngan(page).getByText("TRẦN VĂN BÌNH")).toBeVisible();
    await expect.poll(() => mo.luu.filter((x) => x.uuid === "u01").length).toBeGreaterThan(0);
    expect(mo.luu.find((x) => x.uuid === "u01")!.body.chon_in_gplx).toBe(1);
    await expect(o(page)).toHaveValue("2"); // học viên khác về mặc định theo hạng, không dính lựa chọn của u01
    await napLoTatCa(page);
    expect(chonCuaUuid(mo, "u01")).toBe(1);
    expect(chonCuaUuid(mo, "u02")).toBe(2);
  });

  test("nháp đã có lựa chọn từ trước (3) được nạp lại vào ô khi mở học viên", async ({ page }) => {
    await vao(page, "B2", { luu: [], napLo: [], nhapSan: 3 });
    await expect(o(page)).toHaveValue("3");
    await expect(o(page).locator("option:checked")).toHaveText("In 01 GPLX không thời hạn");
  });

  test("chưa đổi gì thì nháp lưu null (để luôn theo hạng của khóa)", async ({ page }) => {
    const mo = await vao(page, "A1");
    await page.getByTestId("hv-u02").click();
    await expect(ngan(page).getByText("TRẦN VĂN BÌNH")).toBeVisible();
    await expect.poll(() => mo.luu.filter((x) => x.uuid === "u01").length).toBeGreaterThan(0);
    expect(mo.luu.find((x) => x.uuid === "u01")!.body.chon_in_gplx).toBeNull();
  });

  test("ảnh kiểm ô Chọn in GPLX (mô tô, ô tô) ở 1280 và 1440", async ({ page }) => {
    for (const [hang, w] of [["A1", 1280], ["B2", 1440]] as const) {
      await vao(page, hang, { luu: [], napLo: [] }, w);
      await o(page).scrollIntoViewIfNeeded();
      await page.screenshot({ path: `../../anh-kiem/2026-10-16-in-gplx/${hang}-${w}.png` });
    }
  });
});
