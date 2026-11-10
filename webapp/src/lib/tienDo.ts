// THU-01 (CHANGES #100) — thanh tiến độ nhập hồ sơ ở thanh nút đáy. Hàm thuần: nhận cờ hợp lệ đang dùng cho ✓/đỏ
// từng ô, trả các vạch + câu tóm tắt. Không thêm luật kiểm mới.

export type TrangThaiVach = "du" | "sai" | "trong";

/** `o` = giá trị data-o của ô trên form (để nhảy tới), riêng "gplx" là mở popup GPLX đã có. */
export interface Vach {
  o: string;
  ten: string;
  tt: TrangThaiVach;
}

export interface DauVaoTienDo {
  soCccd: string;
  hoTen: string;
  ngaySinh: string;
  noiThuongTru: string;
  ngayCap: string;
  cccdOk: boolean;
  tenOk: boolean;
  nsOk: boolean;
  nttOk: boolean;
  ngayCapOk: boolean;
  gplxLoi: boolean;
}

const vachO = (o: string, ten: string, ok: boolean, giaTri: string): Vach => ({
  o,
  ten,
  tt: ok ? "du" : giaTri.trim() ? "sai" : "trong",
});

/** 4 ô bắt buộc luôn có vạch; Ngày cấp (không bắt buộc) chỉ có vạch khi đã gõ mà sai; GPLX chỉ khi đang có bằng mà lỗi.
 *  Giới tính không tính: tự suy từ số CCCD, luôn có giá trị. */
export function vachTienDo(d: DauVaoTienDo): Vach[] {
  // Đúng thứ tự ô trên form (Ngày cấp nằm ngay sau Số CCCD) để "Còn …" nhảy tới ô thiếu đầu tiên từ trên xuống.
  const ds: Vach[] = [vachO("cccd", "Số CCCD", d.cccdOk, d.soCccd)];
  if (d.ngayCap.trim() && !d.ngayCapOk) ds.push({ o: "ngayCap", ten: "Ngày cấp", tt: "sai" });
  ds.push(
    vachO("hoTen", "Họ tên", d.tenOk, d.hoTen),
    vachO("ngaySinh", "Ngày sinh", d.nsOk, d.ngaySinh),
    vachO("ntt", "Nơi thường trú", d.nttOk, d.noiThuongTru),
  );
  if (d.gplxLoi) ds.push({ o: "gplx", ten: "GPLX đã có", tt: "sai" });
  return ds;
}

/** Tóm tắt cho chữ cạnh vạch: còn bao nhiêu ô chưa xong, ô nào cần nhảy tới trước (theo thứ tự form). */
export function tomTatTienDo(ds: Vach[]): { du: number; tong: number; con: Vach[]; xong: boolean } {
  const con = ds.filter((v) => v.tt !== "du");
  return { du: ds.length - con.length, tong: ds.length, con, xong: con.length === 0 };
}
