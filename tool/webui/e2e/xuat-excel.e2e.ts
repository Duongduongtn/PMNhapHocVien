import { expect, test, type Page } from "@playwright/test";

// KQD-09 — nút "Xuất Excel" kết quả học tập theo khóa ở màn Cập nhật KQĐT + 2 ô thông tin cơ sở ở Cấu hình.
// Backend giả bằng page.route. Kiểm: nút chỉ hiện sau khi chọn khóa · tải về đúng tên file · gọi đúng ma_kh ·
// lỗi 404 hiện thông báo · nút khóa khi đang xuất · lưu tên cơ sở chỉ gửi 2 trường.

const KHOA = { ma_kh: "K40", ten_kh: "B01-K40", hang_gplx: "B", ngay_kg: "2026-07-30", ngay_bg: "2026-09-15", ngay_thi: "2026-09-20",
  dem: { dangky: 1, capnhat: 0, tuchoi: 0, giaitrinh: 0, ketxuat: 0 } };
const HV = [{
  ma_dk: "A1", ho_ten: "Nguyễn Thị Hòa", ngay_sinh: "20/11/1998", so_cccd: "079198001234", so_ho_so: "1", hang: "B.01",
  ma_hang_moi: "B.01", ma_hang: "B11", tt_xuly: "03", ket_luan: null,
  diem: { ly_thuyet: null, mo_phong: null, hinh: null, tien_lui: null, duong: null }, gio_duong: null, km_duong: null,
}];
const XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

async function giaBackend(page: Page) {
  await page.addInitScript(() => localStorage.setItem("tool_session_token", "tok-test"));
  await page.route("**/local/**", (r) => r.fulfill({ json: [] }));
  await page.route("**/local/auth/me", (r) => r.fulfill({ json: { username: "thu1", ho_ten: "Nhân viên thử", vai_tro: "operator" } }));
  await page.route("**/local/config/moi-truong", (r) => r.fulfill({ json: { thu_muc_ghi_duoc: true, duong_dan: "x", da_cau_hinh: true } }));
  await page.route("**/version", (r) => r.fulfill({ json: { build: "dev", commit: "x" } }));
  await page.route("**/local/sync/targets", (r) => r.fulfill({ json: { selected: "t1", targets: [{ key: "t1", name: "DB đích", database: "GPLX_CDB_CSDT", host: "x" }] } }));
  await page.route("**/local/ketqua/khoa?**", (r) => r.fulfill({ json: [KHOA] }));
  await page.route("**/local/ketqua/hoc-vien?**", (r) => r.fulfill({ json: HV }));
  await page.route("**/local/ketqua/chuong-trinh?**", (r) => r.fulfill({ json: { ma_kh: "K40", ct: "cu" } }));
  await page.route("**/local/ketqua/luat", (r) => r.fulfill({ json: { mon_bat_buoc: ["ly_thuyet", "mo_phong", "hinh", "tien_lui", "duong"] } }));
}

async function chonKhoa(page: Page) {
  await page.goto("/ket-qua/cap-nhat");
  await page.getByPlaceholder("Gõ tên khóa hoặc MaKH…").click();
  await page.getByText("B01-K40").first().click();
  await expect(page.getByText("Nguyễn Thị Hòa")).toBeVisible();
}

