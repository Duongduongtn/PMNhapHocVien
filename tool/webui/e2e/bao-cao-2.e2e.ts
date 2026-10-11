import { expect, test, type Page } from "@playwright/test";

// TNB-04 — Lập BC2 bước ①: chọn khóa. Backend giả bằng page.route; không đụng DB thật.

interface Mo {
  cacLanGoi: string[];
  ungVien: string[];
  /** Body của các lần POST /bc2 (tạo BC2). */
  taoBc2?: Record<string, unknown>[];
  /** Hành vi của POST /bc2: lần đầu. */
  taoKieu?: "ok" | "trung" | "mat_ket_noi" | "loi_500";
  /** Bước ③: body các lần POST /bc2/lap. */
  lap?: Record<string, unknown>[];
  lapKieu?: "ok" | "loi_giua_chung" | "409" | "poll_loi" | "that_bai" | "409_dang_ghi" | "409_bc2_khac_khoa" | "409_bc2_da_dong" | "404_bc2_khong_ton_tai" | "abort_dau" | "dang_chay_mai" | "canh_bao";
  hoanTacLoId?: string;
  polls?: number;
  /** TNB-05: chi tiết BC2 đang xem (giả), body các lần gỡ / xóa. */
  chiTiet?: Record<string, unknown>;
  go?: Record<string, unknown>[];
  xoa?: string[];
  goKieu?: "ok" | "409_canh_bao" | "that_bai";
  hoanTacKieu?: "ok" | "loi" | "that_bai";
  hoanTacLan?: number;
  /** Checkpoint 26 */
  tre?: number;                  // ms trễ của POST /bc2/lap (cho double-click)
  soSan?: number;                // số HV nhóm Sẵn sàng của mock ung-vien
  lapTong?: number;
  bumpSo?: boolean;              // gợi ý số lần gọi thứ hai nhảy sang 82/2026
  goiYLan?: number;
  dsExtra?: Record<string, unknown>[];
  xoaKieu?: "409" | "abort";
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

const hvTrong = (ma_dk: string, ten: string, ex: Record<string, unknown> = {}) => ({
  ma_dk, so_ho_so: "", ten, ngay_sinh: "01/05/1990", cmt: `0792${ma_dk.replace(/\D/g, "").padStart(8, "0")}`, hang: "B2",
  ma_kh: "K0A", ten_kh: "Khóa B2-12/2025", tt: "11", ten_trang_thai: "Đã vào BC2, chờ kết quả", tt_cu: "17",
  ten_trang_thai_cu: "Thi sát hạch chưa đạt", go_duoc: true, ly_do_khoa: "", canh_bao_tt_cu: false, khac_khoa_bc1: false, ...ex,
});
const CHI_TIET = {
  ma_bc2: "80/2026", so_bao_cao: "80/2026", ngay_bao_cao: "2026-09-30", trang_thai: 0, dang_mo: true, nguoi_tao: "thu1",
  ngay_tao: "2026-09-30", ma_bci: "BCI-1", ma_kh: "K001", ten_kh: "Khóa B2-01/2026", loai: "oto", tong_ghi: 25, hv_thuc_te: 3,
  lech: true, xoa_duoc: false,
  hoc_vien: [
    hvTrong("H-0001", "Nguyễn Thị Hoà"),
    hvTrong("H-0002", "Trần Văn Bình", { canh_bao_tt_cu: true, tt_cu: "", ten_trang_thai_cu: "" }),
    hvTrong("H-0003", "Lê Đức Anh", { tt: "13", ten_trang_thai: "Đã có kết quả cuối", go_duoc: false,
      ly_do_khoa: "Đã chuyển sang \"Đã có kết quả cuối\" — gỡ khỏi BC2 sẽ làm mất kết quả; dùng Cứu trạng thái nếu cần" }),
  ],
};

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
  await page.route(/\/local\/tnbc2\/bc2\/[^/?]+(\?.*)?$/, async (r) => {
    const req = r.request();
    if (req.method() === "DELETE") {
      if (mo.xoaKieu === "abort") return r.abort("connectionreset");
      if (mo.xoaKieu === "409") {
        return r.fulfill({ status: 409, json: { detail: { ma: "con_hoc_vien", noi_dung: "BC2 số 80/2026 còn 2 học viên — gỡ hết trước khi xóa" } } });
      }
      (mo.xoa ??= []).push(decodeURIComponent(new URL(req.url()).pathname.split("/").pop() ?? ""));
      return r.fulfill({ json: { ma_bc2: "80/2026", da_xoa: true } });
    }
    await r.fulfill({ json: mo.chiTiet ?? CHI_TIET });
  });
  await page.route(/\/local\/tnbc2\/bc2\/[^/?]+\/go$/, async (r) => {
    const b = r.request().postDataJSON();
    (mo.go ??= []).push(b);
    if (mo.goKieu === "409_canh_bao" && !b.da_xem_canh_bao) {
      return r.fulfill({ status: 409, json: { detail: { ma: "can_xac_nhan_canh_bao", noi_dung: "Trạng thái trước đó rỗng",
        canh_bao: [{ ma: "tt_cu_rong", noi_dung: "Trạng thái trước đó rỗng" }] } } });
    }
    mo.polls = 0;
    await r.fulfill({ json: { lo_id: b.lo_id, trang_thai: "dang_chay", xu_ly: 0, tong: b.ds_ma_dk.length, xong: false } });
  });
  await page.route("**/local/auth/me", (r) => r.fulfill({ json: { username: "thu1", ho_ten: "Nhân viên thử", vai_tro: "operator" } }));
  await page.route("**/local/config/moi-truong", (r) => r.fulfill({ json: { thu_muc_ghi_duoc: true, duong_dan: "x", da_cau_hinh: true } }));
  await page.route("**/version", (r) => r.fulfill({ json: { build: "dev", commit: "x" } }));
  await page.route("**/local/tnbc2/bc2/lap", async (r) => {
    const b = r.request().postDataJSON();
    (mo.lap ??= []).push(b);
    mo.polls = 0;
    mo.lapTong = b.ds_ma_dk.length;
    if (mo.tre) await new Promise((res) => setTimeout(res, mo.tre));
    if (mo.lapKieu === "abort_dau" && mo.lap.length === 1) return r.abort("connectionreset");
    const LOI_DONG_BO: Record<string, [number, string, string]> = {
      "409_dang_ghi": [409, "dang_ghi", "Đang có thao tác ghi khác của phân hệ — đợi vài giây rồi thử lại"],
      "409_bc2_khac_khoa": [409, "bc2_khac_khoa", "BC2 số 80/2026 không thuộc BC1 của khóa này"],
      "409_bc2_da_dong": [409, "bc2_da_dong", "BC2 số 80/2026 đã đóng — không thêm học viên được"],
      "404_bc2_khong_ton_tai": [404, "bc2_khong_ton_tai", "Không có BC2 số 80/2026"],
    };
    const ld = mo.lapKieu ? LOI_DONG_BO[mo.lapKieu] : undefined;
    if (ld) return r.fulfill({ status: ld[0], json: { detail: { ma: ld[1], noi_dung: ld[2] } } });
    if ((!mo.lapKieu || mo.lapKieu === "ok") && !b.ma_bc2) {
      // BC2 mới được lập: danh sách và chi tiết phản ánh đúng N học viên (Checkpoint 26 — liên thông lập → xem)
      const n = b.ds_ma_dk.length;
      mo.chiTiet = { ...CHI_TIET, ma_bc2: b.so_bao_cao, so_bao_cao: b.so_bao_cao, tong_ghi: n, hv_thuc_te: n, lech: false,
        hoc_vien: b.ds_ma_dk.map((m: string, i: number) => hvTrong(m, `Học Viên Mới ${i + 1}`)) };
      (mo.dsExtra ??= []).push({ ma_bc2: b.so_bao_cao, so_bao_cao: b.so_bao_cao, ma_kh: b.ma_kh, ten_kh: "Khóa B2-01/2026",
        ngay_bao_cao: b.ngay_bao_cao, tong_ghi: n, hv_thuc_te: n, loai: "oto", dang_mo: true, dong: false });
    }
    if (mo.lapKieu === "409") {
      return r.fulfill({ status: 409, json: { detail: { ma: "khoa_chua_co_bc1", noi_dung: "Khóa K001 chưa có BC1 — chưa lập BC2 được" } } });
    }
    await r.fulfill({ json: { lo_id: b.lo_id, trang_thai: "dang_chay", xu_ly: 0, tong: b.ds_ma_dk.length, xong: false } });
  });
  await page.route("**/local/tnbc2/bc2/*/hoan-tac", async (r) => {
    const b = r.request().postDataJSON();
    mo.hoanTacLoId = b.lo_id;
    mo.hoanTacLan = (mo.hoanTacLan ?? 0) + 1;
    mo.polls = 0;
    await r.fulfill({ json: { lo_id: b.lo_id, trang_thai: "dang_chay", xu_ly: 0, tong: 1, xong: false } });
  });
  await page.route("**/local/tnbc2/bc2/lo/**", async (r) => {
    const loId = decodeURIComponent(new URL(r.request().url()).pathname.split("/").pop() ?? "");
    mo.polls = (mo.polls ?? 0) + 1;
    if ((mo.go?.length ?? 0) > 0 && loId === mo.go![0].lo_id) {
      if (mo.polls === 1) return r.fulfill({ json: { lo_id: loId, trang_thai: "dang_chay", xu_ly: 0, tong: 1, xong: false } });
      if (mo.goKieu === "that_bai") {
        return r.fulfill({ json: { lo_id: loId, trang_thai: "that_bai", xu_ly: 0, tong: 1, xong: true,
          loi_nghiep_vu: { ma: "bc2_da_dong", noi_dung: "BC2 số 80/2026 đã đóng — không gỡ được" } } });
      }
      return r.fulfill({ json: { lo_id: loId, trang_thai: "xong", xu_ly: 1, tong: 1, xong: true, ma_bc2: "80/2026",
        da_go: ["H-0001"], bo_qua: [], chua_ghi: [], canh_bao: [], loi: null } });
    }
    if (loId === mo.hoanTacLoId) {
      if (mo.polls === 1) return r.fulfill({ json: { lo_id: loId, trang_thai: "dang_chay", xu_ly: 0, tong: 1, xong: false } });
      if (mo.hoanTacKieu === "that_bai") {
        return r.fulfill({ json: { lo_id: loId, trang_thai: "that_bai", xu_ly: 0, tong: 0, xong: true,
          loi_nghiep_vu: { ma: "bc2_da_dong", noi_dung: "BC2 số 80/2026 đã đóng — không gỡ được" } } });
      }
      if (mo.hoanTacKieu === "loi" && mo.hoanTacLan === 1) {
        return r.fulfill({ json: { lo_id: loId, trang_thai: "loi_giua_chung", xu_ly: 1, tong: 2, xong: true, ma_bc2: "80/2026",
          da_go: ["H-0001"], bo_qua: [], loi: { ma_dk: "H-0002", noi_dung: "Mất kết nối SQL Server" } } });
      }
      return r.fulfill({ json: { lo_id: loId, trang_thai: "xong", xu_ly: 1, tong: 1, xong: true, ma_bc2: "81/2026",
        da_go: ["T-0001"], bo_qua: [], loi: null } });
    }
    if (mo.polls === 1 || mo.lapKieu === "dang_chay_mai") {
      return r.fulfill({ json: { lo_id: loId, trang_thai: "dang_chay", xu_ly: 0, tong: mo.lapTong ?? 1, xong: false } });
    }
    const lanDau = (mo.lap?.length ?? 0) === 1;
    if (mo.lapKieu === "poll_loi" && lanDau) {
      return r.fulfill({ status: 500, json: { detail: { ma: "khong_truy_van_duoc", noi_dung: "Không truy vấn được SQL Server" } } });
    }
    if (mo.lapKieu === "that_bai") {
      return r.fulfill({ json: { lo_id: loId, trang_thai: "that_bai", xu_ly: 0, tong: 1, xong: true,
        loi_nghiep_vu: { ma: "bc2_da_dong", noi_dung: "BC2 số 81/2026 đã đóng — không thêm học viên được" } } });
    }
    if (mo.lapKieu === "loi_giua_chung" && lanDau) {
      return r.fulfill({ json: { lo_id: loId, trang_thai: "loi_giua_chung", xu_ly: 1, tong: 2, xong: true, ma_bc2: "81/2026",
        da_tao_bc2: true, da_them: ["T-0001"], da_co_tu_truoc: [], bo_qua: [], chua_ghi: ["T-0002"], canh_bao: [],
        loi: { ma_dk: "T-0002", noi_dung: "Mất kết nối SQL Server" } } });
    }
    const sau = mo.lapKieu === "loi_giua_chung";
    const maCo = (mo.lap?.[0]?.ma_bc2 as string) || "";
    return r.fulfill({ json: { lo_id: loId, trang_thai: "xong", xu_ly: 1, tong: 2, xong: true, ma_bc2: sau ? "81/2026" : maCo || "81/2026",
      da_tao_bc2: !sau && !maCo, da_them: sau ? ["T-0002"] : ["T-0001"], da_co_tu_truoc: sau ? ["T-0001"] : [],
      bo_qua: sau ? [] : [{ ma_dk: "T-0003", ma_ly_do: "doi_giua_chung", ly_do: "Phần mềm cũ vừa đổi học viên này — không ghi đè" }],
      chua_ghi: [],
      canh_bao: mo.lapKieu === "canh_bao"
        ? [{ ma_dk: "T-0001", ma: "trang_thai_cu_la_11", noi_dung: "Trạng thái cũ đang là 'Đã vào BC2' — gỡ ra sẽ không về đúng" }]
        : [],
      loi: null } });
  });
  await page.route("**/local/tnbc2/bc2/ung-vien?**", async (r) => {
    const u = new URL(r.request().url());
    mo.ungVien.push(u.search);
    const thang = Number(u.searchParams.get("thi_lai_thang") || 12);
    const thi = THI.map((h) => ({ ...h, trong_nguong: (h.tuoi_thang ?? 99) <= thang }));
    const san = SAN.slice(0, mo.soSan ?? SAN.length);
    await r.fulfill({ json: { ma_kh: u.searchParams.get("ma_kh"), ten_kh: "Khóa B2-01/2026", loai: "oto", hom_nay: "2026-10-11",
      thi_lai_thang: thang, ma_bc2: u.searchParams.get("ma_bc2") || "", bc1: { ma_bci: "BCI-1", so_bao_cao: "112/BCI/2026", so_hoc_sinh: 150 },
      bc2_cua_khoa: [], nhom: { san_sang: san, thi_lai: thi, can_xem: XEM, khong_duoc: KHONG },
      dem: { san_sang: san.length, thi_lai: thi.length, thi_lai_trong_nguong: thi.filter((h) => h.trong_nguong).length,
        can_xem: XEM.length, khong_duoc: KHONG.length } } });
  });
  await page.route("**/local/tnbc2/bc2/goi-y-so?**", async (r) => {
    const maKh = new URL(r.request().url()).searchParams.get("ma_kh");
    const moto = maKh === "M001";
    mo.goiYLan = (mo.goiYLan ?? 0) + 1;
    const soGoiY = mo.bumpSo && (mo.lap?.length ?? 0) > 0 ? "82/2026" : "81/2026";   // nhảy SAU lần gửi đầu
    await r.fulfill({ json: moto
      ? { ma_kh: "M001", ten_kh: "Khóa A1-05/2026", loai: "moto", nam: 2026, so: "870/26-TTTĐ", co_bc1: true,
          bc1: { ma_bci: "BCI-9", so_bao_cao: "A1A2870/26-TTTĐ", so_hoc_sinh: 74 },
          bc2_cua_khoa: [{ ma: "861/26-TTTĐ", trang_thai: 0, tong_ghi: 74 }], trung: false }
      : { ma_kh: "K001", ten_kh: "Khóa B2-01/2026", loai: "oto", nam: 2026, so: soGoiY, co_bc1: true,
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
      ...(mo.dsExtra ?? []),
      { ma_bc2: "80/2026", so_bao_cao: "80/2026", ma_kh: "K001", ten_kh: "Khóa B2-01/2026", ngay_bao_cao: "2026-09-30",
        tong_ghi: 25, hv_thuc_te: 3, loai: "oto", dang_mo: true, dong: false },
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
    await expect(page.getByText("Xác nhận lập BC2 và thêm học viên")).toBeVisible();
    await expect(page.getByText("học viên sẽ thêm")).toBeVisible();
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

test.describe("TNB-04 — Lập BC2 bước ③: xác nhận và ghi", () => {
  async function toiBuoc3(page: Page, mo: Mo, moto = false) {
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    if (moto) await page.getByRole("button", { name: "Mô tô" }).click();
    await page.getByRole("button", { name: "Lập BC2 mới" }).click();
    await page.getByTestId(moto ? "khoa-M001" : "khoa-K001").getByRole("button", { name: "Chọn khóa này →" }).click();
    await expect(page.getByTestId("dai-tom-tat")).toBeVisible();
    await page.getByRole("button", { name: "Bỏ chọn tất cả" }).click();
    await page.getByLabel("Tìm học viên").fill("nguyen thi hoa");
    await page.getByLabel("Tìm học viên").press("Enter");
    await page.getByRole("button", { name: /Tiếp tục/ }).click();
  }
  async function moHopVaTichXacNhan(page: Page, ten: RegExp) {
    await page.getByRole("button", { name: ten }).click();
    await page.getByRole("dialog", { name: "Xác nhận ghi" }).getByLabel(/xác nhận đây là CSDL thật/).check();
  }

  test("BC2 mới: form số/ngày, xác nhận CSDL thật, lập + thêm, rồi Hoàn tác lần vừa rồi", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [] };
    await toiBuoc3(page, mo);
    await expect(page.getByLabel("Số BC2 (= mã báo cáo)")).toHaveValue("81/2026");
    if (process.env.CHUP_ANH) {
      for (const w of [800, 1280, 1440]) {
        await page.setViewportSize({ width: w, height: 800 });
        await page.screenshot({ path: `${process.env.CHUP_ANH}/${w}-buoc-3.png` });
      }
    }
    await page.getByRole("button", { name: "Lập BC2 và thêm 1 học viên" }).click();
    const hop = page.getByRole("dialog", { name: "Xác nhận ghi" });
    const ghi = hop.getByRole("button", { name: "Lập BC2 và thêm" });
    await expect(ghi).toBeDisabled();                         // chưa tích CSDL thật
    await hop.getByLabel(/xác nhận đây là CSDL thật/).check();
    await ghi.click();
    await expect(page.getByText(/Đã thêm 1 học viên vào BC2 số 81\/2026/)).toBeVisible();
    await expect(page.getByText(/Đã tạo BC2 số/)).toBeVisible();
    await expect(page.getByText("1 học viên bị bỏ qua")).toBeVisible();
    if (process.env.CHUP_ANH) await page.screenshot({ path: `${process.env.CHUP_ANH}/1440-buoc-3-ket-qua.png` });
    expect(mo.lap).toHaveLength(1);
    expect(mo.lap![0]).toMatchObject({ ma_kh: "K001", ma_bc2: "", so_bao_cao: "81/2026", ds_ma_dk: ["T-0001"], xac_nhan_csdl_that: true });

    await page.getByRole("button", { name: "Hoàn tác lần vừa rồi" }).click();
    await expect(page.getByText(/đã gỡ 1 học viên khỏi BC2/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Hoàn tác lần vừa rồi" })).toHaveCount(0);   // chỉ một lần
  });

  test("BC2 đang mở (mô tô): không có form số, chỉ thêm học viên vào đúng BC2", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [] };
    await toiBuoc3(page, mo, true);
    await expect(page.getByText(/Thêm vào BC2 số/).first()).toBeVisible();
    await expect(page.getByLabel("Số BC2 (= mã báo cáo)")).toHaveCount(0);
    await moHopVaTichXacNhan(page, /^Thêm 1 học viên$/);
    await page.getByRole("dialog", { name: "Xác nhận ghi" }).getByRole("button", { name: "Thêm học viên" }).click();
    await expect(page.getByText(/Đã thêm 1 học viên vào BC2 số/)).toBeVisible();
    expect(mo.lap![0]).toMatchObject({ ma_bc2: "861/26-TTTĐ" });
  });

  test("lỗi giữa chừng: báo CHƯA ghi, Làm tiếp gửi lại cùng lo_id", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], lapKieu: "loi_giua_chung" };
    await toiBuoc3(page, mo);
    await moHopVaTichXacNhan(page, /^Lập BC2 và thêm 1 học viên$/);
    await page.getByRole("dialog", { name: "Xác nhận ghi" }).getByRole("button", { name: "Lập BC2 và thêm" }).click();
    await expect(page.getByText(/CHƯA ghi 1 học viên/)).toBeVisible();
    await page.getByRole("button", { name: "Làm tiếp" }).click();
    await expect(page.getByText(/đã có từ lần trước/)).toBeVisible();
    expect(mo.lap).toHaveLength(2);
    expect(mo.lap![1].lo_id).toBe(mo.lap![0].lo_id);          // cùng lô ⇒ server không ghi lại HV đã thêm
  });

  test("server từ chối ngay (409 khóa chưa có BC1): hiện lý do, chưa ghi gì", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], lapKieu: "409" };
    await toiBuoc3(page, mo);
    await moHopVaTichXacNhan(page, /^Lập BC2 và thêm 1 học viên$/);
    await page.getByRole("dialog", { name: "Xác nhận ghi" }).getByRole("button", { name: "Lập BC2 và thêm" }).click();
    await expect(page.getByRole("dialog").getByText(/chưa có BC1/)).toBeVisible();
    await expect(page.getByText(/Đã thêm/)).toHaveCount(0);
  });

  test("theo dõi tiến độ gặp lỗi máy chủ: không kẹt, hiện Làm tiếp (cùng lo_id)", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], lapKieu: "poll_loi" };
    await toiBuoc3(page, mo);
    await moHopVaTichXacNhan(page, /^Lập BC2 và thêm 1 học viên$/);
    await page.getByRole("dialog", { name: "Xác nhận ghi" }).getByRole("button", { name: "Lập BC2 và thêm" }).click();
    await expect(page.getByText(/Mất kết nối khi ghi/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Làm tiếp" })).toBeVisible();
  });

  test("lô thất bại bất đồng bộ (BC2 vừa bị đóng): nêu lý do và cho quay lại chọn học viên", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], lapKieu: "that_bai" };
    await toiBuoc3(page, mo);
    await moHopVaTichXacNhan(page, /^Lập BC2 và thêm 1 học viên$/);
    await page.getByRole("dialog", { name: "Xác nhận ghi" }).getByRole("button", { name: "Lập BC2 và thêm" }).click();
    await expect(page.getByText(/đã đóng — không thêm học viên được/)).toBeVisible();
    await page.getByRole("button", { name: "← Quay lại chọn học viên" }).click();
    await expect(page.getByTestId("dai-tom-tat")).toBeVisible();
  });
});

