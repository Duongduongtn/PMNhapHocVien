import { expect, test, type Page } from "@playwright/test";

// KQD-02 (phần đổi 12/10/2026, CHANGES #69) — ô Giờ đường/Km đường trên lưới Cập nhật KQĐT:
// nạp sẵn giá trị đã lưu · gõ hh:mm → thập phân · chỉ sửa giờ/km thì ghi riêng 2 cột (không qua cap-nhat)
// · sửa điểm mà giữ nguyên giờ/km thì KHÔNG gửi null đè giờ cũ. Backend giả bằng page.route.

const KHOA = { ma_kh: "K40", ten_kh: "B01-K40", hang_gplx: "B", ngay_kg: "2026-07-30", ngay_bg: "2026-09-15", ngay_thi: "2026-09-20",
  dem: { dangky: 3, capnhat: 1, tuchoi: 0, giaitrinh: 0, ketxuat: 0 } };
const RONG = { ly_thuyet: null, mo_phong: null, hinh: null, tien_lui: null, duong: null };
const hv = (ma: string, ten: string, gio: number | null, km: number | null, diem: Record<string, number | null> = RONG, tt = "03") => ({
  ma_dk: ma, ho_ten: ten, ngay_sinh: "01/01/2000", so_cccd: "0792" + ma, so_ho_so: ma, hang: "B.01", ma_hang_moi: "B.01", ma_hang: "B11",
  tt_xuly: tt, ket_luan: tt === "09" ? "dat" : null, diem: { ...RONG, ...diem }, gio_duong: gio, km_duong: km,
});
const DANH_SACH = [
  hv("A1", "NGUYỄN VĂN AN", 10, 500),
  hv("A2", "LÊ THỊ BÌNH", 18.4, 719.4),
  hv("A3", "TRẦN VĂN CƯỜNG", null, null),
  hv("A4", "PHẠM THỊ DUNG", 18.4, 719.4, { ly_thuyet: 8, mo_phong: 7, hinh: 8, tien_lui: 7, duong: 8 }, "09"),
  hv("A5", "VÕ THỊ EM", 20.3, 800),
];

type Goi = { ten: string; body: unknown };
async function giaBackend(page: Page, goi: Goi[]) {
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
  await page.route("**/local/ketqua/dat/luu**", (r) => {
    const body = r.request().postDataJSON();
    goi.push({ ten: "dat/luu", body });
    return r.fulfill({ json: { ok: true, da_luu: body.dong.length, bo_qua: [] } });
  });
  await page.route("**/local/ketqua/cap-nhat**", (r) => {
    const body = r.request().postDataJSON();
    goi.push({ ten: "cap-nhat", body });
    return r.fulfill({ json: { ok: true, ma_dk: body.ma_dk, ket_luan: "dat", tt_moi: "09", so_giay: null, quy_doi: {}, ct: "cu" } });
  });
}

async function chonKhoa(page: Page) {
  await page.goto("/ket-qua/cap-nhat");
  await page.getByPlaceholder("Gõ tên khóa hoặc MaKH…").click();
  await page.getByText("B01-K40").first().click();
  await expect(page.getByText("NGUYỄN VĂN AN")).toBeVisible();
}
const dong = (page: Page, ten: string) => page.locator("tr", { hasText: ten });
const oGio = (page: Page, ten: string) => dong(page, ten).locator('input[data-kqd-c="5"]');
const oKm = (page: Page, ten: string) => dong(page, ten).locator('input[data-kqd-c="6"]');
const nutLuu = (page: Page, ten: string) => dong(page, ten).getByRole("button", { name: "Lưu", exact: true });

