// Bộ icon SVG inline (kiểu Lucide) — tránh emoji, tránh phụ thuộc lib.
// Đồng bộ với ui-demo; thêm icon khi màn thật cần (task 17/18/19).
import type { ReactNode } from "react";

const PATHS: Record<string, ReactNode> = {
  scan: <><path d="M3 7V5a2 2 0 0 1 2-2h2M17 3h2a2 2 0 0 1 2 2v2M21 17v2a2 2 0 0 1-2 2h-2M7 21H5a2 2 0 0 1-2-2v-2" /><path d="M7 12h10" /></>,
  send: <><path d="m22 2-7 20-4-9-9-4Z" /><path d="M22 2 11 13" /></>,
  user: <><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 4-6 8-6s8 2 8 6" /></>,
  logout: <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" /></>,
};

export function Icon({ name, className = "w-5 h-5", sw = 2 }: { name: keyof typeof PATHS | string; className?: string; sw?: number }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
      {PATHS[name] ?? null}
    </svg>
  );
}