test.describe("TNB-05 — Xem / gỡ / xóa BC2", () => {
  async function vaoXem(page: Page, mo: Mo) {
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    await page.getByRole("button", { name: "Xem BC2 80/2026" }).click();
    await expect(page.getByText("Chỉ gỡ được học viên còn ở")).toBeVisible();
  }

  test("danh sách BC2: Xem mở chi tiết; HV có kết quả bị khóa kèm lý do; Tổng ghi ≠ thực tế vẫn hiện", async ({ page }) => {
    await vaoXem(page, { cacLanGoi: [], ungVien: [] });
    await expect(page.getByText("Tổng ghi", { exact: false }).first()).toBeVisible();
    await expect(page.getByLabel("Chọn Nguyễn Thị Hoà")).toBeEnabled();
    await expect(page.getByLabel("Chọn Lê Đức Anh")).toBeDisabled();
    await expect(page.getByText(/gỡ khỏi BC2 sẽ làm mất kết quả/)).toBeVisible();
    await expect(page.getByRole("button", { name: /Gỡ 0 học viên khỏi BC2/ })).toBeDisabled();
    await expect(page.getByRole("button", { name: "Xóa BC2 rỗng" })).toBeDisabled();      // còn 3 học viên
    if (process.env.CHUP_ANH) {
      for (const w of [800, 1280, 1440]) {
        await page.setViewportSize({ width: w, height: 800 });
        await page.screenshot({ path: `${process.env.CHUP_ANH}/${w}-xem-bc2.png` });
      }
    }
  });

  test("gỡ học viên: hộp nêu tên + khóa gốc + 'không tự quay lại BC2 cũ', cần tích CSDL thật", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], go: [] };
    await vaoXem(page, mo);
    await page.getByLabel("Chọn Nguyễn Thị Hoà").check();
    await page.getByRole("button", { name: "Gỡ 1 học viên khỏi BC2" }).click();
    const hop = page.getByRole("dialog", { name: "Gỡ học viên khỏi BC2" });
    await expect(hop.getByText(/không\s+tự quay lại BC2 cũ/)).toBeVisible();
    await expect(hop.getByText(/Nguyễn Thị Hoà — Khóa B2-12\/2025/)).toBeVisible();
    const go = hop.getByRole("button", { name: "Gỡ 1 học viên" });
    await expect(go).toBeDisabled();
    await hop.getByLabel(/xác nhận đây là CSDL thật/).check();
    await go.click();
    await expect(hop.getByText(/Đã gỡ 1 học viên khỏi BC2 80\/2026/)).toBeVisible();
    expect(mo.go![0]).toMatchObject({ ds_ma_dk: ["H-0001"], xac_nhan_csdl_that: true, da_xem_canh_bao: false });
  });

  test("HV không có trạng thái trước đó: phải tích đã xem cảnh báo mới gỡ được", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], go: [] };
    await vaoXem(page, mo);
    await page.getByLabel("Chọn Trần Văn Bình").check();
    await page.getByRole("button", { name: "Gỡ 1 học viên khỏi BC2" }).click();
    const hop = page.getByRole("dialog", { name: "Gỡ học viên khỏi BC2" });
    await hop.getByLabel(/xác nhận đây là CSDL thật/).check();
    const go = hop.getByRole("button", { name: "Gỡ 1 học viên" });
    await expect(go).toBeDisabled();                           // chưa tích đã xem cảnh báo
    await hop.getByLabel(/Tôi đã xem và vẫn muốn gỡ/).check();
    await go.click();
    await expect(hop.getByText(/Đã gỡ 1 học viên/)).toBeVisible();
    expect(mo.go![0]).toMatchObject({ ds_ma_dk: ["H-0002"], da_xem_canh_bao: true });
  });

  test("xóa BC2 rỗng: chỉ bật khi 0 học viên, có xác nhận CSDL thật", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], xoa: [],
      chiTiet: { ...CHI_TIET, hv_thuc_te: 0, lech: true, xoa_duoc: true, hoc_vien: [] } };
    await vaoXem(page, mo);
    await expect(page.getByText("Chưa có học viên trong BC2 này.")).toBeVisible();
    await page.getByRole("button", { name: "Xóa BC2 rỗng" }).click();
    const hop = page.getByRole("dialog", { name: "Xóa BC2 rỗng" });
    const xoa = hop.getByRole("button", { name: "Xóa BC2", exact: true });
    await expect(xoa).toBeDisabled();
    await hop.getByLabel(/xác nhận đây là CSDL thật/).check();
    await xoa.click();
    await expect(hop.getByText(/Đã xóa BC2 số/)).toBeVisible();
    expect(mo.xoa).toEqual(["80/2026"]);
  });

  test("Hoàn tác lần thêm vừa rồi: xác nhận rồi hiện số học viên đã gỡ", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [] };
    await vaoXem(page, mo);
    await page.getByRole("button", { name: "Hoàn tác lần thêm vừa rồi" }).click();
    const hop = page.getByRole("dialog", { name: "Hoàn tác lần thêm vừa rồi" });
    await hop.getByLabel(/xác nhận đây là CSDL thật/).check();
    await hop.getByRole("button", { name: "Hoàn tác", exact: true }).click();
    await expect(hop.getByText(/Đã gỡ 1 học viên khỏi BC2/)).toBeVisible();
    expect(mo.hoanTacLoId).toBeTruthy();
  });

  test("'+ Thêm học viên' ở dòng BC2 đang mở đi thẳng vào bước ② của đúng BC2", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [] };
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    await page.getByRole("button", { name: "Thêm học viên vào BC2 80/2026" }).click();
    await expect(page.getByTestId("dai-tom-tat")).toBeVisible();
    await expect.poll(() => mo.ungVien.some((q) => q.includes("ma_bc2=80%2F2026") && q.includes("ma_kh=K001"))).toBe(true);
  });

  test("lô gỡ thất bại bất đồng bộ (BC2 vừa bị đóng): báo lỗi đỏ, KHÔNG báo 'Đã gỡ 0'", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], go: [], goKieu: "that_bai" };
    await vaoXem(page, mo);
    await page.getByLabel("Chọn Nguyễn Thị Hoà").check();
    await page.getByRole("button", { name: "Gỡ 1 học viên khỏi BC2" }).click();
    const hop = page.getByRole("dialog", { name: "Gỡ học viên khỏi BC2" });
    await hop.getByLabel(/xác nhận đây là CSDL thật/).check();
    await hop.getByRole("button", { name: "Gỡ 1 học viên" }).click();
    await expect(hop.getByText(/đã đóng — không gỡ được/)).toBeVisible();
    await expect(hop.getByText(/Đã gỡ 0/)).toHaveCount(0);
  });

  test("server báo cảnh báo TT_XuLy_Old sau khi mở màn (409): hộp hiện ô tích để xác nhận rồi gỡ được", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], go: [], goKieu: "409_canh_bao" };
    await vaoXem(page, mo);
    await page.getByLabel("Chọn Nguyễn Thị Hoà").check();
    await page.getByRole("button", { name: "Gỡ 1 học viên khỏi BC2" }).click();
    const hop = page.getByRole("dialog", { name: "Gỡ học viên khỏi BC2" });
    await hop.getByLabel(/xác nhận đây là CSDL thật/).check();
    await hop.getByRole("button", { name: "Gỡ 1 học viên" }).click();
    await expect(hop.getByLabel(/Tôi đã xem và vẫn muốn gỡ/)).toBeVisible();
    await hop.getByLabel(/Tôi đã xem và vẫn muốn gỡ/).check();
    await hop.getByRole("button", { name: "Gỡ 1 học viên" }).click();
    await expect(hop.getByText(/Đã gỡ 1 học viên/)).toBeVisible();
    expect(mo.go).toHaveLength(2);
    expect(mo.go![1]).toMatchObject({ da_xem_canh_bao: true });
  });

  test("hoàn tác đứt giữa chừng: báo CHƯA hoàn tác xong kèm tên, Làm tiếp chạy lại", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], hoanTacKieu: "loi" };
    await vaoXem(page, mo);
    await page.getByRole("button", { name: "Hoàn tác lần thêm vừa rồi" }).click();
    const hop = page.getByRole("dialog", { name: "Hoàn tác lần thêm vừa rồi" });
    await hop.getByLabel(/xác nhận đây là CSDL thật/).check();
    await hop.getByRole("button", { name: "Hoàn tác", exact: true }).click();
    await expect(hop.getByText(/CHƯA hoàn tác xong — lỗi ở Trần Văn Bình/)).toBeVisible();
    await hop.getByRole("button", { name: "Làm tiếp" }).click();
    await expect(hop.getByText(/Đã gỡ 1 học viên khỏi BC2/)).toBeVisible();
    await expect(hop.getByText(/CHƯA hoàn tác xong/)).toHaveCount(0);
    expect(mo.hoanTacLan).toBe(2);
  });

  test("hoàn tác thất bại (BC2 vừa bị đóng): nêu lý do, không hiện khung xanh", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], hoanTacKieu: "that_bai" };
    await vaoXem(page, mo);
    await page.getByRole("button", { name: "Hoàn tác lần thêm vừa rồi" }).click();
    const hop = page.getByRole("dialog", { name: "Hoàn tác lần thêm vừa rồi" });
    await hop.getByLabel(/xác nhận đây là CSDL thật/).check();
    await hop.getByRole("button", { name: "Hoàn tác", exact: true }).click();
    await expect(hop.getByText(/đã đóng — không gỡ được/)).toBeVisible();
    await expect(hop.getByText(/Đã gỡ 0/)).toHaveCount(0);
  });
});

