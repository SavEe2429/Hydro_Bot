import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  // 🎯 ตำแหน่งที่ต้องเพิ่ม: พร็อพเพอร์ตี้ 'base'
  base: '/Hydro-Bot/', // <--- เพิ่มบรรทัดนี้!
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
