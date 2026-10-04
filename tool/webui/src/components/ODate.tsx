import { useRef, type ReactNode } from "react";
import { Icon } from "./Icon";
import { maskNgay } from "../lib/format";

// Ô nhập ngày dùng chung cho tool — port từ app web (webapp ODate, CHANGES #14):
// - Gõ tay dd/mm/yyyy, tự chèn "/" (maskNgay ở lib/format).
// - Nút lịch mở bộ chọn ngày của trình duyệt (showPicker) → ghi ngược dd/mm/yyyy.
// Giá trị luôn là chuỗi hiển thị dd/mm/yyyy; lớp trên tự parse khi cần.
export function ODate({
  label,
  value,
  onChange,
  req,
  disabled,
  max,
  placeholder = "dd/mm/yyyy",
  className,
}: {
  label?: ReactNode;
  value: string;
  onChange: (v: string) => void;
  req?: boolean;
  disabled?: boolean;
  max?: string; // yyyy-mm-dd — giới hạn ngày tối đa cho bộ chọn lịch
  placeholder?: string;
  className?: string;
}) {
  const lichRef = useRef<HTMLInputElement>(null);

  function moLich() {
    const el = lichRef.current;
    if (!el || disabled) return;
    const m = value.trim().match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    el.value = m ? `${m[3]}-${m[2]}-${m[1]}` : "";
    if (typeof el.showPicker === "function") el.showPicker();
    else el.focus();
  }

  return (
    <div className={className}>
      {label !== undefined && (
        <label className="field-label">
          {label} {req && <span className="text-destructive">*</span>}
        </label>
      )}
      <div className={"relative " + (label !== undefined ? "mt-1" : "")}>
        <input
          className="field-input pr-11"
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(maskNgay(e.target.value))}
          placeholder={placeholder}
          inputMode="numeric"
        />
        <button
          type="button"
          onClick={moLich}
          disabled={disabled}
          aria-label="Chọn ngày từ lịch"
          className="absolute right-1 top-1/2 -translate-y-1/2 w-8 h-8 rounded-md flex items-center justify-center text-muted-foreground hover:bg-muted hover:text-foreground transition-colors disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <Icon name="calendar" className="w-[18px] h-[18px]" />
        </button>
        {/* Bộ chọn ngày ẩn — chỉ bật qua nút lịch; ngoài tab order (gõ tay là chính). */}
        <input
          ref={lichRef}
          type="date"
          tabIndex={-1}
          aria-hidden="true"
          className="sr-only"
          max={max}
          onChange={(e) => {
            const v = e.target.value; // yyyy-mm-dd
            if (!v) return;
            const [y, m, d] = v.split("-");
            onChange(`${d}/${m}/${y}`);
          }}
        />
      </div>
    </div>
  );
}
