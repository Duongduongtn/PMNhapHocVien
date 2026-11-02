import { expect, test, type Page } from "@playwright/test";

// NAP-07 — "GPLX đã có" ở ngăn Chuẩn bị: thu gọn, nhiều bằng, ô gõ tìm, chip + lọc, tự điền từ VPS, cờ "App web có bản mới".
// Backend giả bằng page.route; không đụng DB thật.

interface Mo {
  luu: { uuid: string; body: Record<string, unknown> }[];
  napLo: { items: Record<string, unknown>[] }[];
  nhapSan?: { gplx_da_co_json: string; gplx_goc_json: string | null };
}

const B2 = { nhom: "cu", hang: "B2", so: "790000000123", ngay_tt: "20120815", ngay_cap: "20180427", ngay_hh: "20280427", don_vi: "70" };
const hv = (uuid: string, ten: string, ex: Record<string, unknown> = {}) => ({
  uuid, so_cccd: `0792000000${uuid.slice(-2)}`, so_cmnd_cu: null, ho_ten: ten, ngay_sinh: "19900501", gioi_tinh: "F",
  noi_tt_raw: "Số 5, Hà Nội", ngay_cap: "20200101", noi_cap_cccd: "", co_anh: 1, created_at: null,
  trang_thai: "cho", loi: null, ma_dk: null, so_ho_so: null, gplx_da_co_json: null, ...ex,
});
const DIA_CHI = JSON.stringify({ ma_dvhc: "01001", ma_dvql: "01", ten_xa: "Phường Ba Đình", ten_tinh: "Hà Nội" });

async function vao(page: Page, mo: Mo, opts: { hang?: string; hv01?: Record<string, unknown>; w?: number } = {}) {
  const hang = opts.hang ?? "A1m";
  await page.addInitScript(() => localStorage.setItem("tool_session_token", "tok-test"));
  await page.route("**/local/auth/me", (r) => r.fulfill({ json: { username: "thu1", ho_ten: "Nhân viên thử", vai_tro: "operator" } }));
  await page.route("**/local/config/moi-truong", (r) => r.fulfill({ json: { thu_muc_ghi_duoc: true, duong_dan: "x", da_cau_hinh: true } }));
  await page.route("**/version", (r) => r.fulfill({ json: { build: "dev", commit: "x" } }));
  await page.route("**/local/khoa-hoc?**", (r) => r.fulfill({ json: [{ ma_kh: "K001", ten_kh: "Khóa thử", hang_gplx: hang, hang_dt: hang, ma_so_gtvt: "01", ma_loai_hs: hang.startsWith("A") ? 1 : 2 }] }));
  await page.route("**/local/dvhc/so-gtvt", (r) => r.fulfill({ json: [] }));
  await page.route("**/local/dvhc/noi-cap-gplx", (r) => r.fulfill({ json: [
    { ma: "00", ten: "00 — Tổng cục đường bộ Việt Nam" }, { ma: "70", ten: "70 — Bình Phước" }, { ma: "79", ten: "79 — Hồ Chí Minh" },
  ] }));
  await page.route("**/local/giay-to?**", (r) => r.fulfill({ json: [{ ma_gt: 1, ten_gt: "CCCD" }] }));
  await page.route("**/local/nap/danh-sach", (r) => r.fulfill({ json: [hv("u01", "Nguyễn Thị Hoà", opts.hv01), hv("u02", "Trần Văn Bình")] }));
  await page.route(/\/local\/nap\/nhap(\?.*)?$/, (r) => r.fulfill({ json: [] }));
  await page.route(/\/local\/nap\/nhap\/[^/?]+$/, async (r) => {
    const uuid = decodeURIComponent(new URL(r.request().url()).pathname.split("/").pop() ?? "");
    if (r.request().method() === "PUT") { mo.luu.push({ uuid, body: r.request().postDataJSON() }); return r.fulfill({ json: { ok: true } }); }
    if (r.request().method() === "DELETE") return r.fulfill({ json: { ok: true } });
    await r.fulfill({ json: { uuid, dia_chi_json: DIA_CHI, chi_tiet: null, noi_cap: null, ngay_cap: null, tick_json: null, jp2_b64: null,
      anh_preview: null, updated_at: null, chon_in_gplx: null, gplx_da_co_json: null, gplx_goc_json: null, ...(uuid === "u01" ? mo.nhapSan : {}) } });
  });
  await page.route("**/local/nap/keo/*/anh", (r) => r.fulfill({ status: 404, body: "" }));
  await page.route("**/local/nap/nap-lo", async (r) => {
    const b = r.request().postDataJSON() as { items: { uuid: string }[] };
    mo.napLo.push(b);
    await r.fulfill({ json: { tong: 1, thanh_cong: 1, that_bai: 0, ket_qua: [{ uuid: b.items[0].uuid, ok: true, ma_dk: "M", so_ho_so: "0001" }] } });
  });
  await page.setViewportSize({ width: opts.w ?? 1280, height: 900 });
  await page.goto("/tool/nap");
  if (opts.hv01?.trang_thai === "xong") return;
  await page.getByTestId("hv-u01").click();
  await expect(ngan(page).getByText("NGUYỄN THỊ HOÀ")).toBeVisible();
}

