import { useState } from "react";
import { Icon } from "./Icon";

// Chú giải trạng thái học viên (phân hệ Tốt nghiệp & BC2). Giao diện chính chỉ hiện TÊN nghiệp vụ,
// mã `TT_XuLy` của phần mềm cũ chỉ là chú thích nhỏ để đối chiếu khi cần (bám ui-mock/tnbc2.html).

const HANG: { ten: string; ma: string; nghia: string }[] = [
  { ten: "Đã học xong, chưa tốt nghiệp", ma: "03", nghia: "Ô tô: đã học hết khóa, chưa có giấy chứng nhận tốt nghiệp" },
  { ten: "Đã học xong, chờ lập BC2", ma: "03", nghia: "Mô tô: học xong khóa, sẵn sàng đưa vào BC2" },
  { ten: "Đã tốt nghiệp, chờ lập BC2", ma: "09", nghia: "Ô tô: có giấy tốt nghiệp, chưa vào báo cáo" },
  { ten: "Đã vào BC2, chờ kết quả", ma: "11", nghia: "Đã nằm trong một BC2, chưa có kết quả" },
  { ten: "Chưa đạt BC2 — cần lập lại", ma: "14", nghia: "BC2 trước không đạt, cần đưa vào BC2 mới" },
  { ten: "Thi sát hạch chưa đạt", ma: "17", nghia: "Thi sát hạch rớt, chờ thi lại" },
  { ten: "Vắng sát hạch", ma: "18", nghia: "Không đến thi sát hạch, chờ thi lại" },
  { ten: "Đạt BC2 / Đạt sát hạch / Đã nhận GPLX", ma: "13 · 16 · 19", nghia: "Đã có kết quả cuối — không đưa vào BC2 nữa" },
];

/** Tên trạng thái + mã nhỏ đứng cạnh (dùng ở mọi bảng của phân hệ). */
export function TrangThaiNhan({ ten, ma }: { ten: string; ma?: string }) {
  return (
    <span>
      {ten}
      {ma && <span className="ml-1 text-[10px] font-medium opacity-70">{ma}</span>}
    </span>
  );
}

export default function ChuGiaiTrangThai() {
  const [mo, setMo] = useState(false);
  return (
    <>
      <button
        type="button"
        onClick={() => setMo(true)}
        title="Giải thích các trạng thái"
        className="inline-flex items-center gap-1 h-7 px-2 rounded-md text-[12px] font-semibold text-primary hover:bg-accent"
      >
        <Icon name="info" className="w-3.5 h-3.5" /> Chú giải
      </button>
      {mo && (
        <div
          className="fixed inset-0 z-50 bg-black/40 grid place-items-center p-4"
          onClick={(e) => {
            if (e.target === e.currentTarget) setMo(false);
          }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Chú giải trạng thái học viên"
            className="bg-white rounded-xl shadow-2xl w-[860px] max-w-full max-h-[86vh] flex flex-col"
          >
            <div className="p-4 border-b border-border font-semibold">Chú giải trạng thái học viên</div>
            <div className="p-4 overflow-auto">
              <p className="text-[13px] text-muted-foreground mb-2">
                Mã nhỏ bên cạnh là mã trạng thái trong phần mềm cũ, để bạn đối chiếu khi cần.
              </p>
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="text-left text-[12px] text-muted-foreground">
                    <th className="py-1.5 pr-3 font-semibold">Trạng thái</th>
                    <th className="py-1.5 pr-3 font-semibold">Mã cũ</th>
                    <th className="py-1.5 font-semibold">Nghĩa</th>
                  </tr>
                </thead>
                <tbody>
                  {HANG.map((h) => (
                    <tr key={h.ten} className="border-t border-border">
                      <td className="py-1.5 pr-3 font-medium">{h.ten}</td>
                      <td className="py-1.5 pr-3 font-mono text-[12px]">{h.ma}</td>
                      <td className="py-1.5">{h.nghia}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="p-3 border-t border-border flex justify-end">
              <button
                type="button"
                onClick={() => setMo(false)}
                className="h-8 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
