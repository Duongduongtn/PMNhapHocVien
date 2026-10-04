import { useState } from "react";
import { boDau } from "../lib/format";

// Ô gõ-để-lọc dùng chung (NAP-03 địa chỉ, SYNC-01 chọn khóa): gõ tên (không dấu
// cũng khớp nhờ boDau) → danh sách gợi ý lọc dần → bấm/Enter chọn. Nhanh hơn
// dropdown khi danh sách dài (nhiều xã / nhiều khóa trong năm).
export function ComboLoc({
  value,
  options,
  onChon,
  placeholder,
  disabled,
  className,
}: {
  value: string;
  options: { ma: string; ten: string }[];
  onChon: (ma: string) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}) {
  const [q, setQ] = useState("");
  const [mo, setMo] = useState(false);
  const tenDaChon = options.find((o) => o.ma === value)?.ten ?? "";
  const loc = q.trim() ? options.filter((o) => boDau(o.ten).includes(boDau(q))) : options;
  const chon = (o: { ma: string; ten: string }) => {
    onChon(o.ma);
    setQ("");
    setMo(false);
  };
  return (
    <div className={"relative " + (className ?? "")}>
      <input
        className="field-input"
        value={mo ? q : tenDaChon}
        placeholder={placeholder}
        disabled={disabled}
        onFocus={() => { setMo(true); setQ(""); }}
        onChange={(e) => { setQ(e.target.value); setMo(true); }}
        onBlur={() => window.setTimeout(() => setMo(false), 120)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && loc.length) { e.preventDefault(); chon(loc[0]); }
          else if (e.key === "Escape") setMo(false);
        }}
      />
      {mo && !disabled && (
        <ul className="absolute z-20 left-0 right-0 mt-1 max-h-56 overflow-y-auto rounded-lg border border-border bg-card shadow-lg">
          {loc.length === 0 ? (
            <li className="px-3 py-2 text-[13px] text-muted-foreground">Không tìm thấy</li>
          ) : (
            loc.slice(0, 60).map((o) => (
              <li key={o.ma}>
                <button
                  type="button"
                  onMouseDown={(e) => { e.preventDefault(); chon(o); }}
                  className={"w-full text-left px-3 py-2 text-[13px] hover:bg-muted transition-colors " + (o.ma === value ? "bg-primary/5 font-semibold" : "")}
                >
                  {o.ten}
                </button>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
