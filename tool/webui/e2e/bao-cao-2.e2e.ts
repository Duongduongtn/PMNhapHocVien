import { expect, test, type Page } from "@playwright/test";

// TNB-04 — Lập BC2 bước ①: chọn khóa. Backend giả bằng page.route; không đụng DB thật.

interface Mo {
  cacLanGoi: string[];
  ungVien: string[];
  /** Body của các lần POST /bc2 (tạo BC2). */
  taoBc2?: Record<string, unknown>[];
  /** Hành vi của POST /bc2: lần đầu. */
  taoKieu?: "ok" | "trung" | "mat_ket_noi" | "loi_500";
}

const KHOA = [
  { ma_kh: "K001", ten_kh: "Khóa B2-01/2026", ngay_bg: "2026-09-20", khoa_cu: false, co_bc1: true, so_bc1: "112/BCI/2026",
    bc2_cua_khoa: [], san_sang: 150, can_xem: 3, thi_lai: 74, thi_lai_cua_khoa: 4 },
  { ma_kh: "K002", ten_kh: "Khóa C-02/2026", ngay_bg: "2026-08-10", khoa_cu: false, co_bc1: false, so_bc1: "",
    bc2_cua_khoa: [], san_sang: 20, can_xem: 0, thi_lai: 74, thi_lai_cua_khoa: 0 },
];
const KHOA_MOTO = [
  { ma_kh: "M001", ten_kh: "Khóa A1-05/2026", ngay_bg: "2026-09-01", khoa_cu: false, co_bc1: true, so_bc1: "90/BCI/2026",
    bc2_cua_khoa: [{ ma: "861/26-TTTĐ", trang_thai: 0, tong_ghi: 74 }], san_sang: 12, can_xem: 0, thi_lai: 5, thi_lai_cua_khoa: 1 },
];

const hvUv = (ma_dk: string, ten: string, nhom: string, ex: Record<string, unknown> = {}) => ({
  ma_dk, so_ho_so: "", ten, ngay_sinh: "01/05/1990", cmt: `0792${ma_dk.replace(/\D/g, "").padStart(8, "0")}`, so_giay: "N1|1",
  hang: "B2", ma_kh: "K001", ten_kh: "Khóa B2-01/2026", tt: "09", ten_trang_thai: "Đã tốt nghiệp, chờ lập BC2", ma_bc2: "",
  bg: "2026-09-20", nhom, ma_ly_do: "", ly_do: "", goi_y_xu_ly: null, tich_san: nhom === "san_sang",
  tuoi_thang: null, trong_nguong: false, ...ex,
});
const SAN = Array.from({ length: 3450 }, (_, i) => hvUv(`S-${String(i).padStart(4, "0")}`, `Học Viên ${String(i).padStart(4, "0")}`, "san_sang"));
const THI = [
  hvUv("T-0001", "Nguyễn Thị Hoà", "thi_lai", { ma_kh: "K0A", ten_kh: "Khóa B2-12/2025", bg: "2026-07-20", tt: "14", tuoi_thang: 3, trong_nguong: true, ten_trang_thai: "Chưa đạt BC2 — cần lập lại" }),
  hvUv("T-0002", "Trần Văn Bình", "thi_lai", { ma_kh: "K0A", ten_kh: "Khóa B2-12/2025", bg: "2026-07-20", tt: "17", tuoi_thang: 3, trong_nguong: true, ten_trang_thai: "Thi sát hạch chưa đạt" }),
  hvUv("T-0003", "Lê Đức Anh", "thi_lai", { ma_kh: "K0A", ten_kh: "Khóa B2-12/2025", bg: "2026-07-20", tt: "18", tuoi_thang: 3, trong_nguong: true, ten_trang_thai: "Vắng sát hạch" }),
  hvUv("T-0004", "Phạm Ngọc Ánh", "thi_lai", { ma_kh: "K0B", ten_kh: "Khóa B2-03/2024", bg: "2024-06-01", tt: "17", tuoi_thang: 28, trong_nguong: false, ten_trang_thai: "Thi sát hạch chưa đạt" }),
];
const XEM = [hvUv("X-0001", "Võ Thị Kim Chi", "can_xem", { tt: "03", so_giay: "", ten_trang_thai: "Đã học xong, chưa tốt nghiệp",
  ma_ly_do: "chua_tot_nghiep", ly_do: "Chưa tốt nghiệp — cần có giấy chứng nhận trước", goi_y_xu_ly: "cap_nhat_tot_nghiep" })];
