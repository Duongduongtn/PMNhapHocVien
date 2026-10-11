import { expect, test, type Page } from "@playwright/test";

// TNB-06 — Cứu trạng thái (tab "Học viên không tìm thấy"): tìm → lý do không hiện → chọn đích + lý do → xem lại
// "cũ → mới" → chuyển → hoàn tác một lần. Backend giả bằng page.route; không đụng DB thật.

interface Mo {
  tim: string[];
  chuyen: Record<string, unknown>[];
  hoanTac: Record<string, unknown>[];
  chuyenKieu?: "ok" | "mat_ket_noi" | "mat_ket_noi_roi_tu_choi";
  hoanTacKieu?: "ok" | "da_bi_doi" | "mat_ket_noi";
}

const dich = (ma: string, ten: string, cho = true, lyDo = "") => ({ ma, ten, cho_phep: cho, ly_do: lyDo });
const DICH_DU = [
  dich("09", "Đã tốt nghiệp, chờ lập BC2"),
  dich("14", "Chưa đạt BC2 — cần lập lại"),
  dich("17", "Thi sát hạch chưa đạt"),
  dich("18", "Vắng sát hạch"),
];
const hv = (ma_dk: string, ten: string, ex: Record<string, unknown>) => ({
  ma_dk, so_ho_so: "00001", ten, ngay_sinh: "01/05/1990", cmt: `0792030${ma_dk.replace(/\D/g, "").padStart(5, "0")}`,
  hang: "B2", tt: "13", ma_bc2: "", ma_kh: "K001", so_giay: "N1|7300", ten_kh: "Khóa B2-01/2026", bg: "2026-09-20",
  loai: "oto", khac_loai: false, ten_trang_thai: "Đã có kết quả cuối",
  khong_hien: { ma: "trang_thai_ngoai_tap", noi_dung: "Trạng thái \"Đã có kết quả cuối\" chưa nằm trong nhóm chờ lập BC2", goi_y_xu_ly: "cuu_trang_thai" },
  dich: DICH_DU, cuu_duoc: true, ...ex,
});
const DS = [
  hv("C-0001", "Nguyễn Văn An", {}),
  hv("C-0002", "Trần Thị Bình", {
    tt: "16", ten_trang_thai: "Đã có kết quả cuối",
    khong_hien: { ma: "co_ket_qua_cuoi", noi_dung: "Đã có kết quả cuối (đạt sát hạch)" },
    dich: DICH_DU.map((d) => ({ ...d, cho_phep: false, ly_do: "Không chuyển được vì đã đạt sát hạch" })), cuu_duoc: false,
  }),
  hv("C-0003", "Lê Văn Cường", {
    tt: "03", ten_trang_thai: "Đã học xong, chưa tốt nghiệp", so_giay: "",
    khong_hien: { ma: "chua_tot_nghiep", noi_dung: "Chưa tốt nghiệp — cần có giấy chứng nhận trước", goi_y_xu_ly: "cap_nhat_tot_nghiep" },
    dich: [dich("09", "Đã tốt nghiệp, chờ lập BC2", false, "Đích \"Đã tốt nghiệp\" cần học viên đã có số giấy chứng nhận"),
      ...DICH_DU.slice(1)],
  }),
  hv("C-0005", "Hoàng Văn Em", {
    tt: "03", ten_trang_thai: "Đã học xong, chưa tốt nghiệp", ma_kh: "K999", ten_kh: "Khóa B2-12/2026", bg: "2026-12-30",
    khong_hien: { ma: "khoa_chua_be_giang", noi_dung: "Khóa Khóa B2-12/2026 chưa bế giảng (30/12/2026)" },
    dich: DICH_DU.slice(1),
  }),
  hv("C-0004", "Phạm Văn Dũng", {
    tt: "14", ten_trang_thai: "Chưa đạt BC2 — cần lập lại",
    khong_hien: { ma: "dang_hien", noi_dung: "Đang có trong danh sách (nhóm thi_lai)", nhom: "thi_lai" },
    dich: DICH_DU.map((d) => (d.ma === "14" ? { ...d, cho_phep: false, ly_do: "Học viên đang ở trạng thái này" } : d)),
  }),
];

