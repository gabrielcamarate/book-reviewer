import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    // The design reference (tokens and brand icons) lives beside the app, in ../design.
    fs: { allow: ['..'] },
    proxy: {
      "/downloads": {
        target: `http://127.0.0.1:${process.env.REVIEW_API_PORT ?? "8766"}`,
        changeOrigin: true,
      },
      "/api": {
        target: `http://127.0.0.1:${process.env.REVIEW_API_PORT ?? "8766"}`,
        changeOrigin: true,
      },
    },
  },
})
