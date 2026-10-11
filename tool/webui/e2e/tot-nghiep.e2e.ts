import { expect, test, type Page } from "@playwright/test";

// TNB-01 — luồng "Cập nhật tốt nghiệp ô tô theo lô": chọn khóa → đánh số liên tiếp → kiểm trùng → xem lại → ghi
// → lỗi giữa chừng → làm tiếp. Backend được giả bằng page.route; không đụng DB thật.

const HV = [
  ["C-0001", "Nguyễn Thị Hoà", "03", ""],
  ["C-0002", "Trần Văn Bình", "03", ""],
  ["C-0003", "Lê Đức Anh", "03", ""],
  ["C-0004", "Phạm Thị Ngọc Ánh", "03", ""],
  ["C-0005", "Đỗ Quang Huy", "09", "N1|7300"],
  ["C-0006", "Bùi Văn Sơn", "11", "N1|7301"],
].map(([ma_dk, ten, tt, so_giay], i) => ({
  ma_dk, ten, ngay_sinh: `0${i + 1}/05/1990`, cmt: `0792030${1000 + i}`, hang: "B2", tt,
  ma_bc2: tt === "11" ? "03/BCII/2026" : "", ma_kh: "K001",
  so_giay, so_so_tn: "", ngay_vao_so: "", so_quyet_dinh: "", ngay_ra_qd: "", ngay_in: "",
  trang_thai_tn: tt === "03" ? "chua_tot_nghiep" : tt === "09" ? "da_tot_nghiep" : "da_vao_bc2",
  ten_trang_thai: tt === "03" ? "Đã học xong, chưa tốt nghiệp" : tt === "09" ? "Đã tốt nghiệp, chờ lập BC2" : "Đã vào BC2, chờ kết quả",
  khoa_cu: false, sua_duoc: true, ly_do_khoa: "",
}));

interface Mo {
  kieuLo: "binh_thuong" | "loi_giua_chung" | "bi_gian_doan";
  loIdGhi: string[];
  poll: number;
  huy?: { loId: string; dsMaDk: string[] };
  bodyGhi?: { dong: { ma_dk: string; so_giay: string }[] };
}

