import { useCallback, useEffect, useState } from "react";

// HTG-08 (TDD §6.9) — chế độ sáng/tối: lần đầu theo cài đặt của máy, bấm nút thì lưu lựa chọn và thắng cài đặt máy.
export type Che = "sang" | "toi";

export const KHOA_LUU = "giao_dien";
// Màu thanh trình duyệt (theme-color) = màu đầu dải xanh thương hiệu ở từng chế độ.
export const MAU_THANH: Record<Che, string> = { sang: "#1846b3", toi: "#1c51ce" };

/** Chế độ cần dùng: lựa chọn đã lưu (nếu hợp lệ) thắng, không thì theo máy. Thuần, dễ test. */
export function chonChe(luu: string | null | undefined, mayToi: boolean): Che {
  if (luu === "sang" || luu === "toi") return luu;
  return mayToi ? "toi" : "sang";
}

function docLuu(): string | null {
  try {
    return localStorage.getItem(KHOA_LUU);
  } catch {
    return null; // chế độ riêng tư / bị chặn: vẫn chạy, chỉ không nhớ
  }
}

function mayToi(): boolean {
  return typeof matchMedia === "function" && matchMedia("(prefers-color-scheme: dark)").matches;
}

/** Áp chế độ lên trang: lớp `dark` ở <html>, màu thanh trình duyệt. */
export function apChe(che: Che): void {
  document.documentElement.classList.toggle("dark", che === "toi");
  document.querySelector('meta[name="theme-color"]')?.setAttribute("content", MAU_THANH[che]);
}

export function useGiaoDien(): { che: Che; doi: () => void } {
  const [che, setChe] = useState<Che>(() => chonChe(docLuu(), mayToi()));

  useEffect(() => { apChe(che); }, [che]);

  // Chưa có lựa chọn riêng thì đi theo máy khi người dùng đổi cài đặt máy.
  useEffect(() => {
    if (typeof matchMedia !== "function") return;
    const mq = matchMedia("(prefers-color-scheme: dark)");
    const f = () => { if (!docLuu()) setChe(mq.matches ? "toi" : "sang"); };
    mq.addEventListener("change", f);
    return () => mq.removeEventListener("change", f);
  }, []);

  const doi = useCallback(() => {
    setChe((c) => {
      const moi: Che = c === "toi" ? "sang" : "toi";
      try { localStorage.setItem(KHOA_LUU, moi); } catch { /* không nhớ được thì thôi */ }
      return moi;
    });
  }, []);

  return { che, doi };
}
