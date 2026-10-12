import { expect, test, type Page } from "@playwright/test";

// KQD-07 (task 120) — khung "Kiểm trước kết xuất" ở màn Cập nhật KQĐT. Backend giả bằng page.route.
// Kiểm: mở khung → tóm tắt + chip → ẩn chip giờ/km khi chưa có điểm → lọc → bấm dòng nhảy tới HV ở lưới.

const KHOA = { ma_kh: "K148", ten_kh: "B-K148", hang_gplx: "B", ngay_kg: "2026-09-02", ngay_bg: "2026-10-09", ngay_thi: "2026-10-09",
  dem: { dangky: 3, capnhat: 3, tuchoi: 0, giaitrinh: 0, ketxuat: 0 } };
const dg = (ma: string, ten: string, cccd: string, tt: string, diem: Record<string, number | null>) => ({
  ma_dk: ma, ho_ten: ten, ngay_sinh: "01/01/2000", so_cccd: cccd, so_ho_so: ma, hang: "B", ma_hang_moi: "B", ma_hang: "B",
  tt_xuly: tt, ket_luan: null, diem: { ly_thuyet: null, mo_phong: null, hinh: null, tien_lui: null, duong: null, ...diem },
});
const HV = [
  dg("1", "Nguyễn Văn An", "079201011200", "03", {}),
  dg("2", "Phạm Thị Dung", "079202011567", "09", { ly_thuyet: 8, hinh: 8, tien_lui: 7, duong: 8 }),
  dg("3", "Đặng Quốc Phúc", "079200011790", "10", { ly_thuyet: 8, mo_phong: 7, hinh: 8, tien_lui: 7, duong: 8 }),
];

type Kieu = "thieu" | "du" | "trong" | "moto" | "loi";
function kiemTruoc(kieu: Kieu) {
  const rong = { chua_co_diem: 0, thieu_mon: 0, thieu_gio_km: 0, thieu_ket_luan: 0 };
  if (kieu === "du") return { ma_kh: "K148", tong: 6, du: 6, mo_to_bo_qua: 0, thieu: [], dem: rong };
  if (kieu === "trong") return { ma_kh: "K148", tong: 0, du: 0, mo_to_bo_qua: 0, thieu: [], dem: rong };
  if (kieu === "moto") return { ma_kh: "K148", tong: 0, du: 0, mo_to_bo_qua: 12, thieu: [], dem: rong };
  return {
    ma_kh: "K148", tong: 5, du: 2, mo_to_bo_qua: 0,
    dem: { chua_co_diem: 1, thieu_mon: 1, thieu_gio_km: 2, thieu_ket_luan: 1 },
    thieu: [
      // backend trả cả thieu_gio_km cho HV chưa có điểm → UI phải ẩn chip này
      { ma_dk: "1", ho_ten: "Nguyễn Văn An", so_cccd: "079201011200", tt_xuly: "03", ly_do: ["chua_co_diem", "thieu_gio_km"], mon_thieu: [], canh_bao: [] },
      { ma_dk: "2", ho_ten: "Phạm Thị Dung", so_cccd: "079202011567", tt_xuly: "09", ly_do: ["thieu_mon", "thieu_gio_km"], mon_thieu: ["mo_phong"], canh_bao: [] },
      { ma_dk: "3", ho_ten: "Đặng Quốc Phúc", so_cccd: "079200011790", tt_xuly: "10", ly_do: ["thieu_ket_luan"], mon_thieu: [],
        canh_bao: [{ loai: "gio_duong", gia_tri: 18, goi_y: 20 }, { loai: "km_duong", gia_tri: 700, goi_y: 810 }] },
    ],
  };
}

