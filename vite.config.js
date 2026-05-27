import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [tailwindcss(), sveltekit()],
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