const KHONG = [hvUv("N-0001", "Bùi Văn Sơn", "khong_duoc", { tt: "11", ma_bc2: "03/BCII/2026", ten_trang_thai: "Đã vào BC2, chờ kết quả",
  ma_ly_do: "dang_o_bc2_mo", ly_do: "Đang ở BC2 số 03/BCII/2026 — gỡ khỏi BC2 đó trước", goi_y_xu_ly: "go_khoi_bc2" })];

async function giaBackend(page: Page, mo: Mo) {
  await page.addInitScript(() => localStorage.setItem("tool_session_token", "tok-test"));
  await page.route("**/local/auth/me", (r) => r.fulfill({ json: { username: "thu1", ho_ten: "Nhân viên thử", vai_tro: "operator" } }));
  await page.route("**/local/config/moi-truong", (r) => r.fulfill({ json: { thu_muc_ghi_duoc: true, duong_dan: "x", da_cau_hinh: true } }));
  await page.route("**/version", (r) => r.fulfill({ json: { build: "dev", commit: "x" } }));
  await page.route("**/local/tnbc2/bc2/ung-vien?**", async (r) => {
    const u = new URL(r.request().url());
    mo.ungVien.push(u.search);
    const thang = Number(u.searchParams.get("thi_lai_thang") || 12);
    const thi = THI.map((h) => ({ ...h, trong_nguong: (h.tuoi_thang ?? 99) <= thang }));
    await r.fulfill({ json: { ma_kh: u.searchParams.get("ma_kh"), ten_kh: "Khóa B2-01/2026", loai: "oto", hom_nay: "2026-10-11",
      thi_lai_thang: thang, ma_bc2: u.searchParams.get("ma_bc2") || "", bc1: { ma_bci: "BCI-1", so_bao_cao: "112/BCI/2026", so_hoc_sinh: 150 },
      bc2_cua_khoa: [], nhom: { san_sang: SAN, thi_lai: thi, can_xem: XEM, khong_duoc: KHONG },
      dem: { san_sang: SAN.length, thi_lai: thi.length, thi_lai_trong_nguong: thi.filter((h) => h.trong_nguong).length,
        can_xem: XEM.length, khong_duoc: KHONG.length } } });
  });
  await page.route("**/local/tnbc2/bc2/goi-y-so?**", async (r) => {
    const maKh = new URL(r.request().url()).searchParams.get("ma_kh");
    const moto = maKh === "M001";
    await r.fulfill({ json: moto
      ? { ma_kh: "M001", ten_kh: "Khóa A1-05/2026", loai: "moto", nam: 2026, so: "870/26-TTTĐ", co_bc1: true,
          bc1: { ma_bci: "BCI-9", so_bao_cao: "A1A2870/26-TTTĐ", so_hoc_sinh: 74 },
          bc2_cua_khoa: [{ ma: "861/26-TTTĐ", trang_thai: 0, tong_ghi: 74 }], trung: false }
      : { ma_kh: "K001", ten_kh: "Khóa B2-01/2026", loai: "oto", nam: 2026, so: "81/2026", co_bc1: true,
          bc1: { ma_bci: "BCI-1", so_bao_cao: "112/BCI/2026", so_hoc_sinh: 150, ngay_bao_cao: "2026-09-30" }, bc2_cua_khoa: [], trung: false } });
  });
  await page.route(/\/local\/tnbc2\/bc2(\?.*)?$/, async (r) => {
    const req = r.request();
    if (req.method() === "POST") {
      const b = req.postDataJSON();
      (mo.taoBc2 ??= []).push(b);
      if (mo.taoKieu === "mat_ket_noi" && mo.taoBc2.length === 1) return r.abort("connectionreset");
      if (mo.taoKieu === "loi_500" && mo.taoBc2.length === 1) {
        return r.fulfill({ status: 500, json: { detail: "Tạo BC2 không thấy dòng vừa ghi — kiểm lại ở danh sách BC2" } });
      }
      if ((mo.taoKieu === "mat_ket_noi" || mo.taoKieu === "loi_500") && b.thu_lai) {
        // BC2 đã được tạo ở lần trước: server chỉ trả mã (không có so_bao_cao / ngay_bao_cao / tong_so_thi_sinh)
        return r.fulfill({ json: { ma_bc2: b.so_bao_cao, da_ton_tai: true, ma_kh: b.ma_kh, loai: "oto", ma_bci: "BCI-1", canh_bao: [] } });
      }
      if (mo.taoKieu === "trung") {
        return r.fulfill({ status: 409, json: { detail: { ma: "trung_so", noi_dung: `Số BC2 ${b.so_bao_cao} đã tồn tại — đổi số khác` } } });
      }
      return r.fulfill({ json: { ma_bc2: b.so_bao_cao, da_ton_tai: false, ma_kh: b.ma_kh, loai: "oto", ma_bci: "BCI-1",
        so_bao_cao: b.so_bao_cao, ngay_bao_cao: b.ngay_bao_cao || "2026-10-11", tong_so_thi_sinh: 0, trang_thai: 0, canh_bao: [] } });
    }
    await r.fulfill({ json: { loai: "", dong: "", tong: 2, dang_mo: 1, da_dong: 1, lech: 0, bc2: [
      { ma_bc2: "80/2026", so_bao_cao: "80/2026", ma_kh: "K0X", loai: "oto", dang_mo: true, dong: false },
      { ma_bc2: "861/26-TTÐ", so_bao_cao: "861/26-TTĐ", ma_kh: "M001", loai: "moto", dang_mo: true, dong: false },
    ] } });
  });
  await page.route("**/local/tnbc2/bc2/khoa-san-sang?**", async (r) => {
    const u = new URL(r.request().url());
    mo.cacLanGoi.push(u.search);
    const loai = u.searchParams.get("loai");
    await r.fulfill({ json: { loai, hom_nay: "2026-10-11", thi_lai_thang: 12, thi_lai_tat_ca: 74,
      khoa: loai === "moto" ? KHOA_MOTO : KHOA } });
  });
}

