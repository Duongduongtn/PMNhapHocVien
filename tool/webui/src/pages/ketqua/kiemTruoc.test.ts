import { describe, it, expect } from "vitest";
import { hienThiKiemTruoc, nhanCanhBao } from "./kiemTruoc";
import type { KiemTruocKQD } from "../../lib/api";

const base = (thieu: KiemTruocKQD["thieu"]): KiemTruocKQD => ({
  ma_kh: "KX", tong: 8, du: 2, mo_to_bo_qua: 0, thieu,
  dem: { chua_co_diem: 0, thieu_mon: 0, thieu_gio_km: 0, thieu_ket_luan: 0 },
});
const hv = (ma: string, ly_do: string[], extra: Partial<KiemTruocKQD["thieu"][number]> = {}) => ({
  ma_dk: ma, ho_ten: "HV " + ma, so_cccd: "0010" + ma, tt_xuly: "03", ly_do, mon_thieu: [], canh_bao: [], ...extra,
});

describe("hienThiKiemTruoc — quyết định 12/10/2026 (KQD-07)", () => {
  it("HV chưa có điểm: bỏ chip thieu_gio_km, đếm lại", () => {
    const r = hienThiKiemTruoc(base([
      hv("1", ["chua_co_diem", "thieu_gio_km"]),
      hv("2", ["chua_co_diem", "thieu_gio_km"]),
      hv("3", ["thieu_mon", "thieu_gio_km"], { mon_thieu: ["mo_phong"] }),
    ]));
    expect(r.thieu[0].ly_do).toEqual(["chua_co_diem"]);
    expect(r.thieu[2].ly_do).toEqual(["thieu_mon", "thieu_gio_km"]); // có điểm → vẫn hiện chip giờ/km
    expect(r.dem).toEqual({ chua_co_diem: 2, thieu_mon: 1, thieu_gio_km: 1 });
  });
  it("không đụng danh sách gốc (hàm thuần)", () => {
    const goc = base([hv("1", ["chua_co_diem", "thieu_gio_km"])]);
    hienThiKiemTruoc(goc);
    expect(goc.thieu[0].ly_do).toEqual(["chua_co_diem", "thieu_gio_km"]);
  });
});

describe("nhanCanhBao", () => {
  it("nhãn vàng giống mock", () => {
    expect(nhanCanhBao({ loai: "gio_duong", gia_tri: 18, goi_y: 20 })).toBe("Giờ đường 18 < 20");
    expect(nhanCanhBao({ loai: "km_duong", gia_tri: 700, goi_y: 810 })).toBe("Km đường 700 < 810");
  });
});