async function giaBackend(page: Page, mo: Mo) {
  await page.addInitScript(() => localStorage.setItem("tool_session_token", "tok-test"));
  await page.route("**/local/auth/me", (r) => r.fulfill({ json: { username: "thu1", ho_ten: "Nhân viên thử", vai_tro: "operator" } }));
  await page.route("**/local/config/moi-truong", (r) => r.fulfill({ json: { thu_muc_ghi_duoc: true, duong_dan: "x", da_cau_hinh: true } }));
  await page.route("**/version", (r) => r.fulfill({ json: { build: "dev", commit: "x" } }));
  await page.route("**/local/tnbc2/khoa?**", (r) => r.fulfill({ json: {
    loai: "oto", hom_nay: "2026-10-11", moc_cua_so: "2025-09-11", so_giay_ke_tiep: "N1|7329",
    khoa: [{ ma_kh: "K001", ten_kh: "Khóa B2-01/2026", hang: "B2", ngay_kg: "2026-03-01", ngay_bg: "2026-09-20",
      ghi_duoc: true, khoa_cu: false, tong: 6, chua_tot_nghiep: 4, da_tot_nghiep: 1, da_vao_bc2: 1 }],
  } }));
  await page.route("**/local/tnbc2/tot-nghiep/hv?**", (r) => r.fulfill({ json: {
    ma_kh: "K001", ten_kh: "Khóa B2-01/2026", ngay_bg: "2026-09-20", ghi_duoc: true, khoa_cu: false,
    so_chung: { so_so_tn: "01/XNĐT/2026", ngay_vao_so: "2026-09-25", so_quyet_dinh: "100/TTTĐ", ngay_ra_qd: "2026-09-24", ngay_in: "", so_hv: 12 },
    so_giay_ke_tiep: "N1|7329", tong: 6, dem: { chua_tot_nghiep: 4, da_tot_nghiep: 1, da_vao_bc2: 1 }, hoc_vien: HV,
  } }));
  await page.route("**/local/tnbc2/tot-nghiep/xem-lai", async (r) => {
    const b = r.request().postDataJSON();
    const dem: Record<string, number> = {};
    b.dong.forEach((d: { so_giay: string }) => { if (d.so_giay) dem[d.so_giay] = (dem[d.so_giay] || 0) + 1; });
    const dong = b.dong.map((d: { ma_dk: string; so_giay: string }) => {
      const trung = d.so_giay && dem[d.so_giay] > 1;
      return { ma_dk: d.ma_dk, ket_qua: trung ? "chan" : d.so_giay ? "se_len_09" : "luu_so_truoc", ghi_duoc: !trung,
        chan: trung ? [{ muc: "chan", ma: "trung_trong_lo", noi_dung: `Số giấy ${d.so_giay} bị trùng trong danh sách đang nhập` }] : [],
        canh_bao: [], thong_tin: [] };
    });
    const dm: Record<string, number> = {};
    dong.forEach((d: { ket_qua: string }) => { dm[d.ket_qua] = (dm[d.ket_qua] || 0) + 1; });
    await r.fulfill({ json: { ma_kh: b.ma_kh, ghi_duoc_khoa: true, tong: dong.length, dem: dm,
      khoang_so: { tien_to: "N1|", tu: 7329, den: 7332, so_luong: 4 }, co_chan: false,
      canh_bao: b.chung.ngay_in ? [] : [{ ma: "thieu_ngay_in", noi_dung: "Chưa nhập ngày in giấy", so_dong: dong.length }], dong } });
  });
  await page.route("**/local/tnbc2/tot-nghiep/ghi", async (r) => {
    const b = r.request().postDataJSON();
    mo.loIdGhi.push(b.lo_id);
    mo.bodyGhi = b;
    mo.poll = 0;
    await r.fulfill({ json: { lo_id: b.lo_id, trang_thai: "dang_chay", xu_ly: 0, tong: b.dong.length, xong: false } });
  });
  await page.route("**/local/tnbc2/tot-nghiep/huy", async (r) => {
    const b = r.request().postDataJSON();
    mo.huy = { loId: b.lo_id, dsMaDk: b.ds_ma_dk };
    mo.poll = 0;
    await r.fulfill({ json: { lo_id: b.lo_id, trang_thai: "dang_chay", xu_ly: 0, tong: b.ds_ma_dk.length, xong: false } });
  });
  await page.route("**/local/tnbc2/bc2/lo/**", async (r) => {
    mo.poll++;
    if (mo.huy) {
      if (mo.poll === 1) return r.fulfill({ json: { lo_id: "x", trang_thai: "dang_chay", xu_ly: 0, tong: 1, xong: false } });
      return r.fulfill({ json: { lo_id: "x", trang_thai: "xong", xu_ly: 1, tong: 1, xong: true,
        da_huy: [{ ma_dk: "C-0005", so_giay_cu: "N1|7300" }], da_huy_truoc: [], bo_qua: [], chua_ghi: [], canh_bao: [], loi: null } });
    }
    const lanDau = mo.loIdGhi.length === 1;
    if (mo.poll === 1) return r.fulfill({ json: { lo_id: "x", trang_thai: "dang_chay", xu_ly: 1, tong: 4, xong: false } });
    if (lanDau && mo.kieuLo === "bi_gian_doan") {
      return r.fulfill({ json: { lo_id: "x", trang_thai: "dang_chay", xu_ly: 2, tong: 4, xong: false, bi_gian_doan: true,
        da_ghi: [{ ma_dk: "C-0003", ket_qua: "se_len_09" }, { ma_dk: "C-0001", ket_qua: "se_len_09" }] } });
    }
    if (lanDau && mo.kieuLo === "loi_giua_chung") {
      return r.fulfill({ json: { lo_id: "x", trang_thai: "loi_giua_chung", xu_ly: 3, tong: 4, xong: true,
        da_ghi: [{ ma_dk: "C-0003", ket_qua: "se_len_09" }, { ma_dk: "C-0001", ket_qua: "se_len_09" }],
        da_ghi_truoc: [], bo_qua: [], chua_ghi: ["C-0004", "C-0002"], canh_bao: [], dem: { se_len_09: 2 },
        loi: { ma_dk: "C-0004", noi_dung: "Mất kết nối SQL Server" } } });
    }
    if (mo.loIdGhi.length >= 2) {
      return r.fulfill({ json: { lo_id: "x", trang_thai: "xong", xu_ly: 2, tong: 2, xong: true,
        da_ghi: [{ ma_dk: "C-0004", ket_qua: "se_len_09" }, { ma_dk: "C-0002", ket_qua: "se_len_09" }],
        da_ghi_truoc: ["C-0003", "C-0001"], bo_qua: [], chua_ghi: [], canh_bao: [], dem: { se_len_09: 2 }, loi: null } });
    }
    return r.fulfill({ json: { lo_id: "x", trang_thai: "xong", xu_ly: 4, tong: 4, xong: true,
      da_ghi: HV.slice(0, 4).map((h) => ({ ma_dk: h.ma_dk, ket_qua: "se_len_09" })), da_ghi_truoc: [], bo_qua: [],
      chua_ghi: [], canh_bao: [], dem: { se_len_09: 4 }, loi: null } });
  });
}

