import { Link } from "react-router-dom";
import { Icon } from "../components/Icon";

export default function Home() {
  return (
    <div className="min-h-screen bg-[hsl(210_40%_96%)] flex flex-col items-center justify-center p-4">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-extrabold">Thu nhận hồ sơ học viên</h1>
        <p className="text-sm text-muted-foreground mt-1">Bản demo giao diện (prototype) · CSDT 70004 · chọn app để xem</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-2xl">
        {/* Tool */}
        <Link to="/tool/nap" className="group bg-card border border-border rounded-xl p-6 shadow-sm hover:shadow-md hover:border-primary transition-all">
          <div className="w-12 h-12 rounded-xl bg-primary text-primary-foreground flex items-center justify-center mb-4">
            <Icon name="device" className="w-6 h-6" />
          </div>
          <h2 className="text-base font-bold group-hover:text-primary transition-colors">Tool nạp DB (máy tính)</h2>
          <p className="text-[13px] text-muted-foreground mt-1">Nhân viên nạp DB: kéo hồ sơ từ VPS, map địa chỉ, xử lý ảnh, nạp vào SQL Server, quản lý hồ sơ, tạo khóa.</p>
          <span className="inline-flex items-center gap-1 text-[13px] text-primary font-semibold mt-3">Mở tool <Icon name="chevronRight" className="w-4 h-4" /></span>
        </Link>

        {/* App web */}
        <Link to="/app/quet" className="group bg-card border border-border rounded-xl p-6 shadow-sm hover:shadow-md hover:border-primary transition-all">
          <div className="w-12 h-12 rounded-xl bg-primary text-primary-foreground flex items-center justify-center mb-4">
            <Icon name="phone" className="w-6 h-6" />
          </div>
          <h2 className="text-base font-bold group-hover:text-primary transition-colors">App web (điện thoại)</h2>
          <p className="text-[13px] text-muted-foreground mt-1">Nhân viên tuyển sinh: quét QR căn cước, kiểm tra/sửa thông tin, chụp ảnh chân dung, gửi lên VPS.</p>
          <span className="inline-flex items-center gap-1 text-[13px] text-primary font-semibold mt-3">Mở app web <Icon name="chevronRight" className="w-4 h-4" /></span>
        </Link>
      </div>

      <div className="flex gap-4 mt-6 text-[13px]">
        <Link to="/dang-nhap" className="text-muted-foreground hover:text-primary transition-colors">Đăng nhập (HTG-01)</Link>
        <Link to="/admin/ho-so" className="text-muted-foreground hover:text-primary transition-colors">Quản trị PII (HTG-03)</Link>
      </div>
    </div>
  );
}
