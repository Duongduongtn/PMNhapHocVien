import type { ReactNode } from "react";
import ChuGiaiTrangThai from "./ChuGiaiTrangThai";

/** Khung trang chung của phân hệ Tốt nghiệp & BC2: tiêu đề + mô tả + nút Chú giải + nội dung. */
export default function KhungTrangTnbc2({
  tieuDe,
  moTa,
  children,
}: {
  tieuDe: string;
  moTa: string;
  children?: ReactNode;
}) {
  return (
    <div className="p-4 sm:p-5 max-w-[1200px]">
      <div className="flex items-start gap-3">
        <div className="min-w-0">
          <h1 className="text-lg font-bold">{tieuDe}</h1>
          <p className="text-[13px] text-muted-foreground mt-0.5">{moTa}</p>
        </div>
        <div className="ml-auto shrink-0">
          <ChuGiaiTrangThai />
        </div>
      </div>
      <div className="mt-4">
        {children ?? (
          <div className="rounded-xl border border-dashed border-tn-border bg-tn-soft/50 px-4 py-8 text-center text-[13px] text-muted-foreground">
            Màn này đang được dựng.
          </div>
        )}
      </div>
    </div>
  );
}