test.describe("KQD-02 — giờ/km đường trên lưới (CHANGES #69)", () => {
  test("E10 nút Nạp giờ/km từ PDF DAT chỉ hiện sau khi chọn khóa", async ({ page }) => {
    await giaBackend(page, []);
    await page.goto("/ket-qua/cap-nhat");
    await expect(page.getByRole("button", { name: /Nạp giờ\/km từ PDF DAT/ })).toHaveCount(0);
    await page.getByPlaceholder("Gõ tên khóa hoặc MaKH…").click();
    await page.getByText("B01-K40").first().click();
    await expect(page.getByRole("button", { name: /Nạp giờ\/km từ PDF DAT/ })).toBeVisible();
  });

  test("E1 mở ra là hiện sẵn giờ/km đã lưu (18,4 — không lộ đuôi real); chưa có thì trống + gợi ý", async ({ page }) => {
    await giaBackend(page, []);
    await chonKhoa(page);
    await expect(oGio(page, "LÊ THỊ BÌNH")).toHaveValue("18,4");
    await expect(oKm(page, "LÊ THỊ BÌNH")).toHaveValue("719,4");
    await expect(oGio(page, "TRẦN VĂN CƯỜNG")).toHaveValue("");
    await expect(oGio(page, "TRẦN VĂN CƯỜNG")).toHaveAttribute("placeholder", "≥12");   // B số tự động
    await expect(oKm(page, "TRẦN VĂN CƯỜNG")).toHaveAttribute("placeholder", "≥710");
  });

  test("E2 gõ hh:mm → thập phân; số thập phân giữ nguyên; phút ≥ 60 viền đỏ và Lưu không gọi API", async ({ page }) => {
    const goi: Goi[] = [];
    await giaBackend(page, goi);
    await chonKhoa(page);
    const gio = oGio(page, "NGUYỄN VĂN AN");
    await gio.fill("20:30"); await gio.blur();
    await expect(gio).toHaveValue("20,5");
    await gio.fill("20:20"); await gio.blur();
    await expect(gio).toHaveValue("20,33");
    await gio.fill("20,5"); await gio.blur();
    await expect(gio).toHaveValue("20,5");
    // số đã lưu 20,3 mở lại vẫn 20,3 (không bị hiểu là 20 giờ 3 phút)
    await expect(oGio(page, "VÕ THỊ EM")).toHaveValue("20,3");
    // sai dạng
    await gio.fill("20:75"); await gio.blur();
    await expect(gio).toHaveValue("20:75");
    await expect(gio).toHaveClass(/border-destructive/);
    await nutLuu(page, "NGUYỄN VĂN AN").click();
    await expect(page.getByText(/Giờ đường sai dạng/)).toBeVisible();
    expect(goi).toHaveLength(0);
  });

  test("E3 chỉ sửa giờ/km → ghi riêng 2 cột qua dat/luu (không gọi cap-nhat); không đổi gì thì Lưu mờ", async ({ page }) => {
    const goi: Goi[] = [];
    await giaBackend(page, goi);
    await chonKhoa(page);
    await expect(nutLuu(page, "NGUYỄN VĂN AN")).toBeDisabled();
    await expect(nutLuu(page, "TRẦN VĂN CƯỜNG")).toBeDisabled();
    await oGio(page, "NGUYỄN VĂN AN").fill("11");
    await oGio(page, "NGUYỄN VĂN AN").blur();
    await expect(nutLuu(page, "NGUYỄN VĂN AN")).toBeEnabled();
    await nutLuu(page, "NGUYỄN VĂN AN").click();
    await expect(page.getByText("Đã lưu giờ/km đường của NGUYỄN VĂN AN.")).toBeVisible();
    expect(goi.map((g) => g.ten)).toEqual(["dat/luu"]);
    expect(goi[0].body).toEqual({ ma_kh: "K40", dong: [{ ma_dk: "A1", gio_duong: 11, km_duong: 500 }] });
  });

  test("E4 sửa điểm mà giữ nguyên giờ/km → body cap-nhat mang đúng giờ/km cũ, KHÔNG null", async ({ page }) => {
    const goi: Goi[] = [];
    await giaBackend(page, goi);
    await chonKhoa(page);
    const hinh = dong(page, "PHẠM THỊ DUNG").locator('input[data-kqd-c="2"]');
    await hinh.fill("85");
    await nutLuu(page, "PHẠM THỊ DUNG").click();
    await expect(page.getByText(/Đã lưu PHẠM THỊ DUNG/)).toBeVisible();
    expect(goi.map((g) => g.ten)).toEqual(["cap-nhat"]);
    const b = goi[0].body as { ma_dk: string; diem_goc: Record<string, number>; giu_quydoi: Record<string, number>;
      gio_duong: number | null; km_duong: number | null };
    expect(b.ma_dk).toBe("A4");
    expect(b.diem_goc).toEqual({ hinh: 85 });
    expect(b.giu_quydoi).toEqual({ ly_thuyet: 8, mo_phong: 7, tien_lui: 7, duong: 8 });
    expect(b.gio_duong).toBe(18.4);
    expect(b.km_duong).toBe(719.4);
  });
});
