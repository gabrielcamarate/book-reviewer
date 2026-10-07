import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync } from 'node:fs'
import path from 'node:path'

// Install as an app (PWA): the manifest and its icons come from the design reference, never copied.
const brand = path.resolve(__dirname, '../design/assets/brand')
const ICONS = [['icon-192.png', '192x192'], ['icon-512.png', '512x512']]

function manifest() {
  const tokens = JSON.parse(readFileSync(path.resolve(__dirname, '../design/tokens.json'), 'utf8'))
  const color = (name: string) => tokens.color.tokens.find((token: { name: string }) => token.name === name).value.dark
  return JSON.stringify({
    name: 'Revisor', short_name: 'Revisor', lang: 'pt-BR',
    description: 'Revisa o português do seu livro, traduz para o espanhol da América Latina e devolve dois arquivos Word.',
    start_url: '/', scope: '/', display: 'standalone', background_color: color('background'), theme_color: color('background'),
    icons: ICONS.map(([file, sizes]) => ({ src: `/assets/brand/${file}`, sizes, type: 'image/png', purpose: 'any' })),
  })
}

function installableApp(): Plugin {
  return {
    name: 'revisor-installable-app',
    configureServer(server) {
      server.middlewares.use((request, response, next) => {
        if (request.url === '/manifest.webmanifest') {
          response.setHeader('Content-Type', 'application/manifest+json'); response.end(manifest()); return
        }
        const icon = ICONS.find(([file]) => request.url === `/assets/brand/${file}`)
        if (icon) { response.setHeader('Content-Type', 'image/png'); response.end(readFileSync(path.join(brand, icon[0]))); return }
        next()
      })
    },
    generateBundle() {
      this.emitFile({ type: 'asset', fileName: 'manifest.webmanifest', source: manifest() })
      for (const [file] of ICONS) this.emitFile({ type: 'asset', fileName: `assets/brand/${file}`, source: readFileSync(path.join(brand, file)) })
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), installableApp()],
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
