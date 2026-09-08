import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    coverage: {
      provider: "v8",
      // Route components and server route handlers run in Playwright because they
      // depend on the Next.js request runtime. Unit coverage targets reusable UI
      // and client-domain modules; critical routes remain covered by E2E journeys.
      include: ["src/components/**/*.{ts,tsx}", "src/features/**/*.{ts,tsx}"],
      exclude: [
        "src/test/**",
        "src/**/*.test.*",
        "src/app/layout.tsx",
        "src/app/not-found.tsx",
        // Server-only data loaders are exercised by route E2E tests.
        "src/features/auth/session.ts",
        "src/features/intake/workspace-data.ts",
      ],
      thresholds: { statements: 80, branches: 80, functions: 80, lines: 80 },
    },
  },
});
