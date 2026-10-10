import { Icon } from "../../components/Icon";

// PCG-05 — tab "Rà soát khóa". Dựng ở task 95; hiện chỉ giữ chỗ trong menu phân hệ.
export default function RaSoatKhoa() {
  return (
    <div className="p-6 max-w-3xl">
      <h1 className="text-lg font-semibold flex items-center gap-2">
        <Icon name="search" className="w-5 h-5 text-pc" /> Rà soát khóa
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Màn này sẽ liệt kê các khóa còn thiếu giáo viên, thiếu xe hoặc phân công chồng lịch. Chưa dựng — làm ở task 95.
      </p>
    </div>
  );
}
