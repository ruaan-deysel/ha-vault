import { defineConfig } from "vite";

function preserveLitWhitespace() {
  return {
    name: "preserve-lit-whitespace",
    generateBundle(_options: unknown, bundle: Record<string, { type: string; code?: string }>) {
      for (const file of Object.values(bundle)) {
        if (file.type === "chunk" && file.code) {
          file.code = file.code.replace(/`\[ \t\n\\f\\r\]`/g, '"[ \\t\\n\\f\\r]"');
        }
      }
    },
  };
}

export default defineConfig({
  plugins: [preserveLitWhitespace()],
  build: {
    modulePreload: false,
    outDir: "../custom_components/vault/frontend",
    emptyOutDir: true,
    target: "es2022",
    minify: true,
    sourcemap: false,
    reportCompressedSize: false,
    rollupOptions: {
      input: {
        "vault-cards": "src/index.ts",
      },
      output: {
        format: "es",
        entryFileNames: "[name].js",
        chunkFileNames: "[name]-[hash].js",
      },
    },
  },
});
