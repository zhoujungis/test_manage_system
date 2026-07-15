import { createApp } from 'vue'
import { createPinia } from 'pinia'
import 'element-plus/dist/index.css'
import './style.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import App from './App.vue'
import router from './router'

// F10 fix: 不再 app.use(ElementPlus) —— 现在 Element Plus 组件与 icons
// 在 Vite 编译期由 unplugin-vue-components 自动按需 import，详见 vite.config.js。
// 这里仍保留全局语言包（zhCn），避免影响 ELMessage / ElPagination 等内置组件的默认文案的本地化。

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// F16 fix: 全局错误兜底，避免组件抛错只落到 dev console。
app.config.errorHandler = (err, instance, info) => {
  // eslint-disable-next-line no-console
  console.error('[Vue error]', info, err)
  // 这里也可以接 sentry 等上报
}

app.mount('#app')
