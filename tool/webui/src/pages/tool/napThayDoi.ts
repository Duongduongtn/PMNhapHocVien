// NAP-08 — nhãn tiếng Việt cho mã trường app web vừa đổi (backend chỉ trả mã, không trả giá trị cá nhân).
const NHAN: Record<string, string> = {
  "tt:so_cccd": "Số căn cước",
  "tt:so_cmnd_cu": "Số CMND cũ",
  "tt:ho_ten": "Họ tên",
  "tt:ngay_sinh": "Ngày sinh",
  "tt:gioi_tinh": "Giới tính",
  "tt:noi_tt_raw": "Nơi thường trú",
  "tt:ngay_cap": "Ngày cấp",
  "tt:noi_cap_cccd": "Nơi cấp",
  gplx: "GPLX",
  anh: "Ảnh",
};

// Thứ tự hiển thị: ảnh và GPLX trước (ảnh hưởng nạp nhiều nhất), rồi các trường thông tin.
const THU_TU = ["anh", "gplx", "tt:ho_ten", "tt:so_cccd", "tt:so_cmnd_cu", "tt:ngay_sinh", "tt:gioi_tinh", "tt:noi_tt_raw", "tt:ngay_cap", "tt:noi_cap_cccd"];

/** Các nhãn để hiện, đã sắp thứ tự; bỏ mã lạ và mã `dc_reset` (đó là ghi chú, xem `canMapLai`). */
export function nhanThayDoi(truong: string[]): string[] {
  return THU_TU.filter((m) => truong.includes(m)).map((m) => NHAN[m]);
}

/** Địa chỉ nháp đã bị reset vì nơi thường trú đổi → nhân viên phải map lại. */
export function canMapLai(truong: string[]): boolean {
  return truong.includes("dc_reset");
}

/** Dòng tóm tắt dùng cho chip tooltip và danh sách: "Ảnh · Họ tên · Nơi thường trú (cần map lại)". */
export function tomTatThayDoi(truong: string[]): string {
  const ds = nhanThayDoi(truong).map((n) => (n === "Nơi thường trú" && canMapLai(truong) ? `${n} (cần map lại)` : n));
  return ds.join(" · ");
}

/** "2026-11-04T09:12:00" → "04/11/2026 09:12"; không đọc được thì trả nguyên chuỗi. */
export function gioThayDoi(iso: string): string {
  const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
  return m ? `${m[3]}/${m[2]}/${m[1]} ${m[4]}:${m[5]}` : iso;
}
