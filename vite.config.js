import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    proxy: {
      "/api": {
        target: "https://tcpliage-backend.onrender.com", // Django server
        changeOrigin: true,
      },
      "/media": {
        target: "https://tcpliage-backend.onrender.com",
        changeOrigin: true,
      },
    },
  },
});
