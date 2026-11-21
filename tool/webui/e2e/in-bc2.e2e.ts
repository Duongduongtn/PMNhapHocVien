import { expect, test, type Page } from "@playwright/test";

// TNB-08 — In Báo cáo 2: danh sách BC2 có nút In BC2 + ô tìm + cột Bản in; màn chọn phần thi (ô bấm bật/tắt, Ghi chú tự đổi,
// chọn nhiều, tự lưu, tải lại vẫn giữ); xem trước PDF + In/Lưu PDF; lỗi thiếu phần mềm cũ. Backend giả bằng page.route
// (bước xem trước trả PDF mẫu — PDF thật kiểm ở pytest + nghiệm thu máy CSĐT).

const PDF_MAU = Buffer.from("%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n" +
  "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF");

// Bảng mục ô tô (server tính thật ở tn_bc2_phan_thi.py) — mock chỉ cần đủ cho vài tổ hợp.
const MUC_OTO: Record<string, string> = {
  "L,H,Đ|lan_dau": "SH lần đầu", "L,H,Đ|thi_lai": "SH lại LT + H + Đ", "H,Đ": "SH lại H + Đ", "Đ": "SH lại Đ",
  "L,Đ": "SH lại L+Đ", "L,H": "SH lại LT + H", "L": "SH lại LT", "H": "Sát hạch Hình",
};
const MA_OTO: Record<string, number> = { "SH lần đầu": 1, "SH lại LT + H + Đ": 4, "SH lại H + Đ": 5, "SH lại Đ": 6, "SH lại L+Đ": 18, "SH lại LT + H": 3, "SH lại LT": 2, "Sát hạch Hình": 8 };

interface Hv { ma_dk: string; ho_ten: string; so_cmt: string; mac_dinh: string[]; da_thi: boolean; nguon: string; ten_nguon: string; pm_cu: string }
const HV: Hv[] = [
  { ma_dk: "D1", ho_ten: "NGUYỄN VĂN AN", so_cmt: "070200000001", mac_dinh: ["L", "H", "Đ"], da_thi: false, nguon: "chua_thi", ten_nguon: "Chưa thi", pm_cu: "SH lần đầu (L+M+H+Đ)" },
  { ma_dk: "D2", ho_ten: "TRẦN THỊ BÌNH", so_cmt: "079300000002", mac_dinh: ["Đ"], da_thi: true, nguon: "so", ten_nguon: "Kết quả Sở", pm_cu: "SH lại L+M+H+Đ" },
  { ma_dk: "D3", ho_ten: "LÊ HOÀNG CƯỜNG", so_cmt: "079300000003", mac_dinh: ["L", "H", "Đ"], da_thi: true, nguon: "so", ten_nguon: "Kết quả Sở", pm_cu: "SH lại L+M+H+Đ" },
];

interface Mo {
  luaChon: Record<string, string[]>;       // lựa chọn đã lưu (phía "server" giả)
  put: unknown[];
  daIn: number;
  xemTruoc: number;
  chonPmCu: string[];
  thieuPmCu: boolean;
  coBanIn: boolean;
}

function tinh(h: Hv, phai: string[]) {
  const key = phai.join(",");
  if (phai.length === 0) return { ghi_chu: "", ma_nd: null as number | null };
  const ten = key === "L,H,Đ" ? MUC_OTO[`${key}|${h.da_thi ? "thi_lai" : "lan_dau"}`] : MUC_OTO[key];
  return { ghi_chu: ten, ma_nd: MA_OTO[ten] };
}

