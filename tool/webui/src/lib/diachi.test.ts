import { describe, it, expect } from "vitest";
import { tachDiaChiGoc } from "./diachi";

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