test.describe("TNB-03 → TNB-04 → TNB-05 — Checkpoint 26: lập BC2 và xem/gỡ đầu–cuối", () => {
  async function vaoBuoc2(page: Page, mo: Mo) {
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    await page.getByRole("button", { name: "Lập BC2 mới" }).click();
    await page.getByTestId("khoa-K001").getByRole("button", { name: "Chọn khóa này →" }).click();
    await expect(page.getByTestId("dai-tom-tat")).toBeVisible();
  }
  async function chonMotHocVienVaTiep(page: Page) {
    await page.getByRole("button", { name: "Bỏ chọn tất cả" }).click();
    await page.getByLabel("Tìm học viên").fill("nguyen thi hoa");
    await page.getByLabel("Tìm học viên").press("Enter");
    await page.getByRole("button", { name: /Tiếp tục/ }).click();
  }
  async function ghi(page: Page, nut: RegExp) {
    await page.getByRole("button", { name: nut }).click();
    const hop = page.getByRole("dialog", { name: "Xác nhận ghi" });
    await hop.getByLabel(/xác nhận đây là CSDL thật/).check();
    return hop;
  }

  test("C26-A liên thông: lập BC2 xong → mở BC2 vừa lập thấy đúng N học viên, Tổng ghi = HV thực tế", async ({ page }) => {
    await vaoBuoc2(page, { cacLanGoi: [], ungVien: [] });
    await chonMotHocVienVaTiep(page);
    const hop = await ghi(page, /^Lập BC2 và thêm 1 học viên$/);
    await hop.getByRole("button", { name: "Lập BC2 và thêm" }).click();
    await expect(page.getByText(/Đã thêm 1 học viên vào BC2 số 81\/2026/)).toBeVisible();
    await page.getByRole("button", { name: "Xong" }).click();
    await page.getByRole("button", { name: "Xem BC2 81/2026" }).click();
    await expect(page.getByText(/Tổng ghi\s*1\s*·\s*Học viên thực tế\s*1/)).toBeVisible();
    await expect(page.getByLabel("Chọn Học Viên Mới 1")).toBeEnabled();
  });

  test("C26-B bấm 'Lập' hai lần nhanh → mọi lệnh cùng một lo_id (server chỉ chạy một lô)", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], tre: 700 };
    await vaoBuoc2(page, mo);
    await chonMotHocVienVaTiep(page);
    const hop = await ghi(page, /^Lập BC2 và thêm 1 học viên$/);
    await hop.getByRole("button", { name: "Lập BC2 và thêm" }).dblclick();
    await expect(page.getByText(/Đã thêm 1 học viên/)).toBeVisible();
    expect(new Set(mo.lap!.map((b) => b.lo_id)).size).toBe(1);
  });

  test("C26-C F5 giữa lúc đang ghi: về danh sách, không tự gửi lại lệnh, không có Làm tiếp mồ côi", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], lapKieu: "dang_chay_mai" };
    await vaoBuoc2(page, mo);
    await chonMotHocVienVaTiep(page);
    const hop = await ghi(page, /^Lập BC2 và thêm 1 học viên$/);
    await hop.getByRole("button", { name: "Lập BC2 và thêm" }).click();
    await expect(page.getByText(/Đang ghi/)).toBeVisible();
    await page.reload();
    await expect(page.getByRole("button", { name: "Lập BC2 mới" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Làm tiếp" })).toHaveCount(0);
    expect(mo.lap).toHaveLength(1);                           // không có lệnh ghi nào tự phát sau F5
  });

  test("C26-D xóa BC2 mà server báo còn học viên (409): hiện lý do, không báo 'Đã xóa'", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], xoaKieu: "409", chiTiet: { ...CHI_TIET, hv_thuc_te: 0, xoa_duoc: true, hoc_vien: [] } };
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    await page.getByRole("button", { name: "Xem BC2 80/2026" }).click();
    await page.getByRole("button", { name: "Xóa BC2 rỗng" }).click();
    const hop = page.getByRole("dialog", { name: "Xóa BC2 rỗng" });
    await hop.getByLabel(/xác nhận đây là CSDL thật/).check();
    await hop.getByRole("button", { name: "Xóa BC2", exact: true }).click();
    await expect(hop.getByText(/còn 2 học viên/)).toBeVisible();
    await expect(hop.getByText(/Đã xóa BC2 số/)).toHaveCount(0);
  });

  test("C26-01 máy chủ đang bận ghi (409 dang_ghi): nêu lý do, chưa ghi gì, không Làm tiếp, bấm lại được", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], lapKieu: "409_dang_ghi" };
    await vaoBuoc2(page, mo);
    await chonMotHocVienVaTiep(page);
    const hop = await ghi(page, /^Lập BC2 và thêm 1 học viên$/);
    await hop.getByRole("button", { name: "Lập BC2 và thêm" }).click();
    await expect(hop.getByText(/đợi vài giây rồi thử lại/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Làm tiếp" })).toHaveCount(0);
    await expect(hop.getByRole("button", { name: "Lập BC2 và thêm" })).toBeEnabled();
    await expect(page.getByText(/Đã thêm/)).toHaveCount(0);
  });

  for (const [kieu, mong] of [
    ["409_bc2_khac_khoa", /không thuộc BC1 của khóa này/],
    ["409_bc2_da_dong", /đã đóng — không thêm học viên được/],
    ["404_bc2_khong_ton_tai", /Không có BC2 số 80\/2026/],
  ] as const) {
    test(`C26-02 server từ chối ngay (${kieu}): hiện đúng lý do nghiệp vụ, chưa ghi gì`, async ({ page }) => {
      const mo: Mo = { cacLanGoi: [], ungVien: [], lapKieu: kieu };
      await vaoBuoc2(page, mo);
      await chonMotHocVienVaTiep(page);
      const hop = await ghi(page, /^Lập BC2 và thêm 1 học viên$/);
      await hop.getByRole("button", { name: "Lập BC2 và thêm" }).click();
      await expect(hop.getByText(mong)).toBeVisible();
      await expect(page.getByText(/Đã thêm/)).toHaveCount(0);
    });
  }

  test("C26-04 mất kết nối ngay ở lệnh lập: Làm tiếp gửi lại ĐÚNG số, ngày và danh sách đã xác nhận (số gợi ý nhảy cũng không đổi)", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], lapKieu: "abort_dau", bumpSo: true };
    await vaoBuoc2(page, mo);
    await chonMotHocVienVaTiep(page);
    const hop = await ghi(page, /^Lập BC2 và thêm 1 học viên$/);
    await hop.getByRole("button", { name: "Lập BC2 và thêm" }).click();
    await expect(page.getByText(/Mất kết nối khi ghi/)).toBeVisible();
    // form mount lại và hỏi gợi ý số lần hai (mock trả 82/2026): chờ nó hiện RỒI mới Làm tiếp, để bắt đúng lỗi
    await expect(page.getByLabel("Số BC2 (= mã báo cáo)")).toHaveValue("82/2026");
    await page.getByRole("button", { name: "Làm tiếp" }).click();
    await expect(page.getByText(/Đã thêm 1 học viên/)).toBeVisible();
    expect(mo.lap).toHaveLength(2);
    expect(mo.lap![0].so_bao_cao).toBe("81/2026");
    expect(mo.lap![1]).toMatchObject({
      lo_id: mo.lap![0].lo_id, so_bao_cao: mo.lap![0].so_bao_cao, ngay_bao_cao: mo.lap![0].ngay_bao_cao,
      ds_ma_dk: mo.lap![0].ds_ma_dk, ma_kh: mo.lap![0].ma_kh,
    });
  });

  test("C26-05 dải tóm tắt = số gửi đi: 3.450 + 3 thi lại = 3.453; HV Cần xem / Không đưa được không lọt vào danh sách", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [] };
    await vaoBuoc2(page, mo);
    await page.getByRole("button", { name: /Thêm 3 HV thi lại ≤ 12 tháng/ }).click();
    await expect(page.getByTestId("dai-tom-tat")).toContainText("= 3.453");
    await page.getByRole("button", { name: /Tiếp tục/ }).click();
    const hop = await ghi(page, /^Lập BC2 và thêm 3\.453 học viên$/);
    await hop.getByRole("button", { name: "Lập BC2 và thêm" }).click();
    await expect(page.getByText(/Đã thêm/)).toBeVisible();
    const ds = mo.lap![0].ds_ma_dk as string[];
    expect(ds).toHaveLength(3453);
    expect(ds).not.toContain("X-0001");                       // Cần xem
    expect(ds).not.toContain("N-0001");                       // Không đưa được
    expect(ds).toContain("T-0001");
    expect(ds).not.toContain("T-0004");                       // thi lại cũ hơn ngưỡng: không tích sẵn
  });

  test("C26-06 lô có cảnh báo TT_XuLy_Old='11': hiện tên + nội dung, vẫn Hoàn tác được", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], lapKieu: "canh_bao" };
    await vaoBuoc2(page, mo);
    await chonMotHocVienVaTiep(page);
    const hop = await ghi(page, /^Lập BC2 và thêm 1 học viên$/);
    await hop.getByRole("button", { name: "Lập BC2 và thêm" }).click();
    await expect(page.getByText(/Nguyễn Thị Hoà:/)).toBeVisible();
    await expect(page.getByText(/gỡ ra sẽ không về đúng/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Hoàn tác lần vừa rồi" })).toBeVisible();
  });

  for (const [soHv, coThanh] of [[199, false], [200, true]] as const) {
    test(`C26-07 biên thanh tiến độ: ${soHv} học viên ${coThanh ? "CÓ" : "KHÔNG có"} thanh`, async ({ page }) => {
      const mo: Mo = { cacLanGoi: [], ungVien: [], soSan: soHv, lapKieu: "dang_chay_mai" };
      await vaoBuoc2(page, mo);
      await page.getByRole("button", { name: /Tiếp tục/ }).click();
      const hop = await ghi(page, new RegExp(`^Lập BC2 và thêm ${soHv} học viên$`));
      await hop.getByRole("button", { name: "Lập BC2 và thêm" }).click();
      if (coThanh) await expect(page.getByText(new RegExp(`Đang ghi \\d+/${soHv} học viên`))).toBeVisible();
      else {
        await expect(page.getByText(`Đang ghi ${soHv} học viên…`)).toBeVisible();
        await expect(page.getByText(/Đang ghi \d+\/\d+ học viên/)).toHaveCount(0);
      }
    });
  }

  test("C26-10 BC2 đã đóng: chỉ xem — khóa Thêm/Gỡ/Hoàn tác/Xóa và không có nút 'Đóng BC2' nào", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], chiTiet: { ...CHI_TIET, trang_thai: 1, dang_mo: false, xoa_duoc: false,
      hoc_vien: CHI_TIET.hoc_vien.map((h) => ({ ...h, go_duoc: false, ly_do_khoa: "BC2 đã đóng — không gỡ được" })) } };
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    await expect(page.getByRole("button", { name: /Đóng BC2/ })).toHaveCount(0);
    await page.getByRole("button", { name: "Xem BC2 80/2026" }).click();
    await expect(page.getByText("Đã đóng — chỉ xem")).toBeVisible();
    await expect(page.getByRole("button", { name: "+ Thêm học viên" })).toBeDisabled();
    await expect(page.getByRole("button", { name: "Hoàn tác lần thêm vừa rồi" })).toBeDisabled();
    await expect(page.getByRole("button", { name: /Gỡ 0 học viên khỏi BC2/ })).toBeDisabled();
    await expect(page.getByRole("button", { name: "Xóa BC2 rỗng" })).toBeDisabled();
    await expect(page.getByLabel("Chọn Nguyễn Thị Hoà")).toBeDisabled();
    await expect(page.getByRole("button", { name: /Đóng BC2/ })).toHaveCount(0);
  });

  test("C26-11 xóa BC2 mất kết nối: nêu 'kiểm lại rồi thử', không báo đã xóa, vẫn bấm lại được", async ({ page }) => {
    const mo: Mo = { cacLanGoi: [], ungVien: [], xoaKieu: "abort", chiTiet: { ...CHI_TIET, hv_thuc_te: 0, xoa_duoc: true, hoc_vien: [] } };
    await giaBackend(page, mo);
    await page.goto("/tot-nghiep-bc2/bao-cao-2");
    await page.getByRole("button", { name: "Xem BC2 80/2026" }).click();
    await page.getByRole("button", { name: "Xóa BC2 rỗng" }).click();
    const hop = page.getByRole("dialog", { name: "Xóa BC2 rỗng" });
    await hop.getByLabel(/xác nhận đây là CSDL thật/).check();
    await hop.getByRole("button", { name: "Xóa BC2", exact: true }).click();
    await expect(hop.getByText(/kiểm BC2 đã xóa chưa rồi thử lại/)).toBeVisible();
    await expect(hop.getByText(/Đã xóa BC2 số/)).toHaveCount(0);
    await expect(hop.getByRole("button", { name: "Xóa BC2", exact: true })).toBeEnabled();
  });
});
