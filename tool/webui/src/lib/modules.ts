// Đăng ký phân hệ của tool. Thêm phân hệ mới = thêm 1 phần tử vào MODULES
// (không sửa khung ToolLayout). Mỗi phân hệ có sub-nav riêng, màu nhấn, và
// CSDL mà nó ghi vào (banner nhắc để tránh thao tác nhầm giữa các phân hệ).

export type Accent = "primary" | "sync" | "kq";

/** Nhóm theo CSDL: DB Nạp → cầu nối đồng bộ → DB đích. Màu nhóm = màu nhấn của phân hệ trong nhóm. */
export type Nhom = "nap" | "cau-noi" | "dich";

export const NHOM_INFO: Record<Nhom, { ten: string; db: string; chip: string; dot: string }> = {
  nap: { ten: "DB Nạp", db: "GPLX_CSDT", chip: "text-primary bg-accent border-primary/30", dot: "bg-primary" },
  "cau-noi": { ten: "Cầu nối", db: "Nạp → đích", chip: "text-sync bg-sync-soft border-sync-border", dot: "bg-sync" },
  dich: { ten: "DB đích", db: "GPLX_CDB_CSDT", chip: "text-kq bg-kq-soft border-kq-border", dot: "bg-kq" },
};

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
  /** Nhóm CSDL — quyết định vạch ngăn + tiêu đề nhóm ở menu trái. */
  nhom: Nhom;
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
    nhom: "nap",
    base: "/tool",
    subnav: [
      { to: "/tool/nap", label: "Nạp hồ sơ", icon: "file" },
      { to: "/tool/tra-cuu", label: "Tra cứu DB", icon: "search" },
      { to: "/tool/tao-khoa", label: "Tạo khóa", icon: "plus" },
    ],
  },
  {
    id: "tnbc2",
    label: "Tốt nghiệp & BC2",
    icon: "file",
    accent: "primary",
    nhom: "nap",
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
  {
    id: "sync",
    label: "Đồng bộ CDB",
    icon: "refresh",
    accent: "sync",
    nhom: "cau-noi",
    base: "/sync",
    db: "GPLX_CDB_CSDT",
    subnav: [
      { to: "/sync/ban-dong-bo", label: "Bàn đồng bộ", icon: "refresh" },
      { to: "/sync/tra-cuu", label: "Tra cứu CDB", icon: "search" },
      { to: "/sync/lich-su", label: "Lịch sử & Hủy sync", icon: "clock" },
    ],
  },
  {
    id: "phancong",
    label: "Phân công GV – xe",
    icon: "calendar",
    accent: "kq",
    nhom: "dich",
    base: "/phan-cong",
    db: "GPLX_CDB_CSDT",
    subnav: [
      { to: "/phan-cong/theo-khoa", label: "Phân công theo khóa", icon: "calendar" },
      { to: "/phan-cong/ra-soat", label: "Rà soát khóa", icon: "search" },
      { to: "/phan-cong/han-giay-to", label: "Hạn giấy tờ", icon: "clock" },
    ],
  },
  {
    id: "ketqua",
    label: "Kết quả đào tạo",
    icon: "check",
    accent: "kq",
    nhom: "dich",
    base: "/ket-qua",
    db: "GPLX_CDB_CSDT",
    subnav: [
      { to: "/ket-qua/cap-nhat", label: "Cập nhật KQĐT", icon: "check" },
      { to: "/ket-qua/ket-xuat", label: "Theo dõi kết xuất", icon: "clock" },
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