test.describe("KQD-09 — xuất Excel kết quả học tập theo khóa", () => {
  test("nút chỉ hiện sau khi chọn khóa; bấm → tải về đúng tên file + gọi đúng khóa + báo đã xuất", async ({ page }) => {
    const goi: string[] = [];
    await giaBackend(page);
    await page.route("**/local/ketqua/xuat-excel**", (r) => {
      goi.push(new URL(r.request().url()).searchParams.get("ma_kh") ?? "");
      return r.fulfill({
        status: 200, body: Buffer.from("PK\u0003\u0004gia"),
        headers: {
          "Content-Type": XLSX_MIME, "Access-Control-Expose-Headers": "Content-Disposition",
          "Content-Disposition": "attachment; filename=\"KetQuaHocTap_K40_12-10-2026.xlsx\"; filename*=UTF-8''KetQuaHocTap_K40_12-10-2026.xlsx",
        },
      });
    });
    await page.goto("/ket-qua/cap-nhat");
    await expect(page.getByRole("button", { name: /Xuất Excel/ })).toHaveCount(0);
    await page.getByPlaceholder("Gõ tên khóa hoặc MaKH…").click();
    await page.getByText("B01-K40").first().click();
    const nut = page.getByRole("button", { name: /Xuất Excel/ });
    await expect(nut).toBeVisible();

    const [dl] = await Promise.all([page.waitForEvent("download"), nut.click()]);
    expect(dl.suggestedFilename()).toBe("KetQuaHocTap_K40_12-10-2026.xlsx");
    expect(goi).toEqual(["K40"]);
    await expect(page.getByText(/Đã xuất kết quả học tập khóa K40/)).toBeVisible();
  });

  test("không đọc được header tên file: dùng tên dự phòng KetQuaHocTap_<MaKH>_<dd-mm-yyyy>.xlsx", async ({ page }) => {
    await giaBackend(page);
    await page.route("**/local/ketqua/xuat-excel**", (r) =>
      r.fulfill({ status: 200, body: Buffer.from("PK"), headers: { "Content-Type": XLSX_MIME } }));
    await chonKhoa(page);
    const [dl] = await Promise.all([page.waitForEvent("download"), page.getByRole("button", { name: /Xuất Excel/ }).click()]);
    expect(dl.suggestedFilename()).toMatch(/^KetQuaHocTap_K40_\d{2}-\d{2}-\d{4}\.xlsx$/);
  });

  test("khóa chưa có học viên (404): hiện đúng thông báo, không tải file, nút bấm lại được", async ({ page }) => {
    await giaBackend(page);
    await page.route("**/local/ketqua/xuat-excel**", (r) =>
      r.fulfill({ status: 404, json: { detail: "Khóa chưa có học viên — không có gì để xuất." } }));
    await chonKhoa(page);
    let taiVe = 0;
    page.on("download", () => { taiVe += 1; });
    await page.getByRole("button", { name: /Xuất Excel/ }).click();
    await expect(page.getByText("Khóa chưa có học viên — không có gì để xuất.")).toBeVisible();
    expect(taiVe).toBe(0);
    await expect(page.getByRole("button", { name: /Xuất Excel/ })).toBeEnabled();
  });

  test("đang xuất thì nút khóa (không bấm đúp ra 2 file)", async ({ page }) => {
    let goi = 0;
    await giaBackend(page);
    await page.route("**/local/ketqua/xuat-excel**", async (r) => {
      goi += 1;
      await new Promise((ok) => setTimeout(ok, 800));
      await r.fulfill({ status: 200, body: Buffer.from("PK"), headers: { "Content-Type": XLSX_MIME, "Content-Disposition": "attachment; filename=\"a.xlsx\"" } });
    });
    await chonKhoa(page);
    const nut = page.getByRole("button", { name: /Xuất Excel/ });
    await nut.click();
    await expect(nut).toBeDisabled();
    await nut.click({ force: true }).catch(() => undefined);
    await expect(page.getByText(/Đã xuất kết quả học tập khóa K40/)).toBeVisible();
    expect(goi).toBe(1);
  });
});

test.describe("KQD-09 — thông tin cơ sở ở màn Cấu hình", () => {
  test("nhập 2 ô rồi lưu → chỉ gửi PUT /local/config/co-so với 2 trường, báo đã lưu", async ({ page }) => {
    let body: unknown = null;
    await page.addInitScript(() => localStorage.setItem("tool_session_token", "tok-test"));
    await page.route("**/local/**", (r) => r.fulfill({ json: [] }));
    await page.route("**/local/auth/me", (r) => r.fulfill({ json: { username: "thu1", ho_ten: "NV", vai_tro: "operator" } }));
    await page.route("**/local/config", (r) => r.fulfill({ json: {
      sqlserver_host: "H", sqlserver_database: "D", sqlserver_user: "u", sqlserver_password: "********",
      vps_url: "", vps_api_key: "", co_quan_chu_quan: "", ten_co_so_dao_tao: "" } }));
    await page.route("**/local/config/co-so", (r) => {
      body = r.request().postDataJSON();
      return r.fulfill({ json: { co_quan_chu_quan: "CÔNG TY A", ten_co_so_dao_tao: "TRUNG TÂM B" } });
    });
    await page.goto("/ket-qua/cap-nhat");
    await page.getByRole("button", { name: /Cấu hình/ }).first().click();
    const khoi = page.locator("section", { hasText: "Thông tin cơ sở (đầu file Excel" });
    await khoi.locator("input").nth(0).fill("CÔNG TY A");
    await khoi.locator("input").nth(1).fill("TRUNG TÂM B");
    await khoi.getByRole("button", { name: /Lưu thông tin cơ sở/ }).click();
    await expect(page.getByText("Đã lưu thông tin cơ sở.")).toBeVisible();
    expect(body).toEqual({ co_quan_chu_quan: "CÔNG TY A", ten_co_so_dao_tao: "TRUNG TÂM B" });
  });
});
