import { expect, test, type Page } from "@playwright/test";

// KQD-08 — hộp thoại "Nạp giờ/km từ PDF DAT" ở màn Cập nhật KQĐT. Backend giả bằng page.route.
// Kiểm: chọn PDF → bảng xác nhận (cũ → mới, lý do không có trong khóa) → SỬA số ngay trong bảng
// (hh:mm → thập phân, tô "đã sửa", sai dạng chặn Lưu) → Lưu gửi đúng số đã sửa.

const KHOA = { ma_kh: "K40", ten_kh: "B01-K40", hang_gplx: "B", ngay_kg: "2026-07-30", ngay_bg: "2026-09-15", ngay_thi: "2026-09-20",
  dem: { dangky: 2, capnhat: 0, tuchoi: 0, giaitrinh: 0, ketxuat: 0 } };
const hv = (ma: string, ten: string, gio: number | null, km: number | null) => ({
  ma_dk: ma, ho_ten: ten, ngay_sinh: "01/01/2000", so_cccd: "0792" + ma, so_ho_so: ma, hang: "B.01", ma_hang_moi: "B.01", ma_hang: "B11",
  tt_xuly: "03", ket_luan: null, diem: { ly_thuyet: null, mo_phong: null, hinh: null, tien_lui: null, duong: null },
  gio_duong: gio, km_duong: km,
});
const dong = (o: Record<string, unknown>) => ({
  gio_cu: null, km_cu: null, co_thay_doi: true, chon_duoc: true, tick_san: true, canh_bao: [], ghi_chu: null, tinh_trang: "khop", ...o,
});
const XEM_TRUOC = {
  ma_kh: "K40", hang: "B.01", tong_file: 4,
  dong: [
    dong({ stt: 1, ma_dk: "A1", ho_ten: "NGUYỄN VĂN AN", gio_cu: 10, km_cu: 500, gio_moi: 16.32, km_moi: 725.63 }),
    dong({ stt: 2, ma_dk: "A2", ho_ten: "LÊ THỊ BÌNH", gio_moi: 11, km_moi: 600,
      canh_bao: [{ loai: "gio_duong", gia_tri: 11, goi_y: 12 }] }),
    dong({ stt: 3, ma_dk: "A3", ho_ten: "TRẦN VĂN CƯỜNG", gio_moi: null, km_moi: 0, tinh_trang: "chua_chay_dat", tick_san: false }),
    dong({ stt: 4, ma_dk: "Z9", ho_ten: "PHẠM THỊ DUNG", gio_moi: 20, km_moi: 800, tinh_trang: "khong_co_trong_khoa",
      chon_duoc: false, tick_san: false, co_thay_doi: false,
      ghi_chu: "Mã này đang thuộc khóa B01-K39 (K39) — học viên đã đổi khóa. Chọn đúng khóa đó để nạp." }),
  ],
  vang_trong_file: [{ ma_dk: "A5", ho_ten: "VÕ THỊ EM", so_cccd: "079200000005" }],
};

async function giaBackend(page: Page, luu: { body: unknown }) {
  await page.addInitScript(() => localStorage.setItem("tool_session_token", "tok-test"));
  await page.route("**/local/**", (r) => r.fulfill({ json: [] }));
  await page.route("**/local/auth/me", (r) => r.fulfill({ json: { username: "thu1", ho_ten: "Nhân viên thử", vai_tro: "operator" } }));
  await page.route("**/local/config/moi-truong", (r) => r.fulfill({ json: { thu_muc_ghi_duoc: true, duong_dan: "x", da_cau_hinh: true } }));
  await page.route("**/version", (r) => r.fulfill({ json: { build: "dev", commit: "x" } }));
  await page.route("**/local/sync/targets", (r) => r.fulfill({ json: { selected: "t1", targets: [{ key: "t1", name: "DB đích", database: "GPLX_CDB_CSDT", host: "x" }] } }));
  await page.route("**/local/ketqua/khoa?**", (r) => r.fulfill({ json: [KHOA] }));
  await page.route("**/local/ketqua/hoc-vien?**", (r) => r.fulfill({ json: [hv("A1", "NGUYỄN VĂN AN", 10, 500), hv("A2", "LÊ THỊ BÌNH", null, null)] }));
  await page.route("**/local/ketqua/chuong-trinh?**", (r) => r.fulfill({ json: { ma_kh: "K40", ct: "cu" } }));
  await page.route("**/local/ketqua/luat", (r) => r.fulfill({ json: { mon_bat_buoc: ["ly_thuyet", "mo_phong", "hinh", "tien_lui", "duong"] } }));
  await page.route("**/local/ketqua/dat/xem-truoc**", (r) => r.fulfill({ json: XEM_TRUOC }));
  await page.route("**/local/ketqua/dat/luu**", (r) => {
    luu.body = r.request().postDataJSON();
    const n = (luu.body as { dong: unknown[] }).dong.length;
    return r.fulfill({ json: { ok: true, da_luu: n, bo_qua: [] } });
  });
}