test.describe("TNB-04 — Lập BC2 bước ①: chọn khóa", () => {
  test("hiện khóa kèm đếm Sẵn sàng / Thi lại / Cần xem; khóa chưa có BC1 mờ và khóa nút", async ({ page }) => {
    await giaBackend(page, { cacLanGoi: [], ungVien: [] });
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    await page.getByRole("button", { name: "Lập BC2 mới" }).click();

    const k1 = page.getByTestId("khoa-K001");
    await expect(k1.getByText("Khóa B2-01/2026")).toBeVisible();
    await expect(k1.getByText("150")).toBeVisible();
    await expect(k1.getByText("Thi lại (≤ 12 tháng)")).toBeVisible();
    await expect(k1.getByText("112/BCI/2026")).toBeVisible();

    const k2 = page.getByTestId("khoa-K002");
    await expect(k2.getByText(/chưa có BC1/)).toBeVisible();
    await expect(k2.getByRole("button", { name: "Chọn khóa này →" })).toBeDisabled();
    await k2.click();                                            // bấm cả thẻ cũng không đi tiếp
    await expect(page.getByText("Chọn khóa cần lập BC2")).toBeVisible();
    if (process.env.CHUP_ANH) {
      for (const w of [800, 1280, 1440]) {
        await page.setViewportSize({ width: w, height: 800 });
        await page.screenshot({ path: `${process.env.CHUP_ANH}/${w}-buoc-1.png` });
      }
    }
  });

  test("chọn khóa → sang bước ②, đầu wizard ghi đúng khóa; quay về danh sách được", async ({ page }) => {
    await giaBackend(page, { cacLanGoi: [], ungVien: [] });
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    await page.getByRole("button", { name: "Lập BC2 mới" }).click();
    await page.getByTestId("khoa-K001").getByRole("button", { name: "Chọn khóa này →" }).click();
    await expect(page.getByTestId("dai-tom-tat")).toBeVisible();
    await expect(page.getByText(/Ô tô · Lập BC2 mới · Khóa B2-01\/2026/)).toBeVisible();
    await page.getByRole("button", { name: "← Danh sách BC2" }).click();
    await expect(page.getByRole("button", { name: "Lập BC2 mới" })).toBeVisible();
  });

  test("mô tô: khóa đã có BC2 đang mở → sang thêm học viên vào BC2 đó", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [] };
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    await page.getByRole("button", { name: "Mô tô" }).click();
    await page.getByRole("button", { name: "Lập BC2 mới" }).click();
    const k = page.getByTestId("khoa-M001");
    await expect(k.getByText("Đã có BC2 861/26-TTTĐ")).toBeVisible();
    await k.getByRole("button", { name: "Chọn khóa này →" }).click();
    await expect(page.getByText(/Khóa này đã có BC2 861\/26-TTTĐ/)).toBeVisible();
    await expect(page.getByText(/Thêm vào BC2 số 861\/26-TTTĐ/)).toBeVisible();
    expect(mo.cacLanGoi[0]).toContain("loai=moto");
  });

  test("công tắc Hiện khóa cũ gửi cu=true; Làm tươi gửi lam_tuoi=true", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [] };
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    await page.getByRole("button", { name: "Lập BC2 mới" }).click();
    await expect(page.getByTestId("khoa-K001")).toBeVisible();
    await page.getByLabel("Hiện khóa cũ").check();
    await expect.poll(() => mo.cacLanGoi.some((q) => q.includes("cu=true"))).toBe(true);
    await page.getByRole("button", { name: "Làm tươi" }).click();
    await expect.poll(() => mo.cacLanGoi.some((q) => q.includes("lam_tuoi=true"))).toBe(true);
  });
});