const ngan = (page: Page) => page.getByRole("complementary", { name: "Ngăn chuẩn bị hồ sơ" });
const tich = (page: Page) => ngan(page).getByLabel("Học viên đã có GPLX");

async function chonHang(page: Page, thuTu: number, go: string, ten: string) {
  const o = ngan(page).getByPlaceholder("Gõ hạng, ví dụ B2").nth(thuTu);
  await o.click();
  await o.fill(go);
  await ngan(page).getByRole("button", { name: ten, exact: true }).click();
}

async function napHaiHocVien(page: Page) {
  await page.getByTestId("hv-u02").click();
  await expect(ngan(page).getByText("TRẦN VĂN BÌNH")).toBeVisible();
  await page.getByLabel("Chọn tất cả học viên trong danh sách").check();
  await page.getByRole("button", { name: /Nạp 2 học viên vào/ }).click();
  await ngan(page).getByRole("button", { name: "Bắt đầu nạp" }).click();
  await expect(ngan(page).getByTestId("tien-do-nap")).toContainText("2/2 · 100%");
}

const moi = (): Mo => ({ luu: [], napLo: [] });

test.describe("NAP-07 — GPLX đã có ở màn Nạp", () => {
  test("mặc định thu gọn; tích vào mở đủ ô; bỏ tích thu lại", async ({ page }) => {
    await vao(page, moi());
    await expect(tich(page)).not.toBeChecked();
    await expect(ngan(page).getByPlaceholder("Gõ hạng, ví dụ B2")).toHaveCount(0);
    await tich(page).check();
    await expect(ngan(page).getByText("Bằng 1")).toBeVisible();
    await expect(ngan(page).getByPlaceholder("Gõ mã hoặc tên tỉnh")).toBeVisible();
    await tich(page).uncheck();
    await expect(ngan(page).getByText("Bằng 1")).toHaveCount(0);
  });

  test("ô Hạng gõ tìm không cần dấu, phân biệt hai nhóm luật; bằng mô tô ẩn ô Hết hạn", async ({ page }) => {
    await vao(page, moi());
    await tich(page).check();
    const o = ngan(page).getByPlaceholder("Gõ hạng, ví dụ B2");
    await o.click();
    await o.fill("a1");
    await expect(ngan(page).getByRole("button", { name: "A1 — luật mới", exact: true })).toBeVisible();
    await expect(ngan(page).getByRole("button", { name: "A1 — luật cũ", exact: true })).toBeVisible();
    await ngan(page).getByRole("button", { name: "A1 — luật mới", exact: true }).click();
    await expect(o).toHaveValue("A1 — luật mới");
    await expect(ngan(page).getByText("Ngày hết hạn")).toHaveCount(0);
    await chonHang(page, 0, "b2", "B2 — luật cũ");
    await expect(ngan(page).getByText("Ngày hết hạn")).toBeVisible();
  });

  test("ô Nơi cấp tìm theo mã và tên không dấu; ô ngày tự chèn dấu /", async ({ page }) => {
    await vao(page, moi());
    await tich(page).check();
    const nc = ngan(page).getByPlaceholder("Gõ mã hoặc tên tỉnh");
    await nc.click();
    await nc.fill("binh phuoc");
    await expect(ngan(page).getByRole("button", { name: "70 — Bình Phước" })).toBeVisible();
    await nc.fill("79");
    await nc.press("Enter");
    await expect(nc).toHaveValue("79 — Hồ Chí Minh");
    const ngay = ngan(page).getByText("Ngày cấp", { exact: true }).locator("xpath=following-sibling::div//input[@inputmode='numeric']");
    await ngay.pressSequentially("27042018");
    await expect(ngay).toHaveValue("27/04/2018");
  });

  test("BUG-19: Enter ở ô Hạng, Nơi cấp không chọn sai", async ({ page }) => {
    await vao(page, moi());
    await tich(page).check();
    const hang = ngan(page).getByPlaceholder("Gõ hạng, ví dụ B2");
    const nc = ngan(page).getByPlaceholder("Gõ mã hoặc tên tỉnh");
    const go = async (o: typeof hang, q: string) => {
      await o.click();
      await o.fill(q);
      await o.press("Enter");
    };
    await go(hang, "B1");
    await expect(hang).toHaveValue("B1 — luật cũ");
    await go(hang, "A");
    await expect(hang).toHaveValue("A — luật mới");
    // Có ở cả hai luật: danh sách vẫn mở, ô giữ chữ đang gõ để tự chọn.
    await go(hang, "C");
    await expect(hang).toHaveValue("C");
    await expect(ngan(page).getByRole("button", { name: "C — luật cũ", exact: true })).toBeVisible();
    await ngan(page).getByRole("button", { name: "C — luật cũ", exact: true }).click();
    await expect(hang).toHaveValue("C — luật cũ");
    await go(nc, "79");
    await expect(nc).toHaveValue("79 — Hồ Chí Minh");
    await go(nc, "Ha");
    await expect(nc).toHaveValue("Ha");
  });

  test("BUG-19: Enter ở ô Tỉnh, Xã không chọn nhầm", async ({ page }) => {
    await page.route("**/local/dvhc/tinh", (r) => r.fulfill({ json: [
      { ma_dvql: "01", ten_tinh: "Thành phố Hà Nội" }, { ma_dvql: "42", ten_tinh: "Tỉnh Hà Tĩnh" },
    ] }));
    await page.route("**/local/dvhc/xa?**", (r) => r.fulfill({ json: [
      { ma_dvhc: "X1", ten_xa: "Phường Tân Định", ma_dvql: "01" }, { ma_dvhc: "X2", ten_xa: "Phường Tân Bình", ma_dvql: "01" },
    ] }));
    await vao(page, moi());
    await ngan(page).getByRole("button", { name: "Chọn tay" }).click();
    const tinh = ngan(page).getByPlaceholder("Gõ tên tỉnh/TP…");
    await tinh.click();
    await tinh.fill("Ha");
    await tinh.press("Enter");
    await expect(tinh).toHaveValue("Ha");
    await tinh.fill("Hà Nội");
    await tinh.press("Enter");
    await expect(tinh).toHaveValue("Thành phố Hà Nội");
    const xa = ngan(page).getByPlaceholder("Gõ tên phường/xã…");
    await xa.click();
    await xa.fill("Tân");
    await xa.press("Enter");
    await expect(xa).toHaveValue("Tân");
    await xa.fill("Tân Bình");
    await xa.press("Enter");
    await expect(xa).toHaveValue("Phường Tân Bình");
  });

  test("nhập 2 bằng: chip, báo miễn lý thuyết, nháp lưu, nạp lô gửi ngày yyyymmdd; học viên khác không có bằng", async ({ page }) => {
    const mo = moi();
    await vao(page, mo);
    await tich(page).check();
    await chonHang(page, 0, "b2", "B2 — luật cũ");
    await ngan(page).locator("#gplx-so-0").fill("790000000123");
    await ngan(page).getByText("Ngày cấp", { exact: true }).first().locator("xpath=following-sibling::div//input[@inputmode='numeric']").pressSequentially("27042018");
    await ngan(page).getByRole("button", { name: "+ Thêm GPLX" }).click();
    await chonHang(page, 1, "a1", "A1 — luật mới");
    await ngan(page).locator("#gplx-so-1").fill("790000000456");
    await expect(ngan(page).getByText("miễn thi lý thuyết")).toBeVisible();
    await expect(ngan(page).getByText("trùng hạng đăng ký")).toBeVisible();      // A1 mới trùng khóa A1m
    await expect(page.getByTestId("chip-gplx-u01")).toHaveText("GPLX: B2, A1");
    await napHaiHocVien(page);
    const luu = mo.luu.find((x) => x.uuid === "u01")!;
    const nhapJson = JSON.parse(luu.body.gplx_da_co_json as string);
    expect(nhapJson.map((b: { hang: string }) => b.hang)).toEqual(["B2", "A1m"]);
    const u1 = mo.napLo.flatMap((b) => b.items).find((i) => i.uuid === "u01")!;
    const ds = u1.gplx_da_co as { hang: string; ngay_cap: string; nhom: string }[];
    expect(ds.map((b) => [b.nhom, b.hang])).toEqual([["cu", "B2"], ["moi", "A1m"]]);
    expect(ds[0].ngay_cap).toBe("20180427");
    expect(mo.napLo.flatMap((b) => b.items).find((i) => i.uuid === "u02")!.gplx_da_co).toEqual([]);
  });

  test("số GPLX sai độ dài chỉ nhắc; thiếu hạng báo lỗi ngay trên khối", async ({ page }) => {
    await vao(page, moi());
    await tich(page).check();
    await expect(ngan(page).getByText("Chưa chọn hạng")).toBeVisible();
    await ngan(page).locator("#gplx-so-0").fill("7900");
    await expect(ngan(page).getByText("thường có 12 chữ số")).toBeVisible();
  });

  test("lọc 'Có GPLX đã có': đếm đúng, chỉ hiện học viên có bằng", async ({ page }) => {
    await vao(page, moi(), { hv01: { gplx_da_co_json: JSON.stringify([B2]) } });
    const loc = page.getByTestId("loc-gplx");
    await expect(loc).toContainText("(1)");
    await loc.click();
    await expect(page.getByTestId("hv-u01")).toBeVisible();
    await expect(page.getByTestId("hv-u02")).toHaveCount(0);
    await loc.click();
    await expect(page.getByTestId("hv-u02")).toBeVisible();
  });

  test("đang lọc: Chọn tất cả và nạp lô chỉ tính học viên đang hiện", async ({ page }) => {
    const mo = moi();
    await vao(page, mo, { hv01: { gplx_da_co_json: JSON.stringify([B2]) } });
    await page.getByTestId("hv-u02").click();
    await expect(ngan(page).getByText("TRẦN VĂN BÌNH")).toBeVisible();
    await page.getByTestId("hv-u01").click();
    await expect(ngan(page).getByText("NGUYỄN THỊ HOÀ")).toBeVisible();
    await page.getByTestId("loc-gplx").click();
    await page.getByLabel("Chọn tất cả học viên trong danh sách").check();
    await expect(page.getByTestId("dem-chon")).toContainText("Chọn 1/1");
    await page.getByRole("button", { name: /Nạp 1 học viên vào/ }).click();
    await ngan(page).getByRole("button", { name: "Bắt đầu nạp" }).click();
    await expect(ngan(page).getByTestId("tien-do-nap")).toContainText("1/1 · 100%");
    expect(mo.napLo.flatMap((b) => b.items).map((i) => i.uuid)).toEqual(["u01"]);
  });

  test("tab Đã nạp vẫn có chip và bộ lọc", async ({ page }) => {
    await vao(page, moi(), { hv01: { trang_thai: "xong", ma_dk: "M", so_ho_so: "0001", gplx_da_co_json: JSON.stringify([B2]) } });
    await page.getByRole("button", { name: /Đã nạp/ }).first().click();
    await expect(page.getByTestId("chip-gplx-u01")).toHaveText("GPLX: B2");
    await expect(page.getByTestId("loc-gplx")).toContainText("(1)");
  });

  test("hồ sơ từ app web: tự điền, ghi chú nguồn; sửa thì ghi kèm bản gốc", async ({ page }) => {
    const mo = moi();
    const goc = JSON.stringify([B2]);
    await vao(page, mo, { hv01: { gplx_da_co_json: goc } });
    await expect(tich(page)).toBeChecked();
    await expect(ngan(page).getByText("Từ app web")).toBeVisible();
    await expect(ngan(page).locator("#gplx-so-0")).toHaveValue("790000000123");
    await ngan(page).locator("#gplx-so-0").fill("790000000999");
    await expect(ngan(page).getByText("Từ app web")).toHaveCount(0);
    await page.getByTestId("hv-u02").click();
    await expect.poll(() => mo.luu.filter((x) => x.uuid === "u01").length).toBeGreaterThan(0);
    const b = mo.luu.find((x) => x.uuid === "u01")!.body;
    expect(JSON.parse(b.gplx_da_co_json as string)[0].so).toBe("790000000999");
    expect(b.gplx_goc_json).toBe(goc);
  });

  test("nhân viên đã xóa hết bằng từ app web: giữ không có bằng, nạp gửi rỗng", async ({ page }) => {
    const mo = moi();
    await vao(page, mo, { hv01: { gplx_da_co_json: JSON.stringify([B2]) } });
    await tich(page).uncheck();
    await expect(page.getByTestId("chip-gplx-u01")).toHaveCount(0);
    await napHaiHocVien(page);
    expect(mo.napLo.flatMap((b) => b.items).find((i) => i.uuid === "u01")!.gplx_da_co).toEqual([]);
    expect(mo.luu.find((x) => x.uuid === "u01")!.body.gplx_da_co_json).toBe("[]");
  });

  test("app web đổi sau khi nhân viên sửa: hiện cờ, bấm 'Dùng bản app web' lấy bản mới", async ({ page }) => {
    const banMoi = JSON.stringify([{ ...B2, so: "790000000777" }]);
    const mo: Mo = { ...moi(), nhapSan: { gplx_da_co_json: JSON.stringify([{ ...B2, so: "790000000999" }]), gplx_goc_json: JSON.stringify([B2]) } };
    await vao(page, mo, { hv01: { gplx_da_co_json: banMoi } });
    await expect(ngan(page).getByText("App web có bản mới")).toBeVisible();
    await expect(ngan(page).locator("#gplx-so-0")).toHaveValue("790000000999");
    await ngan(page).getByRole("button", { name: "Dùng bản app web" }).click();
    await expect(ngan(page).getByText("App web có bản mới")).toHaveCount(0);
    await expect(ngan(page).locator("#gplx-so-0")).toHaveValue("790000000777");
  });

  test("app web không đổi: không hiện cờ dù nhân viên đã sửa", async ({ page }) => {
    const goc = JSON.stringify([B2]);
    const mo: Mo = { ...moi(), nhapSan: { gplx_da_co_json: JSON.stringify([{ ...B2, so: "790000000999" }]), gplx_goc_json: goc } };
    await vao(page, mo, { hv01: { gplx_da_co_json: goc } });
    await expect(ngan(page).locator("#gplx-so-0")).toHaveValue("790000000999");
    await expect(ngan(page).getByText("App web có bản mới")).toHaveCount(0);
  });

  test("dòng danh sách vẫn gọn một dòng khi có chip", async ({ page }) => {
    await vao(page, moi(), { hv01: { gplx_da_co_json: JSON.stringify([B2, { ...B2, hang: "C" }, { ...B2, hang: "D" }]) } });
    const dong = await page.getByTestId("hv-u01").boundingBox();
    expect(dong?.height).toBeLessThanOrEqual(55);
    const tran = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(tran).toBe(false);
  });

  test("ảnh kiểm khối GPLX đã có", async ({ page }) => {
    await vao(page, moi(), { hv01: { gplx_da_co_json: JSON.stringify([B2, { ...B2, nhom: "moi", hang: "A1m", ngay_hh: "" }]) } });
    for (const w of [1280, 1440]) {
      await page.setViewportSize({ width: w, height: 900 });
      await tich(page).scrollIntoViewIfNeeded();
      await page.screenshot({ path: `../../anh-kiem/2026-11-02-NAP-07/${w}.png` });
    }
  });
});