async function moHopThoai(page: Page) {
  await page.goto("/ket-qua/cap-nhat");
  await page.getByPlaceholder("Gõ tên khóa hoặc MaKH…").click();
  await page.getByText("B01-K40").first().click();
  await page.getByRole("button", { name: /Nạp giờ\/km từ PDF DAT/ }).click();
  await page.locator('input[type="file"]').setInputFiles({ name: "DAT B.01-K40.pdf", mimeType: "application/pdf", buffer: Buffer.from("%PDF-1.4 gia") });
}

test("xem trước: cũ → mới, lý do không có trong khóa, dòng chưa chạy DAT bỏ tick", async ({ page }) => {
  await giaBackend(page, { body: null });
  await moHopThoai(page);
  const bang = page.getByRole("dialog").or(page.locator("div.fixed.inset-0"));
  await expect(bang.getByText("NGUYỄN VĂN AN")).toBeVisible();
  await expect(bang.getByText("Mã này đang thuộc khóa B01-K39 (K39)")).toBeVisible();
  await expect(bang.getByText("⚠ Chưa chạy DAT")).toBeVisible();
  await expect(bang.getByText("1 học viên của khóa không có trong file")).toBeVisible();
  // 2 dòng tick sẵn (A1, A2); A3 chưa chạy DAT bỏ tick; Z9 không tick được
  await expect(bang.getByRole("button", { name: "Lưu 2 học viên" })).toBeEnabled();
  // số mới nằm trong ô sửa được: 16,32 và 725,63
  const dongAn = bang.locator("tr", { hasText: "NGUYỄN VĂN AN" });
  await expect(dongAn.locator("input").nth(1)).toHaveValue("16,32");
  await expect(dongAn.locator("input").nth(2)).toHaveValue("725,63");
});

test("sửa số ngay trong bảng: hh:mm → thập phân, tô 'đã sửa', sai dạng chặn Lưu, Lưu gửi số đã sửa", async ({ page }) => {
  const luu = { body: null as unknown };
  await giaBackend(page, luu);
  await moHopThoai(page);
  const bang = page.locator("div.fixed.inset-0");
  const dongAn = bang.locator("tr", { hasText: "NGUYỄN VĂN AN" });
  const gio = dongAn.locator("input").nth(1), km = dongAn.locator("input").nth(2);

  await gio.fill("20:30");
  await gio.blur();
  await expect(gio).toHaveValue("20,5");                       // hh:mm → thập phân
  await expect(dongAn.getByText("đã sửa so với PDF")).toBeVisible();

  await gio.fill("20:75");                                      // phút ≥ 60 → sai dạng
  await gio.blur();
  await expect(bang.getByRole("button", { name: "Lưu 2 học viên" })).toBeDisabled();

  await gio.fill("20:30");
  await gio.blur();
  await km.fill("1.008,19");
  await expect(bang.getByRole("button", { name: "Lưu 2 học viên" })).toBeEnabled();
  await bang.getByRole("button", { name: "Lưu 2 học viên" }).click();

  await expect(page.getByText(/Đã lưu giờ\/km đường cho 2 học viên/)).toBeVisible();
  const body = luu.body as { ma_kh: string; dong: { ma_dk: string; gio_duong: number; km_duong: number }[] };
  expect(body.ma_kh).toBe("K40");
  expect(body.dong.find((d) => d.ma_dk === "A1")).toEqual({ ma_dk: "A1", gio_duong: 20.5, km_duong: 1008.19 });
  expect(body.dong.find((d) => d.ma_dk === "A2")).toEqual({ ma_dk: "A2", gio_duong: 11, km_duong: 600 });
  expect(body.dong.find((d) => d.ma_dk === "A3")).toBeUndefined();   // chưa chạy DAT không bị ghi
});