function banIn(mo: Mo) {
  const hoc_vien = HV.map((h, i) => {
    const phai = mo.luaChon[h.ma_dk] ?? h.mac_dinh;
    const daSua = mo.luaChon[h.ma_dk] !== undefined && phai.join() !== h.mac_dinh.join();
    const md = tinh(h, h.mac_dinh);
    const { ghi_chu, ma_nd } = tinh(h, phai);
    return {
      stt: i + 1, ma_dk: h.ma_dk, ho_ten: h.ho_ten, ngay_sinh: "01/01/2000", so_cmt: h.so_cmt, hang: "B2", nhom: "oto",
      phan: ["L", "H", "Đ"], phai_thi: phai, dat: ["L", "H", "Đ"].filter((p) => !phai.includes(p)), da_thi: h.da_thi,
      ma_nd, ghi_chu, da_sua: daSua, nguon: daSua ? "sua" : h.nguon, ten_nguon: daSua ? "User chỉnh sửa" : h.ten_nguon,
      nguon_luc: daSua ? "2026-11-21T08:42:00" : "", ket_qua_sh: "",
      mac_dinh: { phai_thi: h.mac_dinh, dat: ["L", "H", "Đ"].filter((p) => !h.mac_dinh.includes(p)), ma_nd: md.ma_nd, ghi_chu: md.ghi_chu, da_thi: h.da_thi },
      pm_cu: h.pm_cu, pm_cu_khac: h.pm_cu !== md.ghi_chu,
    };
  });
  return {
    ma_bc2: "81/2026", so_bao_cao: "81/2026", ngay_bao_cao: "2026-11-06", dang_mo: true, ma_kh: "70004K26B0107", loai: "oto",
    hoc_vien, so_chon_lai: hoc_vien.filter((h) => h.da_sua).length, so_can_chon: hoc_vien.filter((h) => h.ma_nd === null).length,
  };
}

const BC2 = (mo: Mo) => [
  { ma_bc2: "81/2026", so_bao_cao: "81/2026", ngay_bao_cao: "2026-11-06", ma_bci: "B1", so_bc1: "45/BCI/2026", ma_kh: "K001",
    ten_kh: "Khóa B2-01/2026", loai: "oto", tong_ghi: 3, hv_thuc_te: 3, lech: false, dong: false, dang_mo: true, nguoi_tao: "thu1",
    ngay_tao: "2026-11-06", ban_in: mo.coBanIn ? { da_in_luc: "2026-11-06T09:00:00", so_chon_lai: 1, so_can_chon: 0 } : null },
  { ma_bc2: "79/2026", so_bao_cao: "79/2026", ngay_bao_cao: "2026-09-20", ma_bci: "B2", so_bc1: "108/BCI/2026", ma_kh: "K000",
    ten_kh: "Khóa C-12/2025", loai: "oto", tong_ghi: 40, hv_thuc_te: 40, lech: false, dong: false, dang_mo: true, nguoi_tao: "admin",
    ngay_tao: "2026-09-20", ban_in: null },
];

async function giaBackend(page: Page, mo: Mo) {
  await page.addInitScript(() => localStorage.setItem("tool_session_token", "tok-test"));
  await page.route("**/local/auth/me", (r) => r.fulfill({ json: { username: "thu1", ho_ten: "Nhân viên thử", vai_tro: "operator" } }));
  await page.route("**/local/config/moi-truong", (r) => r.fulfill({ json: { thu_muc_ghi_duoc: true, duong_dan: "x", da_cau_hinh: true } }));
  await page.route("**/version", (r) => r.fulfill({ json: { build: "dev", commit: "x" } }));
  await page.route(/\/local\/tnbc2\/bc2(\?.*)?$/, (r) => {
    const bc2 = BC2(mo);
    return r.fulfill({ json: { loai: "oto", dong: "mo", tong: bc2.length, dang_mo: bc2.length, da_dong: 0, lech: 0, bc2 } });
  });
  await page.route(/\/local\/tnbc2\/bc2\/[^?]*\/ban-in$/, (r) => r.fulfill({ json: banIn(mo) }));
  await page.route(/\/local\/tnbc2\/bc2\/[^?]*\/noi-dung-thi$/, async (r) => {
    const body = r.request().postDataJSON() as { ds: { ma_dk: string; phai_thi: string[] | null }[] };
    mo.put.push(body);
    for (const d of body.ds) {
      if (d.phai_thi === null) delete mo.luaChon[d.ma_dk];
      else mo.luaChon[d.ma_dk] = d.phai_thi;
    }
    await r.fulfill({ json: banIn(mo) });
  });
  await page.route(/\/local\/tnbc2\/bc2\/[^?]*\/xem-truoc$/, async (r) => {
    mo.xemTruoc++;
    if (mo.thieuPmCu) {
      await r.fulfill({ status: 409, json: { detail: { ma: "chua_co_phan_mem_cu", noi_dung: "Máy này chưa dựng được bản in: không tìm thấy mẫu in và bộ Crystal của phần mềm cũ." } } });
      return;
    }
    await r.fulfill({ json: { pdf_base64: PDF_MAU.toString("base64") } });
  });
  await page.route(/\/local\/tnbc2\/bc2\/[^?]*\/da-in$/, (r) => { mo.daIn++; return r.fulfill({ json: { ok: true } }); });
  await page.route("**/local/tnbc2/gplx-cu-dir", async (r) => {
    if (r.request().method() === "PUT") {
      const t = (r.request().postDataJSON() as { thu_muc: string }).thu_muc;
      mo.chonPmCu.push(t);
      mo.thieuPmCu = false;
      await r.fulfill({ json: { thu_muc: t, nguon: "da_luu", ung_vien: [] } });
      return;
    }
    await r.fulfill({ json: { thu_muc: "", nguon: "khong_co", ung_vien: ["D:\\GPLX-v3.1.0.6\\GPLX-v3.1.0.6"] } });
  });
}

