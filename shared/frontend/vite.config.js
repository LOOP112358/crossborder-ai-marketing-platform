import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// __dirname = shared/frontend/
const ROOT = path.resolve(__dirname, '../..')

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      // @ → shared/frontend/src (共享组件/store/layouts/i18n/api)
      '@': path.resolve(__dirname, 'src'),
      // @m1~@m5 → 各模块前端目录
      '@m1': path.resolve(ROOT, 'module1-auth-writing/frontend'),
      '@m2': path.resolve(ROOT, 'module2-matte/frontend'),
      '@m3': path.resolve(ROOT, 'module3-background/frontend'),
      '@m4': path.resolve(ROOT, 'module4-poster/frontend'),
      '@m5': path.resolve(ROOT, 'module5-chat/frontend'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