async function datTichVaDanhSo(page: Page) {
  await page.goto("/tot-nghiep-bc2/tot-nghiep");
  await expect(page.getByText("Nguyễn Thị Hoà")).toBeVisible();
  await page.getByRole("button", { name: "Chọn học viên chưa có số giấy" }).click();
  await page.getByRole("button", { name: "Đánh liên tiếp" }).click();
}

test.describe("TNB-02 — sửa / hủy kết quả tốt nghiệp", () => {
  test("hủy tốt nghiệp: hộp nêu tên + số giấy, cần xác nhận CSDL thật, hủy xong báo kết quả", async ({ page }) => {
    const mo: Mo = { kieuLo: "binh_thuong", loIdGhi: [], poll: 0 };
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/tot-nghiep");
    await expect(page.getByText("Đỗ Quang Huy")).toBeVisible();
    const nutHuy = page.getByRole("button", { name: "Hủy tốt nghiệp", exact: true });
    await expect(nutHuy).toBeDisabled();                       // chưa chọn ai
    await page.getByLabel("Chọn Lê Đức Anh").check();          // HV chưa tốt nghiệp
    await page.getByLabel("Chọn Đỗ Quang Huy").check();
    await expect(nutHuy).toBeDisabled();                       // lẫn HV chưa tốt nghiệp → không hủy được
    await page.getByLabel("Chọn Lê Đức Anh").uncheck();
    await expect(nutHuy).toBeEnabled();
    await nutHuy.click();

    const hop = page.getByRole("dialog", { name: "Hủy kết quả tốt nghiệp" });
    await expect(hop.getByText("Đỗ Quang Huy")).toBeVisible();
    if (process.env.CHUP_ANH) await page.screenshot({ path: `${process.env.CHUP_ANH}/1280-huy-xac-nhan.png` });
    await expect(hop.getByText("N1|7300")).toBeVisible();
    const xacNhan = hop.getByRole("button", { name: "Hủy tốt nghiệp" });
    await expect(xacNhan).toBeDisabled();
    await hop.getByLabel(/xác nhận đây là CSDL thật/).check();
    await xacNhan.click();
    await expect(hop.getByText(/Đã hủy tốt nghiệp 1 học viên/)).toBeVisible();
    if (process.env.CHUP_ANH) await page.screenshot({ path: `${process.env.CHUP_ANH}/1280-huy-ket-qua.png` });
    expect(mo.huy?.dsMaDk).toEqual(["C-0005"]);
  });

  test("sửa nhầm: HV đã tốt nghiệp nhập lại số giấy, lượt ghi gửi số mới", async ({ page }) => {
    const mo: Mo = { kieuLo: "binh_thuong", loIdGhi: [], poll: 0 };
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/tot-nghiep");
    await page.getByLabel("Chọn Đỗ Quang Huy").check();
    await page.getByLabel("Số giấy của Đỗ Quang Huy").fill("N1|7310");
    await page.getByRole("button", { name: /Xem lại & ghi 1 học viên/ }).click();
    await page.getByLabel("Tôi đã xem các cảnh báo trên").check();
    await page.getByLabel(/xác nhận đây là CSDL thật/).check();
    await page.getByRole("button", { name: /^Ghi 1 học viên/ }).click();
    await expect(page.getByText("Kết quả ghi tốt nghiệp")).toBeVisible();
    expect(mo.bodyGhi?.dong).toEqual([{ ma_dk: "C-0005", so_giay: "N1|7310" }]);
  });
});