async function giaBackend(page: Page, mo: Mo) {
  await page.addInitScript(() => localStorage.setItem("tool_session_token", "tok-test"));
  await page.route("**/local/auth/me", (r) => r.fulfill({ json: { username: "thu1", ho_ten: "Nhân viên thử", vai_tro: "operator" } }));
  await page.route("**/local/config/moi-truong", (r) => r.fulfill({ json: { thu_muc_ghi_duoc: true, duong_dan: "x", da_cau_hinh: true } }));
  await page.route("**/version", (r) => r.fulfill({ json: { build: "dev", commit: "x" } }));
  await page.route("**/local/tnbc2/cuu/tim?**", async (r) => {
    const u = new URL(r.request().url());
    mo.tim.push(u.search);
    const loai = u.searchParams.get("loai") || "";
    const ds = DS.map((h) => (loai === "moto" ? { ...h, khac_loai: true, cuu_duoc: false } : h));
    await r.fulfill({ json: { q: u.searchParams.get("q"), loai, tong_khop: ds.length, hien_toi_da: 50, hoc_vien: ds } });
  });
  await page.route("**/local/tnbc2/cuu/chuyen", async (r) => {
    const b = r.request().postDataJSON();
    mo.chuyen.push(b);
    if ((mo.chuyenKieu === "mat_ket_noi" || mo.chuyenKieu === "mat_ket_noi_roi_tu_choi") && mo.chuyen.length === 1) {
      return r.abort("connectionreset");
    }
    if (mo.chuyenKieu === "mat_ket_noi_roi_tu_choi") {
      return r.fulfill({ status: 409, json: { detail: { ma: "khong_cuu_duoc", noi_dung: "Trạng thái mới trùng trạng thái hiện tại" } } });
    }
    await r.fulfill({ json: { lo_id: b.lo_id, ma_dk: b.ma_dk, tt_cu: "03", tt_moi: b.dich, ten_trang_thai_cu: "Đã học xong, chưa tốt nghiệp",
      ten_trang_thai_moi: "Chưa đạt BC2 — cần lập lại", ly_do: b.ly_do, canh_bao: [], trang_thai: "xong",
      da_ton_tai: mo.chuyen.length > 1 } });
  });
  await page.route("**/local/tnbc2/cuu/hoan-tac", async (r) => {
    const b = r.request().postDataJSON();
    mo.hoanTac.push(b);
    if (mo.hoanTacKieu === "mat_ket_noi" && mo.hoanTac.length === 1) return r.abort("connectionreset");
    if (mo.hoanTacKieu === "da_bi_doi") {
      return r.fulfill({ status: 409, json: { detail: { ma: "da_bi_doi", noi_dung: "Học viên đã bị phần mềm cũ đổi trạng thái sau khi chuyển — không hoàn tác được" } } });
    }
    await r.fulfill({ json: { lo_id: b.lo_id, ma_dk: "C-0003", tt_cu: "14", tt_moi: "03", lo_goc: b.lo_id_cuu,
      ten_trang_thai_moi: "Đã học xong, chưa tốt nghiệp", canh_bao: [], trang_thai: "xong" } });
  });
}

async function timVaChon(page: Page, mo: Mo, ten = "Lê Văn Cường") {
  await giaBackend(page, mo);
  await page.goto("/tot-nghiep-bc2/cuu-trang-thai");
  await page.getByLabel(/Tìm học viên không thấy/).fill("van");
  await page.getByRole("button", { name: "Tìm", exact: true }).click();
  await page.getByRole("button", { name: `Chuyển trạng thái ${ten}` }).click();
}

