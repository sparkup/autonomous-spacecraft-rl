import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: true,
    allowedHosts: [
      "autonomous-spacecraft.demo.sparcup.local",
      "autonomous-spacecraft.demo.sparkup.local",
      "autonomousspacecraft.demo.sparcup.local",
      "autonomousspacecraft.demo.sparkup.local",
      "localhost",
      "127.0.0.1"
    ]
  }
});