const moi = (): Mo => ({ luaChon: {}, put: [], daIn: 0, xemTruoc: 0, chonPmCu: [], thieuPmCu: false, coBanIn: false });

async function vaoInBc2(page: Page, mo: Mo) {
  await giaBackend(page, mo);
  await page.goto("/tot-nghiep-bc2/bao-cao-2");
  await page.getByTestId("in-bc2-81/2026").click();
  await expect(page.getByTestId("hv-D1")).toBeVisible();
}

test.describe("TNB-08 — danh sách BC2", () => {
  test("nút In BC2 mỗi dòng, cột Bản in, ô tìm; các nút cuối dòng thẳng hàng", async ({ page }) => {
    const mo = moi();
    mo.coBanIn = true;
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    await expect(page.getByTestId("ban-in-81/2026")).toContainText("Đã in 06/11 · 1 chọn lại");
    await expect(page.getByTestId("ban-in-79/2026")).toContainText("Chưa in từ tool");
    // nút cùng mép trên + cùng cao trong một dòng
    const hop = await page.getByTestId("bc2-81/2026").getByRole("button").evaluateAll((bs) =>
      bs.map((b) => { const r = b.getBoundingClientRect(); return [Math.round(r.top), Math.round(r.height)]; }));
    expect(hop.length).toBe(3);
    expect(new Set(hop.map((x) => x[0])).size).toBe(1);
    expect(new Set(hop.map((x) => x[1])).size).toBe(1);
    // ô tìm
    await page.getByLabel("Tìm BC2").fill("108/bci");
    await expect(page.getByTestId("bc2-79/2026")).toBeVisible();
    await expect(page.getByTestId("bc2-81/2026")).toHaveCount(0);
    await page.getByLabel("Tìm BC2").fill("không có");
    await expect(page.getByText("Không có BC2 khớp.")).toBeVisible();
  });
});

