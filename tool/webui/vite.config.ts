import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Cổng 3011 đã ghi sổ ~/.claude/local-ports.md.
// base "/" (tuyệt đối): FastAPI phục vụ dist ở GỐC cổng tool (DGT-01) và trả index.html cho mọi
// đường dẫn con (F5 / mở link sâu). Với base "./" thì /ket-qua/cap-nhat đòi /ket-qua/assets/*.js
// → server trả HTML thay JS → trắng màn hình. KHÔNG đổi lại "./" (test_dist_base chặn).
export default defineConfig({
  plugins: [react()],
  base: "/",
  server: { port: 3011, strictPort: true },
});
