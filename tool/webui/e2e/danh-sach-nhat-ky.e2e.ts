import { expect, test, type Page } from "@playwright/test";

// TNB-07 — danh sách BC2 (tab Ô tô/Mô tô, lọc mở/đóng, đánh dấu lệch, bấm dòng → chi tiết) và tab Nhật ký.
// Backend giả bằng page.route; không đụng DB thật.

interface Mo {
  bc2: string[];
  nhatKy: string[];
}

const BC2 = [
  { ma_bc2: "80/2026", so_bao_cao: "80/2026", ngay_bao_cao: "2026-09-30", ma_bci: "B1", so_bc1: "112/BCI/2026", ma_kh: "K001",
    ten_kh: "Khóa B2-01/2026", loai: "oto", tong_ghi: 25, hv_thuc_te: 3, lech: true, dong: false, dang_mo: true, nguoi_tao: "thu1", ngay_tao: "2026-09-30" },
  { ma_bc2: "79/2026", so_bao_cao: "79/2026", ngay_bao_cao: "2026-09-20", ma_bci: "B2", so_bc1: "108/BCI/2026", ma_kh: "K000",
    ten_kh: "Khóa B2-12/2025", loai: "oto", tong_ghi: 40, hv_thuc_te: 40, lech: false, dong: false, dang_mo: true, nguoi_tao: "admin", ngay_tao: "2026-09-20" },
];
const CHI_TIET = {
  ma_bc2: "80/2026", so_bao_cao: "80/2026", ngay_bao_cao: "2026-09-30", trang_thai: 0, dang_mo: true, nguoi_tao: "thu1",
  ngay_tao: "2026-09-30", ma_bci: "B1", ma_kh: "K001", ten_kh: "Khóa B2-01/2026", loai: "oto", tong_ghi: 25, hv_thuc_te: 0,
  lech: true, xoa_duoc: true, hoc_vien: [],
};
const NK = [
  { id: 3, luc: "2026-10-11T10:08:05", nguoi: "thu1", loai: "go_hv", ten_loai: "Gỡ học viên khỏi BC2", ma_kh: "K001", ma_bc2: "80/2026",
    lo_id: "lo-3", so_hv: 2, tom_tat_thao_tac: "Gỡ 2 học viên", trang_thai: "xong", ten_trang_thai: "Xong",
    ket_qua: { da_ghi: 2, chua_ghi: 0, bo_qua: 0, tom_tat: "Đã gỡ 2" } },
  { id: 2, luc: "2026-10-11T09:30:00", nguoi: "admin", loai: "them_hv", ten_loai: "Thêm học viên vào BC2", ma_kh: "K001", ma_bc2: "80/2026",
    lo_id: "lo-2", so_hv: 150, tom_tat_thao_tac: "Thêm 150 học viên", trang_thai: "loi_giua_chung", ten_trang_thai: "Lỗi giữa chừng (một phần đã ghi)",
    ket_qua: { da_ghi: 100, chua_ghi: 50, bo_qua: 0, tom_tat: "Đã thêm 100 · Chưa ghi 50" } },
  { id: 1, luc: "2026-10-10T16:45:10", nguoi: "thu1", loai: "cuu_trang_thai", ten_loai: "Cứu trạng thái", ma_kh: "K001", ma_bc2: "",
    lo_id: "lo-1", so_hv: 1, tom_tat_thao_tac: "Cứu trạng thái: Đã học xong, chưa tốt nghiệp (03) → Thi sát hạch chưa đạt (17)", trang_thai: "that_bai", ten_trang_thai: "Thất bại — chưa ghi",
    ket_qua: { da_ghi: 0, chua_ghi: 0, bo_qua: 0, tom_tat: "" } },
];

async function giaBackend(page: Page, mo: Mo) {
  await page.addInitScript(() => localStorage.setItem("tool_session_token", "tok-test"));
  await page.route("**/local/auth/me", (r) => r.fulfill({ json: { username: "thu1", ho_ten: "Nhân viên thử", vai_tro: "operator" } }));
  await page.route("**/local/config/moi-truong", (r) => r.fulfill({ json: { thu_muc_ghi_duoc: true, duong_dan: "x", da_cau_hinh: true } }));
  await page.route("**/version", (r) => r.fulfill({ json: { build: "dev", commit: "x" } }));
  await page.route(/\/local\/tnbc2\/bc2\/[^/?]+(\?.*)?$/, (r) => r.fulfill({ json: CHI_TIET }));
  await page.route(/\/local\/tnbc2\/bc2(\?.*)?$/, async (r) => {
    const u = new URL(r.request().url());
    mo.bc2.push(u.search);
    const dong = u.searchParams.get("dong");
    const bc2 = dong === "dong"
      ? [{ ...BC2[1], ma_bc2: "70/2026", so_bao_cao: "70/2026", dong: true, dang_mo: false, lech: true, tong_ghi: 30, hv_thuc_te: 28 }]
      : BC2;
    await r.fulfill({ json: { loai: u.searchParams.get("loai"), dong: dong ?? "", tong: bc2.length, dang_mo: 2, da_dong: 1,
      lech: bc2.filter((b) => b.lech).length, bc2 } });
  });
  await page.route("**/local/tnbc2/nhat-ky?**", async (r) => {
    const u = new URL(r.request().url());
    mo.nhatKy.push(u.search);
    const loai = u.searchParams.get("loai");
    const ds = loai ? NK.filter((d) => d.loai === loai) : NK;
    await r.fulfill({ json: { loai: loai ?? "", ma_bc2: u.searchParams.get("ma_bc2") ?? "", tong: ds.length, nhat_ky: ds } });
  });
}

