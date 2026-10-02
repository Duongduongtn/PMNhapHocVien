import { Icon } from "./Icon";

// UI-3 (CHANGES #18) — thanh phân trang dùng chung. Trình bày thuần: cha tự cắt dữ liệu
// theo (trang, coTrang). trang tính từ 0. Ẩn khi không có dòng nào.
export function PhanTrang({
  total,
  trang,
  coTrang,
  onTrang,
  onCoTrang,
  cacCo = [20, 50, 100],
}: {
  total: number;
  trang: number;
  coTrang: number;
  onTrang: (t: number) => void;
  onCoTrang?: (c: number) => void;
  cacCo?: number[];
}) {
  if (total <= 0) return null;
  const soTrang = Math.max(1, Math.ceil(total / coTrang));
  const tu = trang * coTrang + 1;
  const den = Math.min(total, (trang + 1) * coTrang);
  return (
    <div className="flex items-center justify-between gap-2 flex-wrap text-[13px] py-3 px-4 lg:px-0">
      <span className="text-muted-foreground tabular-nums">{tu}–{den} / {total}</span>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => onTrang(Math.max(0, trang - 1))}
          disabled={trang === 0}
          aria-label="Trang trước"
          className="h-8 w-8 rounded-md border border-border inline-flex items-center justify-center hover:bg-muted transition-colors disabled:opacity-40"
        >
          <Icon name="chevronLeft" className="w-4 h-4" />
        </button>
        <span className="tabular-nums">Trang {trang + 1}/{soTrang}</span>
        <button
          type="button"
          onClick={() => onTrang(trang + 1 < soTrang ? trang + 1 : trang)}
          disabled={trang + 1 >= soTrang}
          aria-label="Trang sau"
          className="h-8 w-8 rounded-md border border-border inline-flex items-center justify-center hover:bg-muted transition-colors disabled:opacity-40"
        >
          <Icon name="chevronRight" className="w-4 h-4" />
        </button>
        {onCoTrang && (
          <select
            value={coTrang}
            onChange={(e) => onCoTrang(Number(e.target.value))}
            aria-label="Số dòng mỗi trang"
            className="h-8 rounded-md border border-border bg-card px-2 text-[13px]"
          >
            {cacCo.map((n) => (
              <option key={n} value={n}>{n}/trang</option>
            ))}
          </select>
        )}
      </div>
    </div>
  );
}
