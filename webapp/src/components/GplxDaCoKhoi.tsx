import { useState } from "react";
import { ODate } from "./ODate";
import { boDau } from "../lib/text";
import {
  DS_HANG_GPLX, DS_NOI_CAP_GPLX, bangMoi, khoaHang, laBangMoTo, loiBang, soGplxLa, tachKhoaHang, type BangGplx,
} from "../lib/gplxDaCo";

// Ô gõ để tìm (cùng cách dùng với ComboLoc của tool): gõ tới đâu lọc tới đó, không phân biệt dấu, Enter chọn dòng đầu.
function OTim({
  nhan, value, options, onChon, placeholder,
}: {
  nhan: string;
  value: string;
  options: { ma: string; ten: string }[];
  onChon: (ma: string) => void;
  placeholder: string;
}) {
  const [q, setQ] = useState("");
  const [mo, setMo] = useState(false);
  const ten = options.find((o) => o.ma === value)?.ten ?? "";
  const loc = q.trim() ? options.filter((o) => boDau(o.ten).includes(boDau(q))) : options;
  const chon = (ma: string) => { onChon(ma); setQ(""); setMo(false); };
  return (
    <div className="relative">
      <label className="field-label">{nhan}</label>
      <input
        className="field-input mt-1"
        value={mo ? q : ten}
        placeholder={placeholder}
        onFocus={() => { setMo(true); setQ(""); }}
        onChange={(e) => { setQ(e.target.value); setMo(true); }}
        onBlur={() => window.setTimeout(() => setMo(false), 120)}
        onKeyDown={(e) => {
          if (e.key === "Enter") { e.preventDefault(); if (loc.length) chon(loc[0].ma); }
          else if (e.key === "Escape") setMo(false);
          else if (e.key.startsWith("Arrow")) e.stopPropagation(); // không để form nhảy ô khi đang gõ tìm
        }}
      />
      {mo && (
        <ul className="absolute z-20 left-0 right-0 mt-1 max-h-56 overflow-y-auto rounded-lg border border-border bg-card shadow-lg">
          {loc.length === 0 ? (
            <li className="px-3 py-2 text-[13px] text-muted-foreground">Không tìm thấy</li>
          ) : (
            loc.map((o) => (
              <li key={o.ma}>
                <button
                  type="button"
                  onMouseDown={(e) => { e.preventDefault(); chon(o.ma); }}
                  className={"w-full text-left px-3 py-2 text-[13px] hover:bg-muted " + (o.ma === value ? "bg-primary/5 font-semibold" : "")}
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

// Khối "GPLX đã có" (THU-07): thu gọn mặc định, tích vào mở khối nhập, thêm/xóa được nhiều bằng.
export function GplxDaCoKhoi({ ds, onDoi }: { ds: BangGplx[]; onDoi: (ds: BangGplx[]) => void }) {
  const sua = (i: number, p: Partial<BangGplx>) => onDoi(ds.map((b, j) => (j === i ? { ...b, ...p } : b)));
  return (
    <div className="rounded-lg border border-border bg-card p-3">
      {/* Giữ focus khi bấm: ô phía trên mất focus sẽ hiện dòng báo lỗi, form xô xuống làm cú bấm trượt khỏi ô tích */}
      <label className="flex items-center gap-2 text-[13px] font-semibold cursor-pointer" onMouseDown={(e) => e.preventDefault()}>
        <input
          type="checkbox"
          className="accent-primary w-4 h-4"
          checked={ds.length > 0}
          onChange={(e) => onDoi(e.target.checked ? [bangMoi()] : [])}
        />
        Đã có GPLX
      </label>
      {ds.map((b, i) => (
        <div key={i} className="mt-3 border-t border-border pt-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[12.5px] font-semibold">Bằng {i + 1}</span>
            <button type="button" className="text-[12px] text-destructive" onClick={() => onDoi(ds.filter((_, j) => j !== i))}>Xóa</button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <OTim
              nhan="Hạng"
              value={khoaHang(b)}
              options={DS_HANG_GPLX}
              onChon={(k) => sua(i, tachKhoaHang(k))}
              placeholder="Gõ hạng, ví dụ B2"
            />
            <div>
              <label className="field-label" htmlFor={`gplx-so-${i}`}>Số GPLX</label>
              <input
                id={`gplx-so-${i}`}
                className="field-input mt-1"
                inputMode="numeric"
                maxLength={20}
                value={b.so}
                placeholder="12 chữ số"
                onChange={(e) => sua(i, { so: e.target.value.replace(/\|/g, "") })}
              />
            </div>
            <ODate label="Ngày trúng tuyển" value={b.ngay_tt} onChange={(v) => sua(i, { ngay_tt: v })} />
            <ODate label="Ngày cấp" value={b.ngay_cap} onChange={(v) => sua(i, { ngay_cap: v })} />
            {!laBangMoTo(b.hang) && <ODate label="Ngày hết hạn" value={b.ngay_hh} onChange={(v) => sua(i, { ngay_hh: v })} />}
            <OTim
              nhan="Nơi cấp"
              value={b.don_vi}
              options={DS_NOI_CAP_GPLX}
              onChon={(ma) => sua(i, { don_vi: ma })}
              placeholder="Gõ mã hoặc tên tỉnh"
            />
          </div>
          {soGplxLa(b.so) && <p className="text-[12px] text-warning">Số GPLX thường có 12 chữ số — kiểm lại, vẫn gửi được.</p>}
          {loiBang(b).length > 0 && <p className="text-[12px] text-destructive">{loiBang(b).join(" · ")}</p>}
        </div>
      ))}
      {ds.length > 0 && (
        <button
          type="button"
          className="mt-3 h-9 px-3 rounded-lg border border-border bg-card text-[13px] font-medium hover:bg-muted"
          onClick={() => onDoi([...ds, bangMoi()])}
        >
          + Thêm GPLX
        </button>
      )}
    </div>
  );
}
