// Đăng ký phân hệ của tool. Thêm phân hệ mới = thêm 1 phần tử vào MODULES
// (không sửa khung ToolLayout). Mỗi phân hệ có sub-nav riêng, màu nhấn, và
// CSDL mà nó ghi vào (banner nhắc để tránh thao tác nhầm giữa các phân hệ).

export type Accent = "primary" | "sync" | "kq" | "pc" | "tn";

export interface SubNav {
  to: string;
  label: string;
  icon: string; // tên trong bộ Icon
}

export interface ModuleDef {
  id: string;
  label: string;
  icon: string;
  accent: Accent;
  /** Tiền tố route để xác định phân hệ đang mở. */
  base: string;
  /** Tên CSDL phân hệ ghi vào — hiện ở banner nhắc. Bỏ trống nếu không ghi DB. */
  db?: string;
  /** true = `db` là DB Nạp (GPLX_CSDT) của máy CSĐT, không phải CSDL đích (CDB) — banner không gọi `db-dich-info`. */
  dbNap?: boolean;
  subnav: SubNav[];
  /** Phân hệ dự kiến, chưa dựng — hiện mờ, không bấm được. */
  comingSoon?: boolean;
}

export const MODULES: ModuleDef[] = [
  {
    id: "nap",
    label: "Nạp hồ sơ",
    icon: "file",
    accent: "primary",
    base: "/tool",
    subnav: [
      { to: "/tool/nap", label: "Nạp hồ sơ", icon: "file" },
      { to: "/tool/tra-cuu", label: "Tra cứu DB", icon: "search" },
      { to: "/tool/tao-khoa", label: "Tạo khóa", icon: "plus" },
    ],
  },
  {
    id: "sync",
    label: "Đồng bộ CDB",
    icon: "refresh",
    accent: "sync",
    base: "/sync",
    db: "GPLX_CDB_CSDT",
    subnav: [
      { to: "/sync/ban-dong-bo", label: "Bàn đồng bộ", icon: "refresh" },
      { to: "/sync/tra-cuu", label: "Tra cứu CDB", icon: "search" },
      { to: "/sync/lich-su", label: "Lịch sử & Hủy sync", icon: "clock" },
    ],
  },
  {
    id: "ketqua",
    label: "Kết quả đào tạo",
    icon: "check",
    accent: "kq",
    base: "/ket-qua",
    db: "GPLX_CDB_CSDT",
    subnav: [
      { to: "/ket-qua/cap-nhat", label: "Cập nhật KQĐT", icon: "check" },
      { to: "/ket-qua/ket-xuat", label: "Theo dõi kết xuất", icon: "clock" },
    ],
  },
  {
    id: "phancong",
    label: "Phân công GV – xe",
    icon: "calendar",
    accent: "pc",
    base: "/phan-cong",
    db: "GPLX_CDB_CSDT",
    subnav: [
      { to: "/phan-cong/theo-khoa", label: "Phân công theo khóa", icon: "calendar" },
      { to: "/phan-cong/ra-soat", label: "Rà soát khóa", icon: "search" },
    ],
  },
  {
    id: "tnbc2",
    label: "Tốt nghiệp & BC2",
    icon: "file",
    accent: "tn",
    base: "/tot-nghiep-bc2",
    db: "GPLX_CSDT",
    dbNap: true,
    subnav: [
      { to: "/tot-nghiep-bc2/tot-nghiep", label: "Tốt nghiệp (ô tô)", icon: "check" },
      { to: "/tot-nghiep-bc2/bao-cao-2", label: "Báo cáo 2", icon: "file" },
      { to: "/tot-nghiep-bc2/cuu-trang-thai", label: "Học viên không tìm thấy", icon: "search" },
      { to: "/tot-nghiep-bc2/nhat-ky", label: "Nhật ký", icon: "clock" },
    ],
  },
];

/** Phân hệ ứng với đường dẫn hiện tại (so khớp tiền tố `base` dài nhất). */
export function moduleForPath(pathname: string): ModuleDef {
  const match = [...MODULES]
    .filter((m) => !m.comingSoon)
    .sort((a, b) => b.base.length - a.base.length)
    .find((m) => pathname === m.base || pathname.startsWith(m.base + "/"));
  return match ?? MODULES[0];
}
