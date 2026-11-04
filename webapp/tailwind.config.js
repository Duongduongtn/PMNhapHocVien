/** @type {import('tailwindcss').Config} */
// Token đồng bộ với ui-demo (hợp đồng style đã chốt). Màu đọc từ biến CSS ở src/index.css
// (kênh HSL, không kèm hsl()) để sau này thêm chế độ tối chỉ cần đổi bộ biến, không sửa từng màn.
const mau = (ten) => `hsl(var(--${ten}) / <alpha-value>)`;

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ['"Be Vietnam Pro"', "system-ui", "sans-serif"] },
      colors: {
        page: mau("page"),
        background: mau("background"),
        foreground: mau("foreground"),
        card: mau("card"),
        primary: mau("primary"),
        "primary-deep": mau("primary-deep"),
        "primary-foreground": mau("primary-foreground"),
        secondary: mau("secondary"),
        muted: mau("muted"),
        "muted-foreground": mau("muted-foreground"),
        accent: mau("accent"),
        destructive: mau("destructive"),
        success: mau("success"),
        warning: mau("warning"),
        border: mau("border"),
      },
      borderRadius: { lg: "0.625rem", md: "0.5rem" },
      // Bóng có độ lệch và độ nhòe, tông xanh đậm của màu chủ đạo (không dùng quầng sáng không lệch).
      boxShadow: {
        card: "0 1px 2px hsl(222 47% 11% / .06), 0 2px 8px -2px hsl(222 47% 11% / .06)",
        pop: "0 2px 4px hsl(222 76% 25% / .12), 0 12px 28px -8px hsl(222 76% 25% / .35)",
      },
      keyframes: {
        rise: { from: { opacity: "0", transform: "translateY(10px)" }, to: { opacity: "1", transform: "none" } },
        "quet-chay": { from: { transform: "translateY(0)" }, to: { transform: "translateY(88px)" } },
      },
      animation: {
        rise: "rise .45s cubic-bezier(.16,1,.3,1) both",
        "quet-chay": "quet-chay 2.2s cubic-bezier(.45,0,.55,1) infinite alternate",
      },
    },
  },
  plugins: [],
};
