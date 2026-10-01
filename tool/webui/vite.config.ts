import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Cổng 3011 đã ghi sổ ~/.claude/local-ports.md. base './' để static nhúng được vào .exe sau.
export default defineConfig({
  plugins: [react()],
  base: "./",
  server: { port: 3011, strictPort: true },
});
