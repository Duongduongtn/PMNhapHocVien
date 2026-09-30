import { Icon } from "./Icon";

export default function Placeholder({ title, story }: { title: string; story?: string }) {
  return (
    <div className="flex flex-col items-center justify-center text-center gap-3 p-10 min-h-[320px]">
      <div className="w-14 h-14 rounded-2xl bg-accent text-primary flex items-center justify-center">
        <Icon name="file" className="w-7 h-7" />
      </div>
      <h2 className="text-lg font-bold">{title}</h2>
      {story && <span className="text-[12px] text-muted-foreground">Story: {story}</span>}
      <p className="text-sm text-muted-foreground">Màn hình đang dựng — sẽ làm ở lượt <span className="font-mono">/prototype-next</span> tiếp theo.</p>
    </div>
  );
}