async function giaBackend(page: Page, kieu: Kieu) {
  await page.addInitScript(() => localStorage.setItem("tool_session_token", "tok-test"));
  await page.route("**/local/**", (r) => r.fulfill({ json: [] })); // mặc định rỗng cho mọi API không liệt kê
  await page.route("**/local/auth/me", (r) => r.fulfill({ json: { username: "thu1", ho_ten: "Nhân viên thử", vai_tro: "operator" } }));
  await page.route("**/local/config/moi-truong", (r) => r.fulfill({ json: { thu_muc_ghi_duoc: true, duong_dan: "x", da_cau_hinh: true } }));
  await page.route("**/version", (r) => r.fulfill({ json: { build: "dev", commit: "x" } }));
  await page.route("**/local/sync/targets", (r) => r.fulfill({ json: { selected: "t1", targets: [{ key: "t1", name: "DB đích", database: "GPLX_CDB_CSDT", host: "x" }] } }));
  await page.route("**/local/ketqua/khoa?**", (r) => r.fulfill({ json: [KHOA] }));
  await page.route("**/local/ketqua/hoc-vien?**", (r) => r.fulfill({ json: HV }));
  await page.route("**/local/ketqua/chuong-trinh?**", (r) => r.fulfill({ json: { ma_kh: "K148", ct: "cu" } }));
  await page.route("**/local/ketqua/luat", (r) => r.fulfill({ json: { mon_bat_buoc: ["ly_thuyet", "mo_phong", "hinh", "tien_lui", "duong"] } }));
  await page.route("**/local/ketqua/mo-khoa?**", (r) => r.fulfill({ json: { mo_duoc: false, goi_chua_gui: [], goi_da_gui: [], so_hv_mo: 0, so_hv_bo_qua: 0, so_khoa: 0 } }));
  await page.route("**/local/ketqua/sua-sau-gui?**", (r) => r.fulfill({ json: [] }));
  await page.route("**/local/ketqua/kiem-truoc?**", (r) =>
    kieu === "loi" ? r.fulfill({ status: 502, json: { detail: "Không nối được CSDL đích" } }) : r.fulfill({ json: kiemTruoc(kieu) }));
}

async function moKhung(page: Page) {
  await page.goto("/ket-qua/cap-nhat");
  await page.getByPlaceholder("Gõ tên khóa hoặc MaKH…").click();
  await page.getByText("B-K148").first().click();
  await page.getByRole("button", { name: /Kiểm trước kết xuất/ }).click();
}

test("còn thiếu: tóm tắt, chip, ẩn giờ/km khi chưa có điểm, lọc, bấm dòng nhảy tới HV", async ({ page }) => {
  await giaBackend(page, "thieu");
  await moKhung(page);
  const khung = page.getByRole("dialog", { name: "Kiểm trước kết xuất" });
  await expect(khung.getByText(/2\s*học viên đủ điều kiện/)).toBeVisible();
  await expect(khung.getByText(/3\s*học viên còn thiếu/)).toBeVisible();
  // dòng An (chưa có điểm): chỉ chip "Chưa có điểm", KHÔNG chip giờ/km
  const dongAn = khung.getByRole("button", { name: /Nguyễn Văn An/ });
  await expect(dongAn.getByText("Chưa có điểm")).toBeVisible();
  await expect(dongAn.getByText("Thiếu giờ/km thực hành")).toHaveCount(0);
  // dòng Dung (có điểm): thiếu môn nêu rõ + vẫn có chip giờ/km
  const dongDung = khung.getByRole("button", { name: /Phạm Thị Dung/ });
  await expect(dongDung.getByText("Thiếu môn: Mô phỏng")).toBeVisible();
  await expect(dongDung.getByText("Thiếu giờ/km thực hành")).toBeVisible();
  // dòng Phúc: cảnh báo vàng
  await expect(khung.getByText("⚠ Giờ đường 18 < 20")).toBeVisible();
  // đếm giờ/km chỉ còn 1 (không tính HV chưa có điểm)
  await expect(khung.getByRole("button", { name: /Thiếu giờ\/km thực hành · 1/ })).toBeVisible();
  // ghi chú chỉ nhắc
  await expect(khung.getByText("Kiểm tra này chỉ nhắc, không chặn.")).toBeVisible();
  // lọc theo chip
  await khung.getByRole("button", { name: /Thiếu kết luận · 1/ }).click();
  await expect(khung.getByRole("button", { name: /Nguyễn Văn An/ })).toHaveCount(0);
  await khung.getByText("bỏ lọc").click();
  // bấm dòng → đóng khung, lưới lọc đúng HV đó
  await khung.getByRole("button", { name: /Đặng Quốc Phúc/ }).click();
  await expect(page.getByRole("dialog", { name: "Kiểm trước kết xuất" })).toHaveCount(0);
  await expect(page.getByPlaceholder("Tìm tên / CCCD")).toHaveValue("079200011790");
  await expect(page.getByText("Đặng Quốc Phúc")).toBeVisible();
  await expect(page.getByText("Nguyễn Văn An")).toHaveCount(0);
});

for (const [kieu, chu] of [
  ["du", "Khóa đủ điều kiện kết xuất"],
  ["trong", "Khóa chưa có học viên"],
  ["moto", "Khóa mô tô — không xét kết quả đào tạo"],
  ["loi", "Không kết nối được DB đích"],
] as const) {
  test(`trạng thái: ${kieu}`, async ({ page }) => {
    await giaBackend(page, kieu);
    await moKhung(page);
    await expect(page.getByText(chu)).toBeVisible();
    await expect(page.getByText("Kiểm tra này chỉ nhắc, không chặn.")).toBeVisible();
  });
}
