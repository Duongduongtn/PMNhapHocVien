import { useEffect } from "react";
import { ComboLoc } from "../../components/ComboLoc";
import { ODate } from "../../components/ODate";
import {
  DS_HANG_GPLX, bangMoi, dienNoiCapTheoSo, duocMienLyThuyet, khoaHang, laBangMoTo, loiBang, noiCapKhiDoiSo, locSoGplx, soCuSaiDang, suyNoiCapGplx, tachKhoaHang, trungHangDangKy,
  type BangGplx,
} from "./gplxDaCo";

// Khối nhập "GPLX đã có" (NAP-07): mỗi bằng 6 ô, thêm/xóa được nhiều bằng. Ở màn Nạp nằm trong popup GplxDaCoNut
// (trongPopup: bỏ ô tích bật/tắt, nút "+ Thêm GPLX" luôn hiện); hộp bổ sung GPLX ở Tra cứu vẫn dùng ô tích.
export function GplxDaCoKhoi({
  ds,
  onDoi,
  noiCap,
  hangKhoa,
  tuAppWeb,
  coBanMoi,
  onDungBanWeb,
  chuLuu = "nạp",
  trongPopup = false,
  soCu,
}: {
  ds: BangGplx[];
  onDoi: (ds: BangGplx[]) => void;
  noiCap: { ma: string; ten: string }[];
  hangKhoa?: string | null;
  tuAppWeb: boolean;
  coBanMoi: boolean;
  onDungBanWeb: () => void;
  chuLuu?: string; // động từ trong câu chặn trùng hạng: "nạp" ở màn Nạp, "lưu" ở hộp bổ sung
  trongPopup?: boolean;
  soCu?: Set<string>; // số GPLX đã lưu từ trước — giữ nguyên thì không chặn dạng (CHANGES #101)
}) {
  const sua = (i: number, p: Partial<BangGplx>) => onDoi(ds.map((b, j) => (j === i ? { ...b, ...p } : b)));
  // Nơi cấp trống mà số GPLX đủ 12 số → điền sẵn theo 2 số đầu (cả bằng app web gửi về). Đã có nơi cấp thì giữ.
  useEffect(() => {
    if (trongPopup || noiCap.length === 0) return;
    const moi = dienNoiCapTheoSo(ds, noiCap);
    if (moi !== ds) onDoi(moi);
  }, [ds, noiCap, onDoi, trongPopup]);

  return (
    <div className={trongPopup ? "" : "rounded-lg border border-border bg-card p-4"}>
      {trongPopup && ds.length === 0 && <p className="text-[13px] text-muted-foreground">Chưa có bằng nào. Bấm "+ Thêm GPLX" nếu học viên có bằng.</p>}
      {!trongPopup && <label className="flex items-center gap-2 text-[13px] font-semibold cursor-pointer">
        <input
          type="checkbox"
          className="accent-primary w-4 h-4"
          checked={ds.length > 0}
          onChange={(e) => onDoi(e.target.checked ? [bangMoi()] : [])}
        />
        Học viên đã có GPLX
      </label>}

      {coBanMoi && (
        <div className="mt-2 flex flex-wrap items-center gap-2 rounded-md bg-warning/10 px-2 py-1.5 text-[12px] text-warning">
          <span className="flex-1 min-w-[160px]">App web có bản mới, đang giữ bản đã sửa ở đây.</span>
          <button type="button" className="btn btn-secondary btn-row" onClick={onDungBanWeb}>Dùng bản app web</button>
        </div>
      )}

      {(ds.length > 0 || trongPopup) && (
        <>
          {tuAppWeb && !coBanMoi && (
            <p className="mt-2 rounded-md bg-primary/5 px-2 py-1.5 text-[12px] text-primary">Từ app web — kiểm lại với bằng thật, sửa nếu cần.</p>
          )}
          {ds.map((b, i) => (
            <div key={i} className={(trongPopup && i === 0 ? "" : "mt-3 border-t border-border pt-3 ") + "space-y-2"}>
              <div className="flex items-center justify-between">
                <span className="text-[12.5px] font-semibold">Bằng {i + 1}</span>
                <button type="button" className="text-[12px] text-destructive" onClick={() => onDoi(ds.filter((_, j) => j !== i))}>Xóa</button>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="field-label">Hạng</label>
                  <ComboLoc
                    className="mt-1"
                    value={khoaHang(b)}
                    options={DS_HANG_GPLX}
                    onChon={(k) => sua(i, tachKhoaHang(k))}
                    placeholder="Gõ hạng, ví dụ B2"
                  />
                </div>
                <div>
                  <label className="field-label" htmlFor={`gplx-so-${i}`}>Số GPLX</label>
                  <input
                    id={`gplx-so-${i}`}
                    className="field-input mt-1"
                    autoComplete="off"
                    value={b.so}
                    placeholder="12 chữ số"
                    onChange={(e) => {
                      const so = locSoGplx(e.target.value); // CHANGES #101: 12 số, hoặc bằng giấy cũ 2 chữ + 6 số
                      sua(i, { so, don_vi: noiCapKhiDoiSo(b.so, so, b.don_vi, noiCap) }); // điền sẵn nơi cấp theo 2 số đầu
                    }}
                  />
                </div>
                <ODate label="Ngày trúng tuyển" value={b.ngay_tt} onChange={(v) => sua(i, { ngay_tt: v })} />
                <ODate label="Ngày cấp" value={b.ngay_cap} onChange={(v) => sua(i, { ngay_cap: v })} />
                {!laBangMoTo(b.hang) && <ODate label="Ngày hết hạn" value={b.ngay_hh} onChange={(v) => sua(i, { ngay_hh: v })} />}
                <div>
                  <label className="field-label">Nơi cấp</label>
                  <ComboLoc
                    className="mt-1"
                    value={b.don_vi}
                    options={noiCap}
                    onChon={(ma) => sua(i, { don_vi: ma })}
                    placeholder="Gõ mã hoặc tên tỉnh"
                  />
                  {b.don_vi && b.don_vi === suyNoiCapGplx(b.so, noiCap) && (
                    <p className="mt-1 text-[11.5px] text-muted-foreground">Theo 2 số đầu số GPLX — kiểm lại, sửa được.</p>
                  )}
                </div>
              </div>
              {soCuSaiDang(b.so, soCu) && <p className="text-[12px] text-warning">Số GPLX đã lưu từ trước, sai dạng 12 số — kiểm lại khi có bằng thật; giữ nguyên vẫn lưu được.</p>}
              {loiBang(b, soCu).length > 0 && <p className="text-[12px] text-destructive">{loiBang(b, soCu).join(" · ")}</p>}
            </div>
          ))}
          <button type="button" className="btn btn-secondary btn-row mt-3" onClick={() => onDoi([...ds, bangMoi()])}>+ Thêm GPLX</button>
          {trungHangDangKy(hangKhoa, ds) && (
            <p className="mt-2 rounded-md bg-destructive/10 px-2 py-1.5 text-[12px] text-destructive">GPLX đã có không được trùng hạng đăng ký của khóa — sửa lại mới {chuLuu} được.</p>
          )}
          {duocMienLyThuyet(hangKhoa, ds) && (
            <p className="mt-2 rounded-md bg-success/10 px-2 py-1.5 text-[12px] text-success">Khóa mô tô, đã có bằng ô tô: miễn thi lý thuyết.</p>
          )}
        </>
      )}
    </div>
  );
}
