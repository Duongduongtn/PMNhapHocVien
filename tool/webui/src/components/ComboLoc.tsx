import { useState } from "react";
import { chonKhiEnter, locLuaChon, type LuaChon } from "../lib/locLuaChon";

// Ô gõ-để-lọc dùng chung (NAP-03 địa chỉ, SYNC-01 chọn khóa): gõ tên (không dấu
// cũng khớp nhờ boDau) → danh sách gợi ý lọc dần → bấm chọn, hoặc Enter khi chỉ còn
// đúng một khả năng (BUG-19). Nhanh hơn dropdown khi danh sách dài.
export function ComboLoc({
  value,
  options,
  onChon,
  placeholder,
  disabled,
  className,
}: {
  value: string;
  options: LuaChon[];
  onChon: (ma: string) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}) {
  const [q, setQ] = useState("");
  const [mo, setMo] = useState(false);
  const tenDaChon = options.find((o) => o.ma === value)?.ten ?? "";
  const loc = locLuaChon(options, q);
  const chon = (o: LuaChon) => {
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
          if (e.key === "Enter") { e.preventDefault(); const o = chonKhiEnter(options, q); if (o) chon(o); }
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
