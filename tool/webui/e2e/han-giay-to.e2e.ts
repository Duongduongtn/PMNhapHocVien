import { expect, test, type Page } from "@playwright/test";

// PCG-06 (task 122) — tab "Hạn giấy tờ" ở phân hệ Phân công GV–xe. Backend giả bằng page.route; chỉ đọc.

const K = (ma: string, ten: string) => ({ ma_kh: ma, ten_kh: ten });
const DU_LIEU = {
  hom_nay: "2026-10-12", nguong: 30,
  xe: {
    het_han: [{ bien_so: "51A-123.45", hang: "B", muc: "het_han", giay: [{ giay: "gpxtl", ngay: "2026-09-28", con_ngay: -14, muc: "het_han" }], khoa: [K("K148", "B-K148"), K("K149", "B-K149")] }],
    sap_het: [
      { bien_so: "51B-345.67", hang: "C1", muc: "sap_het", giay: [
        { giay: "gpxtl", ngay: "2026-11-05", con_ngay: 24, muc: "sap_het" }, { giay: "gcnkd", ngay: "2026-11-05", con_ngay: 24, muc: "sap_het" }], khoa: [K("K014", "C1-K14")] },
      { bien_so: "51D-567.89", hang: "B", muc: "sap_het", giay: [{ giay: "gpxtl", ngay: "2026-11-09", con_ngay: 28, muc: "sap_het" }], khoa: [] },
    ],
    chua_khai: [{ bien_so: "51E-678.90", hang: "B", khoa: [K("K149", "B-K149")] }],
  },
  gv: {
    het_han: [{ ma_gv: "GV003", ho_ten: "Nguyễn Văn Hải", hang: "B", muc: "het_han", giay: [{ giay: "gplx", ngay: "2026-08-15", con_ngay: -58, muc: "het_han" }], khoa: [K("K147", "B-K147")] }],
    sap_het: [{ ma_gv: "GV021", ho_ten: "Phạm Hữu Lộc", hang: "B", muc: "sap_het", giay: [{ giay: "gplx", ngay: "2026-10-31", con_ngay: 19, muc: "sap_het" }], khoa: [K("K148", "B-K148")] }],
    chua_khai: [{ ma_gv: "GV006", ho_ten: "Võ Thanh Sơn", hang: "B", khoa: [] }],
  },
  ngung: { xe: [{ bien_so: "51F-111.22", hang: "B", khoa: [K("K149", "B-K149")] }], gv: [] },
  dem: {},
};
const SACH = { hom_nay: "2026-10-12", nguong: 30, xe: { het_han: [], sap_het: [], chua_khai: [] }, gv: { het_han: [], sap_het: [], chua_khai: [] }, ngung: { xe: [], gv: [] }, dem: {} };

async function giaBackend(page: Page, kq: unknown, loi = false) {
  await page.addInitScript(() => localStorage.setItem("tool_session_token", "tok-test"));
  await page.route("**/local/**", (r) => r.fulfill({ json: [] }));
  await page.route("**/local/auth/me", (r) => r.fulfill({ json: { username: "thu1", ho_ten: "Nhân viên thử", vai_tro: "operator" } }));
  await page.route("**/local/config/moi-truong", (r) => r.fulfill({ json: { thu_muc_ghi_duoc: true, duong_dan: "x", da_cau_hinh: true } }));
  await page.route("**/version", (r) => r.fulfill({ json: { build: "dev", commit: "x" } }));
  await page.route("**/local/sync/targets", (r) => r.fulfill({ json: { selected: "t1", targets: [{ key: "t1", name: "DB đích", database: "GPLX_CDB_CSDT", host: "x" }] } }));
  await page.route("**/local/phancong/han-giay-to?**", (r) =>
    loi ? r.fulfill({ status: 502, json: { detail: "Không nối được CSDL đích" } }) : r.fulfill({ json: kq }));
}

test("có dữ liệu: đếm, đỏ/vàng, gộp hai loại giấy, khóa, ngưng, chưa khai, bấm khóa mở đúng khóa", async ({ page }) => {
  await giaBackend(page, DU_LIEU);
  await page.goto("/phan-cong/han-giay-to");
  await expect(page.getByRole("heading", { name: /Hạn giấy tờ/ })).toBeVisible();
  // ô đếm
  await expect(page.getByText("1 đã hết hạn").first()).toBeVisible();
  await expect(page.getByText("2 còn ≤ 30 ngày")).toBeVisible();
  // xe quá hạn (đỏ) + gộp 2 loại giấy cùng ngày trên một dòng
  const dongQuaHan = page.getByRole("row", { name: /51A-123\.45/ });
  await expect(dongQuaHan.getByText("Quá hạn 14 ngày")).toBeVisible();
  const dongGop = page.getByRole("row", { name: /51B-345\.67/ });
  await expect(dongGop.getByText("Giấy phép xe tập lái")).toBeVisible();
  await expect(dongGop.getByText("Giấy chứng nhận kiểm định")).toBeVisible();
  // xe không ở khóa nào
  await expect(page.getByRole("row", { name: /51D-567\.89/ }).getByText("Chưa dùng ở khóa nào")).toBeVisible();
  // GV, ngưng, chưa khai
  await expect(page.getByRole("row", { name: /Nguyễn Văn Hải/ }).getByText("Quá hạn 58 ngày")).toBeVisible();
  await expect(page.getByText("Đã ngưng nhưng còn phân công trong khóa chưa bế giảng")).toBeVisible();
  await expect(page.getByRole("row", { name: /51F-111\.22/ })).toBeVisible();
  await expect(page.getByText(/Chưa khai ngày hết hạn — không tính đỏ\/vàng \(2\)/)).toBeVisible();
  // chỉ đọc
  await expect(page.getByText("không ghi gì")).toBeVisible();
  // bấm khóa → mở đúng khóa ở Phân công theo khóa
  await page.getByRole("row", { name: /51A-123\.45/ }).getByRole("button", { name: "B-K148" }).click();
  await expect(page).toHaveURL(/\/phan-cong\/theo-khoa\?khoa=K148/);
});

test("không có gì sắp hết hạn → thông báo riêng", async ({ page }) => {
  await giaBackend(page, SACH);
  await page.goto("/phan-cong/han-giay-to");
  await expect(page.getByText("Không có giấy tờ nào sắp hết hạn trong 30 ngày")).toBeVisible();
});

test("lỗi kết nối → báo, không treo", async ({ page }) => {
  await giaBackend(page, null, true);
  await page.goto("/phan-cong/han-giay-to");
  await expect(page.getByText(/Không nối được CSDL đích/)).toBeVisible();
});

test("sub-nav có đủ 3 tab", async ({ page }) => {
  await giaBackend(page, SACH);
  await page.goto("/phan-cong/han-giay-to");
  for (const t of ["Phân công theo khóa", "Rà soát khóa", "Hạn giấy tờ"]) {
    await expect(page.getByRole("link", { name: t })).toBeVisible();
  }
});
