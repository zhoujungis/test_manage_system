// i18n 配置：默认 zh-CN；从 localStorage 读取用户偏好；fallback 也用 zh-CN。
import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN.js'
import enUS from './locales/en-US.js'

const STORAGE_KEY = 'tm_locale'
const SUPPORTED_LOCALES = ['zh-CN', 'en-US']

function detectLocale() {
  const saved = typeof localStorage !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null
  if (saved && SUPPORTED_LOCALES.includes(saved)) return saved
  if (typeof navigator !== 'undefined' && navigator.language?.startsWith('en')) return 'en-US'
  return 'zh-CN'
}

export const i18n = createI18n({
  legacy: false,                // Composition API 模式
  globalInjection: true,         // 模板可用 $t
  locale: detectLocale(),
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS,
  },
})

export function setLocale(locale) {
  if (!SUPPORTED_LOCALES.includes(locale)) return
  i18n.global.locale.value = locale
  localStorage.setItem(STORAGE_KEY, locale)
  document.documentElement.lang = locale
}

export function getLocale() {
  return i18n.global.locale.value
}

export { SUPPORTED_LOCALES, STORAGE_KEY }