import { Icon } from "../../components/Icon";

// Khung tạm cho các màn phân hệ Đồng bộ CDB — nội dung thật dựng ở các bước sau.
// Giữ để sidebar + sub-nav điều hướng được và kiểm bố cục khung.
export default function SyncComingSoon({ title }: { title: string }) {
  return (
    <div className="p-4">
      <div className="max-w-2xl rounded-lg border border-dashed border-sync-border bg-sync-soft/40 p-8 text-center">
        <span className="inline-grid place-items-center w-12 h-12 rounded-full bg-card border border-sync-border text-sync mb-3 mx-auto">
          <Icon name="refresh" className="w-6 h-6" />
        </span>
        <h2 className="text-base font-bold text-foreground mb-1">{title}</h2>
        <p className="text-[13px] text-muted-foreground max-w-md mx-auto">
          Màn này thuộc phân hệ Đồng bộ CDB, đang được dựng. Khung điều hướng (sidebar phân hệ,
          thanh màn, nhắc CSDL đích) đã sẵn sàng.
        </p>
      </div>
    </div>
  );
}
