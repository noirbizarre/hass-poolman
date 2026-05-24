import { defineConfig } from "vite";
import { resolve } from "node:path";

export default defineConfig({
  build: {
    target: "es2020",
    outDir: resolve(__dirname, "../custom_components/poolman/frontend"),
    emptyOutDir: false,
    sourcemap: true,
    minify: "esbuild",
    lib: {
      entry: resolve(__dirname, "src/index.ts"),
      name: "PoolmanPoolOverviewCard",
      formats: ["es"],
      fileName: () => "poolman-pool-overview-card.js",
    },
    rollupOptions: {
      // Self-contained: bundle Lit so HA serves a single file with no externals.
      external: [],
    },
  },
  test: {
    environment: "happy-dom",
    globals: true,
    include: ["src/**/*.test.ts"],
  },
});