test.describe("TNB-04 — Lập BC2 bước ②: chọn học viên", () => {
  async function vaoBuoc2(page: Page, mo: Mo) {
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    await page.getByRole("button", { name: "Lập BC2 mới" }).click();
    await page.getByTestId("khoa-K001").getByRole("button", { name: "Chọn khóa này →" }).click();
    await expect(page.getByTestId("dai-tom-tat")).toBeVisible();
  }

  test("Sẵn sàng tích sẵn, Thi lại không tích; danh sách ảo chỉ dựng vài dòng của 3.450", async ({ page }) => {
    await vaoBuoc2(page, { cacLanGoi: [], ungVien: [] });
    await expect(page.getByTestId("dai-tom-tat")).toContainText("3.450");
    await expect(page.getByTestId("dai-tom-tat")).toContainText("+ 0");
    const dong = await page.getByRole("list", { name: "Sẵn sàng" }).getByRole("listitem").count();
    expect(dong).toBeGreaterThan(5);
    expect(dong).toBeLessThan(60);                          // KHÔNG dựng cả 3.450 dòng
    await expect(page.getByLabel("Chọn Học Viên 0000")).toBeChecked();
    await expect(page.getByText("Thi lại — 4 học viên từ các khóa trước")).toBeVisible();
  });

  test("thêm HV thi lại trong ngưỡng, chọn cả khóa gốc, bỏ chọn tất cả", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [] };
    await vaoBuoc2(page, mo);
    await page.getByRole("button", { name: /Thêm 3 HV thi lại ≤ 12 tháng/ }).click();
    await page.getByText("Khóa B2-12/2025").click();                    // mở khóa gốc để xem dòng
    if (process.env.CHUP_ANH) {
      for (const w of [800, 1280, 1440]) {
        await page.setViewportSize({ width: w, height: 900 });
        await page.screenshot({ path: `${process.env.CHUP_ANH}/${w}-buoc-2.png` });
      }
    }
    await expect(page.getByTestId("dai-tom-tat")).toContainText("3.450");
    await expect(page.getByTestId("dai-tom-tat")).toContainText("+ 3");
    await expect(page.getByText("3/3 đã chọn")).toBeVisible();
    await expect(page.getByText("0/1 đã chọn")).toBeVisible();
    await page.getByRole("button", { name: "Chọn cả khóa" }).click();     // khóa gốc cũ (1 HV)
    await expect(page.getByTestId("dai-tom-tat")).toContainText("+ 4");
    await page.getByRole("button", { name: "Bỏ chọn tất cả" }).click();
    await expect(page.getByTestId("dai-tom-tat")).toContainText("= 0");
    await expect(page.getByRole("button", { name: /Tiếp tục/ })).toBeDisabled();
  });

  test("đổi số tháng thi lại gửi thi_lai_thang mới và đếm lại", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [] };
    await vaoBuoc2(page, mo);
    await page.getByLabel("Số tháng thi lại").fill("2");
    await page.getByLabel("Số tháng thi lại").press("Enter");
    await expect.poll(() => mo.ungVien.some((q) => q.includes("thi_lai_thang=2"))).toBe(true);
    await expect(page.getByRole("button", { name: /Thêm 0 HV thi lại ≤ 2 tháng/ })).toBeVisible();
  });

  test("tìm + Enter tích đúng người; Cần xem có hướng xử lý, Không đưa được nêu lý do; Tiếp tục sang bước ③", async ({ page }) => {
    await vaoBuoc2(page, { cacLanGoi: [], ungVien: [] });
    await page.getByRole("button", { name: "Bỏ chọn tất cả" }).click();
    await page.getByLabel("Tìm học viên").fill("nguyen thi hoa");
    await page.getByLabel("Tìm học viên").press("Enter");
    await expect(page.getByTestId("dai-tom-tat")).toContainText("+ 1");
    await page.getByLabel("Tìm học viên").fill("");             // xóa ô tìm: lọc áp cho cả bốn nhóm
    await expect(page.getByTestId("dai-tom-tat")).toContainText("+ 1");
    await expect(page.getByText("Chưa tốt nghiệp — cần có giấy chứng nhận trước")).toBeVisible();
    await expect(page.getByText(/Cập nhật tốt nghiệp ở tab/)).toBeVisible();
    await page.getByText(/Không đưa được — 1 học viên/).click();
    await expect(page.getByText(/gỡ khỏi BC2 đó trước/).first()).toBeVisible();
    await page.getByRole("button", { name: /Tiếp tục/ }).click();
    await expect(page.getByText(/Bước 3 đang được dựng — đã chọn 1 học viên/)).toBeVisible();
  });
});

