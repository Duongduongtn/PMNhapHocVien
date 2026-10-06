import { useEffect, useState } from "react";
import { Icon } from "./Icon";
import { getSyncRollbackPreview, postSyncRollback, type SyncRollbackPreview } from "../lib/api";

// Hộp thoại xác nhận Hủy sync 1 khóa đích (dùng chung Lịch sử + Bàn đồng bộ — CHANGES #41).
// Tự tải preview (số bản ghi sẽ xóa) khi mở; gọi onDone(kq) sau khi hủy thành công.
interface Props {
  maKhoaMoi: string;        // mã khóa ĐÍCH (CDB) sẽ hủy
  nhan: string;             // nhãn hiện trên tiêu đề (tên khóa nếu có, không thì mã)
  targetKey?: string;
  dichDbName?: string;      // tên CSDL đích cho câu cảnh báo
  onClose: () => void;
  onDone: (kq: { hs_del: number; nlx_del: number; tong_so_hv: number | null }) => void;
}

export default function HuyncSyncDialog({ maKhoaMoi, nhan, targetKey, dichDbName, onClose, onDone }: Props) {
  const [preview, setPreview] = useState<SyncRollbackPreview | null>(null);
  const [dangXem, setDangXem] = useState(true);
  const [dangXoa, setDangXoa] = useState(false);
  const [loi, setLoi] = useState("");

  useEffect(() => {
    let huy = false;
    getSyncRollbackPreview(maKhoaMoi, targetKey)
      .then((p) => { if (!huy) { setPreview(p); setDangXem(false); } })
      .catch((e) => { if (!huy) { setDangXem(false); setLoi(e instanceof Error ? e.message : "Không đếm được số bản ghi."); } });
    return () => { huy = true; };
  }, [maKhoaMoi, targetKey]);

  const xacNhan = async () => {
    setDangXoa(true); setLoi("");
    try {
      onDone(await postSyncRollback(maKhoaMoi, targetKey));
    } catch (e) {
      setDangXoa(false);
      setLoi(e instanceof Error ? e.message : "Hủy sync thất bại.");
    }
  };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center">
      <div className="absolute inset-0 bg-foreground/30" onClick={() => !dangXoa && onClose()} />
      <div role="dialog" aria-modal="true" className="relative bg-card rounded-xl border border-border shadow-xl w-[480px] max-w-[94vw] p-5">
        <h3 className="font-bold text-[15px] mb-2 flex items-center gap-2 text-destructive">
          <Icon name="warn" className="w-5 h-5 shrink-0" />
          Hủy sync khóa {nhan}?
        </h3>
        {dangXem ? (
          <div className="flex items-center gap-2 text-[13px] text-muted-foreground py-3">
            <Icon name="refresh" className="w-4 h-4 animate-spin" /> Đang đếm số bản ghi sẽ xóa…
          </div>
        ) : preview ? (
          <>
            <ul className="text-[13px] text-foreground space-y-1 mb-3 list-disc pl-5">
              <li>Nhóm nhật ký máy tool còn ở đích: <b className="tabular-nums">{preview.log_con_dich}</b> học viên{preview.log_count > preview.log_con_dich && <span className="text-muted-foreground"> (nhật ký {preview.log_count}, số còn lại đã bị xóa trước đó)</span>}</li>
              <li>Nhóm công cụ cũ (NguoiTao=SYNC): <b className="tabular-nums">{preview.sync_group}</b> học viên</li>
            </ul>
            <p className="text-[12.5px] text-muted-foreground mb-4">
              Xóa Người lái + Hồ sơ + Giấy tờ của <b className="text-destructive tabular-nums">{preview.tong}</b> học viên khỏi
              CSDL đích <b>{dichDbName}</b>. Nhật ký máy tool vẫn giữ lại. <b>Không hoàn tác được.</b>
            </p>
          </>
        ) : null}
        {loi && (
          <div className="mb-3 flex items-start gap-2 text-[12.5px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
            <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" /> {loi}
          </div>
        )}
        <div className="flex justify-end gap-2">
          <button onClick={onClose} disabled={dangXoa} className="h-9 px-4 rounded-lg border border-border text-[13px] hover:bg-muted disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">Đóng</button>
          <button onClick={xacNhan} disabled={dangXem || dangXoa || !preview || preview.tong === 0}
            title={preview && preview.tong === 0 ? "Khóa này không còn học viên nào do tool tạo" : undefined}
            className="inline-flex items-center gap-1.5 h-9 px-4 rounded-lg bg-destructive text-white font-semibold text-[13px] hover:brightness-110 transition-all disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-destructive">
            <Icon name={dangXoa ? "refresh" : "warn"} className={"w-4 h-4 " + (dangXoa ? "animate-spin" : "")} />
            {dangXoa ? "Đang hủy…" : preview ? `Xóa ${preview.tong} hồ sơ` : "Xóa"}
          </button>
        </div>
      </div>
    </div>
  );
}
