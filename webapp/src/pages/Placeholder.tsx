import { Icon } from "../components/Icon";

// Màn tạm cho khung (task 13). Thay bằng màn thật ở task 17/18/19.
export default function Placeholder({ ten, icon = "scan" }: { ten: string; icon?: string }) {
  return (
    <div className="flex flex-col items-center justify-center text-center px-6 py-16 gap-3">
      <div className="w-16 h-16 rounded-2xl bg-primary/10 text-primary flex items-center justify-center">
        <Icon name={icon} className="w-8 h-8" />
      </div>
      <h1 className="text-lg font-bold">{ten}</h1>
      <p className="text-[13px] text-muted-foreground max-w-xs">
        Màn này đang được dựng. Khung app web (điều hướng, bố cục, token giao diện) đã sẵn sàng.
      </p>
    </div>
  );
}