test.describe("TNB-03 — Tạo BC2 rỗng (form)", () => {
  async function vaoForm(page: Page, mo: Mo, moto = false) {
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    if (moto) await page.getByRole("button", { name: "Mô tô" }).click();
    await page.getByRole("button", { name: "Tạo BC2 rỗng" }).click();
    await page.getByTestId(moto ? "khoa-M001" : "khoa-K001").getByRole("button", { name: "Chọn khóa này →" }).click();
    await expect(page.getByLabel("Số BC2 (= mã báo cáo)")).toBeVisible();
  }
  async function xemLaiVaXacNhan(page: Page) {
    await page.getByRole("button", { name: "Xem lại" }).click();
    await page.getByLabel(/xác nhận đây là CSDL thật/).check();
  }

  test("số gợi ý điền sẵn, BC1 chỉ đọc; số trùng bị chặn ngay khi gõ và khóa nút Xem lại", async ({ page }) => {
    await vaoForm(page, { cacLanGoi: [], ungVien: [] });
    await expect(page.getByLabel("Số BC2 (= mã báo cáo)")).toHaveValue("81/2026");
    await expect(page.getByLabel("BC1 của khóa")).toHaveValue("112/BCI/2026");
    await expect(page.getByLabel("BC1 của khóa")).toBeDisabled();
    await expect(page.getByText("ngày 30/09/2026 · 150 học sinh")).toBeVisible();   // PRD: hiện số BC1, ngày, số HV
    if (process.env.CHUP_ANH) {
      for (const w of [800, 1280, 1440]) {
        await page.setViewportSize({ width: w, height: 800 });
        await page.screenshot({ path: `${process.env.CHUP_ANH}/${w}-form-bc2.png` });
      }
    }
    const xem = page.getByRole("button", { name: "Xem lại" });
    await expect(xem).toBeEnabled();
    await page.getByLabel("Số BC2 (= mã báo cáo)").fill("80/2026");
    await expect(page.getByText(/Số BC2 80\/2026 đã tồn tại/)).toBeVisible();
    await expect(xem).toBeDisabled();
    await page.getByLabel("Số BC2 (= mã báo cáo)").fill("861/26-ttđ");     // khác hoa thường và Ð/Đ vẫn trùng
    await expect(page.getByText(/đã tồn tại/)).toBeVisible();
    await page.getByLabel("Số BC2 (= mã báo cáo)").fill("1234567890123456");
    await expect(page.getByText(/tối đa 13 ký tự/)).toBeVisible();
    await expect(xem).toBeDisabled();
  });

  test("xem lại → tích CSDL thật → tạo → thêm học viên vào BC2 vừa tạo (vào thẳng bước ②)", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], taoBc2: [], taoKieu: "ok" };
    await vaoForm(page, mo);
    await page.getByRole("button", { name: "Xem lại" }).click();
    const tao = page.getByRole("button", { name: "Tạo BC2", exact: true });
    await expect(tao).toBeDisabled();                         // chưa tích CSDL thật
    await page.getByLabel(/xác nhận đây là CSDL thật/).check();
    await tao.click();
    await expect(page.getByText(/Đã tạo BC2/)).toBeVisible();
    expect(mo.taoBc2).toHaveLength(1);
    expect(mo.taoBc2![0]).toMatchObject({ ma_kh: "K001", so_bao_cao: "81/2026", xac_nhan_csdl_that: true, thu_lai: false });
    await page.getByRole("button", { name: "Thêm học viên vào BC2 này" }).click();
    await expect(page.getByTestId("dai-tom-tat")).toBeVisible();
    await expect.poll(() => mo.ungVien.some((q) => q.includes("ma_bc2=81%2F2026"))).toBe(true);
  });

  test("mô tô đã có BC2: phải tích đã xem cảnh báo mới tạo được", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], taoBc2: [], taoKieu: "ok" };
    await vaoForm(page, mo, true);
    await expect(page.getByText(/Khóa này đã có BC2 số 861\/26-TTTĐ/)).toBeVisible();
    await page.getByRole("button", { name: "Xem lại" }).click();
    await page.getByLabel(/xác nhận đây là CSDL thật/).check();
    const tao = page.getByRole("button", { name: "Tạo BC2", exact: true });
    await expect(tao).toBeDisabled();
    await page.getByLabel(/Tôi đã xem và vẫn muốn tạo thêm BC2/).check();
    await tao.click();
    await expect(page.getByText(/Đã tạo BC2/)).toBeVisible();
    expect(mo.taoBc2![0]).toMatchObject({ da_xem_canh_bao: true });
  });

  test("mất kết nối: Gửi lại mang thu_lai để không tạo đôi", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], taoBc2: [], taoKieu: "mat_ket_noi" };
    await vaoForm(page, mo);
    await xemLaiVaXacNhan(page);
    await page.getByRole("button", { name: "Tạo BC2", exact: true }).click();
    await expect(page.getByText(/Chưa biết BC2 đã được tạo hay chưa/)).toBeVisible();
    await page.getByRole("button", { name: "Gửi lại" }).click();
    await expect(page.getByText(/BC2 này đã được tạo từ trước/)).toBeVisible();   // da_ton_tai: không vỡ màn hình
    expect(mo.taoBc2).toHaveLength(2);
    expect(mo.taoBc2![0].thu_lai).toBe(false);
    expect(mo.taoBc2![1].thu_lai).toBe(true);
  });

  test("server báo trùng số (409): hiện lý do, không báo thành công", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], taoBc2: [], taoKieu: "trung" };
    await vaoForm(page, mo);
    await xemLaiVaXacNhan(page);
    await page.getByRole("button", { name: "Tạo BC2", exact: true }).click();
    await expect(page.getByRole("dialog").getByText(/đã tồn tại — đổi số khác/)).toBeVisible();
    await expect(page.getByText(/Đã tạo BC2/)).toHaveCount(0);
  });

  test("lỗi máy chủ 500 giữa chừng cũng coi là chưa biết đã tạo chưa: Gửi lại mang thu_lai", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], taoBc2: [], taoKieu: "loi_500" };
    await vaoForm(page, mo);
    await xemLaiVaXacNhan(page);
    await page.getByRole("button", { name: "Tạo BC2", exact: true }).click();
    await expect(page.getByText(/Chưa biết BC2 đã được tạo hay chưa/)).toBeVisible();
    await page.getByRole("button", { name: "Gửi lại" }).click();
    await expect(page.getByText(/BC2 này đã được tạo từ trước/)).toBeVisible();
    expect(mo.taoBc2![1].thu_lai).toBe(true);
  });

  test("xóa ngày báo cáo → khóa nút Xem lại", async ({ page }) => {
    await vaoForm(page, { cacLanGoi: [], ungVien: [] });
    await page.getByLabel("Ngày báo cáo").fill("");
    await expect(page.getByText("Cần nhập ngày báo cáo")).toBeVisible();
    await expect(page.getByRole("button", { name: "Xem lại" })).toBeDisabled();
  });
});