test.describe("TNB-07 — danh sách BC2", () => {
  test("bảng đủ cột, đánh dấu lệch đúng dòng, tóm tắt, bấm dòng mở chi tiết, không có nút sửa/xóa ở danh sách", async ({ page }) => {
    const mo: Mo = { bc2: [], nhatKy: [] };
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    const dong80 = page.getByTestId("bc2-80/2026");
    await expect(dong80.getByText("112/BCI/2026")).toBeVisible();               // BC1
    await expect(dong80.getByText("Khóa B2-01/2026")).toBeVisible();            // khóa
    await expect(dong80.getByText("thu1")).toBeVisible();                       // người tạo
    await expect(dong80.getByText("30/09/2026")).toBeVisible();                 // ngày báo cáo dd/mm/yyyy
    await expect(dong80.getByText("lệch")).toBeVisible();
    await expect(page.getByTestId("bc2-79/2026").getByText("lệch")).toHaveCount(0);
    await expect(page.getByTestId("tom-tat-ds-bc2")).toContainText("2 BC2");
    await expect(page.getByTestId("tom-tat-ds-bc2")).toContainText("1 có");
    await expect(page.getByRole("button", { name: /Xóa|Sửa|Đóng BC2/ })).toHaveCount(0);   // chỉ đọc
    if (process.env.CHUP_ANH) {
      for (const w of [800, 1280, 1440]) {
        await page.setViewportSize({ width: w, height: 800 });
        await page.screenshot({ path: `${process.env.CHUP_ANH}/${w}-danh-sach-bc2.png` });
      }
    }
    await dong80.getByText("80/2026").click();                                  // bấm dòng → chi tiết
    await expect(page.getByText("Chưa có học viên trong BC2 này.")).toBeVisible();
  });

  test("lọc Đã đóng và đổi loại hạng gửi đúng tham số; dòng đã đóng không có nút Thêm", async ({ page }) => {
    const mo: Mo = { bc2: [], nhatKy: [] };
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    await expect(page.getByTestId("bc2-80/2026")).toBeVisible();
    await page.getByRole("button", { name: /Đã đóng/ }).click();
    await expect(page.getByTestId("bc2-70/2026")).toBeVisible();
    await expect(page.getByRole("button", { name: "Thêm học viên vào BC2 70/2026" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Xem BC2 70/2026" })).toBeVisible();
    expect(mo.bc2.some((q) => q.includes("dong=dong") && q.includes("loai=oto"))).toBe(true);
    await page.getByRole("button", { name: "Mô tô" }).click();
    await expect.poll(() => mo.bc2.some((q) => q.includes("loai=moto"))).toBe(true);
  });
});

test.describe("TNB-07 — Nhật ký thao tác", () => {
  test("hiện ai · lúc nào · việc · số HV · kết quả đã/chưa ghi; thời gian dd/mm/yyyy HH:mm; không lộ họ tên/CMT", async ({ page }) => {
    const mo: Mo = { bc2: [], nhatKy: [] };
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/nhat-ky");
    await expect(page.getByText("11/10/2026 10:08")).toBeVisible();
    await expect(page.getByRole("cell", { name: "Gỡ học viên khỏi BC2" })).toBeVisible();
    await expect(page.getByText("Lỗi giữa chừng (một phần đã ghi)")).toBeVisible();
    await expect(page.getByText("Đã thêm 100 · Chưa ghi 50")).toBeVisible();
    await expect(page.getByText("Thất bại — chưa ghi")).toBeVisible();
    await expect(page.getByText("150", { exact: true })).toBeVisible();
    await expect(page.getByText(/không chứa họ tên hay số CMT/)).toBeVisible();
    await expect(page.getByText("3 thao tác gần nhất")).toBeVisible();
    if (process.env.CHUP_ANH) {
      for (const w of [800, 1280, 1440]) {
        await page.setViewportSize({ width: w, height: 800 });
        await page.screenshot({ path: `${process.env.CHUP_ANH}/${w}-nhat-ky.png` });
      }
    }
  });

  test("lọc theo loại và theo số BC2 gửi đúng tham số; không có kết quả thì báo rỗng", async ({ page }) => {
    const mo: Mo = { bc2: [], nhatKy: [] };
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/nhat-ky");
    await expect(page.getByText("Gỡ 2 học viên")).toBeVisible();
    await page.getByLabel("Loại thao tác").selectOption("cuu_trang_thai");
    await expect(page.getByText("Cứu trạng thái: Đã học xong, chưa tốt nghiệp (03) → Thi sát hạch chưa đạt (17)")).toBeVisible();
    await expect(page.getByText("Gỡ 2 học viên")).toHaveCount(0);
    expect(mo.nhatKy.some((q) => q.includes("loai=cuu_trang_thai"))).toBe(true);
    await page.getByLabel("Số BC2 (tùy chọn)").fill("80/2026");
    await expect.poll(() => mo.nhatKy.some((q) => q.includes("ma_bc2=80%2F2026"))).toBe(true);
    await page.getByLabel("Loại thao tác").selectOption("xoa_bc2");
    await expect(page.getByText("Chưa có thao tác nào được ghi.")).toBeVisible();
  });
});
