import { afterEach, describe, expect, it, vi } from "vitest";
import {
  chiTietBc2,
  cuuChuyen,
  ghiTotNghiep,
  goHvKhoiBc2,
  hoanTacLoThem,
  huyTotNghiep,
  lapBc2,
  LoiTnbc2,
  taoBc2,
  taoLoId,
  xoaBc2,
} from "./tnbc2Api";

// TNB-01 — lớp gọi API: biến lỗi của server thành LoiTnbc2, đường dẫn BC2 có dấu `/`, mọi lệnh GHI kèm cổng xác nhận.

type Goi = { url: string; method: string; body: Record<string, unknown> | undefined };
const cuocGoi: Goi[] = [];

function gia(status: number, body: unknown, textStatus = "") {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      cuocGoi.push({
        url,
        method: init?.method ?? "GET",
        body: typeof init?.body === "string" ? JSON.parse(init.body) : undefined,
      });
      return new Response(typeof body === "string" ? body : JSON.stringify(body), { status, statusText: textStatus });
    }),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  cuocGoi.length = 0;
});

describe("TNB-01 — lỗi từ server thành LoiTnbc2", () => {
  it("409 có detail {ma, noi_dung, canh_bao[]} → giữ nguyên mã, http và dữ liệu kèm theo", async () => {
    gia(409, { detail: { ma: "can_xac_nhan_canh_bao", noi_dung: "Cần xem cảnh báo", canh_bao: [{ ma: "khoa_cu" }] } });
    const loi = await ghiTotNghiep("lo-0000001", "K001", [], {} as never, false).catch((e) => e);
    expect(loi).toBeInstanceOf(LoiTnbc2);
    expect(loi.ma).toBe("can_xac_nhan_canh_bao");
    expect(loi.http).toBe(409);
    expect(loi.message).toBe("Cần xem cảnh báo");
    expect(loi.duLieu.canh_bao).toEqual([{ ma: "khoa_cu" }]);
  });

  it("422 của pydantic (detail là mảng) → loi_he_thong, không thành [object Object]", async () => {
    gia(422, { detail: [{ loc: ["body", "dong"], msg: "field required" }] }, "Unprocessable Entity");
    const loi = await ghiTotNghiep("lo-0000001", "K001", [], {} as never, false).catch((e) => e);
    expect(loi.ma).toBe("loi_he_thong");
    expect(loi.message).toBe("422 Unprocessable Entity");
    expect(loi.message).not.toContain("object");
  });

  it("5xx không có JSON → báo mã và tên trạng thái HTTP", async () => {
    gia(502, "Bad Gateway", "Bad Gateway");
    const loi = await chiTietBc2("03/BCII/2026").catch((e) => e);
    expect(loi).toBeInstanceOf(LoiTnbc2);
    expect(loi.http).toBe(502);
    expect(loi.message).toBe("502 Bad Gateway");
  });
});

describe("TNB-01 — đường dẫn và cổng xác nhận", () => {
  it("số BC2 có dấu / được mã hóa trong đường dẫn", async () => {
    gia(200, {});
    await chiTietBc2("03/BCII/2026");
    expect(cuocGoi[0].url).toContain("/local/tnbc2/bc2/03%2FBCII%2F2026");
    expect(cuocGoi[0].url).not.toContain("03/BCII/2026");
  });

  it("mọi lệnh GHI gửi xac_nhan_csdl_that = true", async () => {
    gia(200, {});
    const chung = { so_so_tn: "", ngay_vao_so: "", so_quyet_dinh: "", ngay_ra_qd: "", ngay_in: "" };
    await ghiTotNghiep("lo-0000001", "K001", [], chung, true);
    await huyTotNghiep("lo-0000002", "K001", ["C-0001"]);
    await taoBc2({ ma_kh: "K001", so_bao_cao: "03/BCII", ngay_bao_cao: "", ghi_chu: "", da_xem_canh_bao: false });
    await lapBc2({ lo_id: "lo-0000003", ma_kh: "K001", ma_bc2: "", so_bao_cao: "", ngay_bao_cao: "", ghi_chu: "", ds_ma_dk: [], da_xem_canh_bao: false });
    await goHvKhoiBc2("03/BCII/2026", "lo-0000004", [], false);
    await hoanTacLoThem("03/BCII/2026", "lo-0000005");
    await cuuChuyen("lo-0000006", "C-0001", "14", "Nhập nhầm trạng thái", "oto");
    expect(cuocGoi.length).toBe(7);
    for (const c of cuocGoi) expect(c.body?.xac_nhan_csdl_that, c.url).toBe(true);
  });

  it("xóa BC2 gửi xac_nhan_csdl_that trên query", async () => {
    gia(200, {});
    await xoaBc2("03/BCII/2026");
    expect(cuocGoi[0].method).toBe("DELETE");
    expect(cuocGoi[0].url).toContain("xac_nhan_csdl_that=true");
  });
});

describe("TNB-01 — mã lô", () => {
  it("taoLoId luôn khớp luật server (8–64 ký tự chữ/số/gạch) và không trùng", () => {
    const ds = Array.from({ length: 50 }, () => taoLoId());
    for (const id of ds) expect(id).toMatch(/^[A-Za-z0-9_-]{8,64}$/);
    expect(new Set(ds).size).toBe(50);
  });
});
