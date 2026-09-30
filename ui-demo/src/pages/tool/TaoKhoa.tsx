import { useState } from "react";
import { Icon } from "../../components/Icon";
import { dmHangDT } from "../../lib/mock-data";

export default function TaoKhoa() {
  const [maHang, setMaHang] = useState("B");
  const [optOpen, setOptOpen] = useState(false);
  const hang = dmHangDT.find((h) => h.ma === maHang)!;

  return (
    <div className="p-4 max-w-2xl">
      <div className="flex items-center gap-2 mb-1">
        <h2 className="text-base font-bold">Tạo khóa học</h2>
        <span className="text-[11px] font-semibold text-primary bg-primary/10 rounded-full px-2 py-0.5">KHO-01</span>
      </div>
      <p className="text-[12px] text-muted-foreground mb-4">Tạo khóa qua <span className="font-mono">usp_KhoaHoc_Insert</span>, mã khóa tự sinh; khóa hiện ngay trong app cũ.</p>

      {/* Tự điền */}
      <div className="rounded-md bg-secondary/70 border border-border px-3 py-2 text-[11px] text-muted-foreground leading-relaxed mb-4">
        <b className="text-foreground">Tự điền khi tạo:</b> Mã khóa tự sinh · HangGPLX <b className="text-foreground">{hang.hangGPLX}</b> (suy từ hạng ĐT) · Tuổi tối thiểu <b className="text-foreground">{hang.tuoiToiThieu}</b> · Thời gian ĐT <b className="text-foreground">{hang.thoiGian}</b> · MaCSDT 70004 · MaSoGTVT 70 · TrangThai 1
      </div>

      {/* Bắt buộc */}
      <div className="flex items-center gap-2 mb-2">
        <span className="inline-flex items-center gap-1.5 text-[11px] font-bold text-destructive"><span className="w-1.5 h-1.5 rounded-full bg-destructive" /> BẮT BUỘC</span>
        <div className="flex-1 h-px bg-border" />
        <span className="text-[10px] text-muted-foreground">5 trường · * phải điền</span>
      </div>
      <div className="rounded-lg border border-destructive/25 bg-destructive/[0.03] p-4 space-y-3">
        <div>
          <label className="field-label">Hạng đào tạo <span className="text-destructive">*</span></label>
          <select className="field-input mt-1" value={maHang} onChange={(e) => setMaHang(e.target.value)}>
            {dmHangDT.map((h) => <option key={h.ma} value={h.ma}>{h.ten}</option>)}
          </select>
        </div>
        <div><label className="field-label">Tên khóa <span className="text-destructive">*</span></label><input className="field-input mt-1" defaultValue="B-K150" placeholder="VD: B-K150" /></div>
        <div className="grid grid-cols-2 gap-3">
          <div><label className="field-label">Ngày khai giảng <span className="text-destructive">*</span></label><input className="field-input mt-1" defaultValue="15/10/2026" placeholder="dd/mm/yyyy" /></div>
          <div><label className="field-label">Ngày bế giảng <span className="text-destructive">*</span></label><input className="field-input mt-1" defaultValue="15/01/2027" placeholder="dd/mm/yyyy" /></div>
        </div>
        <div><label className="field-label">Tổng số học viên <span className="text-destructive">*</span></label><input className="field-input mt-1" defaultValue="50" inputMode="numeric" /></div>
      </div>

      {/* Không bắt buộc */}
      <div className="rounded-lg border border-border overflow-hidden mt-4">
        <button type="button" onClick={() => setOptOpen((v) => !v)} className="w-full flex items-center justify-between px-3 py-2.5 bg-muted/40 hover:bg-muted transition-colors text-left">
          <span className="text-[13px] font-semibold flex items-center gap-2"><Icon name="plus" className="w-4 h-4 text-muted-foreground" /> Thông tin thêm <span className="font-normal text-muted-foreground text-[11px]">(không bắt buộc — bỏ qua được)</span></span>
          <Icon name="chevronDown" className={"w-4 h-4 text-muted-foreground transition-transform " + (optOpen ? "rotate-180" : "")} />
        </button>
        {optOpen && (
          <div className="p-3 space-y-3 border-t border-border bg-card">
            <div className="grid grid-cols-2 gap-3">
              <div><label className="field-label">Số quyết định</label><input className="field-input mt-1" placeholder="(có thể trống)" /></div>
              <div><label className="field-label">Ngày quyết định</label><input className="field-input mt-1" placeholder="dd/mm/yyyy" /></div>
            </div>
            <div><label className="field-label">Ngày thi</label><input className="field-input mt-1" placeholder="dd/mm/yyyy" /></div>
            <div><label className="field-label">Ghi chú</label><input className="field-input mt-1" placeholder="..." /></div>
          </div>
        )}
      </div>

      <div className="mt-4">
        <button className="inline-flex items-center gap-2 h-10 px-5 rounded-lg bg-primary text-primary-foreground font-semibold text-sm hover:brightness-110 transition-all shadow-sm">
          <Icon name="plus" className="w-4 h-4" /> Tạo khóa học
        </button>
      </div>
    </div>
  );
}
