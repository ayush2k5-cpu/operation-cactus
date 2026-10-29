import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const backend = "127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": `http://${backend}`,
      "/ws": { target: `ws://${backend}`, ws: true },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },
});
