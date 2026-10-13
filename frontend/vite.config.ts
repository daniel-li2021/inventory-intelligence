import { defineConfig } from "vite";
export default defineConfig({
  base: "/product-static/",
  build: {
    outDir: "../src/inventory_intelligence/product_static",
    emptyOutDir: true,
    assetsDir: ".",
    target: "es2022",
  },
  server: { proxy: { "/api": "http://127.0.0.1:8765" } },
});
