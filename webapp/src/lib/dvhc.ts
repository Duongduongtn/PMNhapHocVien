// Gợi ý Tỉnh/Xã-Phường cho ô "Nơi thường trú" (phương án A: nhập tự do + gợi ý, không ép chọn).
// Dữ liệu đơn vị hành chính 2 cấp 2025 (34 tỉnh + 3.321 xã/phường) nhúng ở src/data/dvhc-2025.json,
// nguồn thanglequoc/vietnamese-provinces-database (lấy từ danhmuchanhchinh.gso.gov.vn).
// Nạp lười (dynamic import) — chỉ tải ~65KB khi user chạm vào ô địa chỉ lần đầu, không nặng bundle.
// Khớp KHÔNG DẤU + gõ một phần (dùng boDau giống ô tìm kiếm màn "Hồ sơ đã gửi"); hiển thị đủ dấu.

import { boDau } from "./text";

interface MucGoi {
  nhan: string; // chuỗi đầy đủ dấu để hiển thị + điền: "Phường Ba Đình, Thành phố Hà Nội"
  khoa: string; // chuỗi bỏ dấu để so khớp: "phuong ba dinh" (xã) hoặc "thanh pho ha noi" (tỉnh)
  uuTien: number; // 0 = xã/phường (ưu tiên trước), 1 = tỉnh/thành
}

let CACHE: MucGoi[] | null = null;

async function nap(): Promise<MucGoi[]> {
  if (CACHE) return CACHE;
  const data = (await import("../data/dvhc-2025.json")).default as {
    provinces: { name: string; wards: string[] }[];
  };
  const ds: MucGoi[] = [];
  for (const p of data.provinces) {
    ds.push({ nhan: p.name, khoa: boDau(p.name), uuTien: 1 });
    for (const w of p.wards) ds.push({ nhan: `${w}, ${p.name}`, khoa: boDau(w), uuTien: 0 });
  }
  CACHE = ds;
  return ds;
}

// Gợi ý theo đoạn đang gõ (đã trim). < 2 ký tự → không gợi ý (tránh nhảy danh sách lúc mới gõ).
// Xếp hạng: khớp ở đầu chuỗi trước, xã trước tỉnh, nhãn ngắn trước. Trả tối đa `gioiHan` nhãn.
export async function goiYDiaChi(doan: string, gioiHan = 8): Promise<string[]> {
  const q = boDau(doan);
  if (q.length < 2) return [];
  const ds = await nap();
  return ds
    .map((m) => ({ m, vt: m.khoa.indexOf(q) }))
    .filter((x) => x.vt >= 0)
    .sort((a, b) => a.vt - b.vt || a.m.uuTien - b.m.uuTien || a.m.nhan.length - b.m.nhan.length)
    .slice(0, gioiHan)
    .map((x) => x.m.nhan);
}
