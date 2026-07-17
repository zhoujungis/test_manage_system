import { createApp } from 'vue'
import { createPinia } from 'pinia'
// H26 fix: 不再全量 import element-plus/dist/index.css —— 之前 vendor chunk
// 因为它一直背着 ~1000KB CSS，抵消了 vite.config.js 里按需加载的优化。
// 各组件 CSS 已在 Vite 编译期由 unplugin-vue-components + ElementPlusResolver()
// 自动注入。
import './style.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import App from './App.vue'
import router from './router'
import { notifyError } from '@/utils/notify'

// F10 fix: 不再 app.use(ElementPlus) —— 现在 Element Plus 组件与 icons
// 在 Vite 编译期由 unplugin-vue-components 自动按需 import，详见 vite.config.js。
// 这里仍保留全局语言包（zhCn），避免影响 ELMessage / ElPagination 等内置组件的默认文案的本地化。

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// M23 fix: 全局错误兜底 — 之前只 console.error；现在弹一个用户可见的提示。
// 这里也可以接 sentry 等上报（注释里挂 TODO）。
// TODO(observability): 接 sentry.captureException(err)
app.config.errorHandler = (err, instance, info) => {
  // eslint-disable-next-line no-console
  console.error('[Vue error]', info, err)
  // 避免重复 toast：request.js 已经处理过 axios 错误
  if (err?.name === 'CanceledError') return
  notifyError(err?.message || '页面出错了，请刷新或联系管理员')
}

// 未捕获 Promise rejection 也兜底（router guard / async setup 失败时）
window.addEventListener('unhandledrejection', (event) => {
  // eslint-disable-next-line no-console
  console.error('[unhandledrejection]', event.reason)
  if (event.reason?.name === 'CanceledError') return
  notifyError(event.reason?.message || '请求异常，请稍后重试')
})

app.mount('#app')