test.describe("TNB-01 — cập nhật tốt nghiệp ô tô theo lô", () => {
  test("happy path: điền sẵn sổ → đánh số liên tiếp theo tên → xem lại → ghi xong", async ({ page }) => {
    const mo: Mo = { kieuLo: "binh_thuong", loIdGhi: [], poll: 0 };
    await giaBackend(page, mo);
    await datTichVaDanhSo(page);
    // điền sẵn từ HV cùng khóa; số giấy đánh theo thứ tự tên (Lê, Nguyễn, Phạm, Trần)
    await expect(page.getByLabel("Số sổ tốt nghiệp")).toHaveValue("01/XNĐT/2026");
    await expect(page.getByLabel("Số giấy của Lê Đức Anh")).toHaveValue("N1|7329");
    await expect(page.getByLabel("Số giấy của Nguyễn Thị Hoà")).toHaveValue("N1|7330");
    await expect(page.getByLabel("Số giấy của Trần Văn Bình")).toHaveValue("N1|7332");
    // HV đã tốt nghiệp tích được (sửa nhầm / hủy) nhưng không bị đánh số đè; HV đã vào BC2 có giấy thì khóa
    await expect(page.getByLabel("Chọn Đỗ Quang Huy")).toBeEnabled();
    await expect(page.getByLabel("Chọn Đỗ Quang Huy")).not.toBeChecked();
    await expect(page.getByLabel("Chọn Bùi Văn Sơn")).toBeDisabled();
    await expect(page.getByText("gỡ khỏi BC2 trước")).toBeVisible();
    if (process.env.CHUP_ANH) await page.screenshot({ path: `${process.env.CHUP_ANH}/1280-khoa-da-vao-bc2.png` });

    await page.getByRole("button", { name: /Xem lại & ghi 4 học viên/ }).click();
    await expect(page.getByText("Cảnh báo", { exact: true })).toBeVisible();
    const ghi = page.getByRole("button", { name: /^Ghi 4 học viên/ });
    await expect(ghi).toBeDisabled();                       // chưa tích xác nhận
    await page.getByLabel("Tôi đã xem các cảnh báo trên").check();
    await page.getByLabel(/xác nhận đây là CSDL thật/).check();
    await ghi.click();
    await expect(page.getByText(/Đã ghi 4 học viên/)).toBeVisible();
    expect(mo.loIdGhi).toHaveLength(1);
  });

  test("trùng số giấy: báo ngay khi gõ, khóa nút Ghi, sửa xong mở lại", async ({ page }) => {
    await giaBackend(page, { kieuLo: "binh_thuong", loIdGhi: [], poll: 0 });
    await datTichVaDanhSo(page);
    const nut = page.getByRole("button", { name: /Xem lại & ghi/ });
    await expect(nut).toBeEnabled();
    await page.getByLabel("Số giấy của Trần Văn Bình").fill("N1|7329");   // trùng với Lê Đức Anh
    await expect(page.getByText("Số giấy bị trùng trong danh sách đang nhập").first()).toBeVisible();
    await expect(nut).toBeDisabled();
    await page.getByLabel("Số giấy của Trần Văn Bình").fill("N1|7340");
    await expect(nut).toBeEnabled();
  });

  test("lỗi giữa chừng: báo CHƯA ghi, Làm tiếp gửi lại cùng lô và không ghi lại HV đã ghi", async ({ page }) => {
    const mo: Mo = { kieuLo: "loi_giua_chung", loIdGhi: [], poll: 0 };
    await giaBackend(page, mo);
    await datTichVaDanhSo(page);
    await page.getByRole("button", { name: /Xem lại & ghi/ }).click();
    await page.getByLabel("Tôi đã xem các cảnh báo trên").check();
    await page.getByLabel(/xác nhận đây là CSDL thật/).check();
    await page.getByRole("button", { name: /^Ghi 4 học viên/ }).click();
    await expect(page.getByText(/CHƯA ghi 2 học viên/)).toBeVisible();
    await expect(page.getByText(/Mất kết nối SQL Server/)).toBeVisible();

    await page.getByRole("button", { name: "Làm tiếp" }).click();
    await expect(page.getByText(/đã ghi từ lần trước/)).toBeVisible();
    expect(mo.loIdGhi).toHaveLength(2);
    expect(mo.loIdGhi[1]).toBe(mo.loIdGhi[0]);              // cùng lo_id ⇒ server không ghi đôi
  });

  test("tool tắt giữa chừng (bi_gian_doan): hộp không treo, hiện Làm tiếp", async ({ page }) => {
    const mo: Mo = { kieuLo: "bi_gian_doan", loIdGhi: [], poll: 0 };
    await giaBackend(page, mo);
    await datTichVaDanhSo(page);
    await page.getByRole("button", { name: /Xem lại & ghi/ }).click();
    await page.getByLabel("Tôi đã xem các cảnh báo trên").check();
    await page.getByLabel(/xác nhận đây là CSDL thật/).check();
    await page.getByRole("button", { name: /^Ghi 4 học viên/ }).click();
    await expect(page.getByText(/Tool bị tắt giữa chừng/)).toBeVisible();
    await page.getByRole("button", { name: "Làm tiếp" }).click();
    await expect(page.getByText(/đã ghi từ lần trước/)).toBeVisible();
    expect(mo.loIdGhi[1]).toBe(mo.loIdGhi[0]);
  });
});
