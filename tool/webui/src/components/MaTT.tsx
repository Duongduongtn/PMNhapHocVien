// Mã trạng thái (TT) chỉ ghi phụ trong ngoặc đơn sau tên nghiệp vụ: "Đã vào BC2, chờ kết quả (11)".
export default function MaTT({ ma }: { ma: string | number }) {
  return <span className="text-[11px] font-normal text-muted-foreground tabular-nums">({ma})</span>;
}
