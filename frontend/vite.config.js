import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import compression from 'vite-plugin-compression'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    // F10 fix: 自动按需注册 Element Plus 组件 / icon，
    // 替代原先 main.js 全量 use(ElementPlus) + 遍历注册全部 icons。
    // 这样 vendor-element chunk 从 ~1000 KB 掉到只装使用的组件。
    AutoImport({
      imports: ['vue', 'vue-router', 'pinia'],
      resolvers: [ElementPlusResolver()],
      dts: false,
    }),
    Components({
      resolvers: [
        // 默认 css：编译期注入各组件的 .css 子包；如要主题可改 'sass'（需装 sass）。
        ElementPlusResolver(),
      ],
      dts: false,
    }),
    compression({ algorithm: 'gzip', ext: '.gz', threshold: 1024 }),
    compression({ algorithm: 'brotliCompress', ext: '.br', threshold: 1024 }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3001,
    proxy: {
      '/api': 'http://localhost:8000',
      '/media': 'http://localhost:8000',
    },
  },
  build: {
    // M38 fix: target es2020 → es2022，新浏览器都支持，省下一些 polyfill
    target: 'es2022',
    // M39 fix: 把 <8KB 的资源 inline 成 data URI，省一次请求
    assetsInlineLimit: 8192,
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('element-plus') || id.includes('@element-plus')) return 'vendor-element'
            if (id.includes('vue') || id.includes('pinia') || id.includes('vue-router')) return 'vendor-vue'
            if (id.includes('axios')) return 'vendor-axios'
            return 'vendor'
          }
        },
      },
    },
  },
})
