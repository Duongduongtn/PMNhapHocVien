import { expect, test, type Page } from "@playwright/test";

// NAP-01 — màn Nạp hồ sơ chia đôi: danh sách gọn (trái) + ngăn Chuẩn bị luôn mở (phải) + nạp lô có danh sách & tiến độ.
// Backend giả bằng page.route; không đụng DB thật.

interface Mo {
  rows: Record<string, unknown>[];
  luu: { uuid: string; body: Record<string, unknown> }[];
  napLo: Record<string, unknown>[];
  xoaNhap: string[];
  napLoiUuid?: string;
}

const KHOA = [{ ma_kh: "K001", ten_kh: "Khóa B2-01/2026", hang_gplx: "B2", hang_dt: "B2", ma_so_gtvt: "01", ma_loai_hs: 2 }];
const hv = (uuid: string, ten: string, ex: Record<string, unknown> = {}) => ({
  uuid, so_cccd: `0792000000${uuid.slice(-2)}`, so_cmnd_cu: null, ho_ten: ten, ngay_sinh: "19900501", gioi_tinh: "F",
  noi_tt_raw: "Số 5, Hà Nội", ngay_cap: "20200101", noi_cap_cccd: "", co_anh: 1, created_at: null,
  trang_thai: "cho", loi: null, ma_dk: null, so_ho_so: null, ...ex,
});
const DIA_CHI = JSON.stringify({ ma_dvhc: "01001", ma_dvql: "01", ten_xa: "Phường Ba Đình", ten_tinh: "Hà Nội" });

function taoMo(): Mo {
  return {
    rows: [
      hv("u01", "Nguyễn Thị Hoà"),
      hv("u02", "Trần Văn Bình", { trang_thai: "loi", loi: "Thiếu địa chỉ 2 cấp" }),
      hv("u03", "Lê Đức Anh", { trang_thai: "xong", ma_dk: "MD-03", so_ho_so: "0003" }),
    ],
    luu: [],
    napLo: [],
    xoaNhap: [],
  };
}

async function giaBackend(page: Page, mo: Mo) {
  await page.addInitScript(() => localStorage.setItem("tool_session_token", "tok-test"));
  await page.route("**/local/auth/me", (r) => r.fulfill({ json: { username: "thu1", ho_ten: "Nhân viên thử", vai_tro: "operator" } }));
  await page.route("**/local/config/moi-truong", (r) => r.fulfill({ json: { thu_muc_ghi_duoc: true, duong_dan: "x", da_cau_hinh: true } }));
  await page.route("**/version", (r) => r.fulfill({ json: { build: "dev", commit: "x" } }));
  await page.route("**/local/khoa-hoc?**", (r) => r.fulfill({ json: KHOA }));
  await page.route("**/local/dvhc/so-gtvt", (r) => r.fulfill({ json: [] }));
  await page.route("**/local/giay-to?**", (r) => r.fulfill({ json: [{ ma_gt: 1, ten_gt: "CCCD" }, { ma_gt: 2, ten_gt: "Ảnh thẻ" }] }));
  await page.route("**/local/nap/danh-sach", (r) => r.fulfill({ json: mo.rows }));
  await page.route(/\/local\/nap\/nhap(\?.*)?$/, (r) => r.fulfill({ json: [] }));
  await page.route(/\/local\/nap\/nhap\/[^/?]+$/, async (r) => {
    const uuid = decodeURIComponent(new URL(r.request().url()).pathname.split("/").pop() ?? "");
    if (r.request().method() === "PUT") {
      mo.luu.push({ uuid, body: r.request().postDataJSON() });
      return r.fulfill({ json: { ok: true } });
    }
    if (r.request().method() === "DELETE") {
      mo.xoaNhap.push(uuid);
      return r.fulfill({ json: { ok: true } });
    }
    await r.fulfill({ json: { uuid, dia_chi_json: DIA_CHI, chi_tiet: null, noi_cap: null, ngay_cap: null, tick_json: null,
      jp2_b64: null, anh_preview: null, updated_at: null } });
  });
  await page.route("**/local/nap/keo/*/anh", (r) => r.fulfill({ status: 404, body: "" }));
  await page.route("**/local/nap/nap-lo", async (r) => {
    const b = r.request().postDataJSON() as { items: { uuid: string }[] };
    mo.napLo.push(b);
    await new Promise((ok) => setTimeout(ok, 250));
    const it = b.items[0];
    const loi = it.uuid === mo.napLoiUuid;
    if (!loi) {
      const i = mo.rows.findIndex((x) => x.uuid === it.uuid);
      mo.rows[i] = { ...mo.rows[i], trang_thai: "xong", ma_dk: `MD-${it.uuid}`, so_ho_so: `00${i + 1}` };
    }
    await r.fulfill({ json: { tong: 1, thanh_cong: loi ? 0 : 1, that_bai: loi ? 1 : 0, ket_qua: [
      loi ? { uuid: it.uuid, ok: false, loi: "Số CCCD đã có trong khóa này" }
        : { uuid: it.uuid, ok: true, ma_dk: `MD-${it.uuid}`, so_ho_so: "0001" }] } });
  });
}

