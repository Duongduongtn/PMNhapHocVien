import { useRef, useState, type ReactNode } from "react";

// Danh sách ảo đơn giản: chỉ dựng các dòng đang nhìn thấy (dòng cao cố định). Dùng cho nhóm ~3.450 học viên.
export default function VirtualList<T>({
  items,
  rowHeight,
  maxHeight,
  keyOf,
  render,
  label,
}: {
  items: T[];
  rowHeight: number;
  maxHeight: number;
  keyOf: (item: T) => string;
  render: (item: T) => ReactNode;
  label?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [top, setTop] = useState(0);
  const cao = Math.min(maxHeight, items.length * rowHeight);
  const batDau = Math.max(0, Math.floor(top / rowHeight) - 6);
  const ketThuc = Math.min(items.length, Math.ceil((top + cao) / rowHeight) + 6);
  return (
    <div ref={ref} role="list" aria-label={label} onScroll={(e) => setTop(e.currentTarget.scrollTop)}
      style={{ height: cao }} className="overflow-auto">
      <div style={{ height: items.length * rowHeight, position: "relative" }}>
        {items.slice(batDau, ketThuc).map((it, i) => (
          <div key={keyOf(it)} role="listitem"
            style={{ position: "absolute", top: (batDau + i) * rowHeight, height: rowHeight, left: 0, right: 0 }}>
            {render(it)}
          </div>
        ))}
      </div>
    </div>
  );
}
