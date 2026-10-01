import { Icon } from "../../components/Icon";

export default function Quet() {
  return (
    <div className="lg:flex lg:gap-6 lg:p-6 lg:max-w-4xl lg:mx-auto lg:items-start">
      {/* Camera viewport (desktop: cột trái) */}
      <div className="lg:w-[340px] lg:shrink-0 lg:rounded-xl lg:overflow-hidden lg:border lg:border-border">
      <div className="relative bg-slate-950 aspect-[3/4] flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 opacity-30" style={{ background: "radial-gradient(circle at 50% 40%, #1e293b, #020617)" }} />
        <div className="absolute w-[78%] aspect-[86/54] rounded-xl border border-white/10 bg-white/[.03]" />
        <div className="relative w-[70%] aspect-square">
          <span className="absolute -top-0.5 -left-0.5 w-8 h-8 border-t-4 border-l-4 border-success rounded-tl-lg" />
          <span className="absolute -top-0.5 -right-0.5 w-8 h-8 border-t-4 border-r-4 border-success rounded-tr-lg" />
          <span className="absolute -bottom-0.5 -left-0.5 w-8 h-8 border-b-4 border-l-4 border-success rounded-bl-lg" />
          <span className="absolute -bottom-0.5 -right-0.5 w-8 h-8 border-b-4 border-r-4 border-success rounded-br-lg" />
          <div className="absolute left-2 right-2 h-0.5 bg-success/80 shadow-[0_0_12px_2px] shadow-success" style={{ top: "60%" }} />
        </div>
        <div className="absolute top-3 left-1/2 -translate-x-1/2 flex items-center gap-1.5 bg-success text-white text-xs font-semibold px-3 py-1.5 rounded-full shadow-lg">
          <Icon name="check" className="w-4 h-4" sw={3} /> Quét thành công
        </div>
        <button aria-label="Bật đèn" className="absolute bottom-3 right-3 w-10 h-10 rounded-full bg-white/15 backdrop-blur flex items-center justify-center text-white hover:bg-white/25 transition-colors">
          <Icon name="torch" className="w-5 h-5" />
        </button>
        <div className="absolute bottom-3 left-3 text-[11px] text-white/70">Đưa mặt trước CCCD vào khung</div>
      </div>
      </div>

      {/* Preview 7 trường (desktop: cột phải) */}
      <div className="p-4 lg:p-0 lg:flex-1 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold">Thông tin từ căn cước</h2>
          <span className="text-[11px] text-muted-foreground">Kiểm tra &amp; sửa nếu sai</span>
        </div>

        <Field label="Số CCCD" req defaultValue="070202008455" />
        <Field label="Số CMND cũ (nếu có)" placeholder="9 số — bỏ trống nếu không có" />
        <Field label="Họ và tên" req defaultValue="NGUYỄN THANH TÂM" />
        <div className="grid grid-cols-2 gap-3">
          <Field label="Ngày sinh" req defaultValue="21/11/2002" />
          <div>
            <label className="field-label">Giới tính <span className="text-destructive">*</span></label>
            <select className="field-input mt-1" defaultValue="Nam"><option>Nam</option><option>Nữ</option></select>
          </div>
        </div>
        <Field label="Nơi thường trú" req defaultValue="Xã Phú Nghĩa, Tỉnh Bình Phước" />
        <Field label="Ngày cấp" defaultValue="10/03/2021" />

        <div className="flex items-center gap-2 text-[12px] text-warning bg-warning/10 border border-warning/30 rounded-lg px-3 py-2">
          <Icon name="wifiOff" className="w-4 h-4 shrink-0" /> Đã lưu nháp — sẽ tự gửi khi có mạng
        </div>

        <button className="w-full h-11 rounded-lg border border-border bg-secondary text-foreground font-semibold text-sm flex items-center justify-center gap-2 hover:bg-muted transition-colors">
          <Icon name="camera" className="w-4 h-4" /> Chụp ảnh chân dung
        </button>
        <button className="w-full h-11 rounded-lg bg-primary text-primary-foreground font-semibold text-sm flex items-center justify-center gap-2 hover:brightness-110 transition-all shadow-sm">
          <Icon name="send" className="w-4 h-4" /> Gửi hồ sơ
        </button>
        <div className="text-center">
          <button className="text-[12px] text-primary font-medium hover:underline">QR hỏng? Nhập tay / Tải ảnh CCCD</button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, req, defaultValue, placeholder }: { label: string; req?: boolean; defaultValue?: string; placeholder?: string }) {
  return (
    <div>
      <label className="field-label">{label} {req && <span className="text-destructive">*</span>}</label>
      <input className="field-input mt-1" defaultValue={defaultValue} placeholder={placeholder} />
    </div>
  );
}
