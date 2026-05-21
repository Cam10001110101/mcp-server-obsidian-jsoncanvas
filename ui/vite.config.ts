import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

// Bundle the viewer into a single self-contained HTML file (JS + CSS inlined),
// which is what lets it load inside the host's sandboxed iframe. Output goes
// straight into the Python package so it ships in the wheel.
export default defineConfig({
  plugins: [viteSingleFile()],
  build: {
    target: "es2020",
    cssMinify: true,
    minify: true,
    rollupOptions: { input: "viewer.html" },
    outDir: fileURLToPath(new URL("../jsoncanvas/_ui", import.meta.url)),
    emptyOutDir: true,
  },
});
