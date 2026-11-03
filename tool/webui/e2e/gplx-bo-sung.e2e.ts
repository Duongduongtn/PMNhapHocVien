import { expect, test, type Page } from "@playwright/test";

// QLY-10, TCB-05 — bổ sung GPLX đã có cho học viên đã nạp. Backend giả bằng page.route; không đụng DB thật.

const COT = ["SoGPLXDaCo", "HangGPLXDaCo", "NgayTTGPLXDaCo", "NgayCapGPLXDaCo", "NgayHHGPLXDaCo", "DonViCapGPLXDaCo"];
const THO_TRONG = Object.fromEntries(COT.map((c) => [c, ""]));
const B2 = { nhom: "cu", hang: "B2", so: "790000000123", ngay_tt: "20120815", ngay_cap: "20180427", ngay_hh: "20280427", don_vi: "70" };
const HV = { ma_dk: "M1", ho_ten: "NGUYỄN VĂN AN", ngay_sinh: "19900501", gioi_tinh: "M", so_cccd: "079200000001", so_cmnd_cu: null, so_ho_so: "001",
  noi_tt: "", hktt: "", noi_ct: "", hkct: "", ngay_cap: null, noi_cap_ma: "", noi_cap_ten: "", co_anh: false, duong_dan_anh: null, ma_loai_hs: 2 };
const gplxDoc = (o: Record<string, unknown> = {}) => ({ ma_dk: "M1", ho_ten: HV.ho_ten, ma_kh: "K1", hang_khoa: "C1", chan: null, gplx: [], lech: false, tho: THO_TRONG, ...o });

interface Mo { luu: { gplx: Record<string, string>[]; tho: Record<string, string> }[] }

async function chung(page: Page, tienTo: string, doc: Record<string, unknown>, mo: Mo, ketLuu?: { status: number; detail: string }) {
  await page.addInitScript(() => localStorage.setItem("tool_session_token", "tok-test"));
  await page.route("**/local/auth/me", (r) => r.fulfill({ json: { username: "thu1", ho_ten: "Nhân viên thử", vai_tro: "operator" } }));
  await page.route("**/local/config/moi-truong", (r) => r.fulfill({ json: { thu_muc_ghi_duoc: true, duong_dan: "x", da_cau_hinh: true } }));
  await page.route("**/version", (r) => r.fulfill({ json: { build: "dev", commit: "x" } }));
  await page.route(/noi-cap-gplx/, (r) => r.fulfill({ json: [{ ma: "70", ten: "70 — Bình Phước" }] }));
  await page.route(new RegExp(`${tienTo}/gplx\\?`), async (r) => {
    if (r.request().method() === "PUT") {
      mo.luu.push(r.request().postDataJSON());
      if (ketLuu) return r.fulfill({ status: ketLuu.status, json: { detail: ketLuu.detail } });
      return r.fulfill({ json: { ok: true, ma_dk: "M1" } });
    }
    await r.fulfill({ json: doc });
  });
}

async function vaoNap(page: Page, doc: Record<string, unknown>, mo: Mo, opts: { bc1?: boolean; ketLuu?: { status: number; detail: string }; w?: number } = {}) {
  await chung(page, "/local/ho-so", doc, mo, opts.ketLuu);
  await page.route("**/local/khoa-hoc/tra-cuu?**", (r) => r.fulfill({ json: [{ ma_kh: "K1", ten_kh: "Khóa C1", hang_gplx: "C1", hang_dt: "C1", bc1: !!opts.bc1 }] }));
  await page.route(/\/local\/ho-so\?makh=/, (r) => r.fulfill({ json: [HV] }));
  await page.setViewportSize({ width: opts.w ?? 1280, height: 900 });
  await page.goto("/tool/tra-cuu");
  await page.getByPlaceholder("VD: B-K149 hoặc 70004K26B010").fill("C1");
  await page.keyboard.press("Enter");
  await page.getByRole("button", { name: /Khóa C1/ }).click();
  await page.getByRole("cell", { name: HV.ho_ten }).click();
  await page.getByRole("button", { name: "GPLX đã có", exact: true }).click();
}

const hop = (page: Page) => page.getByRole("dialog", { name: "GPLX đã có" });

const oNgay = (page: Page, nhan: string) =>
  hop(page).getByText(nhan, { exact: true }).locator('xpath=following-sibling::div//input[@inputmode="numeric"]').first();

async function nhapB2(page: Page) {
  await hop(page).getByLabel("Học viên đã có GPLX").check();
  const o = hop(page).getByPlaceholder("Gõ hạng, ví dụ B2");
  await o.click();
  await o.fill("B2");
  await hop(page).getByRole("button", { name: "B2 — luật cũ", exact: true }).click();
  await hop(page).getByLabel("Số GPLX").fill("790000000123");
  await oNgay(page, "Ngày trúng tuyển").fill("15/08/2012");
  await oNgay(page, "Ngày cấp").fill("27/04/2018");
}