async function vao(page: Page, mo: Mo, w = 1280) {
  await giaBackend(page, mo);
  await page.setViewportSize({ width: w, height: 820 });
  await page.goto("/tool/nap");
  await expect(page.getByTestId("hv-u01")).toBeVisible();
}

const ngan = (page: Page) => page.getByRole("complementary", { name: "Ngăn chuẩn bị hồ sơ" });

test.describe("NAP-01 — màn Nạp chia đôi (danh sách | ngăn Chuẩn bị luôn mở)", () => {
  test("ngăn phải luôn mở, tự hiện học viên đầu danh sách; bấm dòng khác thì đổi dữ liệu", async ({ page }) => {
    const mo = taoMo();
    await vao(page, mo);
    // Lỗi lên đầu → Trần Văn Bình được chọn sẵn
    await expect(ngan(page).getByText("TRẦN VĂN BÌNH")).toBeVisible();
    await expect(ngan(page).getByText("Chuẩn bị hồ sơ")).toBeVisible();
    await page.getByTestId("hv-u01").click();
    await expect(ngan(page).getByText("NGUYỄN THỊ HOÀ")).toBeVisible();
    if (process.env.CHUP_ANH) {
      for (const w of [1280, 1440]) {
        await page.setViewportSize({ width: w, height: 820 });
        await page.screenshot({ path: `${process.env.CHUP_ANH}/${w}-nap-chia-doi.png` });
      }
    }
  });

  test("đổi học viên tự lưu nháp của học viên trước (không mất dữ liệu đang gõ)", async ({ page }) => {
    const mo = taoMo();
    await vao(page, mo);
    await page.getByTestId("hv-u01").click();
    await expect(ngan(page).getByText("NGUYỄN THỊ HOÀ")).toBeVisible();
    await ngan(page).getByPlaceholder("Chi tiết (số nhà/thôn) — không bắt buộc").fill("12 Hai Bà Trưng");
    await page.getByTestId("hv-u02").click();
    await expect(ngan(page).getByText("TRẦN VĂN BÌNH")).toBeVisible();
    await expect.poll(() => mo.luu.filter((x) => x.uuid === "u01").length).toBeGreaterThan(0);
    expect(mo.luu.find((x) => x.uuid === "u01")!.body.chi_tiet).toBe("12 Hai Bà Trưng");
  });

  test("Chọn tất cả + hiện số lượng; nút nạp lô ghi đúng số sẵn sàng", async ({ page }) => {
    const mo = taoMo();
    await vao(page, mo);
    await page.getByTestId("hv-u01").click();                       // mở để biết đủ điều kiện (đã map địa chỉ)
    await expect(ngan(page).getByText("NGUYỄN THỊ HOÀ")).toBeVisible();
    await expect(page.getByTestId("dem-chon")).toContainText("Chọn 0/2");
    await page.getByLabel("Chọn tất cả học viên trong danh sách").check();
    await expect(page.getByTestId("dem-chon")).toContainText("Chọn 2/2");
    await expect(page.getByTestId("dem-chon")).toContainText("Sẵn sàng 2");
    await expect(page.getByRole("button", { name: /Nạp 2 học viên vào Khóa B2-01\/2026/ })).toBeEnabled();
    await page.getByLabel("Chọn tất cả học viên trong danh sách").uncheck();
    await expect(page.getByTestId("dem-chon")).toContainText("Chọn 0/2");
  });

  test("Nạp lô: ngăn phải hiện danh sách sẽ nạp, tiến độ, trạng thái từng dòng, nạp lại dòng lỗi", async ({ page }) => {
    const mo = taoMo();
    mo.napLoiUuid = "u02";
    await vao(page, mo);
    await page.getByTestId("hv-u01").click();
    await expect(ngan(page).getByText("NGUYỄN THỊ HOÀ")).toBeVisible();
    await page.getByLabel("Chọn tất cả học viên trong danh sách").check();
    await page.getByRole("button", { name: /Nạp 2 học viên vào/ }).click();

    const tbl = ngan(page).getByRole("table", { name: "Danh sách học viên sẽ nạp" });
    await expect(tbl.getByRole("row")).toHaveCount(3);               // 1 tiêu đề + 2 học viên
    await expect(tbl.getByText("Chờ")).toHaveCount(2);
    await ngan(page).getByRole("button", { name: "Bắt đầu nạp" }).click();

    await expect(ngan(page).getByTestId("tien-do-nap")).toContainText("2/2 · 100%");
    await expect(tbl.getByText("Số CCCD đã có trong khóa này")).toBeVisible();
    await expect(tbl.getByText(/Số HS/)).toBeVisible();
    await expect(ngan(page).getByRole("button", { name: "Nạp lại 1 lỗi" })).toBeVisible();
    expect(mo.napLo).toHaveLength(2);
    if (process.env.CHUP_ANH) {
      await page.screenshot({ path: `${process.env.CHUP_ANH}/1280-nap-lo-ket-qua.png` });
    }

    mo.napLoiUuid = undefined;                                       // lần nạp lại thành công
    await ngan(page).getByRole("button", { name: "Nạp lại 1 lỗi" }).click();
    await expect(ngan(page).getByText("Lỗi: 0")).toBeVisible();
    expect(mo.napLo).toHaveLength(3);
    await ngan(page).getByRole("button", { name: "Xong" }).click();
    // Đã nạp hết → nhóm Cần xử lý trống; ngăn phải về trạng thái hướng dẫn
    await expect(page.getByTestId("hv-u01")).toHaveCount(0);
    await expect(ngan(page).getByText("Chọn một học viên ở danh sách bên trái")).toBeVisible();
  });

  test("tab Đã nạp: ngăn phải chỉ xem (không có ô sửa)", async ({ page }) => {
    const mo = taoMo();
    await vao(page, mo);
    await page.getByRole("button", { name: /Đã nạp/ }).first().click();
    await expect(page.getByTestId("hv-u03")).toBeVisible();
    await expect(ngan(page).getByText("dữ liệu chỉ đọc")).toBeVisible();
    await expect(ngan(page).getByPlaceholder("Chi tiết (số nhà/thôn) — không bắt buộc")).toHaveCount(0);
  });

  test("dòng gọn: một dòng, không xuống dòng ở 1280 và 1440 (chiều cao dòng cố định)", async ({ page }) => {
    const mo = taoMo();
    await vao(page, mo);
    for (const w of [1280, 1440]) {
      await page.setViewportSize({ width: w, height: 820 });
      const h = await page.getByTestId("hv-u01").evaluate((el) => el.getBoundingClientRect().height);
      expect(h).toBeLessThanOrEqual(56);
      const tran = await page.getByTestId("hv-u01").evaluate((el) => el.scrollWidth > el.clientWidth + 1);
      expect(tran).toBe(false);
    }
  });

  test("màn hẹp (800px): không chia đôi, bấm dòng mở ngăn phủ rồi đóng lưu nháp", async ({ page }) => {
    const mo = taoMo();
    await vao(page, mo, 800);
    await expect(page.getByRole("complementary", { name: "Ngăn chuẩn bị hồ sơ" })).toHaveCount(0);
    await page.getByTestId("hv-u01").click();
    await expect(page.getByText("Chuẩn bị hồ sơ")).toBeVisible();
    await page.getByLabel("Đóng (lưu nháp)").click();
    await expect(page.getByText("Chuẩn bị hồ sơ")).toHaveCount(0);
  });

  test("khung trái ≈50% / ngăn phải ≈50%, tên nút chức năng ở ngăn phải hiện đủ chữ (1280 và 1440)", async ({ page }) => {
    const mo = taoMo();
    await vao(page, mo);
    await page.getByTestId("hv-u01").click();
    await expect(ngan(page).getByText("NGUYỄN THỊ HOÀ")).toBeVisible();
    for (const w of [1280, 1440]) {
      await page.setViewportSize({ width: w, height: 820 });
      const [trai, phai] = await ngan(page).evaluate((el) => [
        (el.previousElementSibling as HTMLElement).getBoundingClientRect().width,
        el.getBoundingClientRect().width,
      ]);
      expect(Math.abs(trai / (trai + phai) - 0.5)).toBeLessThan(0.03);
      for (const ten of ["Sửa ảnh chân dung", "Chuyển đổi sang xã mới", "Chọn tay", "Xóa nháp", /Nạp học viên này vào khóa K001/]) {
        const nut = ngan(page).getByRole("button", { name: ten });
        await expect(nut).toBeVisible();
        const bi = await nut.evaluate((el) => el.scrollWidth > el.clientWidth + 1);
        expect(bi, `nút ${String(ten)} bị cắt chữ ở ${w}px`).toBe(false);
      }
      if (process.env.CHUP_ANH) await page.screenshot({ path: `${process.env.CHUP_ANH}/${w}-nap-50-50.png` });
    }
  });
});
