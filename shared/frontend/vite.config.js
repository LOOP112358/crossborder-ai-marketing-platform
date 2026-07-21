import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

const ROOT = path.resolve(__dirname, '../..')
const NM = path.resolve(__dirname, 'node_modules')

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@m1': path.resolve(ROOT, 'module1-auth-writing/frontend'),
      '@m2': path.resolve(ROOT, 'module2-matte/frontend'),
      '@m3': path.resolve(ROOT, 'module3-background/frontend'),
      '@m4': path.resolve(ROOT, 'module4-poster/frontend'),
      '@m5': path.resolve(ROOT, 'module5-chat/frontend'),
      vue: path.resolve(NM, 'vue'),
      'vue-router': path.resolve(NM, 'vue-router'),
      pinia: path.resolve(NM, 'pinia'),
      'element-plus': path.resolve(NM, 'element-plus'),
      'vue-i18n': path.resolve(NM, 'vue-i18n'),
      axios: path.resolve(NM, 'axios'),
      '@element-plus/icons-vue': path.resolve(NM, '@element-plus/icons-vue'),
    },
    dedupe: ['vue', 'vue-router', 'pinia', 'element-plus', 'vue-i18n'],
  },
  server: {
    port: 5173,
    fs: { allow: [ROOT] },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        ws: true,
      },
      '/static': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