test.describe("TNB-08 — chọn phần thi", () => {
  test("ô hiện sẵn đúng theo dữ liệu, Ghi chú tự đổi khi bấm ô, tự lưu, tải lại vẫn giữ", async ({ page }) => {
    const mo = moi();
    await vaoInBc2(page, mo);
    // điền sẵn: D1 chưa thi → SH lần đầu; D2 đã đạt L, H → SH lại Đ
    await expect(page.getByTestId("ghi-chu-D1")).toHaveText("SH lần đầu");
    await expect(page.getByTestId("ghi-chu-D2")).toHaveText("SH lại Đ");
    await expect(page.getByTestId("phan-D2-L")).toHaveAttribute("data-trang-thai", "dat");
    await expect(page.getByTestId("phan-D2-Đ")).toHaveAttribute("data-trang-thai", "thi");
    await expect(page.getByTestId("hv-D2")).toContainText("PM cũ: SH lại L+M+H+Đ — đã bỏ M");
    // bấm H của D1 → đã đạt H → SH lại L+Đ
    await page.getByTestId("phan-D1-H").click();
    await expect(page.getByTestId("ghi-chu-D1")).toHaveText("SH lại L+Đ");
    await expect(page.getByTestId("trang-thai-luu")).toContainText("Đã lưu");
    await expect(page.getByRole("button", { name: "Về mặc định NGUYỄN VĂN AN" })).toBeVisible();
    expect(mo.put).toHaveLength(1);
    // tải lại (rời màn In rồi vào lại) vẫn giữ
    await page.getByRole("button", { name: "← Danh sách BC2" }).click();
    await page.getByTestId("in-bc2-81/2026").click();
    await expect(page.getByTestId("ghi-chu-D1")).toHaveText("SH lại L+Đ");
    // ↺ về mặc định
    await page.getByRole("button", { name: "Về mặc định NGUYỄN VĂN AN" }).click();
    await expect(page.getByTestId("ghi-chu-D1")).toHaveText("SH lần đầu");
    expect(mo.luaChon["D1"]).toBeUndefined();
  });

  test("bố cục cố định: bấm bật/tắt ô không làm đổi bề rộng cột hay chiều cao dòng (không giật)", async ({ page }) => {
    const mo = moi();
    await vaoInBc2(page, mo);
    const hinh = () => page.evaluate(() => ({
      cot: [...document.querySelectorAll("thead th")].map((t) => Math.round(t.getBoundingClientRect().width)),
      cao: [...document.querySelectorAll("tbody tr")].map((t) => Math.round(t.getBoundingClientRect().height)),
      bang: Math.round(document.querySelector("table")!.getBoundingClientRect().width),
    }));
    const truoc = await hinh();
    expect(new Set(truoc.cao).size).toBe(1);          // mọi dòng cao bằng nhau (có/không dòng chú thích phụ)
    await page.getByTestId("phan-D1-H").click();      // thành "đã đạt" (có dấu ✓, đổi chữ Ghi chú, hiện nút Mặc định)
    await expect(page.getByTestId("ghi-chu-D1")).toHaveText("SH lại L+Đ");
    expect(await hinh()).toEqual(truoc);
    await page.getByRole("button", { name: "Về mặc định NGUYỄN VĂN AN" }).click();
    await expect(page.getByTestId("ghi-chu-D1")).toHaveText("SH lần đầu");
    expect(await hinh()).toEqual(truoc);
  });

  test("tắt hết ô → dòng đỏ, khóa Xem trước; bật lại thì mở", async ({ page }) => {
    const mo = moi();
    await vaoInBc2(page, mo);
    await page.getByTestId("phan-D2-Đ").click();
    await expect(page.getByTestId("ghi-chu-D2")).toHaveText("Phải bật ít nhất 1 phần");
    await expect(page.getByTestId("nut-xem-truoc")).toBeDisabled();
    await expect(page.getByTestId("dem-can")).toContainText("Chưa có phần thi 1");
    await page.getByTestId("phan-D2-Đ").click();
    await expect(page.getByTestId("nut-xem-truoc")).toBeEnabled();
  });

  test("chọn nhiều: bộ ô chung áp cho mọi dòng đã chọn; dải đếm lọc theo mục", async ({ page }) => {
    const mo = moi();
    await vaoInBc2(page, mo);
    await page.getByLabel("Chọn NGUYỄN VĂN AN").check();
    await page.getByLabel("Chọn LÊ HOÀNG CƯỜNG").check();
    await expect(page.getByTestId("thanh-chon-nhieu")).toContainText("Đã chọn 2 học viên");
    await page.getByTestId("chung-L").click();      // cả hai đang phải thi L → đánh dấu đã đạt L
    await expect(page.getByTestId("ghi-chu-D1")).toHaveText("SH lại H + Đ");
    await expect(page.getByTestId("ghi-chu-D3")).toHaveText("SH lại H + Đ");
    await expect(page.getByTestId("ghi-chu-D2")).toHaveText("SH lại Đ");           // dòng không chọn giữ nguyên
    await page.getByRole("button", { name: "Bỏ chọn" }).click();
    await page.getByTestId("dem-oto|5").click();
    await expect(page.getByTestId("hv-D1")).toBeVisible();
    await expect(page.getByTestId("hv-D2")).toHaveCount(0);
    await page.getByLabel("Tìm học viên").fill("cường");
    await expect(page.getByTestId("hv-D3")).toBeVisible();
    await expect(page.getByTestId("hv-D1")).toHaveCount(0);
  });

  test("bàn phím: Tab tới ô, phím cách bật/tắt; rê chuột có chữ giải thích", async ({ page }) => {
    const mo = moi();
    await vaoInBc2(page, mo);
    const o = page.getByTestId("phan-D1-L");
    await expect(o).toHaveAttribute("title", "Lý thuyết — phải thi. Bấm nếu học viên đã đạt phần này.");
    await expect(page.getByTestId("phan-D2-L")).toHaveAttribute("title", /đã đạt \(Kết quả Sở/);
    await o.focus();
    await page.keyboard.press("Space");
    await expect(page.getByTestId("ghi-chu-D1")).toHaveText("SH lại H + Đ");
  });
});

test.describe("TNB-08 — xem trước, In, Lưu PDF", () => {
  test("Xem trước hiện PDF; In… và Lưu PDF ghi lần in; tên tệp đúng", async ({ page }) => {
    const mo = moi();
    await vaoInBc2(page, mo);
    await page.getByTestId("nut-xem-truoc").click();
    await expect(page.getByText("Xem trước bản in")).toBeVisible();
    await expect(page.getByTestId("khung-pdf")).toBeVisible();
    await expect(page.getByTestId("khung-pdf")).toHaveAttribute("src", /^blob:/);
    expect(mo.xemTruoc).toBe(1);
    const tai = page.waitForEvent("download");
    await page.getByTestId("nut-luu-pdf").click();
    expect((await tai).suggestedFilename()).toBe("BC2_81-2026_70004K26B0107.pdf");
    await expect.poll(() => mo.daIn).toBe(1);
    // quay lại sửa nội dung thi
    await page.getByRole("button", { name: "← Sửa nội dung thi" }).click();
    await expect(page.getByTestId("hv-D1")).toBeVisible();
  });

  test("máy chưa có phần mềm cũ: báo rõ, nhập thư mục rồi tự dựng lại; lựa chọn vẫn giữ", async ({ page }) => {
    const mo = moi();
    mo.thieuPmCu = true;
    await vaoInBc2(page, mo);
    await page.getByTestId("phan-D1-H").click();
    await expect(page.getByTestId("ghi-chu-D1")).toHaveText("SH lại L+Đ");
    await page.getByTestId("nut-xem-truoc").click();
    await expect(page.getByText("Máy này chưa dựng được bản in Báo cáo 2")).toBeVisible();
    await page.getByRole("button", { name: "D:\\GPLX-v3.1.0.6\\GPLX-v3.1.0.6" }).click();
    await page.getByRole("button", { name: "Dùng thư mục này" }).click();
    await expect(page.getByTestId("khung-pdf")).toBeVisible();
    expect(mo.chonPmCu).toEqual(["D:\\GPLX-v3.1.0.6\\GPLX-v3.1.0.6"]);
    expect(mo.xemTruoc).toBe(2);
    await page.getByRole("button", { name: "← Sửa nội dung thi" }).click();
    await expect(page.getByTestId("ghi-chu-D1")).toHaveText("SH lại L+Đ");
  });
});

test.describe("TNB-08 — bấm nhanh không làm lệch màn hình với dữ liệu đã lưu", () => {
  test("lần gửi sau không vượt lần gửi trước; Xem trước khóa khi còn đang lưu", async ({ page }) => {
    const mo = moi();
    await giaBackend(page, mo);
    // làm chậm lần PUT đầu để thấy nếu hai lần gửi chạy chồng nhau
    let lan = 0;
    const thuTu: string[] = [];
    await page.route(/\/local\/tnbc2\/bc2\/[^?]*\/noi-dung-thi$/, async (r) => {
      const body = r.request().postDataJSON() as { ds: { ma_dk: string; phai_thi: string[] | null }[] };
      const lanNay = ++lan;
      if (lanNay === 1) await new Promise((x) => setTimeout(x, 600));
      thuTu.push(body.ds[0].phai_thi?.join("") ?? "null");
      for (const d of body.ds) { if (d.phai_thi === null) delete mo.luaChon[d.ma_dk]; else mo.luaChon[d.ma_dk] = d.phai_thi; }
      await r.fulfill({ json: banIn(mo) });
    });
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    await page.getByTestId("in-bc2-81/2026").click();
    await expect(page.getByTestId("hv-D1")).toBeVisible();
    await page.getByTestId("phan-D1-H").click();          // → [L,Đ]  (lần gửi 1, chậm)
    await page.getByTestId("phan-D1-L").click();          // → [Đ]    (lần gửi 2, nhanh)
    await expect(page.getByTestId("nut-xem-truoc")).toBeDisabled();
    await expect(page.getByTestId("trang-thai-luu")).toContainText("Đang lưu");
    await expect(page.getByTestId("trang-thai-luu")).toContainText("Đã lưu");
    expect(thuTu).toEqual(["LĐ", "Đ"]);                    // đúng thứ tự bấm
    expect(mo.luaChon["D1"]).toEqual(["Đ"]);               // dữ liệu lưu = lần bấm cuối
    await expect(page.getByTestId("ghi-chu-D1")).toHaveText("SH lại Đ");
    await expect(page.getByTestId("nut-xem-truoc")).toBeEnabled();
  });
});