// =============================================================================
// Bổ sung sau /kiemthu (12/10/2026) — E5…E9 hộp thoại nạp PDF DAT (KQD-08)
// =============================================================================
const bangModal = (page: Page) => page.locator("div.fixed.inset-0");
const nutLuuModal = (page: Page, n: number) => bangModal(page).getByRole("button", { name: `Lưu ${n} học viên` });

/** Mở màn + chọn khóa + mở hộp thoại (chưa chọn file). */
async function moHopThoaiRong(page: Page) {
  await page.goto("/ket-qua/cap-nhat");
  await page.getByPlaceholder("Gõ tên khóa hoặc MaKH…").click();
  await page.getByText("B01-K40").first().click();
  await page.getByRole("button", { name: /Nạp giờ\/km từ PDF DAT/ }).click();
}
async function chonFile(page: Page, f: { name: string; buffer: Buffer }) {
  await page.locator('input[type="file"]').setInputFiles({ name: f.name, mimeType: "application/pdf", buffer: f.buffer });
}
const PDF_GIA = { name: "DAT B.01-K40.pdf", buffer: Buffer.from("%PDF-1.4 gia") };

test.describe("KQD-08 — hộp thoại nạp PDF DAT: chặn sớm, lưu xong, lỗi, biên, tick", () => {
  test("E5 sai khóa → banner đỏ, không có bảng; .xlsx và > 5 MB chặn ngay ở client (không gọi API)", async ({ page }) => {
    let goiXemTruoc = 0;
    await giaBackend(page, { body: null });
    await page.route("**/local/ketqua/dat/xem-truoc**", (r) => {
      goiXemTruoc += 1;
      return r.fulfill({ status: 400, json: { detail: "File thuộc khóa K39 (75032K260002), khác khóa đang chọn (K40). Chọn đúng file của khóa này." } });
    });
    await moHopThoaiRong(page);

    await chonFile(page, { name: "bao-cao.xlsx", buffer: Buffer.from("PK") });
    await expect(bangModal(page).getByText("Chỉ nhận file PDF báo cáo DAT.")).toBeVisible();
    await chonFile(page, { name: "to.pdf", buffer: Buffer.alloc(5 * 1024 * 1024 + 1, 0x30) });
    await expect(bangModal(page).getByText("File quá lớn (tối đa 5 MB).")).toBeVisible();
    expect(goiXemTruoc).toBe(0);

    await chonFile(page, PDF_GIA);
    await expect(bangModal(page).getByText(/khác khóa đang chọn \(K40\)/)).toBeVisible();
    expect(goiXemTruoc).toBe(1);
    await expect(bangModal(page).locator("table")).toHaveCount(0);
    await expect(bangModal(page).getByRole("button", { name: /^Lưu \d+ học viên$/ })).toBeDisabled();
  });

  test("E6 lưu xong: toast đã lưu X · bỏ qua Y, đóng hộp thoại, lưới tải lại, nháp HV khác còn, ô HV vừa ghi lấy số đã lưu", async ({ page }) => {
    let taiLai = 0;
    await giaBackend(page, { body: null });
    await page.route("**/local/ketqua/hoc-vien?**", (r) => {
      taiLai += 1;
      return r.fulfill({ json: [hv("A1", "NGUYỄN VĂN AN", 10, 500), hv("A2", "LÊ THỊ BÌNH", null, null), hv("A9", "ĐẶNG VĂN GIANG", null, null)] });
    });
    await page.route("**/local/ketqua/dat/luu**", (r) =>
      r.fulfill({ json: { ok: true, da_luu: 2, bo_qua: [{ ma_dk: "Z", ly_do: "Không thuộc khóa này hoặc đã kết xuất/hoàn thành (12/13)." }] } }));
    await page.goto("/ket-qua/cap-nhat");
    await page.getByPlaceholder("Gõ tên khóa hoặc MaKH…").click();
    await page.getByText("B01-K40").first().click();
    await expect(page.getByText("ĐẶNG VĂN GIANG")).toBeVisible();
    // nháp dở: điểm của HV không có trong file + giờ của A1 (sẽ bị nạp đè)
    await page.locator("tr", { hasText: "ĐẶNG VĂN GIANG" }).locator('input[data-kqd-c="2"]').fill("77");
    await page.locator("tr", { hasText: "NGUYỄN VĂN AN" }).locator('input[data-kqd-c="5"]').fill("9");

    await page.getByRole("button", { name: /Nạp giờ\/km từ PDF DAT/ }).click();
    await chonFile(page, PDF_GIA);
    await nutLuuModal(page, 2).click();

    await expect(page.getByText(/Đã lưu giờ\/km đường cho 2 học viên · bỏ qua 1/)).toBeVisible();
    await expect(page.getByText("Nạp giờ/km thực hành đường từ PDF DAT")).toHaveCount(0);   // hộp thoại đã đóng
    expect(taiLai).toBeGreaterThanOrEqual(2);                       // lần đầu + sau khi nạp
    await expect(page.locator("tr", { hasText: "ĐẶNG VĂN GIANG" }).locator('input[data-kqd-c="2"]')).toHaveValue("77");
    await expect(page.locator("tr", { hasText: "NGUYỄN VĂN AN" }).locator('input[data-kqd-c="5"]')).toHaveValue("16,32");
  });

  test("E7 lưu lỗi 502: hộp thoại giữ bảng + số đã sửa để thử lại, không đóng", async ({ page }) => {
    await giaBackend(page, { body: null });
    await page.route("**/local/ketqua/dat/luu**", (r) =>
      r.fulfill({ status: 502, json: { detail: "Không ghi được giờ/km — kiểm kết nối rồi thử lại, chưa có dòng nào được lưu." } }));
    await moHopThoai(page);
    const gio = bangModal(page).locator("tr", { hasText: "NGUYỄN VĂN AN" }).locator("input").nth(1);
    await gio.fill("20:30"); await gio.blur();
    await nutLuuModal(page, 2).click();
    await expect(bangModal(page).getByText(/chưa có dòng nào được lưu/)).toBeVisible();
    await expect(bangModal(page).locator("table")).toBeVisible();
    await expect(gio).toHaveValue("20,5");
    await expect(nutLuuModal(page, 2)).toBeEnabled();               // bấm lại được
  });

  test("E8 biên ô sửa: giờ 999 qua / 999,01 chặn · km 99.999 qua / 100.000 chặn · xóa trống chặn · sửa về số PDF thì hết nhãn đã sửa", async ({ page }) => {
    await giaBackend(page, { body: null });
    await moHopThoai(page);
    const dongAn = bangModal(page).locator("tr", { hasText: "NGUYỄN VĂN AN" });
    const gio = dongAn.locator("input").nth(1), km = dongAn.locator("input").nth(2);
    const luu = nutLuuModal(page, 2);

    await gio.fill("999"); await gio.blur();
    await expect(luu).toBeEnabled();
    await gio.fill("999,01"); await gio.blur();
    await expect(luu).toBeDisabled();
    await gio.fill("16,32"); await gio.blur();
    await expect(luu).toBeEnabled();

    await km.fill("99.999");
    await expect(luu).toBeEnabled();
    await km.fill("100.000");
    await expect(luu).toBeDisabled();
    await km.fill("");
    await expect(luu).toBeDisabled();                               // trống mà đang tick → chặn, không ghi số đoán

    await km.fill("700,5");
    await expect(dongAn.getByText("đã sửa so với PDF")).toBeVisible();
    await km.fill("725,63");                                        // về đúng số PDF
    await expect(dongAn.getByText("đã sửa so với PDF")).toHaveCount(0);
    await expect(luu).toBeEnabled();
  });

  test("E9 tick: chọn tất cả / bỏ hết đổi 'Lưu N'; dòng 🔒/không có/trùng/sai dạng khóa ô tick; đếm 'dòng lỗi' = sai dạng + trùng", async ({ page }) => {
    await giaBackend(page, { body: null });
    const nhieu = {
      ma_kh: "K40", hang: "B.01", tong_file: 6,
      dong: [
        dong({ stt: 1, ma_dk: "A1", ho_ten: "NGUYỄN VĂN AN", gio_cu: 10, km_cu: 500, gio_moi: 16.32, km_moi: 725.63 }),
        dong({ stt: 2, ma_dk: "A2", ho_ten: "LÊ THỊ BÌNH", gio_moi: 18, km_moi: 700, tick_san: false }),
        dong({ stt: 3, ma_dk: "K1", ho_ten: "ĐÃ KẾT XUẤT", gio_moi: 20, km_moi: 800, tinh_trang: "da_ket_xuat", chon_duoc: false, tick_san: false }),
        dong({ stt: 4, ma_dk: "Z9", ho_ten: "KHÔNG CÓ TRONG KHÓA", gio_moi: 20, km_moi: 800, tinh_trang: "khong_co_trong_khoa", chon_duoc: false, tick_san: false }),
        dong({ stt: 5, ma_dk: "L1", ho_ten: "SAI DẠNG", gio_moi: null, km_moi: null, tinh_trang: "loi_dong", chon_duoc: false, tick_san: false, ghi_chu: "Giờ 20:75 sai dạng." }),
        dong({ stt: 6, ma_dk: "A1", ho_ten: "NGUYỄN VĂN AN", gio_moi: 17, km_moi: 730, tinh_trang: "trung_dong", chon_duoc: false, tick_san: false }),
      ],
      vang_trong_file: [],
    };
    await page.route("**/local/ketqua/dat/xem-truoc**", (r) => r.fulfill({ json: nhieu }));
    await moHopThoai(page);
    const b = bangModal(page);
    await expect(nutLuuModal(page, 1)).toBeEnabled();               // chỉ A1 tick sẵn

    for (const ten of ["ĐÃ KẾT XUẤT", "KHÔNG CÓ TRONG KHÓA", "SAI DẠNG"]) {
      await expect(b.locator("tr", { hasText: ten }).locator('input[type="checkbox"]')).toBeDisabled();
    }
    await expect(b.locator("tr", { hasText: "NGUYỄN VĂN AN" }).nth(1).locator('input[type="checkbox"]')).toBeDisabled(); // dòng trùng
    await expect(b.locator("span", { hasText: /^2\s*dòng lỗi$/ })).toBeVisible();                                  // sai dạng + trùng

    const tatCa = b.locator("thead").locator('input[type="checkbox"]');
    await tatCa.check();
    await expect(nutLuuModal(page, 2)).toBeEnabled();               // A1 + A2
    await tatCa.uncheck();
    await expect(nutLuuModal(page, 0)).toBeDisabled();
  });

  test("E12 tick tay dòng chưa chạy DAT → điền sẵn 0 giờ, Lưu được và ghi 0/0; bỏ tick thì không ghi", async ({ page }) => {
    const luu = { body: null as unknown };
    await giaBackend(page, luu);
    await moHopThoai(page);
    const b = bangModal(page);
    const dongA3 = b.locator("tr", { hasText: "TRẦN VĂN CƯỜNG" });
    await expect(dongA3.locator("input").nth(1)).toHaveValue("");           // chưa tick: giờ trống
    await dongA3.locator('input[type="checkbox"]').check();
    await expect(dongA3.locator("input").nth(1)).toHaveValue("0");          // tick tay → điền sẵn 0
    await expect(dongA3.locator("input").nth(2)).toHaveValue("0");
    await expect(nutLuuModal(page, 3)).toBeEnabled();
    await nutLuuModal(page, 3).click();
    await expect(page.getByText(/Đã lưu giờ\/km đường cho 3 học viên/)).toBeVisible();
    const body = luu.body as { dong: { ma_dk: string; gio_duong: number; km_duong: number }[] };
    expect(body.dong.find((d) => d.ma_dk === "A3")).toEqual({ ma_dk: "A3", gio_duong: 0, km_duong: 0 });
  });
});