test.describe("QLY-10 — Tra cứu DB", () => {
  test("nhập tay rồi lưu: gửi đúng bằng và chuỗi thô, báo đã lưu", async ({ page }) => {
    const mo: Mo = { luu: [] };
    await vaoNap(page, gplxDoc(), mo);
    await expect(hop(page).getByText("Chưa có GPLX")).toBeVisible();
    await nhapB2(page);
    await hop(page).getByRole("button", { name: "Lưu vào DB Nạp" }).click();
    await expect(page.getByText("Đã lưu GPLX đã có vào DB Nạp.")).toBeVisible();
    expect(mo.luu).toHaveLength(1);
    expect(mo.luu[0].gplx[0]).toMatchObject({ hang: "B2", so: "790000000123", ngay_tt: "20120815", ngay_cap: "20180427" });
    expect(mo.luu[0].tho).toEqual(THO_TRONG);
  });

  test("đóng hộp thì không ghi gì", async ({ page }) => {
    const mo: Mo = { luu: [] };
    await vaoNap(page, gplxDoc(), mo);
    await nhapB2(page);
    await hop(page).getByRole("button", { name: "Đóng", exact: true }).last().click();
    await expect(hop(page)).toBeHidden();
    expect(mo.luu).toHaveLength(0);
  });

  test("thiếu dữ liệu thì nút Lưu khóa", async ({ page }) => {
    await vaoNap(page, gplxDoc(), { luu: [] });
    await hop(page).getByLabel("Học viên đã có GPLX").check();
    await expect(hop(page).getByRole("button", { name: "Lưu vào DB Nạp" })).toBeDisabled();
  });

  test("trùng hạng đăng ký của khóa thì chặn", async ({ page }) => {
    await vaoNap(page, gplxDoc({ hang_khoa: "B2" }), { luu: [] });
    await nhapB2(page);
    await expect(hop(page).getByText("sửa lại mới lưu được")).toBeVisible();
    await expect(hop(page).getByRole("button", { name: "Lưu vào DB Nạp" })).toBeDisabled();
  });

  test("bản DB hiện đủ, xóa hết phải xác nhận", async ({ page }) => {
    const mo: Mo = { luu: [] };
    const tho = { ...THO_TRONG, SoGPLXDaCo: "790000000123", HangGPLXDaCo: "B2" };
    await vaoNap(page, gplxDoc({ gplx: [B2], tho }), mo);
    await expect(hop(page).getByText("B2 · 790000000123")).toBeVisible();
    await hop(page).getByLabel("Học viên đã có GPLX").uncheck();
    await hop(page).getByRole("button", { name: "Lưu vào DB Nạp" }).click();
    expect(mo.luu).toHaveLength(0);
    await hop(page).getByRole("button", { name: "Xác nhận xóa" }).click();
    await expect(hop(page)).toBeHidden();
    expect(mo.luu[0]).toMatchObject({ gplx: [], tho });
  });

  test("khóa đã lập Báo cáo 1: chỉ xem, không có nút lưu", async ({ page }) => {
    await vaoNap(page, gplxDoc({ gplx: [B2], chan: "Khóa đã lập Báo cáo 1 — không lưu được ở đây. Cần sửa thì dùng phần mềm cũ." }), { luu: [] }, { bc1: true });
    await expect(hop(page).getByText(/Khóa đã lập Báo cáo 1/)).toBeVisible();
    await expect(hop(page).getByRole("button", { name: "Lưu vào DB Nạp" })).toHaveCount(0);
    await expect(hop(page).getByLabel("Học viên đã có GPLX")).toHaveCount(0);
  });

  test("dữ liệu vừa đổi: báo lỗi, có nút tải lại, không đóng hộp", async ({ page }) => {
    await vaoNap(page, gplxDoc(), { luu: [] }, { ketLuu: { status: 409, detail: "Dữ liệu GPLX vừa đổi — tải lại rồi thử lại." } });
    await nhapB2(page);
    await hop(page).getByRole("button", { name: "Lưu vào DB Nạp" }).click();
    await expect(hop(page).getByRole("alert")).toContainText("vừa đổi");
    await expect(hop(page).getByRole("button", { name: "Tải lại" })).toBeVisible();
  });

  test("dữ liệu cũ lệch số phần: cảnh báo vàng", async ({ page }) => {
    await vaoNap(page, gplxDoc({ gplx: [B2], lech: true }), { luu: [] });
    await expect(hop(page).getByText(/số phần không khớp/)).toBeVisible();
  });

  test("khổ 375: không tràn ngang", async ({ page }) => {
    await vaoNap(page, gplxDoc({ gplx: [B2] }), { luu: [] }, { w: 375 });
    const tran = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(tran).toBeLessThanOrEqual(0);
  });
});

