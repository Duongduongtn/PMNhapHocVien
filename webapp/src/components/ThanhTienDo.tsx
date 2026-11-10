import { tomTatTienDo, type Vach } from "../lib/tienDo";

// THU-01 (CHANGES #100): tiến độ nhập hồ sơ, gắn ở mép trên thanh nút dính đáy (máy tính: ngay trên hàng nút cuối form).
// Mỗi ô bắt buộc một vạch: đủ xanh · sai đỏ · chưa nhập xám. Bấm chữ "Còn …" → nhảy tới ô thiếu đầu tiên.
const MAU: Record<Vach["tt"], string> = {
  du: "bg-success",
  sai: "bg-destructive",
  trong: "bg-muted-foreground/25",
};

export function ThanhTienDo({ ds, onNhay }: { ds: Vach[]; onNhay: (o: string) => void }) {
  const { du, tong, con, xong } = tomTatTienDo(ds);
  return (
    <div className="mb-2 flex items-center gap-2.5 min-h-[24px]" data-testid="tien-do">
      <div className="flex gap-1 shrink-0" aria-hidden="true">
        {ds.map((v) => (
          <span key={v.o} title={v.ten} className={"h-1.5 w-5 rounded-full transition-colors duration-200 " + MAU[v.tt]} />
        ))}
      </div>
      {/* Trình đọc màn hình chỉ đọc câu ngắn khi số mục đổi; nút nằm ngoài vùng đọc nên không đọc lại câu dài. */}
      <span role="status" className="sr-only">{xong ? `Đủ ${du}/${tong}, sẵn sàng lưu` : `Còn ${con.length} mục`}</span>
      <div className="min-w-0 flex-1">
        {xong ? (
          <span aria-hidden="true" className="text-[12px] font-medium text-success">Đủ {du}/{tong} — sẵn sàng lưu</span>
        ) : (
          <button
            type="button"
            onClick={() => onNhay(con[0].o)}
            className="block w-full truncate text-left text-[12px] text-muted-foreground hover:text-foreground"
            aria-label={`Còn: ${con.map((v) => `${v.ten} ${v.tt === "sai" ? "sai" : "chưa nhập"}`).join(", ")}. Bấm để tới ${con[0].ten}`}
          >
            Còn {con.length}: <strong className="font-semibold text-foreground">{con.map((v) => v.ten).join(" · ")}</strong>
            <span className="ml-1 text-primary">›</span>
          </button>
        )}
      </div>
    </div>
  );
}
