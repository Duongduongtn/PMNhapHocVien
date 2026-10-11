import { useState } from "react";
import { tachCotDan } from "../../lib/tnbcSoGiay";

// TNB-01 — dán cột số giấy từ Excel cho các học viên đã tích (theo thứ tự đang hiển thị).
export default function DanSoGiayDialog({
  soHocVien,
  onAp,
  onDong,
}: {
  soHocVien: number;
  onAp: (cacSo: string[]) => void;
  onDong: () => void;
}) {
  const [text, setText] = useState("");
  const cacSo = tachCotDan(text);
  const khop = cacSo.length === soHocVien;
  return (
    <div className="fixed inset-0 z-50 bg-black/40 grid place-items-center p-4">
      <div role="dialog" aria-modal="true" aria-label="Dán số giấy từ Excel"
        className="bg-white rounded-xl shadow-2xl w-[520px] max-w-full flex flex-col">
        <div className="p-4 border-b border-border font-semibold">Dán số giấy từ Excel</div>
        <div className="p-4 space-y-2 text-[13px]">
          <p className="text-muted-foreground">
            Dán một cột số giấy (mỗi dòng một số). Số thứ nhất gán cho học viên đầu tiên trong danh sách đang
            hiển thị, rồi lần lượt xuống dưới. Đang có <b>{soHocVien}</b> học viên được chọn.
          </p>
          <textarea
            autoFocus
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={8}
            placeholder={"N1|7329\nN1|7330\n…"}
            className="field-input font-mono"
          />
          <div className={khop ? "text-success" : cacSo.length ? "text-warning" : "text-muted-foreground"}>
            {cacSo.length === 0
              ? "Chưa có số nào."
              : khop
                ? `Đủ ${cacSo.length} số cho ${soHocVien} học viên.`
                : `Có ${cacSo.length} số nhưng đang chọn ${soHocVien} học viên — cần bằng nhau.`}
          </div>
        </div>
        <div className="p-3 border-t border-border flex justify-end gap-2">
          <button type="button" onClick={onDong}
            className="h-9 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">
            Hủy
          </button>
          <button type="button" disabled={!khop} onClick={() => onAp(cacSo)}
            className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
            Áp dụng
          </button>
        </div>
      </div>
    </div>
  );
}
