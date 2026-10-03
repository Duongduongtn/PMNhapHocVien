import { describe, it, expect } from "vitest";
import { tachDiaChiGoc, lamTuoiNhapDiaChi } from "./diachi";

describe("tachDiaChiGoc (NAP-03 CHANGES #19)", () => {
  it("tách chuỗi có tiền tố đầy đủ", () => {
    expect(tachDiaChiGoc("Xã Phú Nghĩa, Huyện Bù Gia Mập, Tỉnh Bình Phước")).toEqual({
      tinh: "Bình Phước", huyen: "Bù Gia Mập", xa: "Phú Nghĩa", chiTiet: "",
    });
  });

  it("có số nhà/thôn ở đầu → dồn vào chi tiết", () => {
    expect(tachDiaChiGoc("Số 12, Ấp 3, Xã An Phước, Huyện Long Thành, Tỉnh Đồng Nai")).toEqual({
      tinh: "Đồng Nai", huyen: "Long Thành", xa: "An Phước", chiTiet: "Số 12, Ấp 3",
    });
  });

  it("Phường + Thành phố", () => {
    expect(tachDiaChiGoc("Phường Cầu Ông Lãnh, Thành phố Hồ Chí Minh")).toEqual({
      tinh: "Hồ Chí Minh", huyen: "", xa: "Cầu Ông Lãnh", chiTiet: "",
    });
  });

  it("không tiền tố, 3 phần → suy vị trí (cuối = tỉnh)", () => {
    expect(tachDiaChiGoc("An Phước, Long Thành, Đồng Nai")).toEqual({
      tinh: "Đồng Nai", huyen: "Long Thành", xa: "An Phước", chiTiet: "",
    });
  });

  it("không tiền tố, 4 phần → phần đầu là chi tiết", () => {
    expect(tachDiaChiGoc("Số 5, An Phước, Long Thành, Đồng Nai")).toEqual({
      tinh: "Đồng Nai", huyen: "Long Thành", xa: "An Phước", chiTiet: "Số 5",
    });
  });

  it("không tiền tố, 2 phần → xã + tỉnh", () => {
    expect(tachDiaChiGoc("An Phước, Đồng Nai")).toEqual({
      tinh: "Đồng Nai", huyen: "", xa: "An Phước", chiTiet: "",
    });
  });

  it("hỗn hợp: xã KHÔNG tiền tố nhưng huyện/tỉnh có → lượt 3 nhận xã (CHANGES #19)", () => {
    expect(tachDiaChiGoc("Số 5, An Phước, Huyện Long Thành, Tỉnh Đồng Nai")).toEqual({
      tinh: "Đồng Nai", huyen: "Long Thành", xa: "An Phước", chiTiet: "Số 5",
    });
    expect(tachDiaChiGoc("An Phước, Huyện Long Thành, Tỉnh Đồng Nai")).toEqual({
      tinh: "Đồng Nai", huyen: "Long Thành", xa: "An Phước", chiTiet: "",
    });
    expect(tachDiaChiGoc("Số 5, Ấp 3, An Phước, Huyện Long Thành, Tỉnh Đồng Nai")).toEqual({
      tinh: "Đồng Nai", huyen: "Long Thành", xa: "An Phước", chiTiet: "Số 5, Ấp 3",
    });
  });

  it("chuỗi rỗng / null → tất cả trống", () => {
    expect(tachDiaChiGoc("")).toEqual({ tinh: "", huyen: "", xa: "", chiTiet: "" });
    expect(tachDiaChiGoc(null)).toEqual({ tinh: "", huyen: "", xa: "", chiTiet: "" });
    expect(tachDiaChiGoc(undefined)).toEqual({ tinh: "", huyen: "", xa: "", chiTiet: "" });
  });

  it("một phần duy nhất, không rõ → về chi tiết", () => {
    expect(tachDiaChiGoc("Chỗ nào đó")).toEqual({ tinh: "", huyen: "", xa: "", chiTiet: "Chỗ nào đó" });
  });

  it("bỏ khoảng trắng thừa + segment rỗng", () => {
    expect(tachDiaChiGoc("  Xã A , , Tỉnh B ")).toEqual({
      tinh: "B", huyen: "", xa: "A", chiTiet: "",
    });
  });
});

// BUG-04: kéo lại khi collector đã sửa địa chỉ → reset nháp địa chỉ đã map theo raw cũ.
describe("lamTuoiNhapDiaChi (BUG-04)", () => {
  const nhap = (over: Partial<{ diaChi: unknown; chiTiet: string; tick: number[] | null }>) =>
    ({ diaChi: null, chiTiet: "", jp2: null, anhPreview: null, tick: null, ...over });

  it("raw ĐỔI + nháp đã map → reset diaChi, điền lại chiTiet từ raw mới, GIỮ giấy tờ", () => {
    const nhapCu = { u1: nhap({ diaChi: { ma_dvhc: "XA_CU" }, chiTiet: "số 1 cũ", tick: [3, 5] }) };
    const rawCu = new Map([["u1", "Xã Cũ, Huyện X, Tỉnh Y"]]);
    const moi = [{ uuid: "u1", noi_tt_raw: "12 Lê Lợi, Phường Mới, Tỉnh Y" }];
    const kq = lamTuoiNhapDiaChi(nhapCu, rawCu, moi);
    expect(kq.u1.diaChi).toBeNull();            // địa chỉ map cũ bị xóa → buộc map lại
    expect(kq.u1.chiTiet).toBe("12 Lê Lợi");    // chiTiet điền lại từ raw mới
    expect(kq.u1.tick).toEqual([3, 5]);         // giấy tờ GIỮ nguyên
  });

  it("raw KHÔNG đổi → giữ nguyên nháp (cùng tham chiếu object)", () => {
    const nhapCu = { u1: nhap({ diaChi: { ma_dvhc: "XA" }, chiTiet: "số 1" }) };
    const rawCu = new Map([["u1", "Xã A, Tỉnh B"]]);
    const moi = [{ uuid: "u1", noi_tt_raw: "Xã A, Tỉnh B" }];
    const kq = lamTuoiNhapDiaChi(nhapCu, rawCu, moi);
    expect(kq).toBe(nhapCu);                     // không đổi gì → cùng reference
    expect(kq.u1.diaChi).toEqual({ ma_dvhc: "XA" });
  });

  it("HV chưa có nháp → bỏ qua (effect tự điền lo)", () => {
    const kq = lamTuoiNhapDiaChi({}, new Map([["u1", "Xã A"]]), [{ uuid: "u1", noi_tt_raw: "Xã B" }]);
    expect(kq).toEqual({});
  });
});
