/** @type {import('tailwindcss').Config} */
// Token đồng bộ với ui-demo (hợp đồng style đã chốt).
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ['"Be Vietnam Pro"', "system-ui", "sans-serif"] },
      colors: {
        background: "hsl(210 40% 98%)",
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
      },
      borderRadius: { lg: "0.625rem", md: "0.5rem" },
    },
  },
  plugins: [],
};
