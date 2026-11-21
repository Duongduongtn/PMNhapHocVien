// TNB-07 (CHANGES #104) — nhãn trạng thái BC2: 0 đang mở · 1 đã đóng (phần mềm cũ đóng) · 2 chưa đóng nhưng đã gửi / có kết quả.
// Khác 0 là khóa: không thêm / gỡ / hoàn tác / xóa ở tool, chỉ xem và in.
const kieu = "text-[11px] font-semibold px-2 rounded-full border whitespace-nowrap";

export default function TrangThaiBc2({ tt, hvKetQua, chiXem }: { tt: number; hvKetQua?: number; chiXem?: boolean }) {
  if (tt === 0) return <span className={`${kieu} text-tn bg-tn-soft border-tn-border`}>Đang mở</span>;
  if (tt === 2)
    return (
      <span className={`${kieu} text-warning bg-warning/10 border-warning/40`}
        title={`${hvKetQua ?? "Có"} học viên trong BC2 đã gửi hoặc đã có kết quả — BC2 bị khóa, chỉ xem và in`}>
        Đã có kết quả{chiXem ? " — chỉ xem" : ""}
      </span>
    );
  return <span className={`${kieu} text-muted-foreground bg-muted border-border`}>Đã đóng{chiXem ? " — chỉ xem" : ""}</span>;
}
