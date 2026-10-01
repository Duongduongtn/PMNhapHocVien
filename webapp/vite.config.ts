import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// App web thu thập (PWA) — build static, nginx VPS phục vụ (TDD §2.1, §2.4).
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "Thu nhận hồ sơ học viên",
        short_name: "Thu nhận HS",
        description: "App web thu thập hồ sơ học viên lái xe (quét QR + chụp ảnh)",
        lang: "vi",
        theme_color: "#1f4ea3",
        background_color: "#ffffff",
        display: "standalone",
        start_url: "/",
        icons: [
          { src: "icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any maskable" },
        ],
      },
    }),
  ],
});
