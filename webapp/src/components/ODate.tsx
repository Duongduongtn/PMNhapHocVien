import { useRef } from "react";
import { Icon } from "./Icon";

// Ô ngày cho nhập liệu nhanh (THU-01/THU-02, CHANGES #14):
// - Gõ tay dd/mm/yyyy bằng bàn phím (nhanh cho người nhập liệu), hoặc CHỈ NĂM (yyyy) —
//   CCCD có học viên chỉ khai năm sinh, không cho mất khả năng đó.
// - Nút lịch mở bộ chọn ngày của trình duyệt (showPicker) → ghi ngược dd/mm/yyyy vào ô.
// Giá trị luôn là chuỗi hiển thị (dd/mm/yyyy hoặc yyyy); lớp trên tự chuẩn hóa sang DB.
export function ODate({
  label,
  value,
  onChange,
  req,
  placeholder = "dd/mm/yyyy",
  autoFocus,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  req?: boolean;
  placeholder?: string;
  autoFocus?: boolean;
}) {
  const lichRef = useRef<HTMLInputElement>(null);

  function moLich() {
    const el = lichRef.current;
    if (!el) return;
    // Mồi lịch bằng giá trị đang có nếu là ngày đầy đủ dd/mm/yyyy.
    const m = value.trim().match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    el.value = m ? `${m[3]}-${m[2]}-${m[1]}` : "";
    if (typeof el.showPicker === "function") el.showPicker();
    else el.focus();
  }

  return (
    <div>
      <label className="field-label">
        {label} {req && <span className="text-destructive">*</span>}
      </label>
      <div className="relative mt-1">
        <input
          className="field-input pr-11"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          inputMode="numeric"
          autoFocus={autoFocus}
        />
        <button
          type="button"
          onClick={moLich}
          aria-label={`Chọn ${label.toLowerCase()} từ lịch`}
          className="absolute right-1 top-1/2 -translate-y-1/2 w-9 h-9 rounded-md flex items-center justify-center text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          <Icon name="calendar" className="w-5 h-5" />
        </button>
        {/* Bộ chọn ngày ẩn — chỉ bật qua nút lịch; không nằm trong tab order (gõ tay là chính). */}
        <input
          ref={lichRef}
          type="date"
          tabIndex={-1}
          aria-hidden="true"
          className="sr-only"
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