test.describe("TCB-05 — Tra cứu CDB", () => {
  async function vaoDich(page: Page, khoa: { dkkh?: boolean; bc1?: boolean }, mo: Mo) {
    await chung(page, "/local/sync/tra-cuu", gplxDoc(), mo);
    await page.route("**/local/sync/targets", (r) => r.fulfill({ json: { targets: [{ key: "t1", name: "DB đích thử" }], selected: "t1", options: {}, tt_xuly_options: [] } }));
    await page.route("**/local/sync/tra-cuu/khoa?**", (r) => r.fulfill({ json: [{ ma_kh: "K1", ten_kh: "Khóa C1", hang_gplx: "C1", hang_dt: "C1", bc1: !!khoa.bc1, dkkh: !!khoa.dkkh }] }));
    await page.route("**/local/sync/tra-cuu/ho-so?**", (r) => r.fulfill({ json: [HV] }));
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto("/sync/tra-cuu");
    await page.getByPlaceholder("VD: B-K149 hoặc 75032K26B010").fill("C1");
    await page.keyboard.press("Enter");
    await page.getByRole("button", { name: /Khóa C1/ }).click();
    await page.getByRole("cell", { name: HV.ho_ten }).click();
  }

  test("lưu vào DB đích, gửi kèm DB đang chọn", async ({ page }) => {
    const mo: Mo = { luu: [] };
    const urls: string[] = [];
    page.on("request", (r) => { if (r.method() === "PUT") urls.push(r.url()); });
    await vaoDich(page, {}, mo);
    await page.getByRole("button", { name: "GPLX đã có", exact: true }).click();
    await nhapB2(page);
    await hop(page).getByRole("button", { name: "Lưu vào DB đích" }).click();
    await expect(page.getByText("Đã lưu GPLX đã có vào DB đích.")).toBeVisible();
    expect(mo.luu).toHaveLength(1);
    expect(urls[0]).toContain("target_key=t1");
  });

  for (const [ten, khoa, chu] of [["DKKH", { dkkh: true }, "kết xuất DKKH"], ["Báo cáo 1", { bc1: true }, "lập Báo cáo 1"]] as const) {
    test(`khóa đã ${ten}: nút khóa, ghi rõ lý do`, async ({ page }) => {
      await vaoDich(page, khoa, { luu: [] });
      await expect(page.getByRole("button", { name: "GPLX đã có", exact: true })).toBeDisabled();
      await expect(page.getByText(new RegExp(`Khóa đã ${chu}: GPLX đã có không lưu được`))).toBeVisible();
    });
  }
});

