/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ['"Be Vietnam Pro"', "system-ui", "sans-serif"] },
      colors: {
        background: "hsl(210 40% 96%)",
        foreground: "hsl(222 47% 11%)",
        card: "hsl(0 0% 100%)",
        primary: "hsl(222 76% 40%)",
        "primary-foreground": "hsl(0 0% 100%)",
        secondary: "hsl(210 40% 96%)",
        muted: "hsl(210 40% 96%)",
        "muted-foreground": "hsl(215 16% 47%)",
        accent: "hsl(224 76% 94%)",
        destructive: "hsl(0 72% 51%)",
        success: "hsl(142 71% 38%)",
        warning: "hsl(32 90% 42%)",
        border: "hsl(214 32% 91%)",
        input: "hsl(214 32% 88%)",
        ring: "hsl(222 76% 40%)",
        // Tông nhấn phân hệ Đồng bộ CDB (teal) — phân biệt phân hệ Nạp (primary xanh)
        sync: "hsl(184 65% 32%)",
        "sync-soft": "hsl(184 55% 95%)",
        "sync-border": "hsl(184 45% 80%)",
        // Tông nhấn phân hệ Kết quả đào tạo (tím) — phân biệt Nạp (primary) & Sync (teal)
        kq: "hsl(262 60% 46%)",
        "kq-soft": "hsl(262 70% 96%)",
        "kq-border": "hsl(262 50% 84%)",
        pc: "hsl(330 62% 44%)",
        "pc-soft": "hsl(330 70% 97%)",
        "pc-border": "hsl(330 50% 84%)",
        // Tông nhấn phân hệ Tốt nghiệp & Báo cáo 2 (cam đất) — theo ui-mock/tnbc2.html
        tn: "hsl(24 82% 40%)",
        "tn-soft": "hsl(24 90% 96%)",
        "tn-border": "hsl(24 70% 74%)",
      },
      borderRadius: { lg: "0.625rem", md: "0.5rem", sm: "0.375rem" },
    },
  },
  plugins: [],
};