test.describe("TNB-06 — Cứu trạng thái học viên", () => {
  test("tìm: nói rõ vì sao không thấy; HV đã đạt/đang có trong danh sách không có nút chuyển; < 2 ký tự bị báo", async ({ page }) => {
    const mo: Mo = { tim: [], chuyen: [], hoanTac: [] };
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/cuu-trang-thai");
    await expect(page.getByText(/Gõ tên hoặc số CMT để tìm/)).toBeVisible();
    await page.getByLabel(/Tìm học viên không thấy/).fill("a");
    await page.getByRole("button", { name: "Tìm", exact: true }).click();
    await expect(page.getByText("Nhập ít nhất 2 ký tự để tìm")).toBeVisible();
    expect(mo.tim).toHaveLength(0);

    await page.getByLabel(/Tìm học viên không thấy/).fill("van");
    await page.getByLabel(/Tìm học viên không thấy/).press("Enter");
    await expect(page.getByText(/chưa nằm trong nhóm chờ lập BC2/)).toBeVisible();
    await expect(page.getByText("Đã có kết quả cuối (đạt sát hạch)")).toBeVisible();
    await expect(page.getByText(/Đang có trong danh sách/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Chuyển trạng thái Nguyễn Văn An" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Chuyển trạng thái Trần Thị Bình" })).toHaveCount(0);   // đã đạt sát hạch
    await expect(page.getByRole("button", { name: "Chuyển trạng thái Phạm Văn Dũng" })).toHaveCount(0);   // đã đủ điều kiện
  });

  test("đích 09 thiếu số giấy bị khóa kèm lý do; thiếu lý do thì chưa Xem lại được", async ({ page }) => {
    const mo: Mo = { tim: [], chuyen: [], hoanTac: [] };
    await timVaChon(page, mo);
    const panel = page.getByRole("complementary", { name: "Chuyển trạng thái học viên" });
    await expect(panel.getByText(/cần học viên đã có số giấy chứng nhận/)).toBeVisible();
    await expect(panel.getByRole("radio", { name: /Đã tốt nghiệp, chờ lập BC2/ })).toBeDisabled();
    await panel.getByRole("radio", { name: /Chưa đạt BC2/ }).check();
    await expect(panel.getByRole("button", { name: "Xem lại" })).toBeDisabled();          // chưa nhập lý do
    await panel.getByLabel(/Lý do/).fill("Nhập nhầm trạng thái vắng, học viên thực tế đã thi");
    await expect(panel.getByRole("button", { name: "Xem lại" })).toBeEnabled();
    await panel.getByLabel(/Lý do/).fill("   ");                                           // chỉ có khoảng trắng
    await expect(panel.getByRole("button", { name: "Xem lại" })).toBeDisabled();
  });

  test("xem lại 'cũ → mới' + lý do, cần tích CSDL thật, chuyển xong có Hoàn tác một lần", async ({ page }) => {
    const mo: Mo = { tim: [], chuyen: [], hoanTac: [] };
    await timVaChon(page, mo);
    const panel = page.getByRole("complementary", { name: "Chuyển trạng thái học viên" });
    await panel.getByRole("radio", { name: /Chưa đạt BC2/ }).check();
    await panel.getByLabel(/Lý do/).fill("Nhập nhầm trạng thái vắng");
    if (process.env.CHUP_ANH) {
      for (const w of [800, 1280, 1440]) {
        await page.setViewportSize({ width: w, height: 800 });
        await page.screenshot({ path: `${process.env.CHUP_ANH}/${w}-cuu-trang-thai.png` });
      }
    }
    await panel.getByRole("button", { name: "Xem lại" }).click();
    const hop = page.getByRole("dialog", { name: "Xác nhận chuyển trạng thái" });
    await expect(hop.getByText("Đã học xong, chưa tốt nghiệp")).toBeVisible();
    await expect(hop.getByText("Chưa đạt BC2 — cần lập lại")).toBeVisible();
    await expect(hop.getByText(/Nhập nhầm trạng thái vắng/)).toBeVisible();
    const chuyen = hop.getByRole("button", { name: "Chuyển", exact: true });
    await expect(chuyen).toBeDisabled();
    await hop.getByLabel(/xác nhận đây là CSDL thật/).check();
    await chuyen.click();
    await expect(panel.getByText(/Đã chuyển/)).toBeVisible();
    expect(mo.chuyen[0]).toMatchObject({ ma_dk: "C-0003", dich: "14", ly_do: "Nhập nhầm trạng thái vắng", xac_nhan_csdl_that: true });
    expect(mo.tim.length).toBeGreaterThanOrEqual(2);                                      // làm tươi kết quả sau khi chuyển

    await panel.getByRole("button", { name: "Hoàn tác" }).click();
    await expect(panel.getByText(/Đã hoàn tác về "Đã học xong, chưa tốt nghiệp"/)).toBeVisible();
    expect(mo.hoanTac[0]).toMatchObject({ lo_id_cuu: mo.chuyen[0].lo_id, xac_nhan_csdl_that: true });
    await expect(panel.getByRole("button", { name: "Hoàn tác" })).toHaveCount(0);          // chỉ một lần
  });

  test("học viên đã bị phần mềm cũ đổi tiếp: hoàn tác bị từ chối kèm lý do", async ({ page }) => {
    const mo: Mo = { tim: [], chuyen: [], hoanTac: [], hoanTacKieu: "da_bi_doi" };
    await timVaChon(page, mo);
    const panel = page.getByRole("complementary", { name: "Chuyển trạng thái học viên" });
    await panel.getByRole("radio", { name: /Thi sát hạch chưa đạt/ }).check();
    await panel.getByLabel(/Lý do/).fill("Rớt sát hạch nhập nhầm");
    await panel.getByRole("button", { name: "Xem lại" }).click();
    await page.getByRole("dialog").getByLabel(/xác nhận đây là CSDL thật/).check();
    await page.getByRole("dialog").getByRole("button", { name: "Chuyển", exact: true }).click();
    await panel.getByRole("button", { name: "Hoàn tác" }).click();
    await expect(panel.getByText(/đã bị phần mềm cũ đổi trạng thái/)).toBeVisible();
    await expect(panel.getByText(/Đã hoàn tác về/)).toHaveCount(0);
  });

  test("mất kết nối khi chuyển: Gửi lại cùng lo_id (không chuyển hai lần)", async ({ page }) => {
    const mo: Mo = { tim: [], chuyen: [], hoanTac: [], chuyenKieu: "mat_ket_noi" };
    await timVaChon(page, mo);
    const panel = page.getByRole("complementary", { name: "Chuyển trạng thái học viên" });
    await panel.getByRole("radio", { name: /Vắng sát hạch/ }).check();
    await panel.getByLabel(/Lý do/).fill("Vắng nhập nhầm");
    await panel.getByRole("button", { name: "Xem lại" }).click();
    const hop = page.getByRole("dialog");
    await hop.getByLabel(/xác nhận đây là CSDL thật/).check();
    await hop.getByRole("button", { name: "Chuyển", exact: true }).click();
    await expect(hop.getByText(/Chưa biết đã chuyển được hay chưa/)).toBeVisible();
    await hop.getByRole("button", { name: "Gửi lại" }).click();
    await expect(panel.getByText(/Đã chuyển/)).toBeVisible();
    expect(mo.chuyen).toHaveLength(2);
    expect(mo.chuyen[1].lo_id).toBe(mo.chuyen[0].lo_id);
  });

  test("chọn loại hạng khác: học viên khác loại bị báo và không có nút chuyển", async ({ page }) => {
    const mo: Mo = { tim: [], chuyen: [], hoanTac: [] };
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/cuu-trang-thai");
    await page.getByLabel(/Tìm học viên không thấy/).fill("van");
    await page.getByRole("button", { name: "Tìm", exact: true }).click();
    await expect(page.getByRole("button", { name: "Chuyển trạng thái Lê Văn Cường" })).toBeVisible();
    await page.getByLabel("Loại hạng").selectOption("moto");
    await expect(page.getByText(/Khác loại hạng với loại đang chọn/).first()).toBeVisible();
    await expect(page.getByRole("button", { name: /Chuyển trạng thái / })).toHaveCount(0);
    expect(mo.tim.some((q) => q.includes("loai=moto"))).toBe(true);
  });

  test("hộp xem lại có mục thu gọn 'dành cho IT' nêu SP sẽ gọi và mã đích", async ({ page }) => {
    const mo: Mo = { tim: [], chuyen: [], hoanTac: [] };
    await timVaChon(page, mo);
    const panel = page.getByRole("complementary", { name: "Chuyển trạng thái học viên" });
    await panel.getByRole("radio", { name: /Vắng sát hạch/ }).check();
    await panel.getByLabel(/Lý do/).fill("Vắng nhập nhầm");
    await panel.getByRole("button", { name: "Xem lại" }).click();
    const hop = page.getByRole("dialog", { name: "Xác nhận chuyển trạng thái" });
    await expect(hop.getByText("usp_NguoiLX_HoSo_UpdateTTXLy")).toBeHidden();      // thu gọn mặc định
    await hop.getByText("Chi tiết kỹ thuật (dành cho IT)").click();
    await expect(hop.getByText("usp_NguoiLX_HoSo_UpdateTTXLy")).toBeVisible();
  });

  test("khóa chưa bế giảng: vẫn đổi được nhưng nói rõ việc này không đưa HV vào danh sách BC2", async ({ page }) => {
    const mo: Mo = { tim: [], chuyen: [], hoanTac: [] };
    await timVaChon(page, mo, "Hoàng Văn Em");
    const panel = page.getByRole("complementary", { name: "Chuyển trạng thái học viên" });
    await expect(panel.getByText(/Khóa của học viên này chưa bế giảng/)).toBeVisible();
    await expect(panel.getByText(/không\s+làm học viên hiện vào danh sách BC2/)).toBeVisible();
  });

  test("hoàn tác mất kết nối: gửi lại cùng lo_id (không hoàn tác hai lần)", async ({ page }) => {
    const mo: Mo = { tim: [], chuyen: [], hoanTac: [], hoanTacKieu: "mat_ket_noi" };
    await timVaChon(page, mo);
    const panel = page.getByRole("complementary", { name: "Chuyển trạng thái học viên" });
    await panel.getByRole("radio", { name: /Chưa đạt BC2/ }).check();
    await panel.getByLabel(/Lý do/).fill("Nhập nhầm");
    await panel.getByRole("button", { name: "Xem lại" }).click();
    await page.getByRole("dialog").getByLabel(/xác nhận đây là CSDL thật/).check();
    await page.getByRole("dialog").getByRole("button", { name: "Chuyển", exact: true }).click();
    await panel.getByRole("button", { name: "Hoàn tác" }).click();
    await expect(panel.getByText(/Mất kết nối khi hoàn tác/)).toBeVisible();
    await panel.getByRole("button", { name: "Hoàn tác" }).click();                  // bấm lại
    await expect(panel.getByText(/Đã hoàn tác về/)).toBeVisible();
    expect(mo.hoanTac).toHaveLength(2);
    expect(mo.hoanTac[1].lo_id).toBe(mo.hoanTac[0].lo_id);
  });

  test("gửi lại sau mất kết nối mà bị từ chối (đã chuyển từ lần trước): báo đang kiểm tra và làm tươi", async ({ page }) => {
    const mo: Mo = { tim: [], chuyen: [], hoanTac: [], chuyenKieu: "mat_ket_noi_roi_tu_choi" };
    await timVaChon(page, mo);
    const panel = page.getByRole("complementary", { name: "Chuyển trạng thái học viên" });
    await panel.getByRole("radio", { name: /Vắng sát hạch/ }).check();
    await panel.getByLabel(/Lý do/).fill("Vắng nhập nhầm");
    await panel.getByRole("button", { name: "Xem lại" }).click();
    const hop = page.getByRole("dialog");
    await hop.getByLabel(/xác nhận đây là CSDL thật/).check();
    await hop.getByRole("button", { name: "Chuyển", exact: true }).click();
    await expect(hop.getByText(/Chưa biết đã chuyển được hay chưa/)).toBeVisible();
    const soLanTim = mo.tim.length;
    await hop.getByRole("button", { name: "Gửi lại" }).click();
    await expect(hop.getByText(/lần gửi trước đã chuyển xong thì học viên đã ở trạng thái mới/)).toBeVisible();
    await expect.poll(() => mo.tim.length).toBeGreaterThan(soLanTim);                // danh sách được làm tươi
  });

  test("đổi loại hạng khi panel đang mở: panel đóng để khỏi dùng danh sách đích của loại cũ", async ({ page }) => {
    const mo: Mo = { tim: [], chuyen: [], hoanTac: [] };
    await timVaChon(page, mo);
    await expect(page.getByRole("complementary", { name: "Chuyển trạng thái học viên" })).toBeVisible();
    await page.getByLabel("Loại hạng").selectOption("moto");
    await expect(page.getByRole("complementary", { name: "Chuyển trạng thái học viên" })).toHaveCount(0);
  });
});
