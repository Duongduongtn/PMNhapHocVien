import { describe, expect, it } from "vitest";
import { tomTatTienDo, vachTienDo, type DauVaoTienDo } from "./tienDo";

const trong: DauVaoTienDo = {
  soCccd: "", hoTen: "", ngaySinh: "", noiThuongTru: "", ngayCap: "",
  cccdOk: false, tenOk: false, nsOk: false, nttOk: false, ngayCapOk: false, gplxLoi: false,
};
const du: DauVaoTienDo = {
  soCccd: "079200000001", hoTen: "NGUYỄN VĂN AN", ngaySinh: "01/05/1990", noiThuongTru: "Số 5",
  ngayCap: "", cccdOk: true, tenOk: true, nsOk: true, nttOk: true, ngayCapOk: false, gplxLoi: false,
};

describe("THU-01 thanh tiến độ nhập hồ sơ (CHANGES #100)", () => {
  it("form trống: 4 vạch xám, còn 4, nhảy tới Số CCCD trước", () => {
    const ds = vachTienDo(trong);
    expect(ds.map((v) => v.tt)).toEqual(["trong", "trong", "trong", "trong"]);
    const t = tomTatTienDo(ds);
    expect([t.du, t.tong, t.con.length, t.con[0].o]).toEqual([0, 4, 4, "cccd"]);
  });

  it("gõ dở thì vạch đỏ, chưa gõ thì xám", () => {
    const ds = vachTienDo({ ...du, soCccd: "0792", cccdOk: false, noiThuongTru: "", nttOk: false });
    expect(ds.map((v) => v.tt)).toEqual(["sai", "du", "du", "trong"]);
    expect(tomTatTienDo(ds).con.map((v) => v.ten)).toEqual(["Số CCCD", "Nơi thường trú"]);
  });

  it("đủ 4 ô: xong, Đủ 4/4", () => {
    const t = tomTatTienDo(vachTienDo(du));
    expect([t.xong, t.du, t.tong]).toEqual([true, 4, 4]);
  });

  it("Ngày cấp trống không tính; gõ sai thì thêm vạch đỏ; GPLX lỗi thêm vạch mở popup", () => {
    expect(vachTienDo({ ...du, ngayCap: "" })).toHaveLength(4);
    const ds = vachTienDo({ ...du, ngayCap: "31/02/2020", ngayCapOk: false, gplxLoi: true });
    expect(ds.map((v) => v.o)).toEqual(["cccd", "ngayCap", "hoTen", "ngaySinh", "ntt", "gplx"]); // đúng thứ tự form
    expect(ds[1]).toEqual({ o: "ngayCap", ten: "Ngày cấp", tt: "sai" });
    expect(ds[5]).toEqual({ o: "gplx", ten: "GPLX đã có", tt: "sai" });
    expect(tomTatTienDo(ds).xong).toBe(false);
    expect(vachTienDo({ ...du, ngayCap: "01/01/2020", ngayCapOk: true })).toHaveLength(4);
  });

  it("Họ tên có chữ nhưng quá dài (tenOk=false) → vạch đỏ, không phải xám", () => {
    const ds = vachTienDo({ ...du, tenOk: false });
    expect(ds[1]).toEqual({ o: "hoTen", ten: "Họ tên", tt: "sai" });
  });
});
