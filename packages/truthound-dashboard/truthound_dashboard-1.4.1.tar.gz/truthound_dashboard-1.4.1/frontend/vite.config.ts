import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { intlayer } from 'vite-intlayer'
import path from 'path'

export default defineConfig(({ command }) => ({
  plugins: [react(), intlayer()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8765',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../src/truthound_dashboard/static',
    emptyOutDir: true,
    sourcemap: false,
  },
  // Use 'public' for dev (includes mockServiceWorker.js), 'public-pip' for production build
  publicDir: command === 'serve' ? 'public' : 'public-pip',
}))