test.describe("QLY-10 — cảnh báo bản app web", () => {
  const CB = (o: Record<string, unknown> = {}) => ({ uuid: "u1", dau_van: "dv1", ma_dk: "M1", nguoi_gui: "Thu nhận 1", updated_at: "2026-11-03T02:15:00+00:00",
    ho_ten: HV.ho_ten, ma_kh: "K1", ten_kh: "Khóa C1", hang_db: [], hang_web: [{ hang: "B2", nhom: "cu" }], khong_thay: false, ...o });
  type MoBq = Mo & { boQua: unknown[] };
  const moMoi = (): MoBq => ({ luu: [], boQua: [] });

  async function vao(page: Page, mo: MoBq, items: unknown[], opts: { kiemDuoc?: boolean } = {}) {
    let conLai = items;
    await chung(page, "/local/ho-so", gplxDoc(), mo);
    await page.route("**/local/ho-so/gplx-bo-sung", (r) => r.fulfill({ json: { kiem_duoc: opts.kiemDuoc ?? true, items: conLai } }));
    await page.route(/gplx-ban-web/, (r) => r.fulfill({ json: { uuid: "u1", dau_van: "dv1", gplx: [B2], nguoi_gui: "Thu nhận 1", updated_at: "2026-11-03T02:15:00+00:00" } }));
    await page.route("**/local/ho-so/gplx/bo-qua", (r) => { mo.boQua.push(r.request().postDataJSON()); conLai = []; return r.fulfill({ json: { ok: true } }); });
    await page.route("**/local/khoa-hoc/tra-cuu?**", (r) => r.fulfill({ json: [{ ma_kh: "K1", ten_kh: "Khóa C1", hang_gplx: "C1", hang_dt: "C1", bc1: false }] }));
    await page.route(/\/local\/ho-so\?makh=/, (r) => r.fulfill({ json: [HV, { ...HV, ma_dk: "M2", ho_ten: "TRẦN VĂN BÌNH" }] }));
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto("/tool/tra-cuu");
  }
  const canhBao = (page: Page) => page.getByRole("button", { name: /hồ sơ có GPLX bổ sung từ app web/ });

  test("báo số hồ sơ, danh sách không hiện số GPLX, tự điền bản app web, lưu kèm bản đó", async ({ page }) => {
    const mo = moMoi();
    await vao(page, mo, [CB()]);
    await expect(canhBao(page)).toContainText("1 hồ sơ");
    await canhBao(page).click();
    const dong = page.getByRole("row", { name: /NGUYỄN VĂN AN/ });
    await expect(dong).toContainText("Khóa C1");
    await expect(dong).toContainText("B2");
    await expect(dong).toContainText("Thu nhận 1");
    await expect(page.locator("body")).not.toContainText("790000000123");
    await dong.getByRole("button", { name: "Xem và duyệt" }).click();
    await expect(hop(page).getByLabel("Số GPLX")).toHaveValue("790000000123");
    await expect(hop(page).getByText("Chưa có GPLX")).toBeVisible();
    expect(mo.luu).toHaveLength(0);
    await hop(page).getByLabel("Số GPLX").fill("790000000999");
    await hop(page).getByRole("button", { name: "Lưu vào DB Nạp" }).click();
    await expect(hop(page)).toBeHidden();
    expect(mo.luu[0].gplx[0].so).toBe("790000000999");
    expect((mo.luu[0] as unknown as { ban_web: unknown }).ban_web).toMatchObject({ uuid: "u1", dau_van: "dv1" });
  });

  test("Bỏ qua: không ghi DB, hết cảnh báo", async ({ page }) => {
    const mo = moMoi();
    await vao(page, mo, [CB()]);
    await canhBao(page).click();
    await page.getByRole("button", { name: "Xem và duyệt" }).click();
    await hop(page).getByRole("button", { name: "Bỏ qua bản này" }).click();
    await expect(hop(page)).toBeHidden();
    await expect(canhBao(page)).toHaveCount(0);
    expect(mo.boQua).toEqual([{ uuid: "u1", dau_van: "dv1" }]);
    expect(mo.luu).toHaveLength(0);
  });

  test("chip + bộ lọc trong lưới khóa", async ({ page }) => {
    await vao(page, moMoi(), [CB()]);
    await page.getByPlaceholder("VD: B-K149 hoặc 70004K26B010").fill("C1");
    await page.keyboard.press("Enter");
    await page.getByRole("button", { name: /Khóa C1/ }).click();
    await expect(page.getByText("App web: B2")).toBeVisible();
    await expect(page.getByRole("cell", { name: /TRẦN VĂN BÌNH/ })).toBeVisible();
    await page.getByLabel("Có GPLX từ app web chưa duyệt").check();
    await expect(page.getByRole("cell", { name: /TRẦN VĂN BÌNH/ })).toHaveCount(0);
    await expect(page.getByRole("cell", { name: /NGUYỄN VĂN AN/ })).toBeVisible();
  });

  test("không tìm thấy trong DB Nạp: không tính vào số, chỉ cho Bỏ qua", async ({ page }) => {
    await vao(page, moMoi(), [CB(), CB({ uuid: "u2", ma_dk: "M9", ho_ten: null, khong_thay: true })]);
    await expect(canhBao(page)).toContainText("1 hồ sơ");
    await canhBao(page).click();
    const dong = page.getByRole("row", { name: /Mã M9/ });
    await expect(dong).toContainText("Không tìm thấy trong DB Nạp");
    await expect(dong.getByRole("button", { name: "Bỏ qua" })).toBeVisible();
    await expect(dong.getByRole("button", { name: "Xem và duyệt" })).toHaveCount(0);
  });

  test("bản app web vừa hết: vẫn mở bản DB để nhập tay", async ({ page }) => {
    await vao(page, moMoi(), [CB()]);
    await page.route(/gplx-ban-web/, (r) => r.fulfill({ status: 404, json: { detail: "Không còn bản bổ sung" } }));
    await canhBao(page).click();
    await page.getByRole("button", { name: "Xem và duyệt" }).click();
    await expect(hop(page).getByText(/Không lấy được bản bổ sung/)).toBeVisible();
    await expect(hop(page).getByLabel("Học viên đã có GPLX")).toBeVisible();
  });

  test("VPS lỗi: báo chưa kiểm được, không báo 0 hồ sơ", async ({ page }) => {
    await vao(page, moMoi(), [], { kiemDuoc: false });
    await expect(page.getByText("Chưa kiểm được GPLX từ app web")).toBeVisible();
    await expect(canhBao(page)).toHaveCount(0);
  });
});
