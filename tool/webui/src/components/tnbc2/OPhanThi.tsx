// TNB-08 — một ô phần thi (L · H · Đ / LT · TH). Xanh đậm = phải thi; xanh lá có dấu ✓ = đã đạt, không thi.
// Bấm là đổi qua lại. `aria-pressed` = đang "phải thi".

const dau = (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round"
    strokeLinejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" /></svg>
);

const KHUNG =
  "min-w-[30px] h-7 px-2 rounded-[7px] text-[12px] font-bold inline-flex items-center justify-center gap-1 " +
  "transition-colors duration-100 ease-out disabled:opacity-45 disabled:cursor-not-allowed";
const THI = "bg-tn text-white shadow-[0_1px_2px_hsl(222_76%_30%/.35)] hover:bg-[hsl(222_76%_34%)]";
const DAT = "bg-[hsl(142_60%_94%)] text-[hsl(142_71%_24%)] ring-1 ring-inset ring-[hsl(142_45%_74%)] hover:bg-[hsl(142_60%_89%)]";

export default function OPhanThi({
  phan,
  phaiThi,
  tieuDe,
  onBam,
  khoa = false,
  testId,
}: {
  phan: string;
  phaiThi: boolean;
  tieuDe: string;
  onBam?: () => void;
  khoa?: boolean;
  testId?: string;
}) {
  return (
    <button type="button" aria-pressed={phaiThi} aria-label={tieuDe} title={tieuDe} disabled={khoa || !onBam}
      onClick={onBam} data-testid={testId} data-trang-thai={phaiThi ? "thi" : "dat"}
      className={`${KHUNG} ${phaiThi ? THI : DAT}`}>
      {!phaiThi && dau}
      {phan}
    </button>
  );
}

/** Ô minh họa cho chú giải (không bấm được). */
export function OMau({ phan, phaiThi }: { phan: string; phaiThi: boolean }) {
  return <span className={`${KHUNG} ${phaiThi ? THI : DAT} pointer-events-none`}>{!phaiThi && dau}{phan}</span>;
}
